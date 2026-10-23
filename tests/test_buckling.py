"""Unit tests for tubular stress, sinusoidal buckling, and helical lockup analysis."""

import pytest

from killsheet.buckling import (
    buoyancy_factor,
    evaluate_tubular_buckling,
    helical_buckling_load_lbf,
    pipe_cross_sectional_area_sq_in,
    pipe_moment_of_inertia_in4,
    radial_clearance_in,
    sinusoidal_buckling_load_lbf,
)


def test_geometry_and_buoyancy():
    # 5.0" OD, 4.276" ID pipe (19.5 lb/ft S-135)
    area = pipe_cross_sectional_area_sq_in(5.0, 4.276)
    assert 5.0 <= area <= 6.0

    inertia = pipe_moment_of_inertia_in4(5.0, 4.276)
    assert 14.0 <= inertia <= 16.0

    # Clearance in 8.5" hole: (8.5 - 5.0) / 2 = 1.75"
    r = radial_clearance_in(8.5, 5.0)
    assert r == 1.75

    # Buoyancy factor for 10 ppg mud: 1 - 10 / 65.45 ~ 0.8472
    bf = buoyancy_factor(10.0)
    assert bf == pytest.approx(0.8472, abs=1e-3)


def test_geometry_errors():
    with pytest.raises(ValueError):
        pipe_cross_sectional_area_sq_in(4.0, 5.0)
    with pytest.raises(ValueError):
        radial_clearance_in(4.5, 5.0)
    with pytest.raises(ValueError):
        buoyancy_factor(-1.0)


def test_sinusoidal_and_helical_buckling():
    # 5.0" OD, 4.276" ID in 8.5" hole, 19.5 lb/ft, 10 ppg, 90° horizontal
    f_sin = sinusoidal_buckling_load_lbf(
        pipe_od_in=5.0,
        pipe_id_in=4.276,
        hole_id_in=8.5,
        pipe_weight_lb_per_ft=19.5,
        mud_weight_ppg=10.0,
        inclination_deg=90.0,
    )
    assert f_sin > 20_000  # typical sinusoidal threshold > 20,000 lbf

    f_hel = helical_buckling_load_lbf(
        pipe_od_in=5.0,
        pipe_id_in=4.276,
        hole_id_in=8.5,
        pipe_weight_lb_per_ft=19.5,
        mud_weight_ppg=10.0,
        inclination_deg=90.0,
    )
    # Helical is sqrt(2) * sinusoidal
    assert f_hel == pytest.approx(f_sin * 1.4142, rel=1e-2)


def test_vertical_buckling_lubinski():
    f_vert = sinusoidal_buckling_load_lbf(
        pipe_od_in=5.0,
        pipe_id_in=4.276,
        hole_id_in=8.5,
        pipe_weight_lb_per_ft=19.5,
        mud_weight_ppg=10.0,
        inclination_deg=0.0,
    )
    assert f_vert > 0


def test_evaluate_tubular_buckling():
    result = evaluate_tubular_buckling(
        pipe_od_in=5.0,
        pipe_id_in=4.276,
        hole_id_in=8.5,
        pipe_weight_lb_per_ft=19.5,
        mud_weight_ppg=10.0,
        inclination_deg=60.0,
        current_axial_force_lbf=10_000.0,
    )
    assert result["buckling_state"] == "STABLE (COMPRESSION BELOW BUCKLING)"
    assert result["sinusoidal_buckling_limit_lbf"] > 10_000

    # Overload into helical
    result_high = evaluate_tubular_buckling(
        pipe_od_in=5.0,
        pipe_id_in=4.276,
        hole_id_in=8.5,
        pipe_weight_lb_per_ft=19.5,
        mud_weight_ppg=10.0,
        inclination_deg=60.0,
        current_axial_force_lbf=100_000.0,
    )
    assert "HELICAL" in result_high["buckling_state"]
