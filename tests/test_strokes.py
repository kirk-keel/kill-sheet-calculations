"""Tests for volumes and pump strokes.

Same example well as tests/test_formulas.py (TVD 11,500 ft, shoe 5,150 ft).
The expected answers were worked by hand.
"""

from killsheet.strokes import (
    bit_to_shoe_strokes,
    bit_to_surface_strokes,
    section_volume,
    strokes_for_volume,
    surface_to_bit_strokes,
    total_volume,
)

# ---------------------------------------------------------------------------
# Example well: 8-1/2" hole, 9-5/8" 47# casing (ID 8.681") set at 5,150 ft
# Sections are (capacity bbl/ft, length ft).
# ---------------------------------------------------------------------------
PUMP_OUTPUT_BBL_PER_STK = 0.117

DRILL_PIPE = (0.0178, 10_600)          # 5" 19.5# DP
DRILL_COLLARS = (0.0077, 900)          # 6-1/2" x 2-13/16" DC
DRILL_STRING = [DRILL_PIPE, DRILL_COLLARS]

DC_IN_OPEN_HOLE = (0.0291, 900)        # (8.5^2 - 6.5^2) / 1029.4
DP_IN_OPEN_HOLE = (0.0459, 5_450)      # (8.5^2 - 5^2) / 1029.4; 6,350 ft of open hole - 900 ft DC
DP_IN_CASING = (0.0489, 5_150)         # (8.681^2 - 5^2) / 1029.4
OPEN_HOLE_ANNULUS = [DC_IN_OPEN_HOLE, DP_IN_OPEN_HOLE]
FULL_ANNULUS = OPEN_HOLE_ANNULUS + [DP_IN_CASING]


def test_section_volumes():
    assert section_volume(*DRILL_PIPE) == 188.7        # 0.0178 x 10,600 = 188.68
    assert section_volume(*DRILL_COLLARS) == 6.9       # 0.0077 x 900 = 6.93
    assert section_volume(*DC_IN_OPEN_HOLE) == 26.2    # 0.0291 x 900 = 26.19
    assert section_volume(*DP_IN_OPEN_HOLE) == 250.2   # 0.0459 x 5,450 = 250.155
    assert section_volume(*DP_IN_CASING) == 251.8      # 0.0489 x 5,150 = 251.835


def test_total_volumes():
    assert total_volume(DRILL_STRING) == 195.6         # 188.7 + 6.9
    assert total_volume(OPEN_HOLE_ANNULUS) == 276.4    # 26.2 + 250.2
    assert total_volume(FULL_ANNULUS) == 528.2         # 276.4 + 251.8


def test_strokes_for_volume():
    # 100 bbl / 0.117 bbl/stk = 854.7 -> 855
    assert strokes_for_volume(100, PUMP_OUTPUT_BBL_PER_STK) == 855


def test_surface_to_bit_strokes():
    # 195.6 / 0.117 = 1,671.8 -> 1,672
    assert surface_to_bit_strokes(DRILL_STRING, PUMP_OUTPUT_BBL_PER_STK) == 1672


def test_surface_to_bit_strokes_with_surface_lines():
    # (5.0 + 195.6) / 0.117 = 200.6 / 0.117 = 1,714.5 -> 1,715
    assert surface_to_bit_strokes(DRILL_STRING, PUMP_OUTPUT_BBL_PER_STK, surface_line_volume_bbl=5.0) == 1715


def test_bit_to_shoe_strokes():
    # 276.4 / 0.117 = 2,362.4 -> 2,362
    assert bit_to_shoe_strokes(OPEN_HOLE_ANNULUS, PUMP_OUTPUT_BBL_PER_STK) == 2362


def test_bit_to_surface_strokes():
    # 528.2 / 0.117 = 4,514.5 -> 4,515
    assert bit_to_surface_strokes(FULL_ANNULUS, PUMP_OUTPUT_BBL_PER_STK) == 4515
