"""Volumetric method and lubricate and bleed - deviated and horizontal wells, tapered string.

The approved deviated and horizontal wells with the tapered string (5" DP over 4" DP,
4" HWDP and 6-1/2" DC); 4" pipe x 8-1/2" hole = (8.5^2 - 4^2) / 1029.4 = 0.0546 bbl/ft.
All three situations for both wells. Same readings as the untapered wells (v0.11).

The taper doesn't change the volume bled (the smallest annulus is still the collars)
or lubricate and bleed (the annulus at surface is still 5" DP x 9-5/8" casing). It
changes the average annulus and the angle-corrected volumes of the 4" sections.
Verified by a well control specialist before this test was written.
"""

import pytest

from killsheet.depths import tvd_at_md
from killsheet.lubricate_and_bleed import cycles_past_kop, lubricate_and_bleed_table
from killsheet.volumetric import (
    AVERAGE,
    LONGEST,
    SMALLEST,
    angle_corrected_volume_to_bleed,
    annular_capacity_choices,
    volume_to_bleed_per_cycle,
)

GRADIENT = 0.5408

DEVIATED = dict(
    td_md=12_712,
    survey=[(3_000, 3_000), (4_000, 3_955), (5_380, 5_150), (12_712, 11_500)],
    pipe_on_bottom=[(0.0291, 600), (0.0546, 900), (0.0546, 3_212), (0.0459, 2_620), (0.0489, 5_380)],
    pipe_above_influx=[(0.0702, 2_712), (0.0291, 600), (0.0546, 900), (0.0546, 500),     # bit 10,000 MD
                       (0.0459, 2_620), (0.0489, 5_380)],
    pipe_out_of_hole=[(0.0702, 7_332), (0.0732, 5_380)],
)
HORIZONTAL = dict(
    td_md=14_900,
    survey=[(9_000, 9_000), (9_900, 9_573), (14_900, 9_573)],
    pipe_on_bottom=[(0.0291, 600), (0.0546, 900), (0.0546, 3_000), (0.0459, 500), (0.0489, 9_900)],
    pipe_above_influx=[(0.0702, 2_900), (0.0291, 600), (0.0546, 900), (0.0546, 100),     # bit 12,000 MD
                       (0.0459, 500), (0.0489, 9_900)],
    pipe_out_of_hole=[(0.0702, 5_000), (0.0732, 9_900)],
)


def angle_corrected(well, situation):
    """(TVD of each section, angle-corrected bbl) walking up from TD."""
    rows, bottom_md = [], well["td_md"]
    for capacity, length in well[situation]:
        top_md = bottom_md - length
        section_tvd = tvd_at_md(bottom_md, well["survey"]) - tvd_at_md(top_md, well["survey"])
        rows.append((section_tvd, angle_corrected_volume_to_bleed(50, GRADIENT, capacity, length, section_tvd)))
        bottom_md = top_md
    return rows


@pytest.mark.parametrize(
    "well, situation, capacities, bleed_bbl",
    [
        (DEVIATED, "pipe_on_bottom", {SMALLEST: 0.0291, AVERAGE: 0.0492, LONGEST: 0.0489}, 2.6),
        (DEVIATED, "pipe_above_influx", {SMALLEST: 0.0291, AVERAGE: 0.0525, LONGEST: 0.0489}, 2.6),
        (DEVIATED, "pipe_out_of_hole", {SMALLEST: 0.0702, AVERAGE: 0.0715, LONGEST: 0.0702}, 6.4),
        (HORIZONTAL, "pipe_on_bottom", {SMALLEST: 0.0291, AVERAGE: 0.0495, LONGEST: 0.0489}, 2.6),
        (HORIZONTAL, "pipe_above_influx", {SMALLEST: 0.0291, AVERAGE: 0.0525, LONGEST: 0.0489}, 2.6),
        (HORIZONTAL, "pipe_out_of_hole", {SMALLEST: 0.0702, AVERAGE: 0.0722, LONGEST: 0.0732}, 6.4),
    ],
)
def test_capacity_choices_and_volume_bled(well, situation, capacities, bleed_bbl):
    choices = annular_capacity_choices(well[situation])
    assert choices == capacities
    assert volume_to_bleed_per_cycle(50, GRADIENT, choices[SMALLEST]) == bleed_bbl


def test_angle_corrected_4_inch_dp_worked_by_hand():
    # 4" DP x 8-1/2" hole: 3,212 ft MD, 2,782 ft TVD
    # 50 / (0.5408 x 2,782 / 3,212) x 0.0546 = 5.83 -> DOWN -> 5.8 bbl
    assert angle_corrected_volume_to_bleed(50, GRADIENT, 0.0546, 3_212, 2_782) == 5.8


@pytest.mark.parametrize(
    "well, situation, expected",
    [
        (DEVIATED, "pipe_on_bottom", [(520, 3.1), (779, 5.8), (2_782, 5.8), (2_269, 4.9), (5_150, 4.7)]),
        (DEVIATED, "pipe_above_influx", [(2_349, 7.4), (519, 3.1), (780, 5.8), (433, 5.8), (2_269, 4.9), (5_150, 4.7)]),
        (DEVIATED, "pipe_out_of_hole", [(6_350, 7.4), (5_150, 7.0)]),
        (HORIZONTAL, "pipe_on_bottom", [(0, None), (0, None), (0, None), (0, None), (9_573, 4.6)]),
        (HORIZONTAL, "pipe_above_influx", [(0, None)] * 5 + [(9_573, 4.6)]),
        (HORIZONTAL, "pipe_out_of_hole", [(0, None), (9_573, 6.9)]),
    ],
)
def test_angle_corrected_volumes_by_section(well, situation, expected):
    assert angle_corrected(well, situation) == expected


def test_lubricate_and_bleed_and_kop_check_are_unchanged_by_the_taper():
    # Annulus at surface is still 5" DP x 9-5/8" casing (0.0489).
    deviated = lubricate_and_bleed_table(1254, 50, [6.0, 7.0, 8.0, 9.0, 10.0, 10.0, 11.0, 11.0, 12.0, 12.0, 12.0],
                                         0.598, 0.0489)
    horizontal = lubricate_and_bleed_table(1058, 50, [8.0, 9.0] + [10.0] * 7, 0.6136, 0.0489)
    assert deviated[-1].bleed_to_psi == horizontal[-1].bleed_to_psi == 0
    assert cycles_past_kop(deviated, 0.0489, 3_000) == []      # 2,209 ft of kill mud vs KOP 3,000
    assert cycles_past_kop(horizontal, 0.0489, 9_000) == []    # 1,779 ft vs KOP 9,000
