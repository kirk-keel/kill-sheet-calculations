"""The full hand-worked kill sheet for a horizontal well.

Untapered string, Driller's method. KOP 9,000 ft, build 10 deg/100 ft to 90 deg,
heel 9,900 ft MD / 9,573 ft TVD with 9-5/8" casing set at the heel, 5,000 ft
8-1/2" lateral to the bit at 14,900 ft MD / 9,573 ft TVD.
Pressures use TVD; volumes and strokes use MD.
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

DRILL_STRING = [(0.0178, 13_400), (0.0087, 900), (0.0077, 600)]         # DP, HWDP, DC (MD)
OPEN_HOLE_ANNULUS = [(0.0291, 600), (0.0459, 900), (0.0459, 3_500)]    # bit up, the lateral
CASED_HOLE_ANNULUS = [(0.0489, 9_900)]
FULL_ANNULUS = OPEN_HOLE_ANNULUS + CASED_HOLE_ANNULUS


def test_section_lengths_add_up():
    check_section_lengths(DRILL_STRING, OPEN_HOLE_ANNULUS, CASED_HOLE_ANNULUS, BIT_MD_FT, SHOE_MD_FT)


def test_pressures_use_tvd():
    # KMW = 10.4 + 650 / (0.052 x 9,573) = 10.4 + 1.3058 = 11.706 -> up -> 11.8
    kmw = kill_mud_weight(SIDPP_PSI, BIT_TVD_FT, ORIGINAL_MUD_WEIGHT_PPG)
    # MAMW = 10.0 + 1,000 / (0.052 x 9,573) = 10.0 + 2.0089 = 12.009 -> down -> 12.0
    mamw = max_allowable_mud_weight(1_000, SHOE_TVD_FT, 10.0)
    assert kmw == 11.8
    assert initial_circulating_pressure(SIDPP_PSI, SCR_PRESSURE_PSI) == 1400
    assert final_circulating_pressure(SCR_PRESSURE_PSI, kmw, ORIGINAL_MUD_WEIGHT_PPG) == 851   # 850.96
    assert mamw == 12.0
    assert maasp(mamw, ORIGINAL_MUD_WEIGHT_PPG, SHOE_TVD_FT) == 796     # 796.47 -> down
    assert maasp(mamw, kmw, SHOE_TVD_FT) == 99                          # 99.56 -> down


def test_volumes_and_strokes_use_md():
    assert total_volume(DRILL_STRING) == 250.9          # 238.5 + 7.8 + 4.6
    assert total_volume(OPEN_HOLE_ANNULUS) == 219.5     # 17.5 + 41.3 + 160.7
    assert total_volume(FULL_ANNULUS) == 703.6          # 219.5 + 484.1
    assert surface_to_bit_strokes(DRILL_STRING, PUMP_OUTPUT_BBL_PER_STK) == 2144
    assert bit_to_shoe_strokes(OPEN_HOLE_ANNULUS, PUMP_OUTPUT_BBL_PER_STK) == 1876
    assert bit_to_surface_strokes(FULL_ANNULUS, PUMP_OUTPUT_BBL_PER_STK) == 6014


def test_kill_mud_position_top_down():
    # (MD, expected TVD, expected strokes)
    for md_ft, tvd_ft, strokes in [
        (9_000, 9_000, 1369),       # KOP: 160.2 bbl
        (9_900, 9_573, 1506),       # heel: 176.2 bbl
        (13_400, 9_573, 2038),      # DP / HWDP crossover in the lateral: 238.5 bbl
        (14_300, 9_573, 2105),      # HWDP / DC crossover: 246.3 bbl
        (14_900, 9_573, 2144),      # bit: 250.9 bbl
    ]:
        assert tvd_at_md(md_ft, KEY_POINTS) == tvd_ft
        assert strokes_to_length(DRILL_STRING, md_ft, PUMP_OUTPUT_BBL_PER_STK) == strokes


def test_annulus_bit_up():
    # (MD, expected strokes from the bit)
    for md_ft, strokes in [
        (14_300, 150),              # top of DC: 17.5 bbl
        (13_400, 503),              # top of HWDP: 58.8 bbl
        (9_900, 1876),              # heel / shoe: 219.5 bbl
        (9_000, 2252),              # KOP: 219.5 + 44.0 = 263.5 bbl
        (0, 6014),                  # surface: 703.6 bbl
    ]:
        assert strokes_to_length(FULL_ANNULUS, BIT_MD_FT - md_ft, PUMP_OUTPUT_BBL_PER_STK) == strokes


def test_drillers_method():
    steps = drillers_method(SIDPP_PSI, SICP_PSI, 1400, 851, 2144, 6014)
    assert [(s.gauge, s.hold_psi, s.strokes) for s in steps] == [
        ("casing", 700, None),
        ("drill pipe", 1400, 6014),
        ("casing", None, None),
        ("drill pipe and casing", 650, None),
        ("casing", 650, None),
        ("casing", 650, 2144),
        ("drill pipe", 851, 6014),
        ("casing", None, None),
        ("drill pipe and casing", 0, None),
    ]
