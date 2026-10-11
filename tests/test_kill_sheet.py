"""The whole kill sheet (killsheet.kill_sheet) - what the printer and the web page show.

Nothing new is calculated in kill_sheet.py, so these tests check it collects
the right answers from the tested modules: baseline well values that match the
printed example sheets.
"""

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
    sheet = volumetric_sheet(**VOLUMETRIC)
    assert (sheet["mud_gradient_psi_per_ft"], sheet["kill_mud_gradient_psi_per_ft"], sheet["maasp_psi"]) \
        == (0.5408, 0.598, 1124)
    assert [(c["choice"], c["bleed_bbl"], c["used"]) for c in sheet["capacity_choices"]] == [
        ("smallest annulus", 2.6, True), ("average annulus", 4.2, False), ("longest annulus", 4.5, False),
    ]
    assert sheet["first_hold_psi"] == 950
    assert [row["hold_psi"] for row in sheet["volumetric"]] == [950, 1000, 1050, 1100, 1150, 1200, 1250]
    assert sheet["volumetric"][-1]["gas_at_surface"] is True
    assert sheet["lubricate_and_bleed"][-1]["bleed_to_psi"] == 0
    assert sheet["kop_md_ft"] is None                        # vertical: no KOP check


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


def test_deviated_well_plot_is_coming_later():
    deviated = dict(BASELINE, bit_md_ft=12_000, drill_string=[("DP", 0.0178, 10_500), ("HWDP", 0.0087, 900),
                    ("DC", 0.0077, 600)], open_hole_annulus=[("DC", 0.0291, 600), ("HWDP", 0.0459, 900),
                    ("DP", 0.0459, 5_350)], key_points=[("KOP", 3_000, 3_000)])
    assert "coming in a later release" in kill_sheet(**deviated, pit_gain_bbl=10)["plot"]["unavailable"]


def test_pit_gain_must_be_more_than_0():
    with pytest.raises(ValueError, match="Pit gain"):
        kill_sheet(**BASELINE, pit_gain_bbl=0)
