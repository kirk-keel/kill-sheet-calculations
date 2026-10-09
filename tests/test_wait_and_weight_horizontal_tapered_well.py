"""The full hand-worked Wait and Weight kill sheet for a horizontal well with a tapered string.

The approved horizontal well (KOP 9,000 ft, heel and 9-5/8" shoe 9,900 ft MD /
9,573 ft TVD, bit 14,900 ft MD / 9,573 ft TVD) with 5" DP over 4" DP
(crossover at 10,400 ft MD, 500 ft into the lateral), 4" HWDP and 6-1/2" DC.
ICP 1,400, FCP 851, SIDPP 650, SCR 750.

    Pressure = ICP - [ SIDPP x (TVD / 9,573) - (FCP - SCR) x (MD / 14,900) ], drop rounded DOWN

The pressure bottoms out at the heel and climbs back to FCP along the lateral.
Verified by a well control specialist before this test was written.
"""

from killsheet.kill_steps import CHECK, HOLD, SHUT_DOWN, START_UP, WEIGHT_UP
from killsheet.schedule import BIT, CROSSOVER, STEP, drill_pipe_pressure, pressure_schedule
from killsheet.wait_and_weight import wait_and_weight_method

ICP_PSI, FCP_PSI, SIDPP_PSI, KMW_PPG = 1400, 851, 650, 11.8
BIT_MD_FT, BIT_TVD_FT = 14_900, 9_573
KEY_POINTS = [("KOP", 9_000, 9_000), ("heel", 9_900, 9_573)]
DRILL_STRING = [(0.0178, 10_400), (0.0108, 3_000), (0.0064, 900), (0.0077, 600)]


def schedule():
    return pressure_schedule(ICP_PSI, FCP_PSI, DRILL_STRING, 0.117,
                             sidpp_psi=SIDPP_PSI, bit_tvd_ft=BIT_TVD_FT, key_points=KEY_POINTS)


def test_wait_and_weight_steps():
    # Same strokes as the approved Driller's method kill sheet: 1,948 to the bit, 6,303 bit to surface
    steps = wait_and_weight_method(700, ICP_PSI, FCP_PSI, KMW_PPG, 1948, 6303)
    assert [(s.stage, s.gauge, s.hold_psi, s.strokes) for s in steps] == [
        (WEIGHT_UP, "pits", None, None),
        (START_UP, "casing", 700, None),
        (HOLD, "drill pipe", 1400, 1948),
        (HOLD, "drill pipe", 851, 6303),
        (SHUT_DOWN, "casing", None, None),
        (CHECK, "drill pipe and casing", 0, None),
    ]


def test_pressure_at_the_lateral_crossover_worked_by_hand():
    # 5" / 4" crossover at 10,400 ft MD, 9,573 ft TVD:
    # 650 x 9,573 / 9,573 = 650.00; 101 x 10,400 / 14,900 = 70.50; drop 579.50 -> 579
    assert drill_pipe_pressure(ICP_PSI, FCP_PSI, SIDPP_PSI, 10_400, 9_573, BIT_MD_FT, BIT_TVD_FT) == 821


def test_schedule():
    # (strokes, MD, TVD, psi, row)
    assert [tuple(row) for row in schedule()] == [
        (0, 0, 0, 1400, STEP),
        (195, 1_281, 1_281, 1322, STEP),
        (390, 2_562, 2_562, 1244, STEP),
        (585, 3_843, 3_843, 1166, STEP),
        (780, 5_130, 5_130, 1087, STEP),
        (975, 6_411, 6_411, 1009, STEP),
        (1170, 7_692, 7_692, 930, STEP),
        (1365, 8_973, 8_973, 852, STEP),            # kept: user rule, steps stay evenly spaced
        (1369, 9_000, 9_000, 850, "KOP"),
        (1506, 9_900, 9_573, 818, "heel"),          # lowest point
        (1560, 10_254, 9_573, 820, STEP),
        (1582, 10_400, 9_573, 821, CROSSOVER),      # 5" / 4" DP, in the lateral
        (1755, 12_270, 9_573, 834, STEP),
        (1859, 13_400, 9_573, 841, CROSSOVER),      # 4" DP / HWDP
        (1909, 14_300, 9_573, 847, CROSSOVER),      # HWDP / DC
        (1948, 14_900, 9_573, 851, BIT),            # FCP
    ]


def test_pressure_bottoms_out_at_the_heel_then_climbs_to_fcp():
    rows = schedule()
    pressures = [row.pressure_psi for row in rows]
    heel = [row.label for row in rows].index("heel")
    assert min(pressures) == pressures[heel] == 818
    assert pressures[:heel + 1] == sorted(pressures[:heel + 1], reverse=True)    # falling to the heel
    assert pressures[heel:] == sorted(pressures[heel:])                          # climbing to FCP


def test_heel_pressure_is_the_same_as_the_untapered_well():
    # The pressure at the heel depends only on its MD and TVD - the taper only
    # changes WHEN the kill mud gets there (1,506 strokes here).
    heel = next(row for row in schedule() if row.label == "heel")
    assert (heel.strokes, heel.pressure_psi) == (1506, 818)
