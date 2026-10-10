"""Core kill sheet formulas for a vertical well with a surface BOP stack.

Units: ppg (mud weight), psi (pressure), ft (true vertical depth).
Every function is "pure": it only uses its inputs and returns a number.

Rounding follows the three rules described in rounding.py.
"""

from killsheet.rounding import (
    round_down_to_tenth,
    round_down_to_whole_number,
    round_to_whole_number,
    round_up_to_next_tenth,
)

# Converts mud weight (ppg) and depth (ft) into hydrostatic pressure (psi).
PSI_PER_FT_PER_PPG = 0.052


def kill_mud_weight(sidpp_psi, tvd_ft, original_mud_weight_ppg):
    """Kill mud weight (ppg), rounded UP to the NEXT 0.1 ppg.

        KMW = OMW + SIDPP / (0.052 x TVD)

    Uses TRUE VERTICAL depth of the bit, not measured depth.
    An exact answer still goes up 0.1 ppg (11.0 -> 11.1) as a safety factor.

    SIDPP must be greater than 0. A zero reading with a float in the string
    is not a true SIDPP - the float must be bumped to find it.
    """
    if sidpp_psi <= 0:
        raise ValueError(
            "SIDPP must be greater than 0 psi. If the drill pipe reads 0 with a "
            "float in the string, bump the float to determine the true SIDPP."
        )
    raw_kmw = original_mud_weight_ppg + sidpp_psi / (PSI_PER_FT_PER_PPG * tvd_ft)
    return round_up_to_next_tenth(raw_kmw)


def initial_circulating_pressure(sidpp_psi, scr_pressure_psi):
    """Initial circulating pressure (psi), rounded to a whole number.

        ICP = SIDPP + SCR pressure

    SCR pressure is the slow circulating rate pressure at the kill pump rate.
    """
    return round_to_whole_number(sidpp_psi + scr_pressure_psi)


def final_circulating_pressure(scr_pressure_psi, kill_mud_weight_ppg, original_mud_weight_ppg):
    """Final circulating pressure (psi), rounded to a whole number.

        FCP = SCR pressure x (KMW / OMW)

    Pass in the already-rounded KMW from kill_mud_weight().
    """
    return round_to_whole_number(scr_pressure_psi * (kill_mud_weight_ppg / original_mud_weight_ppg))


def max_allowable_mud_weight(lot_pressure_psi, shoe_tvd_ft, test_mud_weight_ppg):
    """Maximum allowable mud weight (ppg), rounded DOWN to 0.1 ppg.

        Max MW = Test MW + LOT pressure / (0.052 x Shoe TVD)

    LOT pressure is the surface leak-off pressure from the shoe test,
    and Test MW is the mud weight in the hole during that test.
    """
    raw_max_mw = test_mud_weight_ppg + lot_pressure_psi / (PSI_PER_FT_PER_PPG * shoe_tvd_ft)
    return round_down_to_tenth(raw_max_mw)


def maasp(max_allowable_mud_weight_ppg, current_mud_weight_ppg, shoe_tvd_ft):
    """Maximum allowable annular surface pressure (psi), rounded DOWN to a whole number.

        MAASP = (Max MW - Current MW) x 0.052 x Shoe TVD

    Pass in the already-rounded Max MW from max_allowable_mud_weight().
    Recalculate with the kill mud weight once the annulus is displaced.
    """
    raw_maasp = (max_allowable_mud_weight_ppg - current_mud_weight_ppg) * PSI_PER_FT_PER_PPG * shoe_tvd_ft
    return round_down_to_whole_number(raw_maasp)


def kill_mud_overbalance(kill_mud_weight_ppg, original_mud_weight_ppg, tvd_ft):
    """Extra hydrostatic (psi) of a full column of kill mud, whole psi.

        Overbalance = (KMW - OMW) x 0.052 x TVD

    Because KMW is rounded UP, this is a little MORE than SIDPP
    (baseline well: 1.1 x 0.052 x 11,500 = 657.8 -> 658 psi vs SIDPP 650).
    """
    return round_to_whole_number(
        (kill_mud_weight_ppg - original_mud_weight_ppg) * PSI_PER_FT_PER_PPG * tvd_ft)
