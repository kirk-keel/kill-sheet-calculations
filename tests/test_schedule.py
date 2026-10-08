"""Tests for the Wait and Weight drill pipe step-down schedule.

The pressure follows the DEPTH of the kill mud:
    Pressure = ICP - (ICP - FCP) x (MD of kill mud / Bit MD), drop rounded DOWN

Baseline example well: ICP 1,400 psi, FCP 829 psi, pump 0.117 bbl/stk,
5" DP 10,000 ft + HWDP 900 ft + DC 600 ft = 11,500 ft, 1,627 strokes to the bit.
The expected answers were worked by hand.
"""

import pytest

from killsheet.schedule import (
    BIT,
    CROSSOVER,
    EVERY_100_STROKES,
    STEP,
    TEN_STEPS,
    drill_pipe_pressure,
    pressure_schedule,
    strokes_per_step_for_ten_steps,
)

ICP_PSI = 1400
FCP_PSI = 829
PUMP_OUTPUT_BBL_PER_STK = 0.117
BIT_MD_FT = 11_500
BASELINE_STRING = [(0.0178, 10_000), (0.0087, 900), (0.0077, 600)]
TAPERED_STRING = [(0.0178, 7_000), (0.0074, 3_600), (0.0041, 600), (0.0049, 300)]


def schedule(sections=BASELINE_STRING, icp=ICP_PSI, fcp=FCP_PSI, **kwargs):
    return [tuple(row) for row in pressure_schedule(icp, fcp, sections, PUMP_OUTPUT_BBL_PER_STK, **kwargs)]


def test_drill_pipe_pressure_follows_depth():
    # 571 x 10,000 / 11,500 = 496.5 -> DOWN -> 496; 1,400 - 496 = 904
    assert drill_pipe_pressure(ICP_PSI, FCP_PSI, 10_000, BIT_MD_FT) == 904
    assert drill_pipe_pressure(ICP_PSI, FCP_PSI, 0, BIT_MD_FT) == 1400
    assert drill_pipe_pressure(ICP_PSI, FCP_PSI, BIT_MD_FT, BIT_MD_FT) == 829


def test_strokes_per_step_for_ten_steps():
    assert strokes_per_step_for_ten_steps(1627) == 163     # 162.7 -> 163


def test_ten_steps_schedule_baseline():
    # (strokes, kill mud MD, psi, row)
    # e.g. 163 stks: 163 x 0.117 = 19.1 bbl -> 10,000 x 19.1 / 178.0 = 1,073 ft;
    #      571 x 1,073 / 11,500 = 53.3 -> 53; 1,400 - 53 = 1,347
    assert schedule() == [
        (0, 0, 1400, STEP),
        (163, 1_073, 1347, STEP),
        (326, 2_140, 1294, STEP),
        (489, 3_213, 1241, STEP),
        (652, 4_287, 1188, STEP),
        (815, 5_360, 1134, STEP),
        (978, 6_427, 1081, STEP),
        (1141, 7_500, 1028, STEP),
        (1304, 8_573, 975, STEP),
        (1467, 9_640, 922, STEP),
        (1521, 10_000, 904, CROSSOVER),     # DP / HWDP
        (1588, 10_900, 859, CROSSOVER),     # HWDP / DC
        (1627, 11_500, 829, BIT),           # FCP
    ]


def test_ten_steps_is_the_default():
    assert schedule() == schedule(step_method=TEN_STEPS)


def test_every_100_strokes_schedule_baseline():
    rows = schedule(step_method=EVERY_100_STROKES)
    assert rows[:4] == [
        (0, 0, 1400, STEP),
        (100, 657, 1368, STEP),             # 11.7 bbl: 10,000 x 11.7 / 178.0 = 657 ft
        (200, 1_315, 1335, STEP),
        (300, 1_972, 1303, STEP),
    ]
    assert rows[-5:] == [
        (1500, 9_860, 911, STEP),
        (1521, 10_000, 904, CROSSOVER),
        (1588, 10_900, 859, CROSSOVER),
        (1600, 11_083, 850, STEP),          # 187.2 bbl: 600 ft x 1.4 / 4.6 = 183 ft into the DC
        (1627, 11_500, 829, BIT),
    ]


def test_tapered_string_schedule():
    # 5" DP 7,000 ft over 3-1/2" DP 3,600 ft, HWDP 600 ft, DC 300 ft; 1,326 strokes to the bit
    assert schedule(TAPERED_STRING) == [
        (0, 0, 1400, STEP),
        (133, 876, 1357, STEP),
        (266, 1_747, 1314, STEP),
        (399, 2_624, 1270, STEP),
        (532, 3_494, 1227, STEP),
        (665, 4_371, 1183, STEP),
        (798, 5_247, 1140, STEP),
        (931, 6_118, 1097, STEP),
        (1064, 6_994, 1053, STEP),
        (1065, 7_000, 1053, CROSSOVER),     # 5" / 3-1/2" DP - the line bends here
        (1197, 9_084, 949, STEP),           # 140.0 bbl: 7,000 + 3,600 ft x 15.4 / 26.6
        (1292, 10_600, 874, CROSSOVER),     # 3-1/2" DP / HWDP
        (1314, 11_200, 844, CROSSOVER),     # HWDP / DC
        (1326, 11_500, 829, BIT),
    ]


def test_single_id_string_gives_the_straight_line():
    # One ID all the way down: depth and strokes move together, so the schedule
    # is the familiar straight line (about 57 psi per step here).
    single = [(0.0178, 11_500)]
    pressures = [row[2] for row in schedule(single)]
    assert pressures == [1400, 1343, 1286, 1229, 1172, 1115, 1058, 1001, 944, 886, 829]


@pytest.mark.parametrize("step_method", [TEN_STEPS, EVERY_100_STROKES])
@pytest.mark.parametrize("sections", [BASELINE_STRING, TAPERED_STRING])
def test_schedule_never_drops_below_the_exact_line(sections, step_method):
    # Because the drop is rounded DOWN, every row is at or above the exact
    # pressure for the depth the kill mud has reached (bottomhole pressure never short).
    bit_md = sum(length for _cap, length in sections)
    for _strokes, md_ft, pressure, _label in schedule(sections, step_method=step_method):
        assert pressure >= ICP_PSI - (ICP_PSI - FCP_PSI) * md_ft / bit_md


def test_surface_lines_delay_the_kill_mud():
    # 5.0 bbl of surface lines: the first 5.0 bbl pumped doesn't reach the drill pipe.
    rows = schedule(surface_line_volume_bbl=5.0)
    assert rows[-1] == (1670, 11_500, 829, BIT)     # (5.0 + 190.4) / 0.117
    # 167 stks: 19.5 - 5.0 = 14.5 bbl -> 815 ft; 571 x 815 / 11,500 = 40.5 -> 40; 1,360
    assert rows[1] == (167, 815, 1360, STEP)


def test_unknown_step_method_is_rejected():
    with pytest.raises(ValueError):
        schedule(step_method="every 50 strokes")
