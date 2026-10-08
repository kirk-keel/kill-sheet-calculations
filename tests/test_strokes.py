"""Tests for volumes and pump strokes.

Baseline example well: vertical, untapered string (one drill pipe size + BHA),
TVD 11,500 ft, shoe 5,150 ft. The expected answers were worked by hand.
"""

import pytest

from killsheet.strokes import (
    bit_to_shoe_strokes,
    bit_to_surface_strokes,
    check_section_lengths,
    crossover_strokes,
    section_volume,
    strokes_for_volume,
    strokes_to_length,
    surface_to_bit_strokes,
    total_volume,
    volume_to_length,
)

# ---------------------------------------------------------------------------
# Example well: 8-1/2" hole, 9-5/8" 47# casing (ID 8.681") set at 5,150 ft
# Sections are (capacity bbl/ft, length ft).
# ---------------------------------------------------------------------------
PUMP_OUTPUT_BBL_PER_STK = 0.117

DRILL_PIPE = (0.0178, 10_000)          # 5" 19.5# DP
HWDP = (0.0087, 900)                   # 5" HWDP, ID 3"  (3^2 / 1029.4)
DRILL_COLLARS = (0.0077, 600)          # 6-1/2" x 2-13/16" DC
DRILL_STRING = [DRILL_PIPE, HWDP, DRILL_COLLARS]

DC_IN_OPEN_HOLE = (0.0291, 600)        # (8.5^2 - 6.5^2) / 1029.4
HWDP_IN_OPEN_HOLE = (0.0459, 900)      # (8.5^2 - 5^2) / 1029.4
DP_IN_OPEN_HOLE = (0.0459, 4_850)      # 6,350 ft of open hole - 1,500 ft BHA
DP_IN_CASING = (0.0489, 5_150)         # (8.681^2 - 5^2) / 1029.4
OPEN_HOLE_ANNULUS = [DC_IN_OPEN_HOLE, HWDP_IN_OPEN_HOLE, DP_IN_OPEN_HOLE]
FULL_ANNULUS = OPEN_HOLE_ANNULUS + [DP_IN_CASING]


def test_section_volumes():
    assert section_volume(*DRILL_PIPE) == 178.0        # 0.0178 x 10,000 = 178.0
    assert section_volume(*HWDP) == 7.8                # 0.0087 x 900 = 7.83
    assert section_volume(*DRILL_COLLARS) == 4.6       # 0.0077 x 600 = 4.62
    assert section_volume(*DC_IN_OPEN_HOLE) == 17.5    # 0.0291 x 600 = 17.46
    assert section_volume(*HWDP_IN_OPEN_HOLE) == 41.3  # 0.0459 x 900 = 41.31
    assert section_volume(*DP_IN_OPEN_HOLE) == 222.6   # 0.0459 x 4,850 = 222.615
    assert section_volume(*DP_IN_CASING) == 251.8      # 0.0489 x 5,150 = 251.835


def test_total_volumes():
    assert total_volume(DRILL_STRING) == 190.4         # 178.0 + 7.8 + 4.6
    assert total_volume(OPEN_HOLE_ANNULUS) == 281.4    # 17.5 + 41.3 + 222.6
    assert total_volume(FULL_ANNULUS) == 533.2         # 281.4 + 251.8


def test_strokes_for_volume():
    # 100 bbl / 0.117 bbl/stk = 854.7 -> 855
    assert strokes_for_volume(100, PUMP_OUTPUT_BBL_PER_STK) == 855


def test_surface_to_bit_strokes():
    # 190.4 / 0.117 = 1,627.4 -> 1,627
    assert surface_to_bit_strokes(DRILL_STRING, PUMP_OUTPUT_BBL_PER_STK) == 1627


def test_surface_to_bit_strokes_with_surface_lines():
    # (5.0 + 190.4) / 0.117 = 195.4 / 0.117 = 1,670.1 -> 1,670
    assert surface_to_bit_strokes(DRILL_STRING, PUMP_OUTPUT_BBL_PER_STK, surface_line_volume_bbl=5.0) == 1670


def test_bit_to_shoe_strokes():
    # 281.4 / 0.117 = 2,405.1 -> 2,405
    assert bit_to_shoe_strokes(OPEN_HOLE_ANNULUS, PUMP_OUTPUT_BBL_PER_STK) == 2405


def test_bit_to_surface_strokes():
    # 533.2 / 0.117 = 4,557.3 -> 4,557
    assert bit_to_surface_strokes(FULL_ANNULUS, PUMP_OUTPUT_BBL_PER_STK) == 4557


def test_drill_string_crossover_strokes():
    # Running volume top down: 178.0, 185.8, 190.4 bbl
    # 178.0 / 0.117 = 1,521.4 -> 1,521   (bottom of DP)
    # 185.8 / 0.117 = 1,588.0 -> 1,588   (bottom of HWDP)
    # 190.4 / 0.117 = 1,627.4 -> 1,627   (bit)
    assert crossover_strokes(DRILL_STRING, PUMP_OUTPUT_BBL_PER_STK) == [1521, 1588, 1627]


def test_last_drill_string_crossover_is_surface_to_bit():
    assert crossover_strokes(DRILL_STRING, PUMP_OUTPUT_BBL_PER_STK)[-1] == surface_to_bit_strokes(
        DRILL_STRING, PUMP_OUTPUT_BBL_PER_STK
    )


def test_drill_string_crossovers_with_surface_lines():
    # Surface lines are pumped first: 5.0 + 178.0 = 183.0 / 0.117 = 1,564.1 -> 1,564
    # ... 190.8 -> 1,630.8 -> 1,631; 195.4 -> 1,670.1 -> 1,670 (= surface to bit)
    assert crossover_strokes(DRILL_STRING, PUMP_OUTPUT_BBL_PER_STK, starting_volume_bbl=5.0) == [1564, 1631, 1670]


def test_annulus_crossover_strokes():
    # Running volume bit up: 17.5, 58.8, 281.4, 533.2 bbl
    # 17.5 / 0.117 = 149.6 -> 150   (top of DC)
    # 58.8 / 0.117 = 502.6 -> 503   (top of HWDP)
    # 281.4 / 0.117 = 2,405.1 -> 2,405   (shoe = bit to shoe)
    # 533.2 / 0.117 = 4,557.3 -> 4,557   (surface = bit to surface)
    assert crossover_strokes(FULL_ANNULUS, PUMP_OUTPUT_BBL_PER_STK) == [150, 503, 2405, 4557]


def test_volume_to_a_point_partway_through_a_section():
    # 3,000 ft into the drill pipe: 0.0178 x 3,000 = 53.4
    assert volume_to_length(DRILL_STRING, 3_000) == 53.4
    # 10,500 ft: all the DP (178.0) + 500 ft of HWDP (0.0087 x 500 = 4.35 -> 4.4) = 182.4
    assert volume_to_length(DRILL_STRING, 10_500) == 182.4


def test_volume_to_the_full_length_matches_total_volume():
    assert volume_to_length(DRILL_STRING, 11_500) == total_volume(DRILL_STRING)


def test_strokes_to_length_matches_crossovers():
    strokes = [strokes_to_length(DRILL_STRING, md, PUMP_OUTPUT_BBL_PER_STK) for md in (10_000, 10_900, 11_500)]
    assert strokes == crossover_strokes(DRILL_STRING, PUMP_OUTPUT_BBL_PER_STK) == [1521, 1588, 1627]


def test_length_beyond_the_sections_is_rejected():
    with pytest.raises(ValueError, match="longer than the sections"):
        volume_to_length(DRILL_STRING, 12_000)


def test_section_lengths_that_add_up_pass():
    check_section_lengths(DRILL_STRING, OPEN_HOLE_ANNULUS, [DP_IN_CASING], 11_500, 5_150)


@pytest.mark.parametrize(
    "drill_string, open_hole, cased_hole, message",
    [
        ([(0.0178, 10_100), HWDP, DRILL_COLLARS], OPEN_HOLE_ANNULUS, [DP_IN_CASING], "Drill string"),
        (DRILL_STRING, [DC_IN_OPEN_HOLE, HWDP_IN_OPEN_HOLE], [DP_IN_CASING], "Open hole annulus"),
        (DRILL_STRING, OPEN_HOLE_ANNULUS, [(0.0489, 5_000)], "Cased hole annulus"),
    ],
)
def test_section_lengths_that_dont_add_up_are_rejected(drill_string, open_hole, cased_hole, message):
    with pytest.raises(ValueError, match=message):
        check_section_lengths(drill_string, open_hole, cased_hole, 11_500, 5_150)
