"""Drill pipe pressure schedule (Wait and Weight method) from ICP to FCP.

While kill mud is pumped from surface to the bit, the drill pipe pressure
is stepped down from ICP to FCP. The schedule ends at FCP when kill mud
reaches the bit.

Two ways to step the pressure down (the user chooses):
  - TEN_STEPS (default): 10 equal steps of (surface-to-bit strokes / 10)
  - EVERY_100_STROKES:   a step every 100 strokes

Rounding:
  - The pressure drop per step is rounded DOWN to a whole psi (IADC rule).
    This keeps the schedule from stepping pressure down faster than the
    straight line from ICP to FCP, so bottomhole pressure doesn't fall short.
  - Strokes per step for TEN_STEPS is rounded to a whole stroke (rule 3).
"""

from killsheet.rounding import round_down_to_whole_number, round_to_whole_number

EVERY_100_STROKES = "every 100 strokes"
TEN_STEPS = "10 steps"


def pressure_drop_per_100_strokes(icp_psi, fcp_psi, surface_to_bit_strokes):
    """Pressure drop per 100 strokes (psi/100 stks), rounded DOWN to a whole psi.

        Drop = (ICP - FCP) / (Surface-to-bit strokes / 100)
    """
    raw_drop = (icp_psi - fcp_psi) / (surface_to_bit_strokes / 100)
    return round_down_to_whole_number(raw_drop)


def strokes_per_step_for_ten_steps(surface_to_bit_strokes):
    """Strokes in each of the 10 steps, rounded to a whole stroke.

        Strokes per step = Surface-to-bit strokes / 10
    """
    return round_to_whole_number(surface_to_bit_strokes / 10)


def pressure_drop_per_step_for_ten_steps(icp_psi, fcp_psi):
    """Pressure drop per step (psi/step) for 10 steps, rounded DOWN to a whole psi.

        Drop = (ICP - FCP) / 10
    """
    return round_down_to_whole_number((icp_psi - fcp_psi) / 10)


def pressure_schedule(icp_psi, fcp_psi, surface_to_bit_strokes, step_method=TEN_STEPS):
    """Drill pipe pressure schedule as a list of (strokes, pressure_psi) rows.

    step_method is TEN_STEPS (the default) or EVERY_100_STROKES.

    Starts at (0, ICP), drops by the rounded-down drop each step, and ends
    at (surface-to-bit strokes, FCP).

        Pressure at a step = ICP - (Drop per step x number of steps)
    """
    # Strokes at the start of each step, before the final FCP row.
    if step_method == EVERY_100_STROKES:
        drop_psi = pressure_drop_per_100_strokes(icp_psi, fcp_psi, surface_to_bit_strokes)
        step_strokes = list(range(0, surface_to_bit_strokes, 100))      # 0, 100, 200, ...
    elif step_method == TEN_STEPS:
        drop_psi = pressure_drop_per_step_for_ten_steps(icp_psi, fcp_psi)
        strokes_per_step = strokes_per_step_for_ten_steps(surface_to_bit_strokes)
        step_strokes = [step * strokes_per_step for step in range(10)]  # exactly 10 steps
    else:
        raise ValueError(f"step_method must be {EVERY_100_STROKES!r} or {TEN_STEPS!r}")

    schedule = []
    for step, strokes in enumerate(step_strokes):
        schedule.append((strokes, icp_psi - drop_psi * step))

    # Last row: kill mud at the bit, FCP.
    schedule.append((surface_to_bit_strokes, fcp_psi))
    return schedule
