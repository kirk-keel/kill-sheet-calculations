"""The full hand-worked Wait and Weight kill sheet for a deviated well with a tapered string.

The approved deviated well (KOP 3,000 ft, EOB 4,000 ft MD / 3,955 ft TVD,
bit 12,712 ft MD / 11,500 ft TVD) with 5" DP over 4" DP (crossover at
8,000 ft MD in the tangent), 4" HWDP and 6-1/2" DC.
ICP 1,400, FCP 829, SIDPP 650, SCR 750.

    Pressure = ICP - [ SIDPP x (TVD / 11,500) - (FCP - SCR) x (MD / 12,712) ], drop rounded DOWN

Verified by a well control specialist before this test was written.
"""

from killsheet.kill_steps import BLEED, CHECK, FLOW_CHECK, HOLD, SHUT_DOWN, START_UP, WEIGHT_UP
from killsheet.schedule import BIT, CROSSOVER, STEP, drill_pipe_pressure, pressure_schedule
from killsheet.wait_and_weight import wait_and_weight_method

ICP_PSI, FCP_PSI, SIDPP_PSI, KMW_PPG = 1400, 829, 650, 11.5
BIT_MD_FT, BIT_TVD_FT = 12_712, 11_500
KEY_POINTS = [("KOP", 3_000, 3_000), ("end of build", 4_000, 3_955)]
DRILL_STRING = [(0.0178, 8_000), (0.0108, 3_212), (0.0064, 900), (0.0077, 600)]


def schedule():
    return pressure_schedule(ICP_PSI, FCP_PSI, DRILL_STRING, 0.117,
                             sidpp_psi=SIDPP_PSI, bit_tvd_ft=BIT_TVD_FT, key_points=KEY_POINTS)


def test_wait_and_weight_steps():
    # Same strokes as the approved Driller's method kill sheet: 1,603 to the bit, 5,345 bit to surface
    steps = wait_and_weight_method(800, ICP_PSI, FCP_PSI, KMW_PPG, 1603, 5345, 0)   # SF 0
    assert [(s.stage, s.gauge, s.hold_psi, s.strokes) for s in steps] == [
        (WEIGHT_UP, "pits", None, None),
        (START_UP, "casing", 800, None),
        (CHECK, "drill pipe", 1400, None),           # ICP check at kill rate
        (HOLD, "drill pipe", 1400, 1603),
        (HOLD, "drill pipe", 829, 5345),
        (SHUT_DOWN, "casing", None, None),
        (CHECK, "drill pipe and casing", 0, None),   # trapped pressure = SF = 0
        (BLEED, "choke", None, None),
        (CHECK, "drill pipe and casing", 0, None),   # well dead
        (FLOW_CHECK, "well", None, None),
    ]


def test_pressure_at_1280_strokes_worked_by_hand():
    # 149.8 bbl: all the 5" (142.4) + 7.4 bbl of 4" -> 3,212 x 7.4 / 34.7 = 685 ft -> MD 8,685
    # TVD 3,955 + 4,685 x 7,545 / 8,712 = 8,012
    # 650 x 8,012 / 11,500 = 452.85; 79 x 8,685 / 12,712 = 53.97; drop 398.88 -> 398
    assert drill_pipe_pressure(ICP_PSI, FCP_PSI, SIDPP_PSI, 8_685, 8_012, BIT_MD_FT, BIT_TVD_FT) == 1002


def test_schedule():
    # (strokes, MD, TVD, psi, row)
    assert [tuple(row) for row in schedule()] == [
        (0, 0, 0, 1400, STEP),
        (160, 1_051, 1_051, 1348, STEP),
        (320, 2_101, 2_101, 1295, STEP),
        (456, 3_000, 3_000, 1250, "KOP"),
        (480, 3_157, 3_150, 1242, STEP),
        (609, 4_000, 3_955, 1202, "end of build"),
        (640, 4_208, 4_135, 1193, STEP),
        (800, 5_258, 5_044, 1148, STEP),
        (960, 6_309, 5_955, 1103, STEP),
        (1120, 7_360, 6_865, 1058, STEP),
        (1217, 8_000, 7_419, 1031, CROSSOVER),      # 5" / 4" DP
        (1280, 8_685, 8_012, 1002, STEP),
        (1440, 10_416, 9_512, 928, STEP),
        (1514, 11_212, 10_201, 894, CROSSOVER),     # 4" DP / HWDP
        (1563, 12_112, 10_980, 855, CROSSOVER),     # HWDP / DC
        (1603, 12_712, 11_500, 829, BIT),           # FCP
    ]


def test_drop_speeds_up_in_the_smaller_pipe():
    # 5" DP (800 -> 960 stks): 45 psi per 160 strokes.
    # 4" DP (1,280 -> 1,440 stks): 74 psi per 160 strokes - more feet per stroke.
    psi = {row.strokes: row.pressure_psi for row in schedule()}
    assert psi[800] - psi[960] == 45
    assert psi[1280] - psi[1440] == 74
