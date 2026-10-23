"""Unit tests for wellbore hydraulics, nozzle jet optimization, annular pressure losses, and ECD."""

import pytest

from killsheet.hydraulics import (
    annular_pressure_loss_psi,
    bit_hydraulic_horsepower,
    bit_hydraulics_report,
    bit_pressure_drop_psi,
    equivalent_circulating_density_ppg,
    hydraulic_horsepower_per_sq_in,
    jet_impact_force_lbf,
    nozzle_velocity_fps,
    total_flow_area_sq_in,
)


def test_tfa_calculation():
    # Three 12/32" nozzles: 3 * (pi/4) * (12/32)^2 = 3 * 0.11045 = 0.3313 sq in
    tfa = total_flow_area_sq_in([12, 12, 12])
    assert tfa == pytest.approx(0.3313, abs=1e-3)

    with pytest.raises(ValueError):
        total_flow_area_sq_in([])
    with pytest.raises(ValueError):
        total_flow_area_sq_in([0, 12])


def test_nozzle_velocity_and_bit_pressure_drop():
    tfa = total_flow_area_sq_in([12, 12, 12])  # ~0.3313
    # Q = 400 gpm, MW = 10 ppg
    v = nozzle_velocity_fps(400.0, tfa)
    assert 350 <= v <= 400

    dp = bit_pressure_drop_psi(10.0, 400.0, tfa)
    assert 1200 <= dp <= 1500


def test_horsepower_and_impact_force():
    dp = 1350
    q = 400.0
    hhp = bit_hydraulic_horsepower(dp, q)
    assert hhp == pytest.approx(315.1, abs=1.0)

    # 8.5" bit area = pi/4 * 8.5^2 = 56.74 sq in
    # HSI = 315.1 / 56.74 = 5.55 hp/sq in
    hsi = hydraulic_horsepower_per_sq_in(hhp, 8.5)
    assert 5.0 <= hsi <= 6.0

    jif = jet_impact_force_lbf(10.0, 400.0, dp)
    assert 700 <= jif <= 900


def test_annular_pressure_loss_and_ecd():
    # 8.5" hole, 5.0" drillpipe, 5000 ft section
    # MW = 10 ppg, PV = 15 cP, YP = 10 lbf/100sqft, Q = 400 gpm
    dp_ann = annular_pressure_loss_psi(
        mud_weight_ppg=10.0,
        plastic_viscosity_cp=15.0,
        yield_point_lbf_100sqft=10.0,
        flow_rate_gpm=400.0,
        hole_diameter_in=8.5,
        pipe_od_in=5.0,
        interval_length_ft=5000.0,
    )
    assert dp_ann > 50

    # ECD at 10,000 ft TVD with 150 psi annular loss
    # delta ECD = 150 / (0.052 * 10000) = 0.288 ppg -> ECD = 10.29 ppg
    ecd = equivalent_circulating_density_ppg(10.0, 150.0, 10_000.0)
    assert ecd == 10.29


def test_bit_hydraulics_report():
    report = bit_hydraulics_report(
        mud_weight_ppg=10.5,
        flow_rate_gpm=450.0,
        bit_diameter_in=8.75,
        nozzle_sizes_in_32nds=[11, 11, 11],
    )
    assert report["tfa_sq_in"] > 0
    assert report["nozzle_velocity_fps"] > 0
    assert report["bit_pressure_drop_psi"] > 0
    assert report["hydraulic_horsepower_hhp"] > 0
    assert report["hsi_hp_per_sq_in"] > 0
    assert report["jet_impact_force_lbf"] > 0
