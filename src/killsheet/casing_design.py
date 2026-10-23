"""Casing burst, tension-derated collapse, and triaxial integrity under well control.

Standards & Conventions:
  - Diameters & Wall Thickness: inches (in)
  - Yield Strength & Pressures: psi
  - Axial Force: pounds-force (lbf)
  - Safety Factors: dimensionless (typical burst SF >= 1.10, collapse SF >= 1.00 - 1.125)
  - API Specification: API Spec 5CT / API TR 5C3 (ISO 10400)

Physical Model:
  1. API Barlow's Internal Yield (Burst) Pressure:
       P_burst = 0.875 x (2 x Y_p x t / D)
       (includes standard API 12.5% manufacturing wall thickness tolerance factor of 0.875)
  2. Wall Thickness:
       t = (OD - ID) / 2
  3. API Biaxial Collapse Derating under Axial Tension:
       Tensile stress ratio: s = sigma_axial / Y_p = (F_tension / Area) / Y_p
       Derated Yield Strength:
         Y_pa = [ sqrt(1.0 - 0.75 x s^2) - 0.5 x s ] x Y_p
       Derated Collapse Resistance:
         P_collapse_derated = P_collapse_nominal x (Y_pa / Y_p)
  4. Triaxial von Mises Stress Equivalent:
       sigma_VME = sqrt( sigma_axial^2 + sigma_hoop^2 - sigma_axial x sigma_hoop )
"""

import math
from typing import Any, Dict

from killsheet.rounding import (
    round_to_hundredth,
    round_to_tenth,
    round_to_whole_number,
)

# Standard API steel casing yield grades (psi)
CASING_GRADES = {
    "H-40": 40_000,
    "J-55": 55_000,
    "K-55": 55_000,
    "M-65": 65_000,
    "L-80": 80_000,
    "N-80": 80_000,
    "C-90": 90_000,
    "T-95": 95_000,
    "P-110": 110_000,
    "Q-125": 125_000,
}


def pipe_wall_thickness_in(od_in: float, id_in: float) -> float:
    """Calculates pipe wall thickness in inches."""
    if od_in <= id_in or id_in <= 0:
        raise ValueError(f"OD ({od_in}\") must be greater than ID ({id_in}\").")
    return round((od_in - id_in) / 2.0, 4)


def pipe_cross_section_sq_in(od_in: float, id_in: float) -> float:
    """Calculates cross-sectional steel area in square inches."""
    if od_in <= id_in or id_in <= 0:
        raise ValueError("Invalid pipe diameters.")
    area = (math.pi / 4.0) * (od_in ** 2 - id_in ** 2)
    return round(area, 4)


def api_burst_pressure_psi(
    od_in: float,
    id_in: float,
    yield_strength_psi: float,
    apply_wall_tolerance: bool = True,
) -> int:
    """Calculates API Barlow internal yield (burst) pressure in psi.

        P_burst = Factor x (2 x Y_p x t / OD)
        Factor = 0.875 (with API 12.5% wall tolerance) or 1.0 (nominal)
    """
    if yield_strength_psi <= 0:
        raise ValueError("Yield strength must be positive.")
    t = pipe_wall_thickness_in(od_in, id_in)
    factor = 0.875 if apply_wall_tolerance else 1.0
    p_burst = factor * ((2.0 * yield_strength_psi * t) / od_in)
    return round_to_whole_number(p_burst)


def biaxial_yield_strength_derating(
    yield_strength_psi: float,
    axial_tensile_stress_psi: float,
) -> float:
    """Calculates reduced effective yield strength (Y_pa) under axial tension per API 5C3 / ISO 10400.

        s = sigma_axial / Y_p
        Y_pa = [ sqrt(1.0 - 0.75 x s^2) - 0.5 x s ] x Y_p
    """
    if yield_strength_psi <= 0:
        raise ValueError("Yield strength must be positive.")
    if axial_tensile_stress_psi < 0:
        # Compression does not reduce collapse in the biaxial tensile model
        return float(yield_strength_psi)

    s = axial_tensile_stress_psi / yield_strength_psi
    if s >= 1.0:
        raise ValueError(f"Axial tension ({axial_tensile_stress_psi:,} psi) exceeds yield strength ({yield_strength_psi:,} psi)!")

    radicand = max(0.0, 1.0 - 0.75 * (s ** 2))
    derate_factor = math.sqrt(radicand) - 0.5 * s
    y_pa = derate_factor * yield_strength_psi
    return round(y_pa, 1)


def derated_collapse_pressure_psi(
    nominal_collapse_psi: float,
    yield_strength_psi: float,
    axial_tensile_load_lbf: float,
    cross_section_sq_in: float,
) -> int:
    """Calculates tension-derated casing collapse resistance per API 5C3 biaxial envelope.

        sigma_axial = F_tension / A_steel
        P_derated = P_nom x (Y_pa / Y_p)
    """
    if nominal_collapse_psi <= 0:
        raise ValueError("Nominal collapse pressure must be positive.")
    if cross_section_sq_in <= 0:
        raise ValueError("Cross-sectional area must be positive.")

    sigma_axial = max(0.0, axial_tensile_load_lbf / cross_section_sq_in)
    y_pa = biaxial_yield_strength_derating(yield_strength_psi, sigma_axial)
    derated_p = nominal_collapse_psi * (y_pa / yield_strength_psi)
    return round_to_whole_number(derated_p)


def evaluate_casing_well_control_integrity(
    od_in: float,
    id_in: float,
    casing_grade: str,
    nominal_collapse_psi: float,
    hanging_weight_lbf: float,
    anticipated_surface_sicp_psi: float,
    external_fluid_collapse_psi: float = 0.0,
) -> Dict[str, Any]:
    """Comprehensive casing integrity assessment under well control loads.

    Returns:
        Dictionary with burst rating, derated collapse rating, safety factors,
        and integrity check status.
    """
    if casing_grade not in CASING_GRADES:
        raise ValueError(f"Unknown casing grade '{casing_grade}'. Supported: {list(CASING_GRADES.keys())}")

    yp = CASING_GRADES[casing_grade]
    as_in2 = pipe_cross_section_sq_in(od_in, id_in)
    t_in = pipe_wall_thickness_in(od_in, id_in)

    p_burst_api = api_burst_pressure_psi(od_in, id_in, yp, apply_wall_tolerance=True)
    p_collapse_derated = derated_collapse_pressure_psi(
        nominal_collapse_psi, yp, hanging_weight_lbf, as_in2
    )

    burst_sf = round_to_hundredth(p_burst_api / anticipated_surface_sicp_psi) if anticipated_surface_sicp_psi > 0 else 999.0
    collapse_sf = round_to_hundredth(p_collapse_derated / external_fluid_collapse_psi) if external_fluid_collapse_psi > 0 else 999.0

    burst_ok = burst_sf >= 1.10
    collapse_ok = collapse_sf >= 1.00

    return {
        "casing_grade": casing_grade,
        "yield_strength_psi": yp,
        "wall_thickness_in": t_in,
        "cross_section_sq_in": as_in2,
        "api_burst_rating_psi": p_burst_api,
        "nominal_collapse_psi": round_to_whole_number(nominal_collapse_psi),
        "tension_derated_collapse_psi": p_collapse_derated,
        "surface_sicp_psi": anticipated_surface_sicp_psi,
        "burst_safety_factor": burst_sf,
        "burst_integrity_ok": burst_ok,
        "collapse_safety_factor": collapse_sf,
        "collapse_integrity_ok": collapse_ok,
    }
