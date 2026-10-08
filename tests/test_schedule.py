"""Tests for the Wait and Weight drill pipe pressure schedule.

Baseline example well: ICP 1,400 psi, FCP 829 psi, surface-to-bit 1,627 strokes.
The expected answers were worked by hand.
"""

import pytest

from killsheet.schedule import (
    EVERY_100_STROKES,
    TEN_STEPS,
    pressure_drop_per_100_strokes,
    pressure_drop_per_step_for_ten_steps,
    pressure_schedule,
    strokes_per_step_for_ten_steps,
)

ICP_PSI = 1400
FCP_PSI = 829
SURFACE_TO_BIT_STROKES = 1627


def test_pressure_drop_per_100_strokes_rounds_down():
    # (1,400 - 829) / (1,627 / 100) = 571 / 16.27 = 35.10 -> round DOWN -> 35
    assert pressure_drop_per_100_strokes(ICP_PSI, FCP_PSI, SURFACE_TO_BIT_STROKES) == 35


def test_every_100_strokes_schedule():
    # ICP minus 35 psi every 100 strokes; FCP at surface-to-bit strokes.
    assert pressure_schedule(ICP_PSI, FCP_PSI, SURFACE_TO_BIT_STROKES, EVERY_100_STROKES) == [
        (0, 1400),
        (100, 1365),
        (200, 1330),
        (300, 1295),
        (400, 1260),
        (500, 1225),
        (600, 1190),
        (700, 1155),
        (800, 1120),
        (900, 1085),
        (1000, 1050),
        (1100, 1015),
        (1200, 980),
        (1300, 945),
        (1400, 910),
        (1500, 875),
        (1600, 840),
        (1627, 829),
    ]


def test_ten_steps_is_the_default():
    assert pressure_schedule(ICP_PSI, FCP_PSI, SURFACE_TO_BIT_STROKES) == pressure_schedule(
        ICP_PSI, FCP_PSI, SURFACE_TO_BIT_STROKES, TEN_STEPS
    )


def test_ten_steps_strokes_and_drop():
    # 1,627 / 10 = 162.7 -> 163 strokes per step
    assert strokes_per_step_for_ten_steps(SURFACE_TO_BIT_STROKES) == 163
    # (1,400 - 829) / 10 = 57.1 -> round DOWN -> 57 psi per step
    assert pressure_drop_per_step_for_ten_steps(ICP_PSI, FCP_PSI) == 57


def test_ten_steps_schedule():
    # ICP minus 57 psi every 163 strokes for 10 steps; FCP at surface-to-bit strokes.
    assert pressure_schedule(ICP_PSI, FCP_PSI, SURFACE_TO_BIT_STROKES, TEN_STEPS) == [
        (0, 1400),
        (163, 1343),
        (326, 1286),
        (489, 1229),
        (652, 1172),
        (815, 1115),
        (978, 1058),
        (1141, 1001),
        (1304, 944),
        (1467, 887),
        (1627, 829),
    ]


@pytest.mark.parametrize("step_method", [EVERY_100_STROKES, TEN_STEPS])
def test_schedule_never_drops_below_the_straight_line(step_method):
    # Because the drop is rounded DOWN, every step must be at or above the
    # exact straight line from ICP to FCP (bottomhole pressure never short).
    exact_drop_per_stroke = (ICP_PSI - FCP_PSI) / SURFACE_TO_BIT_STROKES
    for strokes, pressure in pressure_schedule(ICP_PSI, FCP_PSI, SURFACE_TO_BIT_STROKES, step_method):
        assert pressure >= ICP_PSI - exact_drop_per_stroke * strokes


def test_unknown_step_method_is_rejected():
    with pytest.raises(ValueError):
        pressure_schedule(ICP_PSI, FCP_PSI, SURFACE_TO_BIT_STROKES, "every 50 strokes")


def test_schedule_when_strokes_are_an_exact_multiple_of_100():
    # 1,600 strokes: no partial step; the 1,600-stroke row is FCP.
    # (1,400 - 829) / 16 = 35.69 -> 35 psi/100 stks
    schedule = pressure_schedule(ICP_PSI, FCP_PSI, 1600, EVERY_100_STROKES)
    assert schedule[0] == (0, 1400)
    assert schedule[-2] == (1500, 875)      # 1,400 - 35 x 15
    assert schedule[-1] == (1600, 829)
    assert len(schedule) == 17
