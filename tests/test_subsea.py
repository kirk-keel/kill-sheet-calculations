"""Tests for subsea well control calculations (choke line friction, dynamic MAASP, riser margin)."""

import pytest

from killsheet.subsea import (
    choke_line_capacity,
    choke_line_strokes,
    choke_line_volume,
    choke_pressure_bringing_pump_up,
    dynamic_maasp,
    riser_disconnect_bhp,
    riser_margin_mud_weight,
    subsea_kill_summary,
)


def test_choke_line_capacity_and_volume():
    # 3.0" ID choke line, 1,650 ft long
    cap = choke_line_capacity(3.0)
    assert round(cap, 6) == round(9 / 1029.4, 6)

    # 1650 x (9 / 1029.4) = 14.4258 -> rounds to 14.4 bbl
    vol = choke_line_volume(3.0, 1650)
    assert vol == 14.4

    # 14.4 / 0.102 = 141.17 -> 141 strokes
    assert choke_line_strokes(vol, 0.102) == 141


def test_dynamic_maasp_and_choke_pressure():
    # Static MAASP 936 psi, CLF 250 psi
    assert dynamic_maasp(936, 250) == 686

    # When CLF exceeds static MAASP, dynamic MAASP is 0 (cannot be negative)
    assert dynamic_maasp(200, 250) == 0

    # Choke pressure bringing pump up: SICP 700 - CLF 250 = 450 psi
    assert choke_pressure_bringing_pump_up(700, 250) == 450

    # If CLF exceeds SICP, choke is held fully open (0 psi)
    assert choke_pressure_bringing_pump_up(200, 250) == 0


def test_riser_margin_and_disconnect_bhp():
    # TVD 10,000 ft, OMW 12.0 ppg, Water depth 1,500 ft, Air gap 75 ft
    # Subsea TVD = 8,425 ft
    # Mud hydrostatic total = 6,240 psi, Seawater hydro = 666.9 psi
    # Mud weight needed = 5,573.1 / (0.052 x 8,425) = 12.72 ppg -> rounds up to 12.8 ppg
    mw_rm = riser_margin_mud_weight(12.0, 10_000, 1_500, air_gap_ft=75, seawater_density_ppg=8.55)
    assert mw_rm == 12.8

    # Post-disconnect BHP: 666.9 + 0.052 x 12.0 x 8,425 = 5,924.1 -> 5,924 psi
    bhp = riser_disconnect_bhp(12.0, 10_000, 1_500, air_gap_ft=75, seawater_density_ppg=8.55)
    assert bhp == 5924


def test_subsea_kill_summary_comprehensive():
    summary = subsea_kill_summary(
        original_mud_weight_ppg=12.0,
        tvd_ft=10_000,
        shoe_tvd_ft=6_000,
        lot_emw_ppg=15.0,
        sidpp_psi=500,
        sicp_psi=700,
        scr_pressure_psi=750,
        pump_output_bbl_per_stk=0.102,
        choke_line_id_in=3.0,
        choke_line_length_ft=1_650,
        clf_psi=250,
        water_depth_ft=1_500,
        air_gap_ft=75,
    )
    assert summary["kill_mud_weight_ppg"] == 13.0  # 12.0 + 500 / 520 = 12.96 -> 13.0
    assert summary["choke_line_volume_bbl"] == 14.4
    assert summary["choke_line_strokes"] == 141
    assert summary["static_maasp_psi"] == 936
    assert summary["dynamic_maasp_psi"] == 686
    assert summary["choke_pressure_at_kill_rate_psi"] == 450
    assert summary["riser_margin_mud_weight_ppg"] == 12.8
    assert summary["post_disconnect_bhp_psi"] == 5924


def test_subsea_input_validation():
    with pytest.raises(ValueError, match="Choke line ID must be greater than 0"):
        choke_line_capacity(0)

    with pytest.raises(ValueError, match="Choke line length must be greater than 0"):
        choke_line_volume(3.0, -100)

    with pytest.raises(ValueError, match="CLF cannot be negative"):
        dynamic_maasp(800, -50)

    with pytest.raises(ValueError, match="SICP cannot be negative"):
        choke_pressure_bringing_pump_up(-100, 50)

    with pytest.raises(ValueError, match="Subsea TVD .* must be > 0"):
        riser_margin_mud_weight(12.0, 1000, 1000, air_gap_ft=50)
