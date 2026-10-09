"""Reverse circulation kill - deviated and horizontal CWI wells, tapered tubing.

The approved deviated and horizontal completions (v0.19) with 3-1/2" 9.3# tubing to
5,000 ft MD over 2-7/8" 6.5# tubing, in 5-1/2" 17# casing. Pressures (kill weight,
SITP/SICP, limits, FCP) are unchanged by the taper; the strokes and the shape of the
schedule change, with a row at the annulus crossover.
Verified by a well control specialist before this test was written.
"""

from killsheet.reverse_circulation import ANNULUS_CROSSOVER, AT_SSD, STEP, TUBING_DISPLACED, reverse_schedule
from killsheet.strokes import surface_to_bit_strokes, total_volume

DEVIATED_ANNULUS = [(0.0113, 5_000), (0.0152, 6_000)]
DEVIATED_TUBING = [(0.0087, 5_000), (0.0058, 6_000)]
HORIZONTAL_ANNULUS = [(0.0113, 5_000), (0.0152, 3_800)]
HORIZONTAL_TUBING = [(0.0087, 5_000), (0.0058, 3_800)]


def deviated_schedule():
    return [tuple(row) for row in reverse_schedule(
        900, 9.9, 8.6, DEVIATED_ANNULUS, DEVIATED_TUBING, 0.05, 7_642, 0.3322, 10_190, 4_000,
        ssd_tvd_ft=10_017, key_points=[("KOP", 3_000, 3_000), ("end of build", 4_000, 3_955)])]


def horizontal_schedule():
    return [tuple(row) for row in reverse_schedule(
        1_250, 10.8, 8.6, HORIZONTAL_ANNULUS, HORIZONTAL_TUBING, 0.05, 7_179, 0.3552, 9_573, 4_000,
        ssd_tvd_ft=8_800, key_points=[("KOP", 9_000, 9_000), ("heel", 9_900, 9_573)])]


def test_volumes_and_strokes():
    # Deviated: annulus 56.5 + 91.2 = 147.7 bbl; tubing 43.5 + 34.8 = 78.3 bbl
    assert (total_volume(DEVIATED_ANNULUS), surface_to_bit_strokes(DEVIATED_ANNULUS, 0.05)) == (147.7, 2954)
    assert (total_volume(DEVIATED_TUBING), surface_to_bit_strokes(DEVIATED_TUBING, 0.05)) == (78.3, 1566)
    # Horizontal: annulus 56.5 + 57.8 = 114.3 bbl; tubing 43.5 + 22.0 = 65.5 bbl
    assert (total_volume(HORIZONTAL_ANNULUS), surface_to_bit_strokes(HORIZONTAL_ANNULUS, 0.05)) == (114.3, 2286)
    assert (total_volume(HORIZONTAL_TUBING), surface_to_bit_strokes(HORIZONTAL_TUBING, 0.05)) == (65.5, 1310)


def test_deviated_schedule():
    # (strokes, kill fluid MD, TVD, pump psi, max allowable psi, row)
    assert deviated_schedule() == [
        (0, 0, 0, 900, 3104, STEP),
        (295, 1_310, 1_310, 812, 3016, STEP),
        (590, 2_611, 2_611, 724, 2928, STEP),
        (885, 3_920, 3_879, 638, 2842, STEP),
        (1130, 5_000, 4_821, 575, 2779, ANNULUS_CROSSOVER),    # 900 - 1.3 x 0.052 x 4,821 (325.9 -> 325)
        (1180, 5_164, 4_963, 565, 2769, STEP),
        (1475, 6_138, 5_807, 508, 2712, STEP),
        (1770, 7_105, 6_644, 451, 2655, STEP),
        (2065, 8_079, 7_487, 394, 2598, STEP),
        (2360, 9_046, 8_325, 338, 2542, STEP),
        (2655, 10_020, 9_168, 281, 2485, STEP),
        (2954, 11_000, 10_017, 223, 2427, AT_SSD),
        (4520, 11_000, 10_017, 223, 2427, TUBING_DISPLACED),
    ]


def test_horizontal_schedule():
    assert horizontal_schedule() == [
        (0, 0, 0, 1250, 2969, STEP),
        (229, 1_018, 1_018, 1134, 2852, STEP),
        (458, 2_027, 2_027, 1019, 2737, STEP),
        (687, 3_044, 3_044, 902, 2620, STEP),
        (916, 4_053, 4_053, 787, 2505, STEP),
        (1130, 5_000, 5_000, 678, 2397, ANNULUS_CROSSOVER),    # 1,250 - 2.2 x 0.052 x 5,000 (572)
        (1145, 5_053, 5_053, 672, 2391, STEP),
        (1374, 5_802, 5_802, 587, 2305, STEP),
        (1603, 6_558, 6_558, 500, 2218, STEP),
        (1832, 7_308, 7_308, 414, 2133, STEP),
        (2061, 8_064, 8_064, 328, 2046, STEP),
        (2286, 8_800, 8_800, 244, 1962, AT_SSD),
        (3596, 8_800, 8_800, 244, 1962, TUBING_DISPLACED),
    ]


def test_taper_changes_strokes_not_pressures():
    # Same ICP, FCP and limits as the untapered completions (v0.19); fewer annulus strokes.
    deviated, horizontal = deviated_schedule(), horizontal_schedule()
    assert (deviated[0][3], deviated[-1][3], deviated[-1][4]) == (900, 223, 2427)
    assert (horizontal[0][3], horizontal[-1][3], horizontal[-1][4]) == (1250, 244, 1962)
    assert deviated[-2][0] < 3_344 and horizontal[-2][0] < 2_676     # untapered annulus strokes
