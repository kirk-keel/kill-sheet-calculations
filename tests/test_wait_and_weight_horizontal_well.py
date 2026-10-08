"""The full hand-worked Wait and Weight kill sheet for a horizontal well.

Untapered string. KOP 9,000 ft, heel and 9-5/8" shoe 9,900 ft MD / 9,573 ft TVD,
bit 14,900 ft MD / 9,573 ft TVD. ICP 1,400, FCP 851, SIDPP 650, SCR 750.

    Pressure = ICP - [ SIDPP x (TVD / 9,573) - (FCP - SCR) x (MD / 14,900) ], drop rounded DOWN

The pressure bottoms out at the heel and climbs back to FCP along the lateral:
the crew follows the schedule up to FCP.
Verified by a well control specialist before this test was written.
"""

from killsheet.kill_steps import CHECK, HOLD, SHUT_DOWN, START_UP, WEIGHT_UP
from killsheet.schedule import BIT, CROSSOVER, STEP, drill_pipe_pressure, pressure_schedule
from killsheet.wait_and_weight import wait_and_weight_method

ICP_PSI, FCP_PSI, SIDPP_PSI, KMW_PPG = 1400, 851, 650, 11.8
BIT_MD_FT, BIT_TVD_FT = 14_900, 9_573
KEY_POINTS = [("KOP", 9_000, 9_000), ("heel", 9_900, 9_573)]
DRILL_STRING = [(0.0178, 13_400), (0.0087, 900), (0.0077, 600)]


def schedule():
    return pressure_schedule(ICP_PSI, FCP_PSI, DRILL_STRING, 0.117,
                             sidpp_psi=SIDPP_PSI, bit_tvd_ft=BIT_TVD_FT, key_points=KEY_POINTS)


def test_wait_and_weight_steps():
    steps = wait_and_weight_method(700, ICP_PSI, FCP_PSI, KMW_PPG, 2144, 6014)
    assert [(s.stage, s.gauge, s.hold_psi, s.strokes) for s in steps] == [
        (WEIGHT_UP, "pits", None, None),
        (START_UP, "casing", 700, None),
        (HOLD, "drill pipe", 1400, 2144),
        (HOLD, "drill pipe", 851, 6014),
        (SHUT_DOWN, "casing", None, None),
        (CHECK, "drill pipe and casing", 0, None),
    ]


def test_pressure_at_the_heel_worked_by_hand():
    # 650 x 9,573 / 9,573 = 650.00; 101 x 9,900 / 14,900 = 67.11; drop = 582.89 -> 582
    assert drill_pipe_pressure(ICP_PSI, FCP_PSI, SIDPP_PSI, 9_900, 9_573, BIT_MD_FT, BIT_TVD_FT) == 818


def test_schedule():
    # (strokes, MD, TVD, psi, row)
    assert [tuple(row) for row in schedule()] == [
        (0, 0, 0, 1400, STEP),
        (214, 1_405, 1_405, 1315, STEP),
        (428, 2_815, 2_815, 1228, STEP),
        (642, 4_219, 4_219, 1143, STEP),
        (856, 5_630, 5_630, 1056, STEP),
        (1070, 7_034, 7_034, 971, STEP),
        (1284, 8_439, 8_439, 885, STEP),
        (1369, 9_000, 9_000, 850, "KOP"),
        (1498, 9_849, 9_541, 819, STEP),
        (1506, 9_900, 9_573, 818, "heel"),          # lowest point
        (1712, 11_254, 9_573, 827, STEP),
        (1926, 12_658, 9_573, 836, STEP),
        (2038, 13_400, 9_573, 841, CROSSOVER),      # DP / HWDP
        (2105, 14_300, 9_573, 847, CROSSOVER),      # HWDP / DC
        (2144, 14_900, 9_573, 851, BIT),            # FCP
    ]


def test_pressure_bottoms_out_at_the_heel_then_climbs_to_fcp():
    pressures = [row.pressure_psi for row in schedule()]
    heel = [row.label for row in schedule()].index("heel")
    assert min(pressures) == pressures[heel] == 818
    assert pressures[:heel + 1] == sorted(pressures[:heel + 1], reverse=True)    # falling to the heel
    assert pressures[heel:] == sorted(pressures[heel:])                          # climbing to FCP


def test_treating_the_well_as_vertical_would_put_218_psi_too_much_on_the_shoe():
    # Treated as vertical (TVD = MD) at the heel: 549 x 9,900 / 14,900 = 364.8 -> 364; 1,036 psi
    # Correct: 818 psi. The shoe is at the heel, with only 796 psi MAASP.
    as_vertical = drill_pipe_pressure(ICP_PSI, FCP_PSI, SIDPP_PSI, 9_900, 9_900, BIT_MD_FT, BIT_MD_FT)
    assert as_vertical - 818 == 218
