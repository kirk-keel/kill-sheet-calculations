"""Wellbore hydraulics, bit nozzle jet optimization, annular pressure losses, and ECD.

Standards & Conventions:
  - Density & Mud Weight: ppg (0.052 psi/ft per ppg)
  - Flow Rate: gpm (gallons per minute)
  - Pressures: psi
  - Nozzle sizes: 32nds of an inch (e.g., [12, 12, 12] for three 12/32" nozzles)
  - Diameters: inches (in)
  - Depths: feet (ft)
  - Plastic Viscosity (PV): cP (centipoise)
  - Yield Point (YP): lbf/100 sq ft

Physical Model:
  1. Total Flow Area (TFA):
       TFA = sum( (pi / 4) x (nozzle_32nds / 32)^2 )  [sq in]
  2. Nozzle Fluid Velocity:
       V_n = (0.32086 x Q_gpm) / TFA  [ft/s]   (or Q / (3.117 x TFA))
  3. Bit Pressure Loss:
       dP_bit = (MW_ppg x Q_gpm^2) / (10858 x TFA^2)  [psi]  (for Cd = 0.95)
  4. Bit Hydraulic Horsepower (HHP):
       HHP_bit = (dP_bit x Q_gpm) / 1714
  5. Hydraulic Horsepower per Square Inch (HSI):
       HSI = HHP_bit / ((pi / 4) x Bit_Diameter^2)  [hp/sq in]
  6. Jet Impact Force (JIF):
       JIF = 0.01733 x Q_gpm x sqrt(MW_ppg x dP_bit)  [lbf]
  7. Annular Pressure Drop (Bingham Plastic):
       V_ann = (24.5 x Q_gpm) / (D_hole^2 - D_pipe^2)  [ft/min]
       dP_ann = [ (PV x V_ann) / (60000 x (D_hole - D_pipe)^2) + YP / (200 x (D_hole - D_pipe)) ] x Length_ft
  8. Equivalent Circulating Density (ECD):
       ECD = MW_ppg + dP_ann / (0.052 x TVD_ft)  [ppg]
"""

import math
from typing import Any, Dict, List

from killsheet.formulas import PSI_PER_FT_PER_PPG
from killsheet.rounding import (
    round_to_hundredth,
    round_to_tenth,
    round_to_thousandth,
    round_to_whole_number,
)

DISCHARGE_COEFFICIENT_CD = 0.95


def total_flow_area_sq_in(nozzle_sizes_in_32nds: List[int]) -> float:
    """Calculates Total Flow Area (TFA) in square inches for a set of bit nozzles.

    Args:
        nozzle_sizes_in_32nds: List of nozzle diameters in 32nds of an inch (e.g. [11, 11, 11]).

    Returns:
        TFA in sq inches, rounded to 4 decimal places.
    """
    if not nozzle_sizes_in_32nds:
        raise ValueError("Must provide at least one nozzle size.")
    for n in nozzle_sizes_in_32nds:
        if n <= 0:
            raise ValueError(f"Nozzle sizes must be positive integers in 32nds (got {n}).")

    total_area = sum((math.pi / 4.0) * ((size / 32.0) ** 2) for size in nozzle_sizes_in_32nds)
    return round(total_area, 4)


def nozzle_velocity_fps(flow_rate_gpm: float, tfa_sq_in: float) -> float:
    """Calculates fluid exit velocity through bit nozzles in feet per second (ft/s).

        V_n = Q_gpm / (3.117 x TFA)
    """
    if flow_rate_gpm <= 0:
        raise ValueError("Flow rate must be positive.")
    if tfa_sq_in <= 0:
        raise ValueError("Total Flow Area (TFA) must be positive.")
    v = flow_rate_gpm / (3.117 * tfa_sq_in)
    return round_to_tenth(v)


def bit_pressure_drop_psi(
    mud_weight_ppg: float,
    flow_rate_gpm: float,
    tfa_sq_in: float,
    discharge_coefficient: float = DISCHARGE_COEFFICIENT_CD,
) -> int:
    """Calculates pressure drop across the drill bit nozzles (psi).

        dP_bit = (MW x Q^2) / (12031 x Cd^2 x TFA^2)
        With standard Cd = 0.95: 12031 x 0.95^2 = 10858
    """
    if mud_weight_ppg <= 0 or flow_rate_gpm <= 0 or tfa_sq_in <= 0:
        raise ValueError("Mud weight, flow rate, and TFA must be positive.")
    if discharge_coefficient <= 0:
        raise ValueError("Discharge coefficient must be positive.")

    factor = 12031.0 * (discharge_coefficient ** 2)
    dp = (mud_weight_ppg * (flow_rate_gpm ** 2)) / (factor * (tfa_sq_in ** 2))
    return round_to_whole_number(dp)


def bit_hydraulic_horsepower(dp_bit_psi: float, flow_rate_gpm: float) -> float:
    """Calculates hydraulic horsepower expended at the drill bit (HHP).

        HHP = (dP_bit x Q) / 1714
    """
    if dp_bit_psi < 0 or flow_rate_gpm < 0:
        raise ValueError("Pressure drop and flow rate cannot be negative.")
    hhp = (dp_bit_psi * flow_rate_gpm) / 1714.0
    return round_to_tenth(hhp)


def hydraulic_horsepower_per_sq_in(hhp: float, bit_diameter_in: float) -> float:
    """Calculates hydraulic horsepower per square inch of bottomhole area (HSI).

        HSI = HHP / ((pi / 4) x Bit_Diameter^2)
    """
    if bit_diameter_in <= 0:
        raise ValueError("Bit diameter must be positive.")
    area = (math.pi / 4.0) * (bit_diameter_in ** 2)
    return round_to_hundredth(hhp / area)


def jet_impact_force_lbf(
    mud_weight_ppg: float,
    flow_rate_gpm: float,
    dp_bit_psi: float,
) -> int:
    """Calculates hydraulic jet impact force (lbf) cleaning the bottomhole.

        JIF = 0.01733 x Q x sqrt(MW x dP_bit)
    """
    if mud_weight_ppg <= 0 or flow_rate_gpm <= 0 or dp_bit_psi < 0:
        raise ValueError("Mud weight, flow rate, and pressure drop must be non-negative.")
    jif = 0.01733 * flow_rate_gpm * math.sqrt(mud_weight_ppg * dp_bit_psi)
    return round_to_whole_number(jif)


def annular_pressure_loss_psi(
    mud_weight_ppg: float,
    plastic_viscosity_cp: float,
    yield_point_lbf_100sqft: float,
    flow_rate_gpm: float,
    hole_diameter_in: float,
    pipe_od_in: float,
    interval_length_ft: float,
) -> int:
    """Calculates annular friction pressure loss (psi) using the Bingham Plastic rheology model.

        V_ann = (24.5 x Q) / (D_hole^2 - D_pipe^2)   [ft/min]
        dP_ann = [ (PV x V_ann) / (60000 x (Dh - Dp)^2) + YP / (200 x (Dh - Dp)) ] x L
    """
    if hole_diameter_in <= pipe_od_in:
        raise ValueError("Hole diameter must be greater than pipe OD.")
    if interval_length_ft <= 0 or flow_rate_gpm <= 0:
        raise ValueError("Interval length and flow rate must be positive.")

    dh_minus_dp = hole_diameter_in - pipe_od_in
    dh2_minus_dp2 = (hole_diameter_in ** 2) - (pipe_od_in ** 2)

    v_ann = (24.5 * flow_rate_gpm) / dh2_minus_dp2

    visc_term = (plastic_viscosity_cp * v_ann) / (60000.0 * (dh_minus_dp ** 2))
    yield_term = yield_point_lbf_100sqft / (200.0 * dh_minus_dp)

    dp_per_ft = visc_term + yield_term
    total_dp = dp_per_ft * interval_length_ft
    return round_to_whole_number(total_dp)


def equivalent_circulating_density_ppg(
    mud_weight_ppg: float,
    annular_loss_psi: float,
    tvd_ft: float,
) -> float:
    """Calculates Equivalent Circulating Density (ECD) in ppg at depth.

        ECD = MW + dP_ann / (0.052 x TVD)
    """
    if tvd_ft <= 0:
        raise ValueError("TVD must be positive.")
    if mud_weight_ppg <= 0:
        raise ValueError("Mud weight must be positive.")

    delta_ecd = annular_loss_psi / (PSI_PER_FT_PER_PPG * tvd_ft)
    return round_to_hundredth(mud_weight_ppg + delta_ecd)


def bit_hydraulics_report(
    mud_weight_ppg: float,
    flow_rate_gpm: float,
    bit_diameter_in: float,
    nozzle_sizes_in_32nds: List[int],
) -> Dict[str, Any]:
    """Generates a comprehensive bit hydraulics optimization summary."""
    tfa = total_flow_area_sq_in(nozzle_sizes_in_32nds)
    v_nozzle = nozzle_velocity_fps(flow_rate_gpm, tfa)
    dp_bit = bit_pressure_drop_psi(mud_weight_ppg, flow_rate_gpm, tfa)
    hhp = bit_hydraulic_horsepower(dp_bit, flow_rate_gpm)
    hsi = hydraulic_horsepower_per_sq_in(hhp, bit_diameter_in)
    jif = jet_impact_force_lbf(mud_weight_ppg, flow_rate_gpm, dp_bit)

    return {
        "tfa_sq_in": tfa,
        "nozzle_velocity_fps": v_nozzle,
        "bit_pressure_drop_psi": dp_bit,
        "hydraulic_horsepower_hhp": hhp,
        "hsi_hp_per_sq_in": hsi,
        "jet_impact_force_lbf": jif,
    }
