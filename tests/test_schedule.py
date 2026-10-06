"""Tests for the drill pipe pressure schedule.

Same example well: ICP 1,400 psi, FCP 829 psi, surface-to-bit 1,672 strokes.
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
SURFACE_TO_BIT_STROKES = 1672


def test_pressure_drop_per_100_strokes_rounds_down():
    # (1,400 - 829) / (1,672 / 100) = 571 / 16.72 = 34.15 -> round DOWN -> 34
    assert pressure_drop_per_100_strokes(ICP_PSI, FCP_PSI, SURFACE_TO_BIT_STROKES) == 34


def test_pressure_schedule():
    # ICP minus 34 psi every 100 strokes; FCP at surface-to-bit strokes.
    assert pressure_schedule(ICP_PSI, FCP_PSI, SURFACE_TO_BIT_STROKES) == [
        (0, 1400),
        (100, 1366),
        (200, 1332),
        (300, 1298),
        (400, 1264),
        (500, 1230),
        (600, 1196),
        (700, 1162),
        (800, 1128),
        (900, 1094),
        (1000, 1060),
        (1100, 1026),
        (1200, 992),
        (1300, 958),
        (1400, 924),
        (1500, 890),
        (1600, 856),
        (1672, 829),
    ]


def test_every_100_strokes_is_the_default():
    assert pressure_schedule(ICP_PSI, FCP_PSI, SURFACE_TO_BIT_STROKES) == pressure_schedule(
        ICP_PSI, FCP_PSI, SURFACE_TO_BIT_STROKES, EVERY_100_STROKES
    )


def test_ten_steps_strokes_and_drop():
    # 1,672 / 10 = 167.2 -> 167 strokes per step
    assert strokes_per_step_for_ten_steps(SURFACE_TO_BIT_STROKES) == 167
    # (1,400 - 829) / 10 = 57.1 -> round DOWN -> 57 psi per step
    assert pressure_drop_per_step_for_ten_steps(ICP_PSI, FCP_PSI) == 57


def test_ten_steps_schedule():
    # ICP minus 57 psi every 167 strokes for 10 steps; FCP at surface-to-bit strokes.
    assert pressure_schedule(ICP_PSI, FCP_PSI, SURFACE_TO_BIT_STROKES, TEN_STEPS) == [
        (0, 1400),
        (167, 1343),
        (334, 1286),
        (501, 1229),
        (668, 1172),
        (835, 1115),
        (1002, 1058),
        (1169, 1001),
        (1336, 944),
        (1503, 887),
        (1672, 829),
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
    schedule = pressure_schedule(ICP_PSI, FCP_PSI, 1600)
    assert schedule[0] == (0, 1400)
    assert schedule[-2] == (1500, 875)      # 1,400 - 35 x 15
    assert schedule[-1] == (1600, 829)
    assert len(schedule) == 17
