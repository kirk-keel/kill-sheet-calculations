"""Volumetric method and lubricate and bleed - horizontal well, untapered string, all three situations.

The approved horizontal well: KOP 9,000 ft, heel and 9-5/8" shoe 9,900 ft MD /
9,573 ft TVD, 8-1/2" lateral to TD at 14,900 ft MD / 9,573 ft TVD.
10.4 ppg mud (0.5408 psi/ft), 11.8 ppg kill mud (0.6136 psi/ft), SICP 700, MAASP 796.

Gas in the lateral doesn't migrate the way it does vertically - the volumetric method
applies once it reaches the build or vertical section, so there is no angle-corrected
volume for a horizontal section. The volume bled is the vertical IADC #35 volume.
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
    mud_gradient,
    volume_to_bleed_per_cycle,
    volumetric_table,
)

GRADIENT = 0.5408
TD_MD_FT = 14_900
SURVEY = [(9_000, 9_000), (9_900, 9_573), (14_900, 9_573)]

# Annulus from the BOTTOM UP (capacity bbl/ft, length ft MD), including sections with no pipe.
PIPE_ON_BOTTOM = [(0.0291, 600), (0.0459, 900), (0.0459, 3_500), (0.0489, 9_900)]
PIPE_ABOVE_INFLUX = [(0.0702, 2_900), (0.0291, 600), (0.0459, 900), (0.0459, 600), (0.0489, 9_900)]  # bit 12,000 MD
PIPE_OUT_OF_HOLE = [(0.0702, 5_000), (0.0732, 9_900)]


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
        (PIPE_ON_BOTTOM, {SMALLEST: 0.0291, AVERAGE: 0.0472, LONGEST: 0.0489}, 2.6),
        (PIPE_ABOVE_INFLUX, {SMALLEST: 0.0291, AVERAGE: 0.0519, LONGEST: 0.0489}, 2.6),
        (PIPE_OUT_OF_HOLE, {SMALLEST: 0.0702, AVERAGE: 0.0722, LONGEST: 0.0732}, 6.4),
    ],
)
def test_volume_bled_is_the_vertical_iadc_volume(annulus, capacities, bleed_bbl):
    choices = annular_capacity_choices(annulus)
    assert choices == capacities
    assert volume_to_bleed_per_cycle(50, GRADIENT, choices[SMALLEST]) == bleed_bbl


@pytest.mark.parametrize(
    "annulus, expected",
    [
        # Lateral sections: no TVD, so no angle-corrected volume (None).
        # Casing section: 9,900 ft MD, 9,573 ft TVD -> 50 / (0.5408 x 0.967) x 0.0489 = 4.67 -> 4.6
        (PIPE_ON_BOTTOM, [(0, None), (0, None), (0, None), (9_573, 4.6)]),
        (PIPE_ABOVE_INFLUX, [(0, None), (0, None), (0, None), (0, None), (9_573, 4.6)]),
        (PIPE_OUT_OF_HOLE, [(0, None), (9_573, 6.9)]),
    ],
)
def test_no_angle_corrected_volume_in_the_lateral(annulus, expected):
    assert angle_corrected(annulus) == expected


def test_every_hold_is_above_maasp():
    # SICP 700 + 100 + 50 = 850 > MAASP 796: warn and continue.
    rows = volumetric_table(700, 100, 50, 2.6, 796, [26, 22, 18, 13, 8])
    assert [row.hold_psi for row in rows] == [850, 900, 950, 1000, 1050]
    assert all(row.above_maasp for row in rows)
    assert rows[-1].gas_at_surface


def test_lubricate_and_bleed_with_11_8_ppg_kill_mud():
    # 0.6136 / 0.0489 = 12.5 psi per bbl; 8.0 bbl -> 100.4 -> 100
    assert mud_gradient(11.8) == 0.6136
    rows = lubricate_and_bleed_table(1058, 50, [8.0, 9.0] + [10.0] * 7, 0.6136, 0.0489)
    assert [row.bleed_to_psi for row in rows] == [958, 846, 721, 596, 471, 346, 221, 96, 0]
