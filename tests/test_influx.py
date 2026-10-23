"""Unit tests for influx characterization, fluid identification, and real gas properties."""

import pytest

from killsheet.influx import (
    characterize_kick,
    classify_influx_type,
    gas_formation_volume_factor_bg,
    gas_pseudocritical_properties,
    gas_z_factor,
    influx_density_ppg,
    influx_gradient_psi_per_ft,
    influx_height_ft,
)


def test_influx_height():
    # 20 bbl gain in 0.05 bbl/ft annulus -> 400 ft
    h = influx_height_ft(20.0, 0.05)
    assert h == 400.0

    with pytest.raises(ValueError):
        influx_height_ft(-10, 0.05)
    with pytest.raises(ValueError):
        influx_height_ft(10, 0)


def test_influx_gradient_and_density_gas():
    # OMW = 10.0 ppg, mud grad = 0.520 psi/ft
    # SIDPP = 500, SICP = 650 -> diff = 150 psi
    # H_influx = 400 ft -> diff_grad = 150 / 400 = 0.375 psi/ft
    # G_influx = 0.520 - 0.375 = 0.145 psi/ft
    # Density = 0.145 / 0.052 = 2.788 -> 2.79 ppg (Gas / Condensate)
    grad = influx_gradient_psi_per_ft(650.0, 500.0, 400.0, 10.0)
    assert grad == pytest.approx(0.145, abs=1e-3)
    rho = influx_density_ppg(grad)
    assert rho == pytest.approx(2.79, abs=0.01)
    assert classify_influx_type(rho) == "Gas / Condensate"


def test_influx_density_saltwater():
    # SICP close to SIDPP indicates heavy influx (saltwater)
    # diff = 20 psi over 500 ft -> 0.04 psi/ft
    # OMW = 10.0 (0.520) -> G_influx = 0.480 psi/ft
    # Density = 0.480 / 0.052 = 9.23 ppg
    grad = influx_gradient_psi_per_ft(520.0, 500.0, 500.0, 10.0)
    assert grad == pytest.approx(0.480, abs=1e-3)
    rho = influx_density_ppg(grad)
    assert rho == 9.23
    assert classify_influx_type(rho) == "Saltwater / Formation Water"


def test_influx_validation_errors():
    with pytest.raises(ValueError):
        influx_gradient_psi_per_ft(400, 500, 300, 10.0)  # SICP < SIDPP
    with pytest.raises(ValueError):
        influx_gradient_psi_per_ft(600, 500, -10, 10.0)  # negative height


def test_gas_z_factor_and_bg():
    # Typical reservoir conditions: 5000 psig, 180°F, gas gravity 0.65
    props = gas_pseudocritical_properties(0.65)
    assert props["t_pc_deg_r"] > 350
    assert props["p_pc_psia"] > 600

    z = gas_z_factor(5000.0, 180.0, 0.65)
    assert 0.8 <= z <= 1.2

    bg = gas_formation_volume_factor_bg(5000.0, 180.0, z)
    assert bg > 0
    assert bg < 0.05


def test_characterize_kick_report():
    report = characterize_kick(
        sidpp_psi=450.0,
        sicp_psi=680.0,
        pit_gain_bbl=25.0,
        annular_capacity_bbl_per_ft=0.05,
        original_mud_weight_ppg=11.0,
        bit_tvd_ft=10_000.0,
        temperature_deg_f=160.0,
    )
    assert report["influx_height_ft"] == 500.0
    assert report["formation_pressure_psi"] == 6170
    assert report["is_gas"] is True
    assert "Gas" in report["fluid_type"]
    assert report["z_factor"] > 0
    assert report["bg_bbl_per_mscf"] > 0
