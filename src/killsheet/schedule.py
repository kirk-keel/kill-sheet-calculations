"""Drill pipe step-down schedule (Wait and Weight method) from ICP to FCP.

While kill mud is pumped from surface to the bit, the drill pipe pressure is
stepped down from ICP to FCP. The pressure follows WHERE the kill mud is -
not the strokes:

    Pressure = ICP - [ SIDPP x (TVD of kill mud / Bit TVD)
                       - (FCP - SCR) x (MD of kill mud / Bit MD) ]

  - SIDPP x TVD fraction:      the hydrostatic the kill mud has added (depends on TVD)
  - (FCP - SCR) x MD fraction: the extra friction of the heavier mud (depends on MD)

At the bit this is exactly FCP. In a vertical well (TVD = MD) it reduces to
    Pressure = ICP - (ICP - FCP) x (MD of kill mud / Bit MD)
In a horizontal well the pressure bottoms out at the heel and then climbs to
FCP along the lateral: TVD stops changing, but friction keeps building. The
crew follows the schedule back up to FCP.

Why not a straight line against strokes? Strokes only match depth when the
whole string has one ID. Drill pipe, HWDP, collars and tapered strings all
move the kill mud a different distance per stroke, so the line bends at every
crossover. A straight line would take pressure off before the kill mud is
deep enough to replace it. Treating a deviated well as vertical would hold
too MUCH pressure (218 psi too much at the heel of the horizontal example,
straight onto a shoe set at the heel).

Two ways to set the steps (the user chooses):
  - TEN_STEPS (default): 10 equal steps of (surface-to-bit strokes / 10)
  - EVERY_100_STROKES:   a step every 100 strokes
Every crossover and every key point (KOP, end of build, heel) is added as its
own row - those are the inflection points.

Rounding:
  - The drop from ICP at each row is rounded DOWN to a whole psi (IADC rule
    for the pressure reduction schedule), so the pressure is never lower
    than the exact value.
  - Strokes per step for TEN_STEPS is rounded to a whole stroke (rule 3).
"""

from typing import NamedTuple

from killsheet.depths import tvd_at_md
from killsheet.rounding import round_down_to_whole_number, round_to_whole_number
from killsheet.strokes import md_after_strokes, strokes_to_length, surface_to_bit_strokes, total_length

TEN_STEPS = "10 steps"
EVERY_100_STROKES = "every 100 strokes"

# Row labels.
STEP = "step"
CROSSOVER = "crossover"
BIT = "bit"


class ScheduleRow(NamedTuple):
    """One row of the step-down schedule."""

    strokes: int
    md_ft: int
    tvd_ft: int
    pressure_psi: int
    label: str


def strokes_per_step_for_ten_steps(surface_to_bit_strokes):
    """Strokes in each of the 10 steps, rounded to a whole stroke.

        Strokes per step = Surface-to-bit strokes / 10
    """
    return round_to_whole_number(surface_to_bit_strokes / 10)


def drill_pipe_pressure(icp_psi, fcp_psi, sidpp_psi, kill_mud_md_ft, kill_mud_tvd_ft, bit_md_ft, bit_tvd_ft):
    """Drill pipe pressure (psi) with kill mud down to a given MD / TVD.

        Pressure = ICP - [ SIDPP x (TVD of kill mud / Bit TVD)
                           - (FCP - SCR) x (MD of kill mud / Bit MD) ]
        where SCR = ICP - SIDPP

    The drop (the part in brackets) is rounded DOWN to a whole psi.
    At the bit this is exactly FCP. Vertical well: ICP - (ICP - FCP) x MD / Bit MD.
    """
    scr_psi = icp_psi - sidpp_psi
    hydrostatic_added_psi = sidpp_psi * kill_mud_tvd_ft / bit_tvd_ft
    friction_added_psi = (fcp_psi - scr_psi) * kill_mud_md_ft / bit_md_ft
    return icp_psi - round_down_to_whole_number(hydrostatic_added_psi - friction_added_psi)


def pressure_schedule(icp_psi, fcp_psi, drill_string_sections, pump_output_bbl_per_stk,
                      surface_line_volume_bbl=0, step_method=TEN_STEPS,
                      sidpp_psi=None, bit_tvd_ft=None, key_points=()):
    """Drill pipe step-down schedule as a list of ScheduleRow, in stroke order.

    drill_string_sections: (capacity bbl/ft, length ft MD) top down.
    step_method: TEN_STEPS (the default) or EVERY_100_STROKES.

    Vertical well: leave out sidpp_psi, bit_tvd_ft and key_points.
    Deviated or horizontal well: give SIDPP, the bit TVD, and key points as
    (name, MD ft, TVD ft) - e.g. KOP, end of build, heel.

    Rows: every step, every crossover, every key point, and the bit (FCP).
    """
    pump = pump_output_bbl_per_stk
    stb = surface_to_bit_strokes(drill_string_sections, pump, surface_line_volume_bbl)
    bit_md_ft = total_length(drill_string_sections)
    if bit_tvd_ft is None:
        bit_tvd_ft = bit_md_ft                  # vertical well
    vertical = bit_tvd_ft == bit_md_ft and not key_points
    if sidpp_psi is None:
        if not vertical:
            raise ValueError("A deviated or horizontal schedule needs the SIDPP")
        sidpp_psi = 0                           # cancels out in a vertical well
    survey = [(md, tvd) for _name, md, tvd in key_points] + [(bit_md_ft, bit_tvd_ft)]

    def row(strokes, md_ft, label):
        tvd_ft = tvd_at_md(md_ft, survey)
        pressure = drill_pipe_pressure(icp_psi, fcp_psi, sidpp_psi, md_ft, tvd_ft, bit_md_ft, bit_tvd_ft)
        return ScheduleRow(strokes, md_ft, tvd_ft, pressure, label)

    if step_method == TEN_STEPS:
        strokes_per_step = strokes_per_step_for_ten_steps(stb)
        step_strokes = [step * strokes_per_step for step in range(10)]
    elif step_method == EVERY_100_STROKES:
        step_strokes = list(range(0, stb, 100))
    else:
        raise ValueError(f"step_method must be {TEN_STEPS!r} or {EVERY_100_STROKES!r}")

    rows = {}

    def add(strokes, md_ft, label):
        # Two named points at the same strokes share one row ("heel / crossover").
        if strokes in rows and rows[strokes].label != STEP:
            label = f"{rows[strokes].label} / {label}"
        rows[strokes] = row(strokes, md_ft, label)

    for strokes in step_strokes:
        add(strokes, md_after_strokes(strokes, drill_string_sections, pump, surface_line_volume_bbl), STEP)

    # Crossovers: the bottom of every section except the last (that is the bit).
    md_ft = 0
    for _capacity, length_ft in drill_string_sections[:-1]:
        md_ft += length_ft
        add(strokes_to_length(drill_string_sections, md_ft, pump, surface_line_volume_bbl), md_ft, CROSSOVER)

    # Key points: KOP, end of build, heel ... (the line bends here too).
    for name, key_md_ft, _tvd in key_points:
        if key_md_ft < bit_md_ft:
            add(strokes_to_length(drill_string_sections, key_md_ft, pump, surface_line_volume_bbl), key_md_ft, name)

    # Kill mud at the bit: FCP.
    rows[stb] = ScheduleRow(stb, bit_md_ft, bit_tvd_ft, fcp_psi, BIT)
    return [rows[strokes] for strokes in sorted(rows)]
