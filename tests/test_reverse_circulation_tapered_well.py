"""Reverse circulation kill - CWI well with a tapered tubing string, vertical.

3-1/2" 9.3# tubing (ID 2.992") to 5,000 ft over 2-7/8" 6.5# tubing to the SSD at
9,900 ft, in 5-1/2" 17# casing (ID 4.892"). Everything else as the untapered CWI well.
Pressures don't depend on the tubing size; the strokes and the shape of the
schedule do.
Verified by a well control specialist before this test was written.
"""

from killsheet.reverse_circulation import (
    ANNULUS_CROSSOVER,
    AT_SSD,
    STEP,
    TUBING_DISPLACED,
    bullhead_below_ssd_limits,
    reverse_schedule,
    volume_below_ssd,
)
from killsheet.strokes import surface_to_bit_strokes, total_volume

ANNULUS = [(0.0113, 5_000), (0.0152, 4_900)]    # (4.892^2 - 3.5^2) / 1029.4; then 2-7/8" x casing
TUBING = [(0.0087, 5_000), (0.0058, 4_900)]     # 2.992^2 / 1029.4; then 2-7/8"


def schedule():
    return [tuple(row) for row in reverse_schedule(900, 10.0, 8.6, ANNULUS, TUBING, 0.0500, 7_575, 0.335,
                                                   10_100, 4_000)]


def test_volumes_and_strokes():
    # Annulus: 56.5 + 74.5 = 131.0 bbl / 0.05 = 2,620 stks; tubing: 43.5 + 28.4 = 71.9 bbl = 1,438 stks
    assert (total_volume(ANNULUS), surface_to_bit_strokes(ANNULUS, 0.05)) == (131.0, 2620)
    assert (total_volume(TUBING), surface_to_bit_strokes(TUBING, 0.05)) == (71.9, 1438)


def test_schedule():
    # (strokes, kill fluid MD, TVD, pump psi, max allowable psi, row)
    assert schedule() == [
        (0, 0, 0, 900, 3080, STEP),
        (262, 1_159, 1_159, 816, 2996, STEP),
        (524, 2_319, 2_319, 732, 2911, STEP),
        (786, 3_478, 3_478, 647, 2827, STEP),
        (1048, 4_637, 4_637, 563, 2743, STEP),
        (1130, 5_000, 5_000, 536, 2716, ANNULUS_CROSSOVER),   # 56.5 bbl; 900 - 1.4 x 0.052 x 5,000
        (1310, 5_592, 5_592, 493, 2673, STEP),
        (1572, 6_454, 6_454, 431, 2610, STEP),
        (1834, 7_315, 7_315, 368, 2548, STEP),
        (2096, 8_177, 8_177, 305, 2485, STEP),
        (2358, 9_038, 9_038, 243, 2422, STEP),
        (2620, 9_900, 9_900, 180, 2360, AT_SSD),               # FCP
        (4058, 9_900, 9_900, 180, 2360, TUBING_DISPLACED),     # + 1,438 stks up the tubing
    ]


def test_pressure_drops_faster_above_the_crossover():
    # The tighter 3-1/2" x 5-1/2" annulus moves kill fluid further per stroke:
    # about 84 psi per step above 5,000 ft, about 62 below.
    psi = {row[0]: row[3] for row in schedule()}
    assert psi[0] - psi[262] == 84
    assert psi[1572] - psi[1834] == 63
    assert psi[1834] - psi[2096] == 63


def test_pressures_and_volume_below_the_ssd_are_unchanged_by_the_taper():
    rows = schedule()
    assert (rows[0][3], rows[-1][3]) == (900, 180)                  # same ICP and FCP
    assert (rows[0][4], rows[-1][4]) == (3080, 2360)                # same annulus limits
    assert volume_below_ssd(0.0058, 50, 0.0232, 150) == 3.8         # 2-7/8" is at the bottom either way
    assert bullhead_below_ssd_limits(7_575, 10.0, 9_900, 0.335, 10_100) == (2_360, 2_323)
