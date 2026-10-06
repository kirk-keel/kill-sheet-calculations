"""Rounding helpers used by every kill sheet calculation.

The three rounding rules (based on the IADC WellSharp Formula Sheet,
Field Units, Rev 4, 2025):
  1. Kill mud weight is always rounded UP to the NEXT 0.1 ppg - even an
     exact value goes up (10.8 -> 10.9), so the well is killed, not
     just balanced.
  2. Anything that is a MAXIMUM (max allowable mud weight, MAASP) is
     always rounded DOWN. The pressure reduction schedule is also
     rounded DOWN, per IADC.
  3. Everything else uses academic rounding (.5 goes up) to the accuracy
     in IADC's table: pressures and strokes to a whole number, volumes
     to 0.1 bbl.
  Rounded values are carried forward into later calculations.

Every helper first tidies the value to 6 decimal places so that tiny
computer arithmetic errors (10.8 stored as 10.7999999999) can't change
the answer. Python's built-in round() is not used because it rounds .5
to the nearest EVEN number (894.5 -> 894), which is not academic rounding.
"""

import math


def round_up_to_next_tenth(value):
    """Round UP to the NEXT 0.1, even if the value is already exact.

    Examples: 10.73 -> 10.8, 10.81 -> 10.9, 10.80 -> 10.9.

    Used for kill mud weight. An exact value only BALANCES the formation;
    the extra 0.1 ppg is the minimum safety factor that KILLS the well.
    """
    return (math.floor(round(value * 10, 6)) + 1) / 10


def round_down_to_tenth(value):
    """Round DOWN to the previous 0.1 (e.g. 14.39 -> 14.3, 14.30 -> 14.3).

    Used for max allowable mud weight.
    """
    return math.floor(round(value * 10, 6)) / 10


def round_to_tenth(value):
    """Round to the NEAREST 0.1, with .05 always going up (188.68 -> 188.7).

    Used for volumes (bbl).
    """
    return math.floor(round(value * 10, 6) + 0.5) / 10


def round_to_whole_number(value):
    """Round to the NEAREST whole number, with .5 always going up (895.5 -> 896).

    Used for pressures (psi) and strokes.
    """
    return math.floor(round(value, 6) + 0.5)


def round_down_to_whole_number(value):
    """Round DOWN to the previous whole number (e.g. 1497.6 -> 1497).

    Used for MAASP and the pressure reduction schedule.
    """
    return math.floor(round(value, 6))
