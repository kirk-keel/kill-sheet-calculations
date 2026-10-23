"""Kick tolerance, kick intensity, and casing seat drilling window calculations.

Standards & Conventions:
  - Density & Gradients: ppg (0.052 psi/ft per ppg)
  - Pressure: psi
  - Depths: ft (TVD)
  - Volume: bbl
  - Annular Capacity: bbl/ft

Physical Model:
  Evaluates the maximum gas influx volume (Kick Tolerance, KT) that can be shut in
  and circulated out using constant bottomhole pressure without hydraulically
  fracturing the open hole at the casing shoe.
  Uses a single-bubble gas migration model governed by Boyle's Law (P1 x V1 = P2 x V2)
  evaluated at the critical condition where the gas bubble top reaches the casing shoe.
"""

from killsheet.formulas import PSI_PER_FT_PER_PPG
from killsheet.rounding import (
    round_down_to_tenth,
    round_to_tenth,
    round_to_whole_number,
    round_up_to_next_tenth,
)

DEFAULT_GAS_GRADIENT_PSI_PER_FT = 0.10  # Standard conservative gas gradient (0.10 - 0.15 psi/ft)


def kick_intensity_ppg(sidpp_psi: float, tvd_ft: float) -> float:
    """Kick intensity in ppg, rounded to 0.1 ppg.

        Kick Intensity = SIDPP / (0.052 x TVD)

    Represents the equivalent mud weight deficit between the in-situ mud weight
    and the pore pressure of the kicking formation.
    """
    if sidpp_psi < 0:
        raise ValueError(f"SIDPP cannot be negative (got {sidpp_psi} psi).")
    if tvd_ft <= 0:
        raise ValueError(f"TVD must be greater than 0 ft (got {tvd_ft}).")
    return round_to_tenth(sidpp_psi / (PSI_PER_FT_PER_PPG * tvd_ft))


def formation_pore_pressure_psi(mud_weight_ppg: float, tvd_ft: float, sidpp_psi: float) -> int:
    """Formation pore pressure (psi), rounded to whole psi.

        P_form = 0.052 x MW x TVD + SIDPP
    """
    if mud_weight_ppg <= 0 or tvd_ft <= 0:
        raise ValueError("Mud weight and TVD must be greater than 0.")
    if sidpp_psi < 0:
        raise ValueError("SIDPP cannot be negative.")
    return round_to_whole_number(PSI_PER_FT_PER_PPG * mud_weight_ppg * tvd_ft + sidpp_psi)


def shoe_fracture_pressure_psi(lot_emw_ppg: float, shoe_tvd_ft: float) -> int:
    """Formation breakdown / fracture pressure at the casing shoe (psi), whole psi.

        P_frac = 0.052 x LOT_EMW x Shoe_TVD
    """
    if lot_emw_ppg <= 0 or shoe_tvd_ft <= 0:
        raise ValueError("LOT EMW and Shoe TVD must be greater than 0.")
    return round_to_whole_number(PSI_PER_FT_PER_PPG * lot_emw_ppg * shoe_tvd_ft)


def max_gas_height_at_shoe_ft(mud_weight_ppg: float, tvd_ft: float, shoe_tvd_ft: float,
                              lot_emw_ppg: float, sidpp_psi: float,
                              gas_gradient_psi_per_ft: float = DEFAULT_GAS_GRADIENT_PSI_PER_FT) -> int:
    """Maximum vertical height of gas influx (ft) at the casing shoe before exceeding fracture pressure.

        H_max = [P_frac - P_form + 0.052 x MW x (TVD - Shoe_TVD)] / (0.052 x MW - G_gas)

    Returns whole feet, bounded by [0, TVD - Shoe_TVD].
    """
    if tvd_ft <= shoe_tvd_ft:
        raise ValueError(f"TVD ({tvd_ft:,} ft) must be deeper than Shoe TVD ({shoe_tvd_ft:,} ft).")
    if mud_weight_ppg <= 0 or lot_emw_ppg <= 0:
        raise ValueError("Mud weight and LOT EMW must be greater than 0.")

    mud_grad = PSI_PER_FT_PER_PPG * mud_weight_ppg
    if mud_grad <= gas_gradient_psi_per_ft:
        raise ValueError("Mud gradient must exceed gas gradient.")

    p_frac = shoe_fracture_pressure_psi(lot_emw_ppg, shoe_tvd_ft)
    p_form = formation_pore_pressure_psi(mud_weight_ppg, tvd_ft, sidpp_psi)
    open_hole_length = tvd_ft - shoe_tvd_ft

    numerator = p_frac - p_form + mud_grad * open_hole_length
    denominator = mud_grad - gas_gradient_psi_per_ft

    raw_hmax = numerator / denominator
    bounded_hmax = max(0.0, min(float(open_hole_length), raw_hmax))
    return round_to_whole_number(bounded_hmax)


def kick_tolerance_bbl(mud_weight_ppg: float, tvd_ft: float, shoe_tvd_ft: float,
                       lot_emw_ppg: float, sidpp_psi: float,
                       annular_capacity_bbl_per_ft: float,
                       gas_gradient_psi_per_ft: float = DEFAULT_GAS_GRADIENT_PSI_PER_FT) -> float:
    """Maximum gas kick volume (bbl) at bottomhole conditions, rounded DOWN to 0.1 bbl.

        V_shoe = H_max x Annular_Capacity
        KT_bottom = V_shoe x (P_frac / P_form)    [Boyle's Law expansion]

    Rounded DOWN to guarantee conservative safety margin against shoe breakdown.
    """
    if annular_capacity_bbl_per_ft <= 0:
        raise ValueError("Annular capacity must be greater than 0.")

    h_max = max_gas_height_at_shoe_ft(
        mud_weight_ppg, tvd_ft, shoe_tvd_ft, lot_emw_ppg, sidpp_psi, gas_gradient_psi_per_ft
    )
    if h_max <= 0:
        return 0.0

    p_frac = shoe_fracture_pressure_psi(lot_emw_ppg, shoe_tvd_ft)
    p_form = formation_pore_pressure_psi(mud_weight_ppg, tvd_ft, sidpp_psi)

    v_shoe = h_max * annular_capacity_bbl_per_ft
    raw_kt = v_shoe * (p_frac / p_form)
    return round_down_to_tenth(raw_kt)


def required_shoe_lot_ppg(target_kick_volume_bbl: float, mud_weight_ppg: float,
                          tvd_ft: float, shoe_tvd_ft: float, sidpp_psi: float,
                          annular_capacity_bbl_per_ft: float,
                          gas_gradient_psi_per_ft: float = DEFAULT_GAS_GRADIENT_PSI_PER_FT) -> float:
    """Minimum LOT / FIT fracture gradient (ppg EMW) required to safely handle target kick volume.

    Rounds UP to the next 0.1 ppg for conservative casing design.
    """
    if target_kick_volume_bbl <= 0:
        raise ValueError("Target kick volume must be > 0 bbl.")
    if tvd_ft <= shoe_tvd_ft:
        raise ValueError("TVD must be deeper than shoe TVD.")

    p_form = formation_pore_pressure_psi(mud_weight_ppg, tvd_ft, sidpp_psi)
    mud_grad = PSI_PER_FT_PER_PPG * mud_weight_ppg
    diff_grad = mud_grad - gas_gradient_psi_per_ft
    open_hole_ft = tvd_ft - shoe_tvd_ft

    # Solving: V_shoe x P_frac / P_form = target_kick_volume
    # where V_shoe = [P_frac - P_form + mud_grad x OH] / diff_grad x C_ann
    # Let K = (target_kick_volume x P_form x diff_grad) / C_ann
    # P_frac x [P_frac - P_form + mud_grad x OH] = K
    # Quadratic equation: P_frac^2 + B x P_frac - K = 0
    b_coeff = -(p_form - mud_grad * open_hole_ft)
    k_const = (target_kick_volume_bbl * p_form * diff_grad) / annular_capacity_bbl_per_ft

    # P_frac = (-B + sqrt(B^2 + 4K)) / 2
    discriminant = b_coeff ** 2 + 4 * k_const
    p_frac_req = (-b_coeff + (discriminant ** 0.5)) / 2.0

    raw_lot = p_frac_req / (PSI_PER_FT_PER_PPG * shoe_tvd_ft)
    return round_up_to_next_tenth(raw_lot)


def kick_tolerance_summary(mud_weight_ppg: float, tvd_ft: float, shoe_tvd_ft: float,
                           lot_emw_ppg: float, sidpp_psi: float,
                           annular_capacity_bbl_per_ft: float,
                           gas_gradient_psi_per_ft: float = DEFAULT_GAS_GRADIENT_PSI_PER_FT) -> dict:
    """Comprehensive kick tolerance evaluation summary dictionary."""
    ki = kick_intensity_ppg(sidpp_psi, tvd_ft)
    p_form = formation_pore_pressure_psi(mud_weight_ppg, tvd_ft, sidpp_psi)
    p_frac = shoe_fracture_pressure_psi(lot_emw_ppg, shoe_tvd_ft)
    h_max = max_gas_height_at_shoe_ft(
        mud_weight_ppg, tvd_ft, shoe_tvd_ft, lot_emw_ppg, sidpp_psi, gas_gradient_psi_per_ft
    )
    v_shoe = round_to_tenth(h_max * annular_capacity_bbl_per_ft)
    kt_bottom = kick_tolerance_bbl(
        mud_weight_ppg, tvd_ft, shoe_tvd_ft, lot_emw_ppg, sidpp_psi,
        annular_capacity_bbl_per_ft, gas_gradient_psi_per_ft
    )

    return {
        "mud_weight_ppg": mud_weight_ppg,
        "kick_intensity_ppg": ki,
        "equivalent_pore_pressure_ppg": round_to_tenth(mud_weight_ppg + ki),
        "formation_pressure_psi": p_form,
        "shoe_fracture_pressure_psi": p_frac,
        "shoe_maasp_psi": round_to_whole_number(p_frac - PSI_PER_FT_PER_PPG * mud_weight_ppg * shoe_tvd_ft),
        "max_gas_height_at_shoe_ft": h_max,
        "max_gas_volume_at_shoe_bbl": v_shoe,
        "kick_tolerance_bottomhole_bbl": kt_bottom,
    }
