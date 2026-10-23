"""Tubular stress, sinusoidal buckling, and helical lockup analysis.

Standards & Conventions:
  - Diameters & Clearance: inches (in)
  - Length & Depth: feet (ft)
  - Force & Critical Loads: pounds-force (lbf)
  - Unit Weight: pounds per foot (lb/ft) and pounds per inch (lb/in)
  - Young's Modulus of Steel (E): 30,000,000 psi
  - Steel Density: 489.5 lb/cu ft (~65.45 ppg)

Physical Model:
  Evaluates compressive buckling thresholds for drill strings, casing, and coiled
  tubing in directional and horizontal wellbores:
    1. Moment of Inertia: I = (pi / 64) x (OD^4 - ID^4)
    2. Radial Clearance: r = (Hole_ID - Pipe_OD) / 2
    3. Buoyancy Factor: BF = 1 - (Mud_Weight_ppg / 65.5)
    4. Paslay-Dawson Critical Sinusoidal Buckling Load:
         F_crit_sin = 2.0 x sqrt(E x I x w_e x sin(theta) / r)
    5. Helical Buckling Load (Wu & Juvkam-Wold / Lubinski):
         F_crit_hel = sqrt(2) x F_crit_sin  (Wu & Juvkam-Wold: 2.83 x sqrt(E I w_e sin(theta) / r))
    6. Vertical Hole Buckling (Lubinski):
         F_crit_vert = 1.946 x (E x I x w_e^2)^(1/3)
"""

import math
from typing import Any, Dict

from killsheet.rounding import (
    round_to_hundredth,
    round_to_tenth,
    round_to_thousandth,
    round_to_whole_number,
)

YOUNGS_MODULUS_STEEL_PSI = 30_000_000.0  # psi
STEEL_DENSITY_PPG = 65.45                # ppg equivalent


def pipe_cross_sectional_area_sq_in(od_in: float, id_in: float) -> float:
    """Calculates pipe steel cross-sectional area (sq in)."""
    if od_in <= id_in or id_in < 0:
        raise ValueError(f"Outer diameter ({od_in}\") must be greater than inner diameter ({id_in}\").")
    area = (math.pi / 4.0) * (od_in ** 2 - id_in ** 2)
    return round(area, 4)


def pipe_moment_of_inertia_in4(od_in: float, id_in: float) -> float:
    """Calculates pipe area moment of inertia I (in^4).

        I = (pi / 64) x (OD^4 - ID^4)
    """
    if od_in <= id_in or id_in < 0:
        raise ValueError(f"Outer diameter ({od_in}\") must be greater than inner diameter ({id_in}\").")
    inertia = (math.pi / 64.0) * (od_in ** 4 - id_in ** 4)
    return round(inertia, 4)


def buoyancy_factor(mud_weight_ppg: float) -> float:
    """Calculates the Archimedes buoyancy factor for steel in drilling fluid.

        BF = 1 - (MW_ppg / 65.45)
    """
    if mud_weight_ppg <= 0:
        raise ValueError("Mud weight must be positive.")
    bf = 1.0 - (mud_weight_ppg / STEEL_DENSITY_PPG)
    return max(0.0, round(bf, 4))


def radial_clearance_in(hole_or_casing_id_in: float, pipe_od_in: float) -> float:
    """Calculates radial clearance between wellbore wall and pipe (inches).

        r = (Wellbore_ID - Pipe_OD) / 2
    """
    if hole_or_casing_id_in <= pipe_od_in:
        raise ValueError(
            f"Wellbore ID ({hole_or_casing_id_in}\") must be greater than Pipe OD ({pipe_od_in}\")."
        )
    return round((hole_or_casing_id_in - pipe_od_in) / 2.0, 4)


def sinusoidal_buckling_load_lbf(
    pipe_od_in: float,
    pipe_id_in: float,
    hole_id_in: float,
    pipe_weight_lb_per_ft: float,
    mud_weight_ppg: float,
    inclination_deg: float,
) -> int:
    """Calculates Paslay-Dawson critical sinusoidal buckling compressive load (lbf).

    For inclined/horizontal wellbores (theta > 0):
        F_c = 2 x sqrt(E x I x w_e x sin(theta) / r)
    where:
        E = 30,000,000 psi
        I = moment of inertia (in^4)
        w_e = buoyed weight per inch (lb/in) = (weight_lb_ft x BF) / 12
        r = radial clearance (in)
        theta = wellbore inclination angle from vertical

    For vertical wellbores (theta = 0):
        Lubinski vertical buckling threshold:
        F_vert = 1.946 x (E x I x w_e^2)^(1/3)
    """
    if pipe_weight_lb_per_ft <= 0:
        raise ValueError("Pipe weight must be positive.")
    if inclination_deg < 0 or inclination_deg > 180:
        raise ValueError(f"Inclination must be between 0° and 180° (got {inclination_deg}°).")

    i_in4 = pipe_moment_of_inertia_in4(pipe_od_in, pipe_id_in)
    r_in = radial_clearance_in(hole_id_in, pipe_od_in)
    bf = buoyancy_factor(mud_weight_ppg)

    # Buoyed weight per inch
    we_lb_per_in = (pipe_weight_lb_per_ft * bf) / 12.0

    if inclination_deg < 1e-3:
        # Lubinski vertical buckling formulation
        f_vert = 1.946 * ((YOUNGS_MODULUS_STEEL_PSI * i_in4 * (we_lb_per_in ** 2)) ** (1.0 / 3.0))
        return round_to_whole_number(f_vert)

    theta_rad = math.radians(inclination_deg)
    sin_theta = math.sin(theta_rad)

    radicand = (YOUNGS_MODULUS_STEEL_PSI * i_in4 * we_lb_per_in * sin_theta) / r_in
    f_sin = 2.0 * math.sqrt(radicand)
    return round_to_whole_number(f_sin)


def helical_buckling_load_lbf(
    pipe_od_in: float,
    pipe_id_in: float,
    hole_id_in: float,
    pipe_weight_lb_per_ft: float,
    mud_weight_ppg: float,
    inclination_deg: float,
) -> int:
    """Calculates critical helical buckling compressive load (lbf) via Wu & Juvkam-Wold / Dawson.

        F_hel = sqrt(2) x F_sin  (approx 1.414 x F_sin)
    """
    f_sin = sinusoidal_buckling_load_lbf(
        pipe_od_in=pipe_od_in,
        pipe_id_in=pipe_id_in,
        hole_id_in=hole_id_in,
        pipe_weight_lb_per_ft=pipe_weight_lb_per_ft,
        mud_weight_ppg=mud_weight_ppg,
        inclination_deg=inclination_deg,
    )
    f_hel = math.sqrt(2.0) * f_sin
    return round_to_whole_number(f_hel)


def evaluate_tubular_buckling(
    pipe_od_in: float,
    pipe_id_in: float,
    hole_id_in: float,
    pipe_weight_lb_per_ft: float,
    mud_weight_ppg: float,
    inclination_deg: float,
    current_axial_force_lbf: float,
) -> Dict[str, Any]:
    """Evaluates tubular stability under current axial load (compression > 0, tension < 0).

    Returns:
        Dictionary with moments, clearances, sinusoidal limit, helical limit,
        and current buckling state ('STABLE', 'SINUSOIDAL BUCKLING', 'HELICAL BUCKLING').
    """
    f_sin = sinusoidal_buckling_load_lbf(
        pipe_od_in, pipe_id_in, hole_id_in, pipe_weight_lb_per_ft, mud_weight_ppg, inclination_deg
    )
    f_hel = helical_buckling_load_lbf(
        pipe_od_in, pipe_id_in, hole_id_in, pipe_weight_lb_per_ft, mud_weight_ppg, inclination_deg
    )

    if current_axial_force_lbf <= 0:
        state = "STABLE (PIPE IN TENSION)"
    elif current_axial_force_lbf < f_sin:
        state = "STABLE (COMPRESSION BELOW BUCKLING)"
    elif current_axial_force_lbf < f_hel:
        state = "SINUSOIDAL BUCKLING (SNABBING / WAVING)"
    else:
        state = "HELICAL BUCKLING (RISK OF SPIRAL LOCKUP)"

    margin_to_sin = f_sin - current_axial_force_lbf
    margin_to_hel = f_hel - current_axial_force_lbf

    return {
        "moment_of_inertia_in4": pipe_moment_of_inertia_in4(pipe_od_in, pipe_id_in),
        "radial_clearance_in": radial_clearance_in(hole_id_in, pipe_od_in),
        "buoyancy_factor": buoyancy_factor(mud_weight_ppg),
        "sinusoidal_buckling_limit_lbf": f_sin,
        "helical_buckling_limit_lbf": f_hel,
        "axial_force_lbf": current_axial_force_lbf,
        "buckling_state": state,
        "margin_to_sinusoidal_lbf": round_to_whole_number(margin_to_sin),
        "margin_to_helical_lbf": round_to_whole_number(margin_to_hel),
    }
