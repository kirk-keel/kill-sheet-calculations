"""Subsea well control calculations for subsea BOP stacks.

Units: ppg (mud weight), psi (pressure), ft (depth/length), bbl (volume),
bbl/ft (capacity), bbl/stk (pump output), in (choke line diameter).

Adds the subsea-specific physics:
  - Choke line friction (CLF) acting on the annulus side of the subsea BOP
  - Dynamic MAASP: allowable surface casing reading is reduced by CLF
  - Choke pressure management during pump start-up: hold SICP - CLF so BHP stays constant
  - Choke line volume and displacement strokes
  - Riser margin mud weight and disconnected-riser BHP
"""

from killsheet.formulas import PSI_PER_FT_PER_PPG, kill_mud_weight, maasp, max_allowable_mud_weight
from killsheet.rounding import (
    round_down_to_tenth,
    round_down_to_whole_number,
    round_to_tenth,
    round_to_whole_number,
    round_up_to_next_tenth,
)
from killsheet.strokes import strokes_for_volume

DEFAULT_SEAWATER_DENSITY_PPG = 8.55      # standard 0.445 psi/ft seawater gradient


def choke_line_capacity(choke_line_id_in):
    """Capacity of the choke line in bbl/ft.

        Capacity = ID^2 / 1029.4
    """
    if choke_line_id_in <= 0:
        raise ValueError(f"Choke line ID must be greater than 0 in (got {choke_line_id_in}).")
    return (choke_line_id_in ** 2) / 1029.4


def choke_line_volume(choke_line_id_in, choke_line_length_ft):
    """Internal volume of the choke line in bbl, rounded to 0.1 bbl.

        Volume = Capacity x Length
    """
    if choke_line_length_ft <= 0:
        raise ValueError(f"Choke line length must be greater than 0 ft (got {choke_line_length_ft}).")
    cap = choke_line_capacity(choke_line_id_in)
    return round_to_tenth(cap * choke_line_length_ft)


def choke_line_strokes(choke_line_volume_bbl, pump_output_bbl_per_stk):
    """Strokes to displace the choke line, rounded to whole strokes."""
    return strokes_for_volume(choke_line_volume_bbl, pump_output_bbl_per_stk)


def dynamic_maasp(static_maasp_psi, clf_psi):
    """Dynamic MAASP while circulating up the choke line (psi), whole psi.

        Dynamic MAASP = max(0, Static MAASP - CLF)

    While circulating up the choke line, choke line friction (CLF) adds to the
    casing/shoe pressure. The allowable surface gauge reading must be reduced
    by CLF to keep shoe pressure below the formation breakdown limit.
    """
    if clf_psi < 0:
        raise ValueError(f"CLF cannot be negative (got {clf_psi} psi).")
    return max(0, round_down_to_whole_number(static_maasp_psi - clf_psi))


def choke_pressure_bringing_pump_up(sicp_psi, clf_psi):
    """Surface choke pressure to hold while bringing the pump to kill rate.

        Target Choke Pressure = max(0, SICP - CLF)

    As the pump comes up to speed, CLF builds up on the annulus side and acts
    as backpressure on the bottomhole. To keep BHP strictly constant at formation
    pressure, the choke must be opened so surface casing pressure falls by CLF.
    """
    if sicp_psi < 0:
        raise ValueError(f"SICP cannot be negative (got {sicp_psi} psi).")
    if clf_psi < 0:
        raise ValueError(f"CLF cannot be negative (got {clf_psi} psi).")
    return max(0, round_to_whole_number(sicp_psi - clf_psi))


def riser_margin_mud_weight(original_mud_weight_ppg, tvd_ft, water_depth_ft, air_gap_ft=0,
                            seawater_density_ppg=DEFAULT_SEAWATER_DENSITY_PPG):
    """Riser margin mud weight (ppg), rounded UP to the next 0.1 ppg.

    The mud weight required below the mudline to maintain bottomhole hydrostatic
    pressure if the marine riser is disconnected and seawater stands above the mudline.

        P_hyd_total = 0.052 x OMW x TVD
        P_seawater  = 0.052 x SW_density x water_depth
        P_subsea_needed = P_hyd_total - P_seawater
        TVD_subsea  = TVD - water_depth - air_gap
        MW_rm = P_subsea_needed / (0.052 x TVD_subsea)
    """
    if tvd_ft <= 0:
        raise ValueError(f"TVD must be greater than 0 ft (got {tvd_ft}).")
    if water_depth_ft <= 0:
        raise ValueError(f"Water depth must be greater than 0 ft (got {water_depth_ft}).")
    if air_gap_ft < 0:
        raise ValueError(f"Air gap cannot be negative (got {air_gap_ft}).")
    if original_mud_weight_ppg <= 0:
        raise ValueError(f"Original mud weight must be greater than 0 ppg (got {original_mud_weight_ppg}).")
    subsea_tvd = tvd_ft - water_depth_ft - air_gap_ft
    if subsea_tvd <= 0:
        raise ValueError(f"Subsea TVD (TVD - water depth - air gap) must be > 0 ft (got {subsea_tvd}).")

    p_hyd_total = PSI_PER_FT_PER_PPG * original_mud_weight_ppg * tvd_ft
    p_seawater = PSI_PER_FT_PER_PPG * seawater_density_ppg * water_depth_ft
    p_needed = p_hyd_total - p_seawater
    raw_mw_rm = p_needed / (PSI_PER_FT_PER_PPG * subsea_tvd)
    return round_up_to_next_tenth(raw_mw_rm)


def riser_disconnect_bhp(original_mud_weight_ppg, tvd_ft, water_depth_ft, air_gap_ft=0,
                         seawater_density_ppg=DEFAULT_SEAWATER_DENSITY_PPG):
    """Bottomhole hydrostatic pressure (psi) after riser disconnect.

    Evaluates hydrostatic with seawater from surface/sea level to seabed, and original mud
    below the seabed to total depth.
    """
    if tvd_ft <= 0 or water_depth_ft <= 0 or original_mud_weight_ppg <= 0:
        raise ValueError("TVD, water depth, and original mud weight must be greater than 0.")
    subsea_tvd = tvd_ft - water_depth_ft - air_gap_ft
    if subsea_tvd < 0:
        raise ValueError("Water depth + air gap cannot exceed total TVD.")
    p_sw = PSI_PER_FT_PER_PPG * seawater_density_ppg * water_depth_ft
    p_mud = PSI_PER_FT_PER_PPG * original_mud_weight_ppg * subsea_tvd
    return round_to_whole_number(p_sw + p_mud)


def subsea_kill_summary(original_mud_weight_ppg, tvd_ft, shoe_tvd_ft, lot_emw_ppg,
                        sidpp_psi, sicp_psi, scr_pressure_psi, pump_output_bbl_per_stk,
                        choke_line_id_in, choke_line_length_ft, clf_psi,
                        water_depth_ft, air_gap_ft=0,
                        seawater_density_ppg=DEFAULT_SEAWATER_DENSITY_PPG):
    """Complete subsea kill sheet calculation summary as a dictionary."""
    kmw = kill_mud_weight(sidpp_psi, tvd_ft, original_mud_weight_ppg)
    cl_vol = choke_line_volume(choke_line_id_in, choke_line_length_ft)
    cl_stk = choke_line_strokes(cl_vol, pump_output_bbl_per_stk)

    # Static MAASP from shoe test
    test_lot_psi = (lot_emw_ppg - original_mud_weight_ppg) * PSI_PER_FT_PER_PPG * shoe_tvd_ft
    mamw = max_allowable_mud_weight(test_lot_psi, shoe_tvd_ft, original_mud_weight_ppg)
    static_maasp_psi = maasp(mamw, original_mud_weight_ppg, shoe_tvd_ft)
    dyn_maasp_psi = dynamic_maasp(static_maasp_psi, clf_psi)

    choke_start_psi = choke_pressure_bringing_pump_up(sicp_psi, clf_psi)
    mw_rm = riser_margin_mud_weight(original_mud_weight_ppg, tvd_ft, water_depth_ft, air_gap_ft, seawater_density_ppg)
    post_disc_bhp = riser_disconnect_bhp(original_mud_weight_ppg, tvd_ft, water_depth_ft, air_gap_ft, seawater_density_ppg)
    formation_pressure = round_to_whole_number(sidpp_psi + PSI_PER_FT_PER_PPG * original_mud_weight_ppg * tvd_ft)

    return {
        "kill_mud_weight_ppg": kmw,
        "choke_line_volume_bbl": cl_vol,
        "choke_line_strokes": cl_stk,
        "static_maasp_psi": static_maasp_psi,
        "dynamic_maasp_psi": dyn_maasp_psi,
        "choke_line_friction_psi": clf_psi,
        "choke_pressure_at_kill_rate_psi": choke_start_psi,
        "riser_margin_mud_weight_ppg": mw_rm,
        "riser_margin_delta_ppg": round_to_tenth(mw_rm - original_mud_weight_ppg),
        "post_disconnect_bhp_psi": post_disc_bhp,
        "formation_pressure_psi": formation_pressure,
        "disconnect_overbalance_psi": post_disc_bhp - formation_pressure,
    }
