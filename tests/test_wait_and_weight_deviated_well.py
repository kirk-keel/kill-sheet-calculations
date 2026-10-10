"""The full hand-worked Wait and Weight kill sheet for a deviated (build-and-hold) well.

Untapered string. KOP 3,000 ft, EOB 4,000 ft MD / 3,955 ft TVD,
bit 12,712 ft MD / 11,500 ft TVD. ICP 1,400, FCP 829, SIDPP 650, SCR 750.

    Pressure = ICP - [ SIDPP x (TVD / 11,500) - (FCP - SCR) x (MD / 12,712) ], drop rounded DOWN

Verified by a well control specialist before this test was written.
"""

from killsheet.kill_steps import BLEED, CHECK, FLOW_CHECK, HOLD, SHUT_DOWN, START_UP, WEIGHT_UP
from killsheet.schedule import BIT, CROSSOVER, STEP, drill_pipe_pressure, pressure_schedule
from killsheet.wait_and_weight import wait_and_weight_method

ICP_PSI, FCP_PSI, SIDPP_PSI, KMW_PPG = 1400, 829, 650, 11.5
BIT_MD_FT, BIT_TVD_FT = 12_712, 11_500
KEY_POINTS = [("KOP", 3_000, 3_000), ("end of build", 4_000, 3_955)]
DRILL_STRING = [(0.0178, 11_212), (0.0087, 900), (0.0077, 600)]


def test_wait_and_weight_steps():
    steps = wait_and_weight_method(800, ICP_PSI, FCP_PSI, KMW_PPG, 1812, 5039, 0)   # SF 0
    assert [(s.stage, s.gauge, s.hold_psi, s.strokes) for s in steps] == [
        (WEIGHT_UP, "pits", None, None),
        (START_UP, "casing", 800, None),
        (CHECK, "drill pipe", 1400, None),           # ICP check at kill rate
        (HOLD, "drill pipe", 1400, 1812),
        (HOLD, "drill pipe", 829, 5039),
        (SHUT_DOWN, "casing", None, None),
        (CHECK, "drill pipe and casing", 0, None),   # trapped pressure = SF = 0
        (BLEED, "choke", None, None),
        (CHECK, "drill pipe and casing", 0, None),   # well dead
        (FLOW_CHECK, "well", None, None),
    ]


def test_pressure_at_kop_worked_by_hand():
    # 650 x 3,000 / 11,500 = 169.57; 79 x 3,000 / 12,712 = 18.64; drop = 150.92 -> 150
    assert drill_pipe_pressure(ICP_PSI, FCP_PSI, SIDPP_PSI, 3_000, 3_000, BIT_MD_FT, BIT_TVD_FT) == 1250


def test_schedule():
    rows = pressure_schedule(ICP_PSI, FCP_PSI, DRILL_STRING, 0.117,
                             sidpp_psi=SIDPP_PSI, bit_tvd_ft=BIT_TVD_FT, key_points=KEY_POINTS)
    # (strokes, MD, TVD, psi, row)
    assert [tuple(row) for row in rows] == [
        (0, 0, 0, 1400, STEP),
        (181, 1_191, 1_191, 1341, STEP),
        (362, 2_382, 2_382, 1281, STEP),
        (456, 3_000, 3_000, 1250, "KOP"),
        (543, 3_567, 3_541, 1223, STEP),
        (609, 4_000, 3_955, 1202, "end of build"),
        (724, 4_758, 4_611, 1169, STEP),
        (905, 5_949, 5_643, 1119, STEP),
        (1086, 7_140, 6_674, 1068, STEP),
        (1267, 8_325, 7_701, 1017, STEP),
        (1448, 9_516, 8_732, 966, STEP),
        (1629, 10_706, 9_763, 915, STEP),
        (1706, 11_212, 10_201, 894, CROSSOVER),     # DP / HWDP
        (1773, 12_112, 10_980, 855, CROSSOVER),     # HWDP / DC
        (1812, 12_712, 11_500, 829, BIT),           # FCP
    ]


def test_treating_the_well_as_vertical_would_hold_too_much_pressure():
    # Treated as vertical (TVD = MD) at end of build: 571 x 4,000 / 12,712 = 179.7 -> 179; 1,221 psi
    # Correct (TVD for hydrostatic, MD for friction): 1,202 psi - 19 psi less.
    as_vertical = drill_pipe_pressure(ICP_PSI, FCP_PSI, SIDPP_PSI, 4_000, 4_000, BIT_MD_FT, BIT_MD_FT)
    correct = drill_pipe_pressure(ICP_PSI, FCP_PSI, SIDPP_PSI, 4_000, 3_955, BIT_MD_FT, BIT_TVD_FT)
    assert (as_vertical, correct) == (1221, 1202)
