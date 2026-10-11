"""The whole kill sheet (killsheet.kill_sheet) - what the printer and the web page show.

Nothing new is calculated in kill_sheet.py, so these tests check it collects
the right answers from the tested modules: baseline well values that match the
printed example sheets.
"""

import importlib
import sys
from pathlib import Path

import pytest

from killsheet.kill_sheet import DRILLERS, WAIT_AND_WEIGHT, kill_sheet, volumetric_sheet
from killsheet.wait_and_weight import ICP_RECALCULATED

BASELINE = dict(
    title="baseline",
    bit_tvd_ft=11_500,
    shoe_tvd_ft=5_150,
    original_mud_weight_ppg=10.4,
    lot_pressure_psi=1_350,
    test_mud_weight_ppg=9.6,
    sidpp_psi=650,
    sicp_psi=800,
    scr_pressure_psi=750,
    safety_margin_psi=50,
    pump_output_bbl_per_stk=0.117,
    drill_string=[('5" 19.5# DP', 0.0178, 10_000), ('5" HWDP', 0.0087, 900), ('6-1/2" DC', 0.0077, 600)],
    open_hole_annulus=[('DC x 8-1/2" hole', 0.0291, 600), ('HWDP x 8-1/2" hole', 0.0459, 900),
                       ('DP x 8-1/2" hole', 0.0459, 4_850)],
    cased_hole_annulus=[('DP x 9-5/8" casing', 0.0489, 5_150)],
)

VOLUMETRIC = dict(
    title="volumetric",
    original_mud_weight_ppg=10.4,
    kill_mud_weight_ppg=11.5,
    shoe_tvd_ft=5_150,
    lot_pressure_psi=1_350,
    test_mud_weight_ppg=9.6,
    sicp_psi=800,
    safety_margin_psi=100,
    working_pressure_psi=50,
    annulus_bottom_up=[('DC x 8-1/2" hole', 0.0291, 600), ('HWDP x 8-1/2" hole', 0.0459, 900),
                       ('DP x 8-1/2" hole', 0.0459, 4_850), ('DP x 9-5/8" casing', 0.0489, 5_150)],
    sicp_rises_after_each_cycle=[30, 28, 25, 22, 20, 14, 4],
    sicp_gas_at_surface_psi=1_254,
    bbl_pumped_each_cycle=[6.0, 7.0, 8.0, 9.0, 10.0, 10.0, 11.0, 11.0, 12.0, 12.0, 12.0],
    pit_gain_bbl=10,
)


def test_drillers_summary():
    sheet = kill_sheet(**BASELINE)
    assert (sheet["kill_mud_weight_ppg"], sheet["icp_psi"], sheet["fcp_psi"]) == (11.5, 1400, 829)
    assert (sheet["max_allowable_mud_weight_ppg"], sheet["maasp_original_psi"], sheet["maasp_after_kill_psi"]) \
        == (14.6, 1124, 830)
    assert (sheet["surface_to_bit_strokes"], sheet["bit_to_shoe_strokes"], sheet["bit_to_surface_strokes"]) \
        == (1627, 2405, 4557)
    assert sheet["method"] == DRILLERS
    assert sheet["schedule"] is None                        # Driller's has no step-down chart


def test_depth_tables():
    sheet = kill_sheet(**BASELINE)
    assert [(r["name"], r["md_ft"], r["strokes"]) for r in sheet["string_depths"]] == [
        ('bottom of 5" 19.5# DP', 10_000, 1521), ('bottom of 5" HWDP', 10_900, 1588), ("bit", 11_500, 1627),
    ]
    assert [(r["name"], r["md_ft"], r["strokes"]) for r in sheet["annulus_depths"]] == [
        ('top of DC x 8-1/2" hole', 10_900, 150), ('top of HWDP x 8-1/2" hole', 10_000, 503),
        ('shoe / top of DP x 8-1/2" hole', 5_150, 2405), ("surface", 0, 4557),
    ]


def test_drillers_steps():
    steps = kill_sheet(**BASELINE)["steps"]
    assert [step["hold_psi"] for step in steps] == [850, 1450, None, 700, 700, 700, 871, None, 42, None, 0, None]


def test_wait_and_weight_schedule():
    sheet = kill_sheet(**BASELINE, method=WAIT_AND_WEIGHT)
    schedule = sheet["schedule"]
    assert (schedule[0]["strokes"], schedule[0]["pressure_psi"], schedule[0]["pressure_plus_sf_psi"]) == (0, 1400, 1450)
    assert [(r["strokes"], r["pressure_plus_sf_psi"], r["label"]) for r in schedule[-3:]] == [
        (1521, 954, "crossover"), (1588, 909, "crossover"), (1627, 879, "bit"),
    ]
    assert sheet["icp_check"] is None                       # no reading yet
    assert sheet["steps"][-4]["hold_psi"] == 50              # trapped = SF


def test_wait_and_weight_high_icp_reading_recalculates():
    sheet = kill_sheet(**BASELINE, method=WAIT_AND_WEIGHT, sidpp_at_start_psi=680, sicp_at_start_psi=830,
                       observed_icp_psi=1470)
    check = sheet["icp_check"]
    assert (check["icp_plus_sf_psi"], check["observed_psi"], check["status"]) == (1450, 1470, ICP_RECALCULATED)
    assert "ICP 1,420 psi, FCP 829 psi" in check["message"]
    assert sheet["steps"][-4]["hold_psi"] == 61              # 50 + 829 - 818


def test_unknown_method_is_refused():
    with pytest.raises(ValueError):
        kill_sheet(**BASELINE, method="bullhead")


def test_volumetric_sheet():
    # The pre-v1.3 example readings: gas at surface after cycle 7 - earlier than the forecast
    sheet = volumetric_sheet(**VOLUMETRIC)
    assert (sheet["mud_gradient_psi_per_ft"], sheet["kill_mud_gradient_psi_per_ft"], sheet["maasp_psi"]) \
        == (0.5408, 0.598, 1124)
    assert [(c["choice"], c["bleed_bbl"], c["used"]) for c in sheet["capacity_choices"]] == [
        ("smallest annulus", 2.6, False), ("average annulus", 4.2, False), ("longest annulus", 4.5, False),
    ]                                                       # the default is the annulus at the gas
    assert [row["hold_psi"] for row in sheet["volumetric"]] == [950, 1000, 1050, 1100, 1150, 1200, 1250]
    assert [row["bleed_bbl"] for row in sheet["volumetric"]] == [2.6, 4.2, 4.2, 4.5, 4.5, 4.5, 4.5]
    assert sheet["volumetric"][-1]["gas_at_surface"] is True
    assert sheet["readings_gas_at_surface_bbl"] == 29.0
    assert sheet["arrival_warning"].startswith("Readings show gas at surface at 29.0 bbl bled; the single-bubble "
                                               "model predicts 38.8 bbl")
    assert sheet["stopping_volume_bbl"] == 39.0             # pit gain 10 + 29.0 bled (the readings)
    assert sheet["kop_md_ft"] is None                       # vertical: no KOP check


def test_kill_plot_on_the_sheet_drillers():
    # The user-approved hand example: 10 bbl kick, SF 50
    plot = kill_sheet(**BASELINE, pit_gain_bbl=10)["plot"]
    assert (plot["peak_casing"]["casing_psi"], plot["peak_casing"]["gas_volume_bbl"]) == (1272, 53.6)
    assert plot["max_shoe"]["shoe_psi"] == 3681
    assert (plot["fracture_at_shoe_psi"], plot["maasp_psi"]) == (3909, 1124)
    assert (plot["trapped_drill_pipe_psi"], plot["trapped_casing_psi"]) == (42, 42)
    assert plot["points"][0] == {"strokes": 0, "drill_pipe_psi": 650, "casing_psi": 800,
                                 "gas_volume_bbl": 10, "label": "shut in"}
    assert "Single-bubble gas model" in plot["model_limits"]


def test_kill_plot_on_the_sheet_wait_and_weight():
    plot = kill_sheet(**BASELINE, method=WAIT_AND_WEIGHT, pit_gain_bbl=10)["plot"]
    assert (plot["peak_casing"]["casing_psi"], plot["max_shoe"]["shoe_psi"]) == (1048, 3648)
    assert (plot["trapped_drill_pipe_psi"], plot["trapped_casing_psi"]) == (50, 50)
    assert plot["warnings"] == []


def test_kill_plot_high_icp_uses_the_recalculated_pressures():
    plot = kill_sheet(**BASELINE, method=WAIT_AND_WEIGHT, sidpp_at_start_psi=680, sicp_at_start_psi=830,
                      observed_icp_psi=1470, pit_gain_bbl=10)["plot"]
    assert plot["points"][2]["drill_pipe_psi"] == 1470          # at kill rate: recalculated ICP + SF
    assert (plot["trapped_drill_pipe_psi"], plot["trapped_casing_psi"]) == (61, 61)


def test_no_pit_gain_no_plot():
    assert kill_sheet(**BASELINE)["plot"] == {"unavailable": "Enter the pit gain to forecast the kill plot."}


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "examples"))


def example(name, **changes):
    return kill_sheet(**dict(importlib.import_module(name).WELL, **changes))


def test_deviated_plot_user_approved_hand_example():
    # 30 deg tangent: influx 344 ft MD = 298 ft TVD; SICP 780 -> gradient 0.5408 - 130 / 298 = 0.1046
    plot = example("deviated_well")["plot"]
    assert (plot["peak_casing"]["casing_psi"], plot["peak_casing"]["gas_volume_bbl"]) == (1272, 53.7)
    assert abs(plot["peak_casing"]["strokes"] - 4580) <= 10
    assert plot["max_shoe"]["shoe_psi"] == 3656                 # top of gas at the shoe
    assert abs(plot["max_shoe"]["strokes"] - 2631) <= 30
    assert (plot["trapped_drill_pipe_psi"], plot["trapped_casing_psi"]) == (42, 42)
    assert plot["casing_forecast_valid"] and plot["notes"] == []


def test_deviated_gauges_copied_from_the_vertical_well_are_not_physical():
    # SICP 800 over 298 ft TVD: 0.5408 - 150 / 298 = 0.0374 psi/ft
    warnings = example("deviated_well", sicp_psi=800)["plot"]["warnings"]
    assert any("0.0374 psi/ft. Influx gradient below 0.05 psi/ft is not physical. "
               "Check SICP/SIDPP and the influx volume." in w for w in warnings)


def test_horizontal_casing_flat_until_the_gas_leaves_the_lateral():
    plot = example("horizontal_well")["plot"]
    assert plot["notes"] == ["Influx in the lateral: gas gradient 0.1 psi/ft assumed (can't be read from the "
                             "gauges; conservative, over-predicts casing and shoe pressure)."]
    leaves = next(p for p in plot["points"] if p["label"].startswith("top of gas leaves the lateral"))
    assert abs(leaves["strokes"] - 1792) <= 10
    flat = [p["casing_psi"] for p in plot["points"] if 0 < p["strokes"] <= leaves["strokes"]]
    assert set(flat) <= {700, 701}                              # SIDPP + SF: no change while in the lateral
    assert (plot["peak_casing"]["casing_psi"], plot["peak_casing"]["gas_volume_bbl"]) == (1211, 48.0)
    assert plot["max_shoe"]["shoe_psi"] == 5877                  # shoe at the heel: shoe = BHP
    assert (plot["trapped_drill_pipe_psi"], plot["trapped_casing_psi"]) == (3, 3)   # 650 + 50 - 697


def test_horizontal_sicp_above_sidpp_casing_forecast_does_not_apply():
    plot = example("horizontal_well", sicp_psi=700)["plot"]
    assert plot["casing_forecast_valid"] is False
    assert any("With the influx in the lateral, SICP should read the same as SIDPP (+/-10 psi). "
               "SICP is 50 psi higher." in w and "Use the drill pipe schedule only." in w for w in plot["warnings"])
    assert not any("MAASP" in w for w in plot["warnings"])      # no peak / shoe checks on an invalid forecast


def test_horizontal_sicp_within_10_psi_is_fine():
    assert example("horizontal_well", sicp_psi=660)["plot"]["casing_forecast_valid"] is True


def test_wait_and_weight_kill_mud_rounding_note():
    assert example("wait_and_weight_horizontal_well")["kill_mud_rounding_note"] == (
        "Kill mud rounding (11.706 -> 11.8 ppg) adds 47 psi to BHP during the step-down.")
    assert kill_sheet(**BASELINE, method=WAIT_AND_WEIGHT)["kill_mud_rounding_note"] == (
        "Kill mud rounding (11.487 -> 11.5 ppg) adds 8 psi to BHP during the step-down.")
    assert kill_sheet(**BASELINE)["kill_mud_rounding_note"] is None      # Driller's: no step-down


def test_wait_and_weight_horizontal_shoe_margin_less_than_drillers():
    plot = example("wait_and_weight_horizontal_well")["plot"]
    assert (plot["fracture_at_shoe_psi"], plot["max_shoe"]["shoe_psi"]) == (5973, 5925)       # margin 48
    assert ("W&W shoe margin 48 psi is less than Driller's 96 psi because of kill mud rounding. "
            "Consider a smaller SF, a finer KMW rounding, or Driller's method.") in plot["warnings"]


def test_wait_and_weight_vertical_shoe_margin_better_than_drillers_no_warning():
    plot = kill_sheet(**BASELINE, method=WAIT_AND_WEIGHT, pit_gain_bbl=10)["plot"]
    assert not any("shoe margin" in w for w in plot["warnings"])     # W&W 261 vs Driller's 228


def test_pit_gain_must_be_more_than_0():
    with pytest.raises(ValueError, match="Pit gain"):
        kill_sheet(**BASELINE, pit_gain_bbl=0)


def test_volumes_page_1():
    # Each volume = sum of rounded section volumes; strokes = volume / 0.117
    volumes = [(v["name"], v["volume_bbl"], v["strokes"]) for v in kill_sheet(**BASELINE)["volumes"]]
    assert volumes == [
        ("Surface to bit", 190.4, 1627),                         # 178.0 + 7.8 + 4.6
        ("Open hole annulus (bit to shoe)", 281.4, 2405),        # 17.5 + 41.3 + 222.6
        ("Cased hole annulus (shoe to surface)", 251.8, 2152),   # 0.0489 x 5,150
        ("Total annulus (bit to surface)", 533.2, 4557),
        ("Total well system", 723.6, 6185),                      # 723.6 / 0.117 = 6,184.6 (not 1,627 + 4,557)
    ]


def test_volumes_with_surface_lines():
    volumes = {v["name"]: (v["volume_bbl"], v["strokes"])
               for v in kill_sheet(**BASELINE, surface_line_volume_bbl=5.0)["volumes"]}
    assert volumes["Surface lines"] == (5.0, 43)                 # 5.0 / 0.117 = 42.7
    assert volumes["Drill string"] == (190.4, 1627)
    assert volumes["Surface to bit"] == (195.4, 1670)


def test_schematic_sections():
    schematic = kill_sheet(**BASELINE)["schematic"]
    assert [(r["name"], r["top_md_ft"], r["bottom_md_ft"], r["volume_bbl"]) for r in schematic["string"]] == [
        ('5" 19.5# DP', 0, 10_000, 178.0), ('5" HWDP', 10_000, 10_900, 7.8), ('6-1/2" DC', 10_900, 11_500, 4.6),
    ]
    assert [(r["top_md_ft"], r["bottom_md_ft"]) for r in schematic["annulus"]] == [
        (10_900, 11_500), (10_000, 10_900), (5_150, 10_000), (0, 5_150),           # bit up
    ]
    assert (schematic["shoe_md_ft"], schematic["bit_md_ft"], schematic["key_points"]) == (5_150, 11_500, [])
