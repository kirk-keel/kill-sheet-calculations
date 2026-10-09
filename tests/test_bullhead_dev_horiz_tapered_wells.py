"""Bullheading while drilling - deviated and horizontal wells, tapered string.

The approved deviated and horizontal wells with the tapered string (5" DP over 4" DP,
4" HWDP and 6-1/2" DC). Annular shut; the same rate down the string and the backside.
The taper changes WHEN kill fluid reaches each point (the strokes), not the limit
at that point - those depend on TVD and on which fluid is where.
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
    minimum_spm_to_beat_gas_migration,
)
from killsheet.strokes import surface_to_bit_strokes, total_volume

DEVIATED_STRING = [(0.0178, 8_000), (0.0108, 3_212), (0.0064, 900), (0.0077, 600)]
DEVIATED_ANNULUS = [(0.0291, 600), (0.0546, 900), (0.0546, 3_212), (0.0459, 2_620), (0.0489, 5_380)]
HORIZONTAL_STRING = [(0.0178, 10_400), (0.0108, 3_000), (0.0064, 900), (0.0077, 600)]
HORIZONTAL_ANNULUS = [(0.0291, 600), (0.0546, 900), (0.0546, 3_000), (0.0459, 500), (0.0489, 9_900)]


def deviated_chart():
    return [tuple(row) for row in bullhead_chart(
        10.4, 11.5, 14.6, 5_150, DEVIATED_STRING, DEVIATED_ANNULUS, 0.117, 3_000,
        overdisplacement_bbl=10.0, shoe_md_ft=5_380, bit_tvd_ft=11_500,
        key_points=[("KOP", 3_000, 3_000), ("end of build", 4_000, 3_955)])]


def horizontal_chart():
    return [tuple(row) for row in bullhead_chart(
        10.4, 11.8, 12.0, 9_573, HORIZONTAL_STRING, HORIZONTAL_ANNULUS, 0.117, 3_000,
        overdisplacement_bbl=10.0, shoe_md_ft=9_900, bit_tvd_ft=9_573,
        key_points=[("KOP", 9_000, 9_000), ("heel", 9_900, 9_573)])]


def test_volumes_strokes_and_minimum_rate():
    assert (total_volume(DEVIATED_STRING), surface_to_bit_strokes(DEVIATED_STRING, 0.117)) == (187.5, 1603)
    annulus_top_down = list(reversed(DEVIATED_ANNULUS))
    assert (total_volume(annulus_top_down), surface_to_bit_strokes(annulus_top_down, 0.117)) == (625.4, 5345)
    # Largest annulus is now 4" pipe x 8-1/2" hole: (185 / 60) x 0.0546 / 0.117 = 1.44 -> UP -> 2 spm
    assert minimum_spm_to_beat_gas_migration(185, 0.0546, 0.117) == 2


def test_deviated_limit_at_the_5_x_4_crossover_worked_by_hand():
    # String kill fluid at 8,000 MD / 7,419 TVD, annulus kill fluid at 2,912 (above the shoe):
    # 0.052 x [14.6 x 5,150 - (11.5 x 7,419 + 10.4 x 4,081) + 10.4 x 6,350] = 700.4 -> 700
    survey = [(3_000, 3_000), (4_000, 3_955), (5_380, 5_150), (12_712, 11_500)]
    assert bullhead_limits(8_000, 2_912, 10.4, 11.5, 14.6, 5_380, 5_150, 12_712, survey)[0] == 700


def test_deviated_chart():
    # (strokes, string kill MD, annulus kill MD, string max, annulus max, row)
    assert deviated_chart() == [
        (0, 0, 0, 1124, 1124, STEP),
        (456, 3_000, 1_092, 953, 1062, "KOP (string)"),
        (535, 3_517, 1_280, 924, 1051, STEP),
        (609, 4_000, 1_458, 898, 1041, "end of build (string)"),
        (1070, 7_034, 2_560, 748, 978, STEP),
        (1217, 8_000, 2_912, 700, 958, STRING_CROSSOVER),       # 5" / 4" DP
        (1254, 8_398, 3_000, 680, 953, "KOP (annulus)"),
        (1514, 11_212, 3_621, 541, 919, STRING_CROSSOVER),
        (1563, 12_112, 3_740, 496, 912, STRING_CROSSOVER),
        (1603, 12_712, 3_836, 466, 907, STRING_AT_BIT),         # lowest string limit
        (1605, 12_712, 3_840, 466, 907, STEP),                  # kept 2 strokes later (user rule)
        (1672, 12_712, 4_000, 466, 898, "end of build (annulus)"),
        (2140, 12_712, 5_120, 466, 843, STEP),
        (2249, 12_712, 5_380, 466, 830, ANNULUS_AT_SHOE),
        (2675, 12_712, 6_467, 520, 830, STEP),
        (3210, 12_712, 7_830, 588, 830, STEP),
        (3745, 12_712, 9_004, 646, 830, STEP),
        (4280, 12_712, 10_150, 703, 830, STEP),
        (4815, 12_712, 11_296, 760, 830, STEP),
        (5345, 12_712, 12_712, 830, 830, ANNULUS_AT_BOTTOM),
        (5430, 12_712, 12_712, 830, 830, OVERDISPLACED),
    ]


def test_taper_moves_the_low_point_earlier_not_lower():
    # Untapered deviated well: 466 psi at 1,812 strokes. Tapered: 466 psi at 1,603 strokes.
    at_bit = next(row for row in deviated_chart() if row[5] == STRING_AT_BIT)
    assert (at_bit[0], at_bit[3]) == (1603, 466)


def test_horizontal_chart():
    assert horizontal_chart() == [
        (0, 0, 0, 796, 796, STEP),
        (630, 4_141, 1_507, 495, 686, STEP),
        (1260, 8_282, 3_014, 193, 577, STEP),
        (1369, 9_000, 3_276, 141, 557, "KOP (string)"),
        (1506, 9_900, 3_603, 99, 534, "heel (string)"),         # final value already
        (1582, 10_400, 3_785, 99, 520, STRING_CROSSOVER),       # 5" / 4" DP, in the lateral
        (1859, 13_400, 4_448, 99, 472, STRING_CROSSOVER),
        (1890, 13_959, 4_522, 99, 467, STEP),
        (1909, 14_300, 4_569, 99, 463, STRING_CROSSOVER),
        (1948, 14_900, 4_661, 99, 457, STRING_AT_BIT),
        (2520, 14_900, 6_029, 99, 357, STEP),
        (3150, 14_900, 7_538, 99, 247, STEP),
        (3762, 14_900, 9_000, 99, 141, "KOP (annulus)"),
        (3780, 14_900, 9_045, 99, 139, STEP),
        (4138, 14_900, 9_900, 99, 99, f"heel (annulus) / {ANNULUS_AT_SHOE}"),
        (4410, 14_900, 10_563, 99, 99, STEP),
        (5040, 14_900, 11_913, 99, 99, STEP),
        (5670, 14_900, 13_263, 99, 99, STEP),
        (6303, 14_900, 14_900, 99, 99, ANNULUS_AT_BOTTOM),
        (6388, 14_900, 14_900, 99, 99, OVERDISPLACED),
    ]


def test_horizontal_heel_is_unchanged_by_a_taper_in_the_lateral():
    # Same 1,506 strokes and 99 psi as the untapered well: the taper is beyond the heel.
    heel = next(row for row in horizontal_chart() if row[5] == "heel (string)")
    assert (heel[0], heel[3]) == (1506, 99)
