"""Bullheading while drilling - deviated and horizontal wells, untapered string.

The approved deviated and horizontal wells (v0.3). Annular shut; the same rate down
the string and the backside. Limits use TVD for every column; rows at every key point
(KOP, end of build, heel) on each side, and named points at their exact depth.
Verified by a well control specialist before this test was written.
"""

from killsheet.bullhead import (
    ANNULUS_AT_BOTTOM,
    ANNULUS_AT_SHOE,
    OVERDISPLACED,
    STEP,
    STRING_AT_BIT,
    STRING_CROSSOVER,
    bullhead_chart,
    bullhead_limits,
)


def deviated_chart():
    return [tuple(row) for row in bullhead_chart(
        10.4, 11.5, 14.6, 5_150,
        [(0.0178, 11_212), (0.0087, 900), (0.0077, 600)],
        [(0.0291, 600), (0.0459, 900), (0.0459, 5_832), (0.0489, 5_380)],
        0.117, 3_000, overdisplacement_bbl=10.0, shoe_md_ft=5_380, bit_tvd_ft=11_500,
        key_points=[("KOP", 3_000, 3_000), ("end of build", 4_000, 3_955)])]


def horizontal_chart():
    return [tuple(row) for row in bullhead_chart(
        10.4, 11.8, 12.0, 9_573,
        [(0.0178, 13_400), (0.0087, 900), (0.0077, 600)],
        [(0.0291, 600), (0.0459, 900), (0.0459, 3_500), (0.0489, 9_900)],
        0.117, 3_000, overdisplacement_bbl=10.0, shoe_md_ft=9_900, bit_tvd_ft=9_573,
        key_points=[("KOP", 9_000, 9_000), ("heel", 9_900, 9_573)])]


def test_deviated_limit_at_kop_annulus_worked_by_hand():
    # String kill fluid at 8,240 MD = 7,627 TVD; annulus kill fluid at 3,000 (above the shoe):
    # 0.052 x [14.6 x 5,150 - (11.5 x 7,627 + 10.4 x 3,873) + 10.4 x 6,350] = 688.5 -> 688
    survey = [(3_000, 3_000), (4_000, 3_955), (5_380, 5_150), (12_712, 11_500)]
    assert bullhead_limits(8_240, 3_000, 10.4, 11.5, 14.6, 5_380, 5_150, 12_712, survey) == (688, 953)


def test_deviated_chart():
    # (strokes, string kill MD, annulus kill MD, string max, annulus max, row)
    assert deviated_chart() == [
        (0, 0, 0, 1124, 1124, STEP),
        (456, 3_000, 1_092, 953, 1062, "KOP (string)"),
        (504, 3_314, 1_206, 936, 1055, STEP),
        (609, 4_000, 1_458, 898, 1041, "end of build (string)"),
        (1008, 6_623, 2_411, 768, 986, STEP),
        (1254, 8_240, 3_000, 688, 953, "KOP (annulus)"),
        (1512, 9_937, 3_617, 604, 919, STEP),
        (1672, 10_987, 4_000, 552, 898, "end of build (annulus)"),
        (1706, 11_212, 4_082, 541, 894, STRING_CROSSOVER),
        (1773, 12_112, 4_241, 496, 886, STRING_CROSSOVER),
        (1812, 12_712, 4_335, 466, 881, STRING_AT_BIT),         # lowest string limit
        (2016, 12_712, 4_824, 466, 857, STEP),
        (2249, 12_712, 5_380, 466, 830, ANNULUS_AT_SHOE),
        (2520, 12_712, 6_071, 501, 830, STEP),
        (3024, 12_712, 7_356, 564, 830, STEP),
        (3528, 12_712, 8_641, 628, 830, STEP),
        (4032, 12_712, 9_924, 692, 830, STEP),
        (4536, 12_712, 11_210, 755, 830, STEP),
        (5039, 12_712, 12_712, 830, 830, ANNULUS_AT_BOTTOM),
        (5124, 12_712, 12_712, 830, 830, OVERDISPLACED),
    ]


def test_horizontal_string_limit_reaches_its_final_value_at_the_heel():
    # Kill fluid at the heel (9,573 TVD), annulus kill fluid above the shoe:
    # 0.052 x [12.0 x 9,573 - 11.8 x 9,573] = 99.56 -> 99. The flat lateral adds no
    # hydrostatic, and with the shoe at the heel nothing pushes back from below.
    survey = [(9_000, 9_000), (9_900, 9_573), (14_900, 9_573)]
    assert bullhead_limits(9_900, 3_603, 10.4, 11.8, 12.0, 9_900, 9_573, 14_900, survey) == (99, 534)
    rows = horizontal_chart()
    heel = next(row for row in rows if row[5] == "heel (string)")
    assert all(row[3] == 99 for row in rows[rows.index(heel):])


def test_horizontal_chart():
    assert horizontal_chart() == [
        (0, 0, 0, 796, 796, STEP),
        (601, 3_950, 1_438, 508, 691, STEP),
        (1202, 7_900, 2_875, 221, 587, STEP),
        (1369, 9_000, 3_276, 141, 557, "KOP (string)"),
        (1506, 9_900, 3_603, 99, 534, "heel (string)"),
        (1803, 11_855, 4_315, 99, 482, STEP),
        (2038, 13_400, 4_875, 99, 441, STRING_CROSSOVER),
        (2105, 14_300, 5_037, 99, 429, STRING_CROSSOVER),
        (2144, 14_900, 5_129, 99, 423, STRING_AT_BIT),
        (2404, 14_900, 5_753, 99, 377, STEP),
        (3005, 14_900, 7_190, 99, 273, STEP),
        (3606, 14_900, 8_628, 99, 168, STEP),
        (3762, 14_900, 9_000, 99, 141, "KOP (annulus)"),
        (4138, 14_900, 9_900, 99, 99, f"heel (annulus) / {ANNULUS_AT_SHOE}"),
        (4207, 14_900, 10_076, 99, 99, STEP),
        (4808, 14_900, 11_608, 99, 99, STEP),
        (5409, 14_900, 13_141, 99, 99, STEP),
        (6014, 14_900, 14_900, 99, 99, ANNULUS_AT_BOTTOM),
        (6099, 14_900, 14_900, 99, 99, OVERDISPLACED),
    ]


def test_named_points_are_shown_at_their_exact_depth():
    # Working depth back from rounded strokes would put these a few feet off
    # (end of build at 4,005; the DP/HWDP crossover at 13,394).
    deviated = {row[5]: row for row in deviated_chart()}
    horizontal = {row[5]: row for row in horizontal_chart()}
    assert deviated["end of build (string)"][1] == 4_000
    assert deviated["KOP (annulus)"][2] == 3_000
    assert horizontal["KOP (string)"][1] == 9_000
    crossovers = [row[1] for row in horizontal_chart() if row[5] == STRING_CROSSOVER]
    assert crossovers == [13_400, 14_300]
