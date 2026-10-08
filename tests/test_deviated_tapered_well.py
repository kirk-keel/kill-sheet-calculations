"""The full hand-worked kill sheet for a deviated well with a tapered string.

The approved deviated well (KOP 3,000 ft, EOB 4,000 ft MD / 3,955 ft TVD,
9-5/8" shoe 5,380 ft MD / 5,150 ft TVD, bit 12,712 ft MD / 11,500 ft TVD)
with 5" DP over 4" DP (crossover at 8,000 ft MD in the tangent), 4" HWDP
and 6-1/2" DC. Driller's method.
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

BIT_MD_FT, BIT_TVD_FT = 12_712, 11_500
SHOE_MD_FT, SHOE_TVD_FT = 5_380, 5_150
KEY_POINTS = [(3_000, 3_000), (4_000, 3_955), (SHOE_MD_FT, SHOE_TVD_FT), (BIT_MD_FT, BIT_TVD_FT)]
ORIGINAL_MUD_WEIGHT_PPG = 10.4
SIDPP_PSI, SICP_PSI, SCR_PRESSURE_PSI = 650, 800, 750
PUMP_OUTPUT_BBL_PER_STK = 0.117

DRILL_STRING = [                # top down (capacity bbl/ft, length ft MD)
    (0.0178, 8_000),            # 5" 19.5# DP
    (0.0108, 3_212),            # 4" 14# DP, ID 3.340"
    (0.0064, 900),              # 4" HWDP, ID 2-9/16"
    (0.0077, 600),              # 6-1/2" DC
]
OPEN_HOLE_ANNULUS = [           # bit up
    (0.0291, 600),              # DC x 8-1/2" hole
    (0.0546, 900),              # 4" HWDP x 8-1/2" hole, (8.5^2 - 4^2) / 1029.4
    (0.0546, 3_212),            # 4" DP x 8-1/2" hole
    (0.0459, 2_620),            # 5" DP x 8-1/2" hole
]
CASED_HOLE_ANNULUS = [(0.0489, 5_380)]      # 5" DP x 9-5/8" casing
FULL_ANNULUS = OPEN_HOLE_ANNULUS + CASED_HOLE_ANNULUS


def test_section_lengths_add_up():
    check_section_lengths(DRILL_STRING, OPEN_HOLE_ANNULUS, CASED_HOLE_ANNULUS, BIT_MD_FT, SHOE_MD_FT)


def test_pressures_are_unchanged_by_the_taper():
    kmw = kill_mud_weight(SIDPP_PSI, BIT_TVD_FT, ORIGINAL_MUD_WEIGHT_PPG)
    mamw = max_allowable_mud_weight(1_350, SHOE_TVD_FT, 9.6)
    assert kmw == 11.5
    assert initial_circulating_pressure(SIDPP_PSI, SCR_PRESSURE_PSI) == 1400
    assert final_circulating_pressure(SCR_PRESSURE_PSI, kmw, ORIGINAL_MUD_WEIGHT_PPG) == 829
    assert mamw == 14.6
    assert maasp(mamw, ORIGINAL_MUD_WEIGHT_PPG, SHOE_TVD_FT) == 1124
    assert maasp(mamw, kmw, SHOE_TVD_FT) == 830


def test_volumes():
    assert [section_volume(*s) for s in DRILL_STRING] == [142.4, 34.7, 5.8, 4.6]
    assert [section_volume(*s) for s in FULL_ANNULUS] == [17.5, 49.1, 175.4, 120.3, 263.1]
    assert total_volume(DRILL_STRING) == 187.5
    assert total_volume(OPEN_HOLE_ANNULUS) == 362.3
    assert total_volume(FULL_ANNULUS) == 625.4


def test_strokes():
    assert surface_to_bit_strokes(DRILL_STRING, PUMP_OUTPUT_BBL_PER_STK) == 1603     # 187.5 / 0.117
    assert bit_to_shoe_strokes(OPEN_HOLE_ANNULUS, PUMP_OUTPUT_BBL_PER_STK) == 3097   # 362.3 / 0.117
    assert bit_to_surface_strokes(FULL_ANNULUS, PUMP_OUTPUT_BBL_PER_STK) == 5345     # 625.4 / 0.117


def test_kill_mud_position_top_down():
    # (MD, expected TVD, expected strokes)
    for md_ft, tvd_ft, strokes in [
        (3_000, 3_000, 456),        # KOP: 53.4 bbl
        (4_000, 3_955, 609),        # EOB: 71.2 bbl
        (8_000, 7_419, 1217),       # 5" / 4" DP crossover: 142.4 bbl (TVD interpolated)
        (11_212, 10_201, 1514),     # 4" DP / HWDP crossover: 177.1 bbl
        (12_112, 10_980, 1563),     # HWDP / DC crossover: 182.9 bbl
        (12_712, 11_500, 1603),     # bit: 187.5 bbl
    ]:
        assert tvd_at_md(md_ft, KEY_POINTS) == tvd_ft
        assert strokes_to_length(DRILL_STRING, md_ft, PUMP_OUTPUT_BBL_PER_STK) == strokes


def test_annulus_bit_up():
    # (MD, expected strokes from the bit)
    for md_ft, strokes in [
        (12_112, 150),              # top of DC: 17.5 bbl
        (11_212, 569),              # top of 4" HWDP: 66.6 bbl
        (8_000, 2068),              # top of 4" DP: 242.0 bbl
        (5_380, 3097),              # shoe: 362.3 bbl
        (4_000, 3674),              # EOB: 362.3 + 67.5 = 429.8 bbl
        (3_000, 4091),              # KOP: 362.3 + 116.4 = 478.7 bbl
        (0, 5345),                  # surface: 625.4 bbl
    ]:
        assert strokes_to_length(FULL_ANNULUS, BIT_MD_FT - md_ft, PUMP_OUTPUT_BBL_PER_STK) == strokes


def test_drillers_method():
    steps = drillers_method(SIDPP_PSI, SICP_PSI, 1400, 829, 1603, 5345)
    assert [(s.gauge, s.hold_psi, s.strokes) for s in steps] == [
        ("casing", 800, None),
        ("drill pipe", 1400, 5345),
        ("casing", None, None),
        ("drill pipe and casing", 650, None),
        ("casing", 650, None),
        ("casing", 650, 1603),
        ("drill pipe", 829, 5345),
        ("casing", None, None),
        ("drill pipe and casing", 0, None),
    ]
