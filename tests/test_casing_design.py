"""Unit tests for casing burst, tension-derated collapse, and well control integrity."""

import pytest

from killsheet.casing_design import (
    api_burst_pressure_psi,
    biaxial_yield_strength_derating,
    derated_collapse_pressure_psi,
    evaluate_casing_well_control_integrity,
    pipe_cross_section_sq_in,
    pipe_wall_thickness_in,
)


def test_dimensions():
    # 9-5/8" 40 lb/ft (ID = 8.835")
    t = pipe_wall_thickness_in(9.625, 8.835)
    assert t == pytest.approx(0.395, abs=1e-3)

    as_in2 = pipe_cross_section_sq_in(9.625, 8.835)
    assert 11.0 <= as_in2 <= 12.0


def test_api_burst():
    # 9-5/8" 40 lb/ft L-80 casing (Yp = 80,000 psi)
    # Barlow with 0.875: 0.875 * (2 * 80000 * 0.395 / 9.625) = 5745 psi
    p_burst = api_burst_pressure_psi(9.625, 8.835, 80_000, apply_wall_tolerance=True)
    assert 5600 <= p_burst <= 5900


def test_biaxial_collapse_derating():
    # L-80 steel (80,000 psi yield) under 20,000 psi axial tension (s = 0.25)
    # y_pa = [sqrt(1 - 0.75 * 0.25^2) - 0.5 * 0.25] * 80000 = [0.976 - 0.125] * 80000 = 68,095 psi
    y_pa = biaxial_yield_strength_derating(80_000, 20_000)
    assert 65_000 <= y_pa <= 70_000

    # Under zero tension -> y_pa == yp
    assert biaxial_yield_strength_derating(80_000, 0) == 80_000.0


def test_derated_collapse():
    # Nominal collapse = 3000 psi
    p_col_derated = derated_collapse_pressure_psi(
        nominal_collapse_psi=3000.0,
        yield_strength_psi=80_000.0,
        axial_tensile_load_lbf=200_000.0,
        cross_section_sq_in=11.45,
    )
    assert p_col_derated < 3000
    assert p_col_derated > 2000


def test_casing_well_control_evaluation():
    rep = evaluate_casing_well_control_integrity(
        od_in=9.625,
        id_in=8.835,
        casing_grade="L-80",
        nominal_collapse_psi=3090.0,
        hanging_weight_lbf=250_000.0,
        anticipated_surface_sicp_psi=1500.0,
        external_fluid_collapse_psi=2000.0,
    )
    assert rep["burst_integrity_ok"] is True
    assert rep["burst_safety_factor"] > 1.10
    assert rep["tension_derated_collapse_psi"] < 3090.0
    assert rep["casing_grade"] == "L-80"
