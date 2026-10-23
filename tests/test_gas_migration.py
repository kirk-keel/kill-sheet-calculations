"""Unit tests for gas migration dynamics and surface pressure accumulation."""

import pytest

from killsheet.gas_migration import (
    evaluate_gas_migration,
    gas_migration_velocity_ft_per_hr,
    pressure_buildup_rate_psi_per_hr,
    time_to_depth_hours,
)


def test_migration_velocity():
    # 10 ppg mud, 0 deg vertical
    v_vert = gas_migration_velocity_ft_per_hr(10.0, inclination_deg=0.0)
    assert 500 <= v_vert <= 1500

    # Incline to 45 deg -> velocity increases along high side
    v_45 = gas_migration_velocity_ft_per_hr(10.0, inclination_deg=45.0)
    assert v_45 > v_vert

    # Horizontal 90 deg -> vertical rise reaches 0
    v_90 = gas_migration_velocity_ft_per_hr(10.0, inclination_deg=90.0)
    assert v_90 == 0.0


def test_pressure_buildup_rate():
    # 10 ppg mud at 1000 ft/hr -> 0.052 * 10 * 1000 = 520 psi/hr
    dp_dt = pressure_buildup_rate_psi_per_hr(10.0, 1000.0)
    assert dp_dt == 520


def test_time_to_depth():
    # 5,000 ft at 1,000 ft/hr -> 5.0 hrs
    t = time_to_depth_hours(5000.0, 1000.0)
    assert t == 5.0


def test_evaluate_gas_migration():
    rep = evaluate_gas_migration(
        mud_weight_ppg=12.0,
        bit_tvd_ft=10_000.0,
        shoe_tvd_ft=6_000.0,
        initial_sicp_psi=500.0,
        use_field_rule_of_thumb=True,
    )
    assert rep["migration_velocity_ft_per_hr"] == 1000.0
    assert rep["pressure_rise_rate_psi_per_hr"] == 624  # 0.052 * 12 * 1000 = 624
    assert rep["time_to_casing_shoe_hr"] == 4.0        # (10000 - 6000) / 1000 = 4.0
    assert rep["time_to_casing_shoe_min"] == 240
    assert rep["time_to_surface_bop_hr"] == 10.0       # 10000 / 1000 = 10.0
    assert rep["projected_sicp_at_shoe_psi"] == 500 + 624 * 4


def test_validation_errors():
    with pytest.raises(ValueError):
        gas_migration_velocity_ft_per_hr(8.0, gas_density_ppg=9.0)
    with pytest.raises(ValueError):
        evaluate_gas_migration(10.0, 5000.0, 6000.0, 500.0)
