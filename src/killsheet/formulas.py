"""Core kill sheet formulas for a vertical well with a surface BOP stack.

Units: ppg (mud weight), psi (pressure), ft (true vertical depth).
Every function is "pure": it only uses its inputs and returns a number.

Rounding rules (IADC WellSharp Formula Sheet, Field Units, Rev 4, 2025):
  1. Kill mud weight is always rounded UP to 0.1 ppg.
  2. Anything that is a MAXIMUM (max allowable mud weight, MAASP) is
     always rounded DOWN.
  3. Everything else uses ordinary rounding (.5 goes up) to the
     accuracy in IADC's table (e.g. pressures to a whole psi).
  Rounded values are carried forward into later calculations.
"""

import math

# Converts mud weight (ppg) and depth (ft) into hydrostatic pressure (psi).
PSI_PER_FT_PER_PPG = 0.052


def round_up_to_tenth(value):
    """Round UP to the next 0.1 (e.g. 10.81 -> 10.9, 10.80 -> 10.8).

    The value is first tidied to 6 decimal places so that tiny computer
    arithmetic errors (10.8 stored as 10.8000000001) don't push it up an
    extra 0.1 ppg.
    """
    return math.ceil(round(value * 10, 6)) / 10


def round_down_to_tenth(value):
    """Round DOWN to the previous 0.1 (e.g. 14.39 -> 14.3, 14.30 -> 14.3).

    Tidied to 6 decimal places first, for the same reason as round_up_to_tenth.
    """
    return math.floor(round(value * 10, 6)) / 10


def round_to_whole_number(value):
    """Round to the NEAREST whole number, with .5 always going up (895.5 -> 896).

    Used for pressures (psi). Python's built-in round() is not used because
    it rounds .5 to the nearest EVEN number (894.5 -> 894), which is not
    how anyone rounds on a kill sheet.
    """
    return math.floor(round(value, 6) + 0.5)


def round_down_to_whole_number(value):
    """Round DOWN to the previous whole number (e.g. 1497.6 -> 1497).

    Used for maximum pressures such as MAASP, which must never be overstated.
    """
    return math.floor(round(value, 6))


def kill_mud_weight(sidpp_psi, tvd_ft, original_mud_weight_ppg):
    """Kill mud weight (ppg), rounded UP to 0.1 ppg.

        KMW = OMW + SIDPP / (0.052 x TVD)

    Uses TRUE VERTICAL depth of the bit, not measured depth.
    """
    raw_kmw = original_mud_weight_ppg + sidpp_psi / (PSI_PER_FT_PER_PPG * tvd_ft)
    return round_up_to_tenth(raw_kmw)


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
