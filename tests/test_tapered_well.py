"""The full hand-worked kill sheet for a tapered string in a vertical well.

5" DP over 3-1/2" DP, plus HWDP and DC, in 7" 26# casing (ID 6.276") set at
9,500 ft and a 6-1/8" hole to 11,500 ft TVD. Driller's method.
Every expected answer was worked by hand and verified by a well control
specialist before this test was written.
"""

from killsheet.drillers import drillers_method
from killsheet.formulas import (
    final_circulating_pressure,
    initial_circulating_pressure,
    kill_mud_weight,
    maasp,
    max_allowable_mud_weight,
)
from killsheet.strokes import (
    bit_to_shoe_strokes,
    bit_to_surface_strokes,
    crossover_strokes,
    section_volume,
    surface_to_bit_strokes,
    total_volume,
)

# --- Well and kick data --------------------------------------------------------
TVD_FT = 11_500
SHOE_TVD_FT = 9_500
ORIGINAL_MUD_WEIGHT_PPG = 10.4
LOT_PRESSURE_PSI = 1_100
TEST_MUD_WEIGHT_PPG = 10.0
SIDPP_PSI = 650
SICP_PSI = 800
SCR_PRESSURE_PSI = 750
PUMP_OUTPUT_BBL_PER_STK = 0.117

# --- Drill string, top down: (capacity bbl/ft, length ft) ----------------------
DRILL_STRING = [
    (0.0178, 7_000),        # 5" 19.5# DP, ID 4.276"
    (0.0074, 3_600),        # 3-1/2" 13.3# DP, ID 2.764"
    (0.0041, 600),          # 3-1/2" HWDP, ID 2-1/16"
    (0.0049, 300),          # 4-3/4" DC, ID 2-1/4"
]

# --- Annulus, bit up -----------------------------------------------------------
OPEN_HOLE_ANNULUS = [
    (0.0145, 300),          # DC x 6-1/8" hole
    (0.0245, 600),          # HWDP x 6-1/8" hole
    (0.0245, 1_100),        # 3-1/2" DP x 6-1/8" hole
]
CASED_HOLE_ANNULUS = [
    (0.0264, 2_500),        # 3-1/2" DP x 7" casing
    (0.0140, 7_000),        # 5" DP x 7" casing
]
FULL_ANNULUS = OPEN_HOLE_ANNULUS + CASED_HOLE_ANNULUS


def test_pressures():
    kmw = kill_mud_weight(SIDPP_PSI, TVD_FT, ORIGINAL_MUD_WEIGHT_PPG)
    mamw = max_allowable_mud_weight(LOT_PRESSURE_PSI, SHOE_TVD_FT, TEST_MUD_WEIGHT_PPG)

    assert kmw == 11.5                                                       # 11.487 -> up
    assert initial_circulating_pressure(SIDPP_PSI, SCR_PRESSURE_PSI) == 1400
    assert final_circulating_pressure(SCR_PRESSURE_PSI, kmw, ORIGINAL_MUD_WEIGHT_PPG) == 829
    assert mamw == 12.2                                                      # 12.227 -> down
    assert maasp(mamw, ORIGINAL_MUD_WEIGHT_PPG, SHOE_TVD_FT) == 889          # 889.2 -> down
    assert maasp(mamw, kmw, SHOE_TVD_FT) == 345                              # 345.8 -> down


def test_volumes():
    assert [section_volume(*s) for s in DRILL_STRING] == [124.6, 26.6, 2.5, 1.5]
    assert [section_volume(*s) for s in FULL_ANNULUS] == [4.4, 14.7, 27.0, 66.0, 98.0]
    assert total_volume(DRILL_STRING) == 155.2
    assert total_volume(OPEN_HOLE_ANNULUS) == 46.1
    assert total_volume(FULL_ANNULUS) == 210.1


def test_strokes():
    assert surface_to_bit_strokes(DRILL_STRING, PUMP_OUTPUT_BBL_PER_STK) == 1326      # 155.2 / 0.117
    assert bit_to_shoe_strokes(OPEN_HOLE_ANNULUS, PUMP_OUTPUT_BBL_PER_STK) == 394     # 46.1 / 0.117
    assert bit_to_surface_strokes(FULL_ANNULUS, PUMP_OUTPUT_BBL_PER_STK) == 1796     # 210.1 / 0.117


def test_kill_mud_position_at_each_drill_string_crossover():
    # 5"/3-1/2" XO 7,000 ft, top of HWDP 10,600 ft, top of DC 11,200 ft, bit 11,500 ft
    assert crossover_strokes(DRILL_STRING, PUMP_OUTPUT_BBL_PER_STK) == [1065, 1292, 1314, 1326]


def test_annulus_crossovers_bit_up():
    # top of DC 11,200, top of HWDP 10,600, shoe 9,500, 3-1/2"/5" XO 7,000, surface
    assert crossover_strokes(FULL_ANNULUS, PUMP_OUTPUT_BBL_PER_STK) == [38, 163, 394, 958, 1796]


def test_drillers_method():
    steps = drillers_method(SIDPP_PSI, SICP_PSI, 1400, 829, 1326, 1796, 0, 658)   # SF 0, overbalance 658
    assert [(s.gauge, s.hold_psi, s.strokes) for s in steps] == [
        ("casing", 800, None),                      # 1st: start-up
        ("drill pipe", 1400, 1796),                 # 1st: hold ICP, minimum bottoms up
        ("casing", None, None),                     # 1st: shut-down
        ("drill pipe and casing", 650, None),       # 1st: check
        ("casing", 650, None),                      # 2nd: start-up
        ("casing", 650, 1326),                      # 2nd: kill mud surface to bit
        ("drill pipe", 821, 1796),  # DP with kill mud at the bit: 829 + 650 + 0 - 658                  # 2nd: kill mud bit to surface
        ("casing", None, None),                     # 2nd: shut-down
        ("drill pipe and casing", 0, None),         # 2nd: trapped pressure (clamped at 0)
        ("choke", None, None),                      # 2nd: bleed if any pressure
        ("drill pipe and casing", 0, None),         # 2nd: check - well dead
        ("well", None, None),                       # 2nd: flow check
    ]
