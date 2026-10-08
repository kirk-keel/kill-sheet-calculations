"""The full hand-worked kill sheet for a horizontal well with a tapered string.

The approved horizontal well (KOP 9,000 ft, heel and 9-5/8" shoe 9,900 ft MD /
9,573 ft TVD, bit 14,900 ft MD / 9,573 ft TVD) with 5" DP over 4" DP
(crossover at 10,400 ft MD, 500 ft into the lateral), 4" HWDP and 6-1/2" DC.
Driller's method.
Verified by a well control specialist before this test was written.
"""

from killsheet.depths import tvd_at_md
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
    check_section_lengths,
    section_volume,
    strokes_to_length,
    surface_to_bit_strokes,
    total_volume,
)

BIT_MD_FT, BIT_TVD_FT = 14_900, 9_573
SHOE_MD_FT, SHOE_TVD_FT = 9_900, 9_573          # casing set at the heel
KEY_POINTS = [(9_000, 9_000), (9_900, 9_573), (BIT_MD_FT, BIT_TVD_FT)]
ORIGINAL_MUD_WEIGHT_PPG = 10.4
SIDPP_PSI, SICP_PSI, SCR_PRESSURE_PSI = 650, 700, 750
PUMP_OUTPUT_BBL_PER_STK = 0.117

DRILL_STRING = [                # top down (capacity bbl/ft, length ft MD)
    (0.0178, 10_400),           # 5" 19.5# DP
    (0.0108, 3_000),            # 4" 14# DP, ID 3.340"
    (0.0064, 900),              # 4" HWDP, ID 2-9/16"
    (0.0077, 600),              # 6-1/2" DC
]
OPEN_HOLE_ANNULUS = [           # bit up (the lateral)
    (0.0291, 600),              # DC x 8-1/2" hole
    (0.0546, 900),              # 4" HWDP x 8-1/2" hole
    (0.0546, 3_000),            # 4" DP x 8-1/2" hole
    (0.0459, 500),              # 5" DP x 8-1/2" hole
]
CASED_HOLE_ANNULUS = [(0.0489, 9_900)]      # 5" DP x 9-5/8" casing
FULL_ANNULUS = OPEN_HOLE_ANNULUS + CASED_HOLE_ANNULUS


def test_section_lengths_add_up():
    check_section_lengths(DRILL_STRING, OPEN_HOLE_ANNULUS, CASED_HOLE_ANNULUS, BIT_MD_FT, SHOE_MD_FT)


def test_pressures_are_unchanged_by_the_taper():
    kmw = kill_mud_weight(SIDPP_PSI, BIT_TVD_FT, ORIGINAL_MUD_WEIGHT_PPG)
    mamw = max_allowable_mud_weight(1_000, SHOE_TVD_FT, 10.0)
    assert kmw == 11.8
    assert initial_circulating_pressure(SIDPP_PSI, SCR_PRESSURE_PSI) == 1400
    assert final_circulating_pressure(SCR_PRESSURE_PSI, kmw, ORIGINAL_MUD_WEIGHT_PPG) == 851
    assert mamw == 12.0
    assert maasp(mamw, ORIGINAL_MUD_WEIGHT_PPG, SHOE_TVD_FT) == 796
    assert maasp(mamw, kmw, SHOE_TVD_FT) == 99


def test_volumes():
    assert [section_volume(*s) for s in DRILL_STRING] == [185.1, 32.4, 5.8, 4.6]
    assert [section_volume(*s) for s in FULL_ANNULUS] == [17.5, 49.1, 163.8, 23.0, 484.1]
    assert total_volume(DRILL_STRING) == 227.9
    assert total_volume(OPEN_HOLE_ANNULUS) == 253.4
    assert total_volume(FULL_ANNULUS) == 737.5


def test_strokes():
    assert surface_to_bit_strokes(DRILL_STRING, PUMP_OUTPUT_BBL_PER_STK) == 1948     # 227.9 / 0.117
    assert bit_to_shoe_strokes(OPEN_HOLE_ANNULUS, PUMP_OUTPUT_BBL_PER_STK) == 2166   # 253.4 / 0.117
    assert bit_to_surface_strokes(FULL_ANNULUS, PUMP_OUTPUT_BBL_PER_STK) == 6303     # 737.5 / 0.117


def test_kill_mud_position_top_down():
    # (MD, expected TVD, expected strokes)
    for md_ft, tvd_ft, strokes in [
        (9_000, 9_000, 1369),       # KOP: 160.2 bbl
        (9_900, 9_573, 1506),       # heel: 176.2 bbl
        (10_400, 9_573, 1582),      # 5" / 4" DP crossover in the lateral: 185.1 bbl
        (13_400, 9_573, 1859),      # 4" DP / HWDP crossover: 217.5 bbl
        (14_300, 9_573, 1909),      # HWDP / DC crossover: 223.3 bbl
        (14_900, 9_573, 1948),      # bit: 227.9 bbl
    ]:
        assert tvd_at_md(md_ft, KEY_POINTS) == tvd_ft
        assert strokes_to_length(DRILL_STRING, md_ft, PUMP_OUTPUT_BBL_PER_STK) == strokes


def test_annulus_bit_up():
    # (MD, expected strokes from the bit)
    for md_ft, strokes in [
        (14_300, 150),              # top of DC: 17.5 bbl
        (13_400, 569),              # top of 4" HWDP: 66.6 bbl
        (10_400, 1969),             # top of 4" DP: 230.4 bbl
        (9_900, 2166),              # heel / shoe: 253.4 bbl
        (9_000, 2542),              # KOP: 253.4 + 44.0 = 297.4 bbl
        (0, 6303),                  # surface: 737.5 bbl
    ]:
        assert strokes_to_length(FULL_ANNULUS, BIT_MD_FT - md_ft, PUMP_OUTPUT_BBL_PER_STK) == strokes


def test_drillers_method():
    steps = drillers_method(SIDPP_PSI, SICP_PSI, 1400, 851, 1948, 6303)
    assert [(s.gauge, s.hold_psi, s.strokes) for s in steps] == [
        ("casing", 700, None),
        ("drill pipe", 1400, 6303),
        ("casing", None, None),
        ("drill pipe and casing", 650, None),
        ("casing", 650, None),
        ("casing", 650, 1948),
        ("drill pipe", 851, 6303),
        ("casing", None, None),
        ("drill pipe and casing", 0, None),
    ]
