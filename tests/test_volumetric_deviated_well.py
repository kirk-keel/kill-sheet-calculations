"""Volumetric method and lubricate and bleed - deviated well, untapered string, all three situations.

The approved deviated (build-and-hold) well: KOP 3,000 ft, end of build 4,000 ft MD /
3,955 ft TVD, 9-5/8" shoe 5,380 ft MD / 5,150 ft TVD, TD 12,712 ft MD / 11,500 ft TVD.
10.4 ppg mud (0.5408 psi/ft), 11.5 ppg kill mud, SICP 800, MAASP 1,124.

The volume bled is the vertical IADC #35 volume (user rule - it bleeds the least mud);
the angle-corrected volume = 50 / (0.5408 x TVD/MD) x capacity is for information.
Verified by a well control specialist before this test was written.
"""

import pytest

from killsheet.depths import tvd_at_md
from killsheet.lubricate_and_bleed import lubricate_and_bleed_table
from killsheet.volumetric import (
    AVERAGE,
    LONGEST,
    SMALLEST,
    angle_corrected_volume_to_bleed,
    annular_capacity_choices,
    volume_to_bleed_per_cycle,
    volumetric_table,
)

GRADIENT = 0.5408
TD_MD_FT = 12_712
SURVEY = [(3_000, 3_000), (4_000, 3_955), (5_380, 5_150), (12_712, 11_500)]

# Annulus from the BOTTOM UP (capacity bbl/ft, length ft MD), including sections with no pipe.
PIPE_ON_BOTTOM = [(0.0291, 600), (0.0459, 900), (0.0459, 5_832), (0.0489, 5_380)]
PIPE_ABOVE_INFLUX = [(0.0702, 2_712), (0.0291, 600), (0.0459, 900), (0.0459, 3_120), (0.0489, 5_380)]  # bit 10,000 MD
PIPE_OUT_OF_HOLE = [(0.0702, 7_332), (0.0732, 5_380)]


def angle_corrected(annulus):
    """(TVD of each section, angle-corrected bbl) walking up from TD."""
    rows, bottom_md = [], TD_MD_FT
    for capacity, length in annulus:
        top_md = bottom_md - length
        section_tvd = tvd_at_md(bottom_md, SURVEY) - tvd_at_md(top_md, SURVEY)
        rows.append((section_tvd, angle_corrected_volume_to_bleed(50, GRADIENT, capacity, length, section_tvd)))
        bottom_md = top_md
    return rows


@pytest.mark.parametrize(
    "annulus, capacities, bleed_bbl",
    [
        (PIPE_ON_BOTTOM, {SMALLEST: 0.0291, AVERAGE: 0.0464, LONGEST: 0.0459}, 2.6),
        (PIPE_ABOVE_INFLUX, {SMALLEST: 0.0291, AVERAGE: 0.0516, LONGEST: 0.0489}, 2.6),
        (PIPE_OUT_OF_HOLE, {SMALLEST: 0.0702, AVERAGE: 0.0715, LONGEST: 0.0702}, 6.4),
    ],
)
def test_volume_bled_is_the_vertical_iadc_volume(annulus, capacities, bleed_bbl):
    # Same as a vertical well: the bleed only depends on the smallest capacity.
    choices = annular_capacity_choices(annulus)
    assert choices == capacities
    assert volume_to_bleed_per_cycle(50, GRADIENT, choices[SMALLEST]) == bleed_bbl


def test_angle_corrected_volume_worked_by_hand():
    # DC x 8-1/2" hole: 600 ft MD, 520 ft TVD (10,980 -> 11,500)
    # 50 / (0.5408 x 520 / 600) x 0.0291 = 3.10 -> DOWN -> 3.1 bbl (vs 2.6 bled)
    assert angle_corrected_volume_to_bleed(50, GRADIENT, 0.0291, 600, 520) == 3.1


@pytest.mark.parametrize(
    "annulus, expected",
    [
        (PIPE_ON_BOTTOM, [(520, 3.1), (779, 4.9), (5_051, 4.8), (5_150, 4.7)]),
        (PIPE_ABOVE_INFLUX, [(2_349, 7.4), (519, 3.1), (780, 4.8), (2_702, 4.9), (5_150, 4.7)]),
        (PIPE_OUT_OF_HOLE, [(6_350, 7.4), (5_150, 7.0)]),
    ],
)
def test_angle_corrected_volumes_by_section(annulus, expected):
    assert angle_corrected(annulus) == expected


def test_angle_corrected_is_always_more_than_the_volume_bled():
    for annulus in (PIPE_ON_BOTTOM, PIPE_ABOVE_INFLUX, PIPE_OUT_OF_HOLE):
        bled = volume_to_bleed_per_cycle(50, GRADIENT, annular_capacity_choices(annulus)[SMALLEST])
        assert all(corrected >= bled for _tvd, corrected in angle_corrected(annulus))


def test_cycles_and_lubricate_and_bleed_pipe_on_bottom():
    rows = volumetric_table(800, 100, 50, 2.6, 1124, [30, 28, 25, 22, 20, 14, 4])
    assert [(row.hold_psi, row.above_maasp) for row in rows] == [
        (950, False), (1000, False), (1050, False), (1100, False), (1150, True), (1200, True), (1250, True),
    ]
    assert rows[-1].gas_at_surface
    # The kill mud lands in the vertical part of the well above KOP (3,000 ft):
    # about 108 bbl / 0.0489 = 2,209 ft of column, so no angle correction is needed.
    lube = lubricate_and_bleed_table(1254, 50, [6.0, 7.0, 8.0, 9.0, 10.0, 10.0, 11.0, 11.0, 12.0, 12.0, 12.0],
                                     0.598, 0.0489)
    assert lube[-1].bleed_to_psi == 0
