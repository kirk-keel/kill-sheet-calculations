"""Tests for kick tolerance, kick intensity, and casing seat drilling window calculations."""

import pytest

from killsheet.kick_tolerance import (
    formation_pore_pressure_psi,
    kick_intensity_ppg,
    kick_tolerance_bbl,
    kick_tolerance_summary,
    max_gas_height_at_shoe_ft,
    required_shoe_lot_ppg,
    shoe_fracture_pressure_psi,
)


def test_kick_intensity():
    # SIDPP 350 psi at 10,000 ft TVD: 350 / 520 = 0.673 -> 0.7 ppg
    assert kick_intensity_ppg(350, 10_000) == 0.7


def test_pressures_and_kick_tolerance_benchmark():
    # Benchmark case from SPE / Well Control suite:
    # MW = 12.5 ppg, LOT = 14.5 ppg, Shoe TVD = 5,000 ft, TVD = 10,000 ft
    # SIDPP = 350 psi, C_ann = 0.0459 bbl/ft, Gas grad = 0.10 psi/ft
    p_frac = shoe_fracture_pressure_psi(14.5, 5_000)
    assert p_frac == 3770

    p_form = formation_pore_pressure_psi(12.5, 10_000, 350)
    assert p_form == 6850

    # Max gas height at shoe:
    # (3770 - 6850 + 0.65 x 5000) / (0.65 - 0.10) = 170 / 0.55 = 309.09 -> 309 ft
    h_max = max_gas_height_at_shoe_ft(12.5, 10_000, 5_000, 14.5, 350, gas_gradient_psi_per_ft=0.10)
    assert h_max == 309

    # Kick tolerance:
    # V_shoe = 309.09 x 0.0459 = 14.187 bbl
    # KT = 14.187 x (3770 / 6850) = 7.808 -> rounds down to 7.8 bbl
    kt = kick_tolerance_bbl(12.5, 10_000, 5_000, 14.5, 350, 0.0459, gas_gradient_psi_per_ft=0.10)
    assert kt == 7.8


def test_required_shoe_lot():
    # If target kick volume is 7.8 bbl, required LOT EMW should round up to 14.5 ppg
    lot_req = required_shoe_lot_ppg(
        target_kick_volume_bbl=7.8,
        mud_weight_ppg=12.5,
        tvd_ft=10_000,
        shoe_tvd_ft=5_000,
        sidpp_psi=350,
        annular_capacity_bbl_per_ft=0.0459,
        gas_gradient_psi_per_ft=0.10,
    )
    assert lot_req == 14.5


def test_kick_tolerance_summary():
    summary = kick_tolerance_summary(
        mud_weight_ppg=12.5,
        tvd_ft=10_000,
        shoe_tvd_ft=5_000,
        lot_emw_ppg=14.5,
        sidpp_psi=350,
        annular_capacity_bbl_per_ft=0.0459,
    )
    assert summary["kick_intensity_ppg"] == 0.7
    assert summary["equivalent_pore_pressure_ppg"] == 13.2
    assert summary["formation_pressure_psi"] == 6850
    assert summary["shoe_fracture_pressure_psi"] == 3770
    assert summary["shoe_maasp_psi"] == 520
    assert summary["max_gas_height_at_shoe_ft"] == 309
    assert summary["kick_tolerance_bottomhole_bbl"] == 7.8


def test_kick_tolerance_validation():
    with pytest.raises(ValueError, match="cannot be negative"):
        kick_intensity_ppg(-50, 10_000)

    with pytest.raises(ValueError, match="must be deeper than Shoe TVD"):
        max_gas_height_at_shoe_ft(12.5, 5_000, 5_000, 14.5, 350)

    with pytest.raises(ValueError, match="Mud gradient must exceed gas gradient"):
        max_gas_height_at_shoe_ft(1.0, 10_000, 5_000, 14.5, 350, gas_gradient_psi_per_ft=0.10)
