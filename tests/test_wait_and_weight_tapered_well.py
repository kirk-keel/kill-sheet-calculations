"""The full hand-worked Wait and Weight kill sheet for a tapered string in a vertical well.

5" DP over 3-1/2" DP, plus HWDP and DC, in 7" casing (shoe 9,500 ft) and a
6-1/8" hole to 11,500 ft TVD. Same pressures and strokes as the approved
Driller's method kill sheet for this well (tests/test_tapered_well.py).
Verified by a well control specialist before this test was written.
"""

from killsheet.kill_steps import CHECK, HOLD, SHUT_DOWN, START_UP, WEIGHT_UP
from killsheet.schedule import BIT, CROSSOVER, drill_pipe_pressure, pressure_schedule
from killsheet.strokes import bit_to_surface_strokes, surface_to_bit_strokes
from killsheet.wait_and_weight import wait_and_weight_method

ICP_PSI, FCP_PSI, KMW_PPG = 1400, 829, 11.5
PUMP_OUTPUT_BBL_PER_STK = 0.117
DRILL_STRING = [(0.0178, 7_000), (0.0074, 3_600), (0.0041, 600), (0.0049, 300)]
FULL_ANNULUS = [(0.0145, 300), (0.0245, 600), (0.0245, 1_100), (0.0264, 2_500), (0.0140, 7_000)]


def test_strokes():
    assert surface_to_bit_strokes(DRILL_STRING, PUMP_OUTPUT_BBL_PER_STK) == 1326
    assert bit_to_surface_strokes(FULL_ANNULUS, PUMP_OUTPUT_BBL_PER_STK) == 1796


def test_wait_and_weight_steps():
    steps = wait_and_weight_method(800, ICP_PSI, FCP_PSI, KMW_PPG, 1326, 1796)
    assert [(s.stage, s.gauge, s.hold_psi, s.strokes) for s in steps] == [
        (WEIGHT_UP, "pits", None, None),
        (START_UP, "casing", 800, None),
        (HOLD, "drill pipe", 1400, 1326),           # step down ICP -> FCP, surface to bit
        (HOLD, "drill pipe", 829, 1796),            # hold FCP, bit to surface
        (SHUT_DOWN, "casing", None, None),
        (CHECK, "drill pipe and casing", 0, None),
    ]
    # 1,326 + 1,796 = 3,122 strokes (Driller's method on the same well: 1,796 + 1,326 + 1,796 = 4,918)
    assert sum(s.strokes for s in steps if s.strokes) == 3122


def test_inflection_points_at_each_crossover():
    # Pressure at each crossover = 1,400 - (571 x MD / 11,500), drop rounded DOWN
    crossovers = [tuple(row) for row in pressure_schedule(ICP_PSI, FCP_PSI, DRILL_STRING, PUMP_OUTPUT_BBL_PER_STK)
                  if row.label in (CROSSOVER, BIT)]
    assert crossovers == [
        (1065, 7_000, 1053, CROSSOVER),     # 347.6 -> 347
        (1292, 10_600, 874, CROSSOVER),     # 526.3 -> 526
        (1314, 11_200, 844, CROSSOVER),     # 556.1 -> 556
        (1326, 11_500, 829, BIT),           # FCP
    ]


def test_a_straight_line_against_strokes_would_be_112_psi_short_at_the_crossover():
    # Straight line: 1,400 - 571 x 1,065 / 1,326 = 941.4 psi.
    # By depth (kill mud at 7,000 ft): 1,053 psi. The straight line would take
    # 112 psi off before the kill mud is deep enough to replace it.
    straight_line = ICP_PSI - (ICP_PSI - FCP_PSI) * 1065 / 1326
    by_depth = drill_pipe_pressure(ICP_PSI, FCP_PSI, 7_000, 11_500)
    assert by_depth == 1053
    assert round(by_depth - straight_line) == 112
