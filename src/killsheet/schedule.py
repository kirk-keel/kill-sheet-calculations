"""Drill pipe step-down schedule (Wait and Weight method) from ICP to FCP.

While kill mud is pumped from surface to the bit, the drill pipe pressure is
stepped down from ICP to FCP. The pressure follows the DEPTH the kill mud has
reached - that is where the extra hydrostatic comes from - not the strokes:

    Drill pipe pressure = ICP - (ICP - FCP) x (MD of kill mud / Bit MD)

For a string with one ID all the way down, depth and strokes move together
and this is a straight line against strokes. When the ID changes (drill pipe
to HWDP to collars, or a tapered string) each stroke moves the kill mud a
different distance, so the line bends at every crossover. A straight line
against strokes would then take pressure off before the kill mud is deep
enough to replace it, and bottomhole pressure would fall short.

Two ways to set the steps (the user chooses):
  - TEN_STEPS (default): 10 equal steps of (surface-to-bit strokes / 10)
  - EVERY_100_STROKES:   a step every 100 strokes
Every crossover is added as its own row - those are the inflection points.

Rounding:
  - The drop from ICP at each row is rounded DOWN to a whole psi (IADC rule
    for the pressure reduction schedule), so the pressure is never lower
    than the exact line.
  - Strokes per step for TEN_STEPS is rounded to a whole stroke (rule 3).
"""

from typing import NamedTuple

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
    pressure_psi: int
    label: str


def strokes_per_step_for_ten_steps(surface_to_bit_strokes):
    """Strokes in each of the 10 steps, rounded to a whole stroke.

        Strokes per step = Surface-to-bit strokes / 10
    """
    return round_to_whole_number(surface_to_bit_strokes / 10)


def drill_pipe_pressure(icp_psi, fcp_psi, kill_mud_md_ft, bit_md_ft):
    """Drill pipe pressure (psi) with kill mud down to a given MD - vertical well.

        Pressure = ICP - (ICP - FCP) x (MD of kill mud / Bit MD)

    The drop from ICP is rounded DOWN to a whole psi. At the bit this is FCP.
    """
    drop_psi = round_down_to_whole_number((icp_psi - fcp_psi) * kill_mud_md_ft / bit_md_ft)
    return icp_psi - drop_psi


def pressure_schedule(icp_psi, fcp_psi, drill_string_sections, pump_output_bbl_per_stk,
                      surface_line_volume_bbl=0, step_method=TEN_STEPS):
    """Drill pipe step-down schedule as a list of ScheduleRow, in stroke order.

    drill_string_sections: (capacity bbl/ft, length ft) top down.
    step_method: TEN_STEPS (the default) or EVERY_100_STROKES.

    Rows: every step, every crossover (the inflection points), and the bit,
    where the pressure is FCP.
    """
    pump = pump_output_bbl_per_stk
    stb = surface_to_bit_strokes(drill_string_sections, pump, surface_line_volume_bbl)
    bit_md_ft = total_length(drill_string_sections)

    if step_method == TEN_STEPS:
        strokes_per_step = strokes_per_step_for_ten_steps(stb)
        step_strokes = [step * strokes_per_step for step in range(10)]
    elif step_method == EVERY_100_STROKES:
        step_strokes = list(range(0, stb, 100))
    else:
        raise ValueError(f"step_method must be {TEN_STEPS!r} or {EVERY_100_STROKES!r}")

    rows = {}
    for strokes in step_strokes:
        md_ft = md_after_strokes(strokes, drill_string_sections, pump, surface_line_volume_bbl)
        rows[strokes] = ScheduleRow(strokes, md_ft, drill_pipe_pressure(icp_psi, fcp_psi, md_ft, bit_md_ft), STEP)

    # Crossovers: the bottom of every section except the last (that is the bit).
    md_ft = 0
    for _capacity, length_ft in drill_string_sections[:-1]:
        md_ft += length_ft
        strokes = strokes_to_length(drill_string_sections, md_ft, pump, surface_line_volume_bbl)
        rows[strokes] = ScheduleRow(strokes, md_ft, drill_pipe_pressure(icp_psi, fcp_psi, md_ft, bit_md_ft), CROSSOVER)

    # Kill mud at the bit: FCP.
    rows[stb] = ScheduleRow(stb, bit_md_ft, fcp_psi, BIT)
    return [rows[strokes] for strokes in sorted(rows)]
