"""The volumetric forecast (killsheet/volumetric_model.py) - user-approved v1.3.

1. Every case is checked against the independent reference model
   (tests/reference_model.py, reference_volumetric) cycle by cycle: hold, correction,
   tier, annulus, bleed, gas position, lowest BHP, highest shoe, decisions, gas at surface.
2. The numbers worked through with the user are asserted exactly.
3. Every warning that should fire is asserted word for word - and the cases where
   none should fire are asserted quiet.
"""

import importlib
import sys
from pathlib import Path

import pytest

from killsheet.formulas import max_allowable_mud_weight
from killsheet.kill_plot import fracture_at_shoe
from killsheet.kill_sheet import volumetric_sheet
from killsheet.lubricate_and_bleed import (
    end_of_lubricate_and_bleed,
    lubricate_and_bleed_to_volume,
    remaining_underbalance,
)
from killsheet.volumetric import mud_gradient
from killsheet.volumetric_model import (
    TIER_SF_REDUCED,
    TIER_STANDARD,
    TIER_SUPERVISOR,
    Annulus,
    VolumetricModel,
    arrival_warning,
    correction_note,
    influx_at_shut_in,
    maasp_label,
    precheck_warning,
    tier_warning,
)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "examples"))
from reference_model import reference_volumetric  # noqa: E402


def example(name, **changes):
    return dict(importlib.import_module(f"volumetric_{name}_well").WELL, **changes)


# Every example, the other horizontal settings, and the tier-4 fixture (low leak-off).
CASES = {
    "on_bottom": example("pipe_on_bottom"),
    "on_bottom_no_float": example("pipe_on_bottom_no_float"),
    "tapered_on_bottom": example("tapered_pipe_on_bottom"),
    "tapered_shoe_at_risk": example("tapered_shoe_at_risk"),
    "deviated": example("deviated"),
    "deviated_tapered": example("deviated_tapered"),
    "horizontal_100_50": example("horizontal"),
    "horizontal_50_50": example("horizontal", safety_margin_psi=50),
    "horizontal_75_25": example("horizontal", safety_margin_psi=75, working_pressure_psi=25),
    "horizontal_tapered": example("horizontal_tapered"),
    "above_influx": example("pipe_above_influx"),
    "out_of_hole": example("pipe_out_of_hole"),
    "tapered_above_influx": example("tapered_pipe_above_influx"),
    "tapered_out_of_hole": example("tapered_pipe_out_of_hole"),
    "tier4_fixture": example("tapered_shoe_at_risk", lot_pressure_psi=1_000),
    "horizontal_shoe_margin_50": example("horizontal", shoe_margin_psi=50),
}


def forecast(well):
    sections = [(c, l) for _n, c, l in well["annulus_bottom_up"]]
    td_md = well.get("td_md_ft") or sum(l for _c, l in sections)
    annulus = Annulus(sections, td_md, well.get("td_tvd_ft") or td_md, well.get("shoe_md_ft") or well["shoe_tvd_ft"],
                      well["shoe_tvd_ft"], well.get("key_points", ()))
    mud = mud_gradient(well["original_mud_weight_ppg"])
    influx = influx_at_shut_in(annulus, well["pit_gain_bbl"], well["sicp_psi"], well.get("sidpp_psi"), mud)
    mamw = max_allowable_mud_weight(well["lot_pressure_psi"], well["shoe_tvd_ft"], well["test_mud_weight_ppg"])
    model = VolumetricModel(annulus, influx, mud, well["sicp_psi"], well["safety_margin_psi"],
                            well["working_pressure_psi"], fracture_at_shoe(mamw, well["shoe_tvd_ft"]),
                            well["pit_gain_bbl"], shoe_margin_psi=well.get("shoe_margin_psi", 0))
    return influx, *model.forecast()


@pytest.fixture(scope="module", params=list(CASES))
def case(request):
    well = CASES[request.param]
    return request.param, forecast(well), reference_volumetric(well)


# --- 1. Against the reference model -----------------------------------------------

def test_forecast_matches_the_reference_cycle_by_cycle(case):
    name, (influx, rows, _surface), ref = case
    assert (influx.formation_psi, influx.pf_estimated, influx.height_md_ft, influx.height_tvd_ft,
            influx.gradient_psi_per_ft) == (ref["pf"], ref["pf_estimated"], ref["influx_md"], ref["influx_tvd"],
                                            ref["gradient"]), name
    mine = [(r.cycle, r.standard_hold_psi, r.hold_psi, r.correction_psi, r.tier, r.capacity_bbl_per_ft, r.bleed_bbl,
             r.total_bled_bbl, r.gas_top_tvd_ft, r.gas_below_shoe, r.lowest_bhp_vs_pf_psi, r.highest_shoe_psi,
             tuple(r.decision) if r.decision else None) for r in rows]
    theirs = [(c["cycle"], c["standard"], c["hold"], c["correction"], c["tier"], c["capacity"], c["bleed"], c["total"],
               c["gas_top_tvd"], c["gas_below_shoe"], c["low_bhp_vs_pf"], c["high_shoe"],
               tuple(c["decision"].values()) if c["decision"] else None) for c in ref["cycles"]]
    assert mine == theirs, name


def test_gas_at_surface_matches_the_reference(case):
    name, (_influx, _rows, surface), ref = case
    s = ref["surface"]
    assert tuple(surface) == (s["cycle"], s["during"], s["casing"], s["bled"], s["volume"]), name


# --- 2. The numbers worked through with the user -------------------------------------

def test_baseline_hand_example():
    influx, rows, surface = forecast(CASES["on_bottom"])
    assert (influx.formation_psi, influx.height_md_ft, influx.gradient_psi_per_ft) == (6868, 344, 0.1)
    assert [(r.capacity_bbl_per_ft, r.bleed_bbl) for r in rows[:4]] == [
        (0.0291, 2.6), (0.0459, 4.2), (0.0459, 4.2), (0.0489, 4.5)]          # the annulus at the gas
    assert [r.hold_psi for r in rows] == [950 + 50 * n for n in range(10)]   # no correction needed
    assert {r.tier for r in rows} == {TIER_STANDARD}
    assert tuple(surface) == (10, "bleed", 1400, 38.8, 48.8)                # Boyle: 68,336 / 1,400
    assert max(r.highest_shoe_psi for r in rows) == 3835                    # 74 psi under fracture 3,909


def test_horizontal_100_50_is_limited_by_the_shoe_every_cycle():
    _i, rows, _s = forecast(CASES["horizontal_100_50"])
    assert [r.tier for r in rows] == [TIER_SF_REDUCED] * 8
    assert [r.lowest_bhp_vs_pf_psi for r in rows] == [67, 96, 96, 95, 95, 96, 96, 95]   # effective SF
    assert (rows[0].hold_psi, rows[0].correction_psi) == (853, 87)
    assert max(r.highest_shoe_psi for r in rows) == 5973                                 # held at fracture


@pytest.mark.parametrize("name, sf, raise_psi", [("horizontal_50_50", 50, 87), ("horizontal_75_25", 75, 89)])
def test_horizontal_smaller_sf_holds_pf_plus_sf_with_no_warning(name, sf, raise_psi):
    _i, rows, _s = forecast(CASES[name])
    assert rows[0].correction_psi == raise_psi                     # the build, corrected up front
    assert min(r.lowest_bhp_vs_pf_psi for r in rows) >= sf
    assert all(r.tier in (0, 1) for r in rows)


def test_shoe_at_risk_reaches_a_supervisor_decision():
    _i, rows, _s = forecast(CASES["tapered_shoe_at_risk"])
    assert [r.tier for r in rows[:4]] == [TIER_SF_REDUCED, TIER_SUPERVISOR, 1, 1]
    assert rows[0].hold_psi == 888 and rows[0].lowest_bhp_vs_pf_psi == 5          # SF 50 reduced to 5
    assert tuple(rows[1].decision) == (940, 51, 14, 888, -2)


def test_tier_4_fixture_low_leak_off():
    # LOT 1,000 psi: MAASP 790 < SICP 885 - the shoe is over fracture at shut-in
    _i, rows, _s = forecast(CASES["tier4_fixture"])
    assert rows[0].tier == TIER_SUPERVISOR
    assert tuple(rows[0].decision) == (985, 130, 195, 790, -80)
    assert tier_warning(rows[0], 50) == (
        "SUPERVISOR DECISION, cycle 1: hold 985 psi keeps BHP >= Pf + 130 but puts the shoe 195 psi over "
        "fracture. Hold 790 psi keeps the shoe at fracture but BHP 80 psi under Pf (influx). "
        "Constant-BHP doctrine favors 985.")


def test_narrowing_annulus_correction():
    # Tapered swab: the gas enters the 0.0140 annulus - the hold is raised up front
    _i, rows, _s = forecast(CASES["tapered_above_influx"])
    assert [(r.cycle, r.correction_psi) for r in rows if r.correction_psi] == [(2, 55)]
    assert min(r.lowest_bhp_vs_pf_psi for r in rows) >= 50


# --- 3. Wording - fires when it should, quiet when it shouldn't ----------------------

def test_precheck():
    assert precheck_warning(650, 100, 50, 796) == (
        "Shoe margin 146 psi is less than SF + Pw 150. Volumetric with these margins will exceed fracture. "
        "Reduce SF/Pw or consider bullheading.")
    assert precheck_warning(650, 50, 50, 796) is None
    assert precheck_warning(800, 100, 50, 1124) is None


def test_tier_3_wording():
    _i, rows, _s = forecast(CASES["horizontal_100_50"])
    assert tier_warning(rows[0], 100) == ("Cycle 1: hold limited by the shoe. SF reduced from 100 to 67 psi. "
                                          "BHP still above Pf.")
    _i, quiet, _s = forecast(CASES["horizontal_50_50"])
    assert {tier_warning(r, 50) for r in quiet} == {None}


def test_correction_and_maasp_wording():
    assert correction_note(87) == ("+87 psi: gas will gain vertical height during this bleed "
                                   "(narrower annulus / build section).")
    assert maasp_label(1150, 1124, True) == "ABOVE MAASP, gas below shoe, shoe overpressured"
    assert maasp_label(1150, 1124, False) == "above MAASP, gas above shoe, MAASP no longer applies, continue"
    assert maasp_label(1100, 1124, True) is None


def test_arrival_warning_20_percent():
    assert arrival_warning(38.8, 38.8) is None
    assert arrival_warning(31.1, 38.8) is None                      # 19.8% early: quiet
    assert arrival_warning(29.0, 38.8, 1351) == (
        "Readings show gas at surface at 29.0 bbl bled; the single-bubble model predicts 38.8 bbl (gas top at "
        "1,351 ft). Gas arriving early is common (dispersed or breaking out of solution). Check the pit gain and "
        "readings. L&B volumes follow the readings.")
    assert arrival_warning(50.0, 38.8).startswith("Readings show gas at surface at 50.0 bbl bled; the model "
                                                  "predicts 38.8 bbl. Gas arriving late")


@pytest.mark.parametrize("name", ["on_bottom", "on_bottom_no_float", "tapered_on_bottom", "deviated",
                                  "deviated_tapered", "out_of_hole", "tapered_out_of_hole"])
def test_quiet_examples(name):
    sheet = volumetric_sheet(**CASES[name])
    assert sheet["precheck"] is None and sheet["arrival_warning"] is None
    assert not any(row["warning"] for row in sheet["volumetric"])


def test_early_gas_on_the_sheet():
    # The crew sees gas at surface after cycle 7 (29.0 bbl) - the model says 38.8
    well = dict(CASES["on_bottom"], sicp_rises_after_each_cycle=[30, 28, 26, 24, 22, 20, 8])
    assert volumetric_sheet(**well)["arrival_warning"].startswith(
        "Readings show gas at surface at 29.0 bbl bled; the single-bubble model predicts 38.8 bbl")


# --- The sheet: lubricate and bleed and the end state --------------------------------

def test_lubricate_and_bleed_stops_at_the_gas_volume():
    rows = lubricate_and_bleed_to_volume(1400, 50, [5.0, 5.0, 5.0], 0.5980, 0.0489, 12.3)
    assert [(r.pump_to_psi, r.bbl_pumped, r.hydrostatic_added_psi, r.bleed_to_psi) for r in rows] == [
        (1450, 5.0, 61, 1339), (1389, 5.0, 61, 1278), (1328, 2.3, 28, 1250)]   # last cycle: only what is left


def test_remaining_underbalance_worked_by_hand():
    # 48.8 bbl / 0.0489 = 998 ft of 11.5 ppg; 0.5980 x 998 + 0.5408 x 10,502 = 6,276 -> 6,868 - 6,276 = 592
    assert remaining_underbalance(6868, 48.8, 0.5980, 0.5408, 11_500, 0.0489, lambda md: round(md)) == 592


def test_end_messages():
    assert end_of_lubricate_and_bleed(839, 592, 100) == (
        "Casing 839 psi. Remaining underbalance 592 psi. Do not bleed casing below 692 psi. Not dead. "
        "Kill required (strip to bottom and circulate, or bullhead).")
    assert end_of_lubricate_and_bleed(218, 0, 100) == (
        "Hydrostatic control regained. Casing 218 psi is trapped pressure. Bleed off in small increments, "
        "check 0, flow check, then strip to bottom and circulate.")


@pytest.mark.parametrize("name, stop, cycles, casing, under", [
    ("on_bottom", 48.8, 87, 839, 592),
    ("tapered_shoe_at_risk", 33.9, 82, 599, 512),
    ("horizontal_100_50", 45.7, 78, 731, 582),
    ("above_influx", 66.4, 44, 218, 0),
    ("out_of_hole", 83.1, 35, 154, 0),
])
def test_example_end_states(name, stop, cycles, casing, under):
    sheet = volumetric_sheet(**CASES[name])
    assert (sheet["stopping_volume_bbl"], len(sheet["lubricate_and_bleed"]), sheet["end_casing_psi"],
            sheet["remaining_underbalance_psi"]) == (stop, cycles, casing, under)
    assert sheet["lubricated_bbl"] == stop


def test_horizontal_sheet_notes():
    notes = volumetric_sheet(**CASES["horizontal_100_50"])["notes"]
    assert ("Gas lying in the lateral may not migrate, so casing can stay flat for a long time. Volumetric steps "
            "start when casing begins to rise.") in notes
    assert ("Shoe at the heel: shoe pressure = BHP. Kick tolerance is very small. If the pre-check fires, consider "
            "bullheading before volumetric.") in notes


def test_no_float_sheet_says_the_string_must_be_open():
    sheet = volumetric_sheet(**CASES["on_bottom_no_float"])
    assert sheet["influx"]["pf_note"] == "from SIDPP 650 psi"
    assert "Drill pipe pressure method valid only if the string is open." in sheet["pipe_note"]
    assert sheet["plot"]["drill_pipe_label"] is None                 # the drill pipe line is drawn


def test_plot_layers():
    plot = volumetric_sheet(**CASES["tapered_shoe_at_risk"])["plot"]["volumetric"]
    kinds = [a["kind"] for a in plot["annotations"]]
    assert "supervisor" in kinds and "shoe" in kinds and "correction" in kinds and "shoe passed" in kinds
    first = plot["points"][1]
    assert (first["casing_psi"], first["standard_psi"]) == (888, 985)      # hold to use vs standard


def test_horizontal_bubble_path_starts_at_the_heel():
    # The bubble lies at the heel - the path rule must not reach back to the DC annulus at the bit
    _i, rows, _s = forecast(CASES["horizontal_50_50"])
    assert (rows[0].capacity_bbl_per_ft, rows[0].bleed_bbl) == (0.0459, 4.2)


def test_standard_is_re_based_after_a_shoe_limited_cycle():
    _i, rows, _s = forecast(CASES["tapered_shoe_at_risk"])
    assert [(r.standard_hold_psi, r.hold_psi, r.correction_psi, r.tier) for r in rows[:5]] == [
        (985, 888, 0, 3),          # limited by the shoe
        (938, 940, 2, 4),          # re-based: 888 + 50
        (990, 1043, 53, 1),        # re-based: 940 + 50 - the correction now sits on its own column
        (1040, 1244, 151, 1),
        (1090, 1294, 0, 0)]
    assert all(r.hold_psi >= r.standard_hold_psi for r in rows if r.tier in (0, 1))
    sheet = volumetric_sheet(**CASES["tapered_shoe_at_risk"])
    assert sheet["volumetric"][2]["reasons"][0] == ("Standard re-based after shoe-limited cycle 2: previous hold "
                                                   "used + Pw.")
    assert sheet["tiers"].startswith("Tier 0: standard hold, no correction.")


def test_shoe_margin_50():
    # Horizontal 100/50 with a 50 psi margin below fracture: shoe limit 5,923
    _i, rows, _s = forecast(CASES["horizontal_shoe_margin_50"])
    assert {r.tier for r in rows} == {TIER_SF_REDUCED}
    assert max(r.highest_shoe_psi for r in rows) == 5923
    assert [r.lowest_bhp_vs_pf_psi for r in rows] == [17, 46, 46, 45, 46, 45, 46, 45, 78]
    assert precheck_warning(650, 100, 50, 796, 50) == (
        "Shoe margin 96 psi is less than SF + Pw 150. Volumetric with these margins will exceed fracture. "
        "Reduce SF/Pw or consider bullheading.")
    assert precheck_warning(650, 25, 25, 796, 50) is None


def test_shoe_margin_wording_in_a_supervisor_decision():
    _i, rows, _s = forecast(dict(CASES["tier4_fixture"], shoe_margin_psi=50))
    first = next(r for r in rows if r.tier == TIER_SUPERVISOR)
    assert "over the shoe limit (fracture - 50 psi)" in tier_warning(first, 50, 50)
    assert "keeps the shoe at the shoe limit (fracture - 50 psi)" in tier_warning(first, 50, 50)

