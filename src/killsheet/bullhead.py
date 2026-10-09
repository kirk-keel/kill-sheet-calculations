"""Bullheading while drilling: push the influx back into the formation.

When a kick is too large to handle at surface, the annular can be shut and
kill fluid pumped down the drill string AND the backside at the SAME rate, at
the same time, the whole way. With the annular shut the fluid has nowhere to
go but back into the formation: pressure builds until injectivity is
established, then falls as the fluid is pushed away. The goal is INJECTIVITY,
not breaking down the formation - stay below the max on both sides.

Limits (each row of the chart uses the LOWER of the two):
  Formation limit - from the LOT / MAMW at the shoe (the weak point).
  Equipment limit - the lowest rating or tested value of the equipment.

Max static surface pressure (influx treated as original mud - conservative):

  Annulus: 0.052 x [MAMW x Shoe TVD - weight of fluid above the shoe x TVD]
  String:  0.052 x [MAMW x Shoe TVD
                    - weight of string fluid x TVD to the bit
                    + weight of annulus fluid x TVD from the shoe to the bit]

The shoe is on the annulus side; the string reaches it by going down to the
bit and back up the annulus, so the string limit depends on what is in BOTH
columns. Both limits are rounded DOWN (rule 2).

Kill fluid density is the kill mud weight - always rounded UP to the next
0.1 ppg (rule 1).
"""

from typing import NamedTuple

from killsheet.depths import tvd_at_md
from killsheet.formulas import PSI_PER_FT_PER_PPG
from killsheet.rounding import round_down_to_whole_number, round_to_whole_number
from killsheet.schedule import strokes_per_step_for_ten_steps
from killsheet.strokes import md_after_strokes, strokes_to_length, surface_to_bit_strokes, total_length

# Row labels.
STEP = "step"
STRING_CROSSOVER = "string crossover"
STRING_AT_BIT = "kill fluid at the bit (string)"
ANNULUS_AT_SHOE = "kill fluid at the shoe (annulus)"
ANNULUS_AT_BOTTOM = "kill fluid at bottom (annulus) - kill point"
OVERDISPLACED = "overdisplaced"


class BullheadRow(NamedTuple):
    """One row of the bullhead pressure chart (strokes are the same on both sides)."""

    strokes: int
    string_kill_md_ft: int          # how far kill fluid is down the string
    annulus_kill_md_ft: int         # how far kill fluid is down the annulus
    string_max_psi: int             # lower of formation and equipment limits
    annulus_max_psi: int
    label: str


def equipment_limit(equipment_ratings):
    """The equipment limit (psi): the lowest rating or tested value.

    equipment_ratings: list of (name, psi), e.g. [("BOP stack, tested", 3_500), ...]
    Returns (name, psi) of the limiting piece of equipment.
    """
    return min(equipment_ratings, key=lambda item: item[1])


def gas_migration_rate(sicp_increase_psi_per_hr, mud_gradient_psi_per_ft):
    """Gas migration rate (ft/hr), to a whole ft/hr - IADC #34.

        Migration rate = SICP increase over the last hour / Mud gradient
    """
    return round_to_whole_number(sicp_increase_psi_per_hr / mud_gradient_psi_per_ft)


def minimum_spm_to_beat_gas_migration(migration_rate_ft_per_hr, annular_capacity_bbl_per_ft,
                                      pump_output_bbl_per_stk):
    """Minimum pump rate (spm) to stay ahead of migrating gas, rounded UP - IADC #13.

        SPM = (Migration rate / 60) x Annular capacity / Pump output

    Use the LARGEST annular capacity the gas is in (conservative). It is a
    minimum, so it is rounded UP to a whole spm (the mirror of rule 2).
    """
    raw_spm = migration_rate_ft_per_hr / 60 * annular_capacity_bbl_per_ft / pump_output_bbl_per_stk
    return -round_down_to_whole_number(-raw_spm)        # round UP


def bullhead_limits(kill_md_string_ft, kill_md_annulus_ft, original_mud_weight_ppg, kill_fluid_ppg,
                    mamw_ppg, shoe_md_ft, shoe_tvd_ft, bit_md_ft, survey):
    """Formation limit on each side (psi), rounded DOWN: (string_max, annulus_max).

    kill_md_string_ft / kill_md_annulus_ft: how far kill fluid has got down each side (MD).
    survey: (MD, TVD) points for the well path, including the bit.
    """
    bit_tvd = tvd_at_md(bit_md_ft, survey)
    string_kill_tvd = tvd_at_md(kill_md_string_ft, survey)
    # Annulus above the shoe: kill fluid down to the shoe at most.
    annulus_kill_tvd_above_shoe = tvd_at_md(min(kill_md_annulus_ft, shoe_md_ft), survey)
    # Annulus below the shoe: kill fluid from the shoe down to the kill fluid front.
    annulus_kill_tvd_below = tvd_at_md(max(kill_md_annulus_ft, shoe_md_ft), survey)

    shoe_strength = mamw_ppg * shoe_tvd_ft
    above_shoe = kill_fluid_ppg * annulus_kill_tvd_above_shoe + original_mud_weight_ppg * (
        shoe_tvd_ft - annulus_kill_tvd_above_shoe)
    string_column = kill_fluid_ppg * string_kill_tvd + original_mud_weight_ppg * (bit_tvd - string_kill_tvd)
    below_shoe = kill_fluid_ppg * (annulus_kill_tvd_below - shoe_tvd_ft) + original_mud_weight_ppg * (
        bit_tvd - annulus_kill_tvd_below)

    annulus_max = PSI_PER_FT_PER_PPG * (shoe_strength - above_shoe)
    string_max = PSI_PER_FT_PER_PPG * (shoe_strength - string_column + below_shoe)
    return round_down_to_whole_number(string_max), round_down_to_whole_number(annulus_max)


def bullhead_chart(original_mud_weight_ppg, kill_fluid_ppg, mamw_ppg, shoe_tvd_ft,
                   drill_string_sections, annulus_sections_bottom_up, pump_output_bbl_per_stk,
                   equipment_limit_psi, overdisplacement_bbl=0, shoe_md_ft=None, bit_tvd_ft=None,
                   key_points=()):
    """The bullhead pressure chart - the same strokes down both sides.

    Steps: 10 steps of the ANNULUS strokes to bottom (the longer side), plus a
    row at every string crossover, where kill fluid reaches the bit, where it
    reaches the shoe in the annulus, the kill point, and after overdisplacement.

    Vertical well: leave out shoe_md_ft, bit_tvd_ft and key_points.
    """
    pump = pump_output_bbl_per_stk
    bit_md_ft = total_length(drill_string_sections)
    shoe_md_ft = shoe_tvd_ft if shoe_md_ft is None else shoe_md_ft
    bit_tvd_ft = bit_md_ft if bit_tvd_ft is None else bit_tvd_ft
    survey = [(md, tvd) for _name, md, tvd in key_points] + [(shoe_md_ft, shoe_tvd_ft), (bit_md_ft, bit_tvd_ft)]
    annulus_top_down = list(reversed(annulus_sections_bottom_up))

    string_strokes = surface_to_bit_strokes(drill_string_sections, pump)
    annulus_strokes = surface_to_bit_strokes(annulus_top_down, pump)
    overdisplace_strokes = round_to_whole_number(overdisplacement_bbl / pump)

    rows = {}

    def add(strokes, label):
        string_md = md_after_strokes(min(strokes, string_strokes), drill_string_sections, pump)
        annulus_md = md_after_strokes(min(strokes, annulus_strokes), annulus_top_down, pump)
        string_max, annulus_max = bullhead_limits(string_md, annulus_md, original_mud_weight_ppg, kill_fluid_ppg,
                                                  mamw_ppg, shoe_md_ft, shoe_tvd_ft, bit_md_ft, survey)
        if strokes in rows and rows[strokes].label != STEP:
            label = f"{rows[strokes].label} / {label}"
        rows[strokes] = BullheadRow(strokes, string_md, annulus_md, min(string_max, equipment_limit_psi),
                                    min(annulus_max, equipment_limit_psi), label)

    strokes_per_step = strokes_per_step_for_ten_steps(annulus_strokes)
    for step in range(10):
        add(step * strokes_per_step, STEP)
    md_ft = 0
    for _capacity, length_ft in drill_string_sections[:-1]:
        md_ft += length_ft
        add(strokes_to_length(drill_string_sections, md_ft, pump), STRING_CROSSOVER)
    add(string_strokes, STRING_AT_BIT)
    add(strokes_to_length(annulus_top_down, shoe_md_ft, pump), ANNULUS_AT_SHOE)
    add(annulus_strokes, ANNULUS_AT_BOTTOM)
    if overdisplace_strokes:
        add(annulus_strokes + overdisplace_strokes, OVERDISPLACED)
    return [rows[strokes] for strokes in sorted(rows)]
