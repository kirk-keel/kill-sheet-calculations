"""Gas migration dynamics, percolation rise velocity, and shut-in pressure accumulation.

Standards & Conventions:
  - Density & Mud Weight: ppg (0.052 psi/ft per ppg)
  - Depths: feet (ft)
  - Pressures: psi
  - Velocities: feet per hour (ft/hr)
  - Time: hours and minutes
  - Inclination: degrees (0° = vertical, 90° = horizontal)

Physical Model:
  During an off-bottom shut-in or lubricate & bleed operation, gas percolates upward
  through the liquid column due to density differential (buoyancy):
    1. Standard Field Rule: V_rise ~ 1,000 ft/hr
    2. Hydrodynamic Bubble Slip (Harmathy / Hasan-Kabir):
         V_rise_vert = 1.53 x [ g x (rho_L - rho_g) x sigma / rho_L^2 ]^0.25
    3. Inclination Factor (Zukoski / Hasan-Kabir):
         In inclined wellbores, gas migrates along the high side of the borehole
         with reduced liquid drag, increasing velocity by up to 30-50% around 45°-60°:
         F_inc = 1.0 + 1.2 x sin(theta) x cos(theta)
    4. Shut-in Casing Pressure Accumulation Rate:
         dP/dt = 0.052 x Mud_Weight_ppg x V_rise  [psi/hr]
    5. Arrival Times:
         T_shoe = (Bit_TVD - Shoe_TVD) / V_rise  [hours]
         T_surface = Bit_TVD / V_rise            [hours]
"""

import math
from typing import Any, Dict

from killsheet.formulas import PSI_PER_FT_PER_PPG
from killsheet.rounding import (
    round_to_hundredth,
    round_to_tenth,
    round_to_whole_number,
)

STANDARD_FIELD_GAS_VELOCITY_FT_PER_HR = 1000.0  # ft/hr standard rule of thumb


def gas_migration_velocity_ft_per_hr(
    mud_weight_ppg: float,
    gas_density_ppg: float = 1.5,
    surface_tension_dynes_per_cm: float = 30.0,
    inclination_deg: float = 0.0,
) -> float:
    """Calculates gas bubble rise velocity through drilling mud in ft/hr.

    Args:
        mud_weight_ppg: Mud weight in ppg.
        gas_density_ppg: Influx gas density in ppg (default 1.5 ppg).
        surface_tension_dynes_per_cm: Interfacial surface tension (default 30 dynes/cm).
        inclination_deg: Wellbore inclination angle from vertical (0° to 90°).

    Returns:
        Rise velocity in ft/hr, rounded to 0.1 ft/hr.
    """
    if mud_weight_ppg <= gas_density_ppg or gas_density_ppg <= 0:
        raise ValueError("Mud weight must be greater than gas density.")
    if inclination_deg < 0 or inclination_deg > 90:
        raise ValueError(f"Inclination must be between 0° and 90° (got {inclination_deg}°).")

    # Liquid density in lb/cu ft
    rho_l = mud_weight_ppg * 7.48052
    rho_g = gas_density_ppg * 7.48052

    # Gravity g = 32.174 ft/s^2, surface tension sigma converted to lbf/ft (1 dyne/cm = 6.852e-5 lbf/ft)
    sigma_lbf_ft = surface_tension_dynes_per_cm * 6.8521766e-5
    gc = 32.174

    # Harmathy terminal rise velocity in ft/s
    radicand = (gc * (rho_l - rho_g) * sigma_lbf_ft) / (rho_l ** 2)
    v_fps = 1.53 * (radicand ** 0.25)

    # Convert ft/s to ft/hr: 1 ft/s = 3600 ft/hr
    v_vert_ft_hr = v_fps * 3600.0

    # Apply Zukoski wellbore inclination factor
    theta_rad = math.radians(inclination_deg)
    # Gas rise diminishes to 0 as inclination reaches 90° (pure horizontal lateral where gas segregates to roof)
    f_inc = (1.0 + 1.2 * math.sin(theta_rad) * math.cos(theta_rad)) * math.cos(theta_rad)

    v_effective = v_vert_ft_hr * max(0.0, f_inc)
    return round_to_tenth(v_effective)


def pressure_buildup_rate_psi_per_hr(
    mud_weight_ppg: float,
    migration_velocity_ft_per_hr: float = STANDARD_FIELD_GAS_VELOCITY_FT_PER_HR,
) -> int:
    """Calculates shut-in casing pressure rise rate (psi/hr) due to unexpanded gas migration.

        dP/dt = 0.052 x MW x V_migration
    """
    if mud_weight_ppg <= 0 or migration_velocity_ft_per_hr <= 0:
        raise ValueError("Mud weight and migration velocity must be positive.")
    rate = PSI_PER_FT_PER_PPG * mud_weight_ppg * migration_velocity_ft_per_hr
    return round_to_whole_number(rate)


def time_to_depth_hours(distance_ft: float, migration_velocity_ft_per_hr: float) -> float:
    """Calculates time in hours for migrating gas to traverse a distance."""
    if distance_ft <= 0 or migration_velocity_ft_per_hr <= 0:
        raise ValueError("Distance and velocity must be positive.")
    return round_to_hundredth(distance_ft / migration_velocity_ft_per_hr)


def evaluate_gas_migration(
    mud_weight_ppg: float,
    bit_tvd_ft: float,
    shoe_tvd_ft: float,
    initial_sicp_psi: float,
    inclination_deg: float = 0.0,
    use_field_rule_of_thumb: bool = False,
) -> Dict[str, Any]:
    """Evaluates gas migration velocity, surface pressure rise, and critical arrival times.

    Returns:
        Dictionary with velocity, pressure accumulation rate, time to shoe,
        and time to surface BOP stack.
    """
    if bit_tvd_ft <= shoe_tvd_ft or shoe_tvd_ft <= 0:
        raise ValueError("Bit TVD must be greater than shoe TVD, and shoe TVD must be positive.")

    if use_field_rule_of_thumb:
        velocity = STANDARD_FIELD_GAS_VELOCITY_FT_PER_HR
    else:
        velocity = gas_migration_velocity_ft_per_hr(
            mud_weight_ppg=mud_weight_ppg, inclination_deg=inclination_deg
        )

    # Protect against horizontal stall (velocity = 0)
    if velocity <= 1e-3:
        velocity = 1.0

    dp_dt = pressure_buildup_rate_psi_per_hr(mud_weight_ppg, velocity)
    t_shoe = time_to_depth_hours(bit_tvd_ft - shoe_tvd_ft, velocity)
    t_surface = time_to_depth_hours(bit_tvd_ft, velocity)

    return {
        "migration_velocity_ft_per_hr": velocity,
        "pressure_rise_rate_psi_per_hr": dp_dt,
        "time_to_casing_shoe_hr": t_shoe,
        "time_to_casing_shoe_min": round_to_whole_number(t_shoe * 60.0),
        "time_to_surface_bop_hr": t_surface,
        "time_to_surface_bop_min": round_to_whole_number(t_surface * 60.0),
        "initial_sicp_psi": initial_sicp_psi,
        "projected_sicp_at_shoe_psi": round_to_whole_number(initial_sicp_psi + dp_dt * t_shoe),
    }
