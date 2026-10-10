"""The full hand-worked kill sheet for a deviated (build-and-hold) well.

Untapered string, Driller's method. KOP 3,000 ft, build 3 deg/100 ft to 30 deg,
EOB 4,000 ft MD / 3,955 ft TVD, 9-5/8" shoe 5,380 ft MD / 5,150 ft TVD,
bit 12,712 ft MD / 11,500 ft TVD.
Pressures use TVD; volumes and strokes use MD.
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

DRILL_STRING = [(0.0178, 11_212), (0.0087, 900), (0.0077, 600)]         # DP, HWDP, DC (MD)
OPEN_HOLE_ANNULUS = [(0.0291, 600), (0.0459, 900), (0.0459, 5_832)]    # bit up
CASED_HOLE_ANNULUS = [(0.0489, 5_380)]
FULL_ANNULUS = OPEN_HOLE_ANNULUS + CASED_HOLE_ANNULUS


def test_section_lengths_add_up():
    check_section_lengths(DRILL_STRING, OPEN_HOLE_ANNULUS, CASED_HOLE_ANNULUS, BIT_MD_FT, SHOE_MD_FT)


def test_pressures_use_tvd():
    kmw = kill_mud_weight(SIDPP_PSI, BIT_TVD_FT, ORIGINAL_MUD_WEIGHT_PPG)
    mamw = max_allowable_mud_weight(1_350, SHOE_TVD_FT, 9.6)
    assert kmw == 11.5
    assert initial_circulating_pressure(SIDPP_PSI, SCR_PRESSURE_PSI) == 1400
    assert final_circulating_pressure(SCR_PRESSURE_PSI, kmw, ORIGINAL_MUD_WEIGHT_PPG) == 829
    assert mamw == 14.6
    assert maasp(mamw, ORIGINAL_MUD_WEIGHT_PPG, SHOE_TVD_FT) == 1124
    assert maasp(mamw, kmw, SHOE_TVD_FT) == 830


def test_volumes_and_strokes_use_md():
    assert total_volume(DRILL_STRING) == 212.0
    assert total_volume(OPEN_HOLE_ANNULUS) == 326.5
    assert total_volume(FULL_ANNULUS) == 589.6
    assert surface_to_bit_strokes(DRILL_STRING, PUMP_OUTPUT_BBL_PER_STK) == 1812
    assert bit_to_shoe_strokes(OPEN_HOLE_ANNULUS, PUMP_OUTPUT_BBL_PER_STK) == 2791
    assert bit_to_surface_strokes(FULL_ANNULUS, PUMP_OUTPUT_BBL_PER_STK) == 5039


def test_kill_mud_position_top_down():
    # (MD, expected TVD, expected strokes)
    for md_ft, tvd_ft, strokes in [
        (3_000, 3_000, 456),        # KOP: 53.4 bbl
        (4_000, 3_955, 609),        # EOB: 71.2 bbl
        (11_212, 10_201, 1706),     # DP / HWDP crossover: 199.6 bbl (TVD interpolated)
        (12_112, 10_980, 1773),     # HWDP / DC crossover: 207.4 bbl (TVD interpolated)
        (12_712, 11_500, 1812),     # bit: 212.0 bbl
    ]:
        assert tvd_at_md(md_ft, KEY_POINTS) == tvd_ft
        assert strokes_to_length(DRILL_STRING, md_ft, PUMP_OUTPUT_BBL_PER_STK) == strokes


def test_annulus_bit_up():
    # (MD, expected strokes from the bit)
    for md_ft, strokes in [
        (12_112, 150),              # top of DC: 17.5 bbl
        (11_212, 503),              # top of HWDP: 58.8 bbl
        (5_380, 2791),              # shoe: 326.5 bbl
        (4_000, 3368),              # EOB: 326.5 + 67.5 = 394.0 bbl
        (3_000, 3785),              # KOP: 326.5 + 116.4 = 442.9 bbl
        (0, 5039),                  # surface: 589.6 bbl
    ]:
        assert strokes_to_length(FULL_ANNULUS, BIT_MD_FT - md_ft, PUMP_OUTPUT_BBL_PER_STK) == strokes


def test_drillers_method():
    steps = drillers_method(SIDPP_PSI, SICP_PSI, 1400, 829, 1812, 5039, 0, 658)   # SF 0, overbalance 658
    assert [(s.gauge, s.hold_psi, s.strokes) for s in steps] == [
        ("casing", 800, None),
        ("drill pipe", 1400, 5039),
        ("casing", None, None),
        ("drill pipe and casing", 650, None),
        ("casing", 650, None),
        ("casing", 650, 1812),
        ("drill pipe", 821, 5039),  # DP with kill mud at the bit: 829 + 650 + 0 - 658
        ("casing", None, None),
        ("drill pipe and casing", 0, None),         # 2nd: trapped pressure (clamped at 0)
        ("choke", None, None),                      # 2nd: bleed if any pressure
        ("drill pipe and casing", 0, None),         # 2nd: check - well dead
        ("well", None, None),                       # 2nd: flow check
    ]
