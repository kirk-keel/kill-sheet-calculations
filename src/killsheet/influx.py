"""Influx characterization, fluid identification, and real gas properties.

Standards & Conventions:
  - Density & Mud Weight: ppg (0.052 psi/ft per ppg)
  - Pressure: psi (gauge)
  - Temperature: degrees Fahrenheit (°F)
  - Volume: barrels (bbl)
  - Gradient: psi/ft
  - Gas Gravity: dimensionless (air = 1.0, standard natural gas ~ 0.65)

Physical Model:
  Calculates influx gradient and density from shut-in drillpipe (SIDPP) and casing
  (SICP) pressures and pit gain height in the annulus:
      P_influx_gradient = 0.052 x OMW - (SICP - SIDPP) / H_influx
      Influx Density (ppg) = Influx Gradient / 0.052

  Classifies kicking fluid type:
    - Gas / Dry Methane (< 1.5 ppg)
    - Wet Gas / Condensate (1.5 - 3.5 ppg)
    - Oil (3.5 - 7.0 ppg)
    - Saltwater / Formation Brine (> 7.0 ppg)

  Computes real gas deviation factor (Z-factor) via Beggs-Brill & Sutton correlations,
  and gas formation volume factor (Bg).
"""

import math
from typing import Any, Dict

from killsheet.formulas import PSI_PER_FT_PER_PPG
from killsheet.rounding import (
    round_to_hundredth,
    round_to_tenth,
    round_to_thousandth,
    round_to_whole_number,
)

# Fluid density classification thresholds (in ppg)
GAS_MAX_PPG = 3.5
OIL_MAX_PPG = 7.0
SALTWATER_MAX_PPG = 9.5


def influx_height_ft(pit_gain_bbl: float, annular_capacity_bbl_per_ft: float) -> float:
    """Calculates height of influx bubble in the annulus (ft).

    Args:
        pit_gain_bbl: Pit volume gain at shut-in (bbl).
        annular_capacity_bbl_per_ft: Annular capacity around BHA or drill collars (bbl/ft).

    Returns:
        Influx height in feet, rounded to 0.1 ft.
    """
    if pit_gain_bbl <= 0:
        raise ValueError(f"Pit gain must be positive (got {pit_gain_bbl} bbl).")
    if annular_capacity_bbl_per_ft <= 0:
        raise ValueError(f"Annular capacity must be positive (got {annular_capacity_bbl_per_ft} bbl/ft).")
    return round_to_tenth(pit_gain_bbl / annular_capacity_bbl_per_ft)


def influx_gradient_psi_per_ft(
    sicp_psi: float,
    sidpp_psi: float,
    influx_height_ft: float,
    original_mud_weight_ppg: float,
) -> float:
    """Calculates the pressure gradient of the kick influx (psi/ft).

        G_influx = 0.052 x OMW - (SICP - SIDPP) / H_influx

    Args:
        sicp_psi: Shut-in casing pressure (psi).
        sidpp_psi: Shut-in drill pipe pressure (psi).
        influx_height_ft: Vertical height of influx in annulus (ft).
        original_mud_weight_ppg: Current drilling mud weight (ppg).

    Returns:
        Influx gradient in psi/ft, rounded to 3 decimal places.
    """
    if influx_height_ft <= 0:
        raise ValueError(f"Influx height must be positive (got {influx_height_ft} ft).")
    if original_mud_weight_ppg <= 0:
        raise ValueError(f"Original mud weight must be positive (got {original_mud_weight_ppg} ppg).")
    if sicp_psi < sidpp_psi:
        raise ValueError(
            f"SICP ({sicp_psi} psi) cannot be less than SIDPP ({sidpp_psi} psi) for a legitimate influx."
        )

    mud_gradient = PSI_PER_FT_PER_PPG * original_mud_weight_ppg
    diff_gradient = (sicp_psi - sidpp_psi) / influx_height_ft
    gradient = mud_gradient - diff_gradient
    return round_to_thousandth(gradient)


def influx_density_ppg(gradient_psi_per_ft: float) -> float:
    """Converts influx gradient to equivalent density in ppg.

        Density = Gradient / 0.052

    Returns density rounded to 2 decimal places.
    """
    if gradient_psi_per_ft < 0:
        raise ValueError(f"Influx gradient cannot be negative (got {gradient_psi_per_ft} psi/ft).")
    return round_to_hundredth(gradient_psi_per_ft / PSI_PER_FT_PER_PPG)


def classify_influx_type(density_ppg: float) -> str:
    """Classifies the influx fluid type based on equivalent density in ppg."""
    if density_ppg < 0:
        return "Unknown / Measurement Error"
    if density_ppg <= 1.5:
        return "Gas (Dry / Methane)"
    if density_ppg <= GAS_MAX_PPG:
        return "Gas / Condensate"
    if density_ppg <= OIL_MAX_PPG:
        return "Oil"
    if density_ppg <= SALTWATER_MAX_PPG:
        return "Saltwater / Formation Water"
    return "Heavy Brine / Mineralized Fluid"


def gas_pseudocritical_properties(gas_gravity: float = 0.65) -> Dict[str, float]:
    """Calculates pseudocritical temperature (°R) and pressure (psia) for natural gas via Sutton correlations.

    Args:
        gas_gravity: Specific gravity of natural gas relative to air (default 0.65).

    Returns:
        Dictionary with 't_pc_deg_r' and 'p_pc_psia'.
    """
    if gas_gravity <= 0.4 or gas_gravity >= 2.0:
        raise ValueError(f"Gas gravity out of typical range 0.4 to 2.0 (got {gas_gravity}).")
    t_pc = 168.0 + 325.0 * gas_gravity - 12.5 * (gas_gravity ** 2)
    p_pc = 677.0 + 15.0 * gas_gravity - 37.5 * (gas_gravity ** 2)
    return {"t_pc_deg_r": round_to_hundredth(t_pc), "p_pc_psia": round_to_tenth(p_pc)}


def gas_z_factor(
    pressure_psig: float,
    temperature_deg_f: float,
    gas_gravity: float = 0.65,
) -> float:
    """Calculates real gas compressibility deviation factor (Z-factor) via Beggs-Brill & Sutton correlations.

    Args:
        pressure_psig: Reservoir or wellbore pressure in psig.
        temperature_deg_f: Temperature in °F.
        gas_gravity: Specific gravity of gas (air = 1.0, default 0.65).

    Returns:
        Z-factor (dimensionless), rounded to 4 decimal places.
    """
    if pressure_psig < 0:
        raise ValueError(f"Pressure cannot be negative (got {pressure_psig} psig).")
    if temperature_deg_f < -40:
        raise ValueError(f"Temperature cannot be below -40°F (got {temperature_deg_f}°F).")

    p_psia = pressure_psig + 14.7
    t_deg_r = temperature_deg_f + 459.67

    pc = gas_pseudocritical_properties(gas_gravity)
    t_pr = t_deg_r / pc["t_pc_deg_r"]
    p_pr = p_psia / pc["p_pc_psia"]

    if t_pr <= 0.92:
        t_pr = 0.921

    # Beggs and Brill explicit correlation
    a = 1.39 * math.sqrt(t_pr - 0.92) - 0.36 * t_pr - 0.101
    term_e = 9.0 * (t_pr - 1.0)
    exp_term = 10.0 ** term_e if term_e < 50 else 1e50
    b = (0.62 - 0.23 * t_pr) * p_pr + (0.066 / (t_pr - 0.86) - 0.037) * (p_pr ** 2) + (0.32 * (p_pr ** 6)) / exp_term
    c = 0.132 - 0.32 * math.log10(t_pr)
    term_f = 0.3106 - 0.49 * t_pr + 0.1824 * (t_pr ** 2)
    d = 10.0 ** term_f

    # Guard against extreme exp overflow
    b_clamped = min(max(b, -50.0), 50.0)
    z = a + (1.0 - a) / math.exp(b_clamped) + c * (p_pr ** d)
    return round(float(z), 4)


def gas_formation_volume_factor_bg(
    pressure_psig: float,
    temperature_deg_f: float,
    z_factor: float,
) -> float:
    """Calculates gas formation volume factor Bg in cu ft / standard cu ft (scf).

        Bg = 0.02827 x (Z x T_deg_R) / P_psia   [cu ft / scf]

    Args:
        pressure_psig: Pressure (psig).
        temperature_deg_f: Temperature (°F).
        z_factor: Gas compressibility factor.

    Returns:
        Bg in cu ft / scf, rounded to 6 decimal places.
    """
    p_psia = pressure_psig + 14.7
    t_deg_r = temperature_deg_f + 459.67
    if p_psia <= 0:
        raise ValueError("Absolute pressure must be positive.")
    bg = 0.02827 * (z_factor * t_deg_r) / p_psia
    return round(float(bg), 6)


def characterize_kick(
    sidpp_psi: float,
    sicp_psi: float,
    pit_gain_bbl: float,
    annular_capacity_bbl_per_ft: float,
    original_mud_weight_ppg: float,
    bit_tvd_ft: float,
    temperature_deg_f: float = 150.0,
    gas_gravity: float = 0.65,
) -> Dict[str, Any]:
    """Generates a complete engineering report characterizing the kick influx.

    Returns:
        Dictionary with influx height, gradient, density, fluid type,
        pore pressure, and gas Z-factor / Bg if gas.
    """
    h_influx = influx_height_ft(pit_gain_bbl, annular_capacity_bbl_per_ft)
    g_influx = influx_gradient_psi_per_ft(sicp_psi, sidpp_psi, h_influx, original_mud_weight_ppg)
    rho_influx = influx_density_ppg(max(0.0, g_influx))
    fluid_type = classify_influx_type(rho_influx)

    p_form = round_to_whole_number(
        PSI_PER_FT_PER_PPG * original_mud_weight_ppg * bit_tvd_ft + sidpp_psi
    )

    z = gas_z_factor(p_form, temperature_deg_f, gas_gravity)
    bg = gas_formation_volume_factor_bg(p_form, temperature_deg_f, z)

    return {
        "influx_height_ft": h_influx,
        "influx_gradient_psi_per_ft": g_influx,
        "influx_density_ppg": rho_influx,
        "fluid_type": fluid_type,
        "formation_pressure_psi": p_form,
        "is_gas": rho_influx <= GAS_MAX_PPG,
        "z_factor": z,
        "bg_cu_ft_per_scf": bg,
        "bg_bbl_per_mscf": round(bg * 1000.0 / 5.61458, 4),
    }
