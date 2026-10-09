"""Volumetric method and lubricate and bleed - vertical well, tapered string, all three situations.

The approved vertical tapered well: 5" DP over 3-1/2" DP, HWDP and DC, 7" 26#
casing (ID 6.276") to 9,500 ft, 6-1/8" hole to 11,500 ft. 10.4 ppg mud
(0.5408 psi/ft), 11.5 ppg kill mud (0.5980 psi/ft), SICP 800, MAASP 889.
Safety margin 100 psi, working pressure 50 psi (kept so the MAASP warnings show).
Verified by a well control specialist before this test was written.
"""

import pytest

from killsheet.formulas import maasp, max_allowable_mud_weight
from killsheet.lubricate_and_bleed import lubricate_and_bleed_table
from killsheet.volumetric import (
    AVERAGE,
    LONGEST,
    SMALLEST,
    annular_capacity_choices,
    volume_to_bleed_per_cycle,
    volumetric_table,
)

GRADIENT, KILL_GRADIENT = 0.5408, 0.598

# Annulus from the BOTTOM UP, including sections with no pipe in them.
PIPE_ON_BOTTOM = [(0.0145, 300), (0.0245, 600), (0.0245, 1_100), (0.0264, 2_500), (0.0140, 7_000)]
PIPE_ABOVE_INFLUX = [                   # bit at 10,000 ft; HWDP across the shoe
    (0.0364, 1_500),                    # 6-1/8" hole, no pipe: 6.125^2 / 1029.4
    (0.0145, 300),                      # DC x 6-1/8" hole
    (0.0245, 200),                      # HWDP x 6-1/8" hole
    (0.0264, 400),                      # HWDP x 7" casing: (6.276^2 - 3.5^2) / 1029.4
    (0.0264, 2_100),                    # 3-1/2" DP x 7" casing
    (0.0140, 7_000),                    # 5" DP x 7" casing
]
PIPE_OUT_OF_HOLE = [(0.0364, 2_000), (0.0383, 9_500)]     # hole and casing (6.276^2 / 1029.4), no pipe


def test_maasp():
    # MAMW = 10.0 + 1,100 / (0.052 x 9,500) = 12.227 -> 12.2; (12.2 - 10.4) x 494 = 889.2 -> 889
    assert maasp(max_allowable_mud_weight(1_100, 9_500, 10.0), 10.4, 9_500) == 889


@pytest.mark.parametrize(
    "annulus, capacities, bleed_bbl",
    [
        # Pipe on bottom: the smallest annulus is the 5" DP in the 7" casing, near surface
        (PIPE_ON_BOTTOM, {SMALLEST: 0.0140, AVERAGE: 0.0183, LONGEST: 0.0140}, {SMALLEST: 1.2, AVERAGE: 1.6}),
        (PIPE_ABOVE_INFLUX, {SMALLEST: 0.0140, AVERAGE: 0.0198, LONGEST: 0.0140}, {SMALLEST: 1.2, AVERAGE: 1.8}),
        (PIPE_OUT_OF_HOLE, {SMALLEST: 0.0364, AVERAGE: 0.0380, LONGEST: 0.0383}, {SMALLEST: 3.3, AVERAGE: 3.5}),
    ],
)
def test_capacity_choices_and_bleed_volumes(annulus, capacities, bleed_bbl):
    choices = annular_capacity_choices(annulus)
    assert choices == capacities
    for choice, expected_bbl in bleed_bbl.items():
        assert volume_to_bleed_per_cycle(50, GRADIENT, choices[choice]) == expected_bbl


def test_smallest_annulus_is_near_surface_not_at_the_bha():
    # 5" DP x 7" casing (0.0140) is tighter than DC x 6-1/8" hole (0.0145).
    assert annular_capacity_choices(PIPE_ON_BOTTOM)[SMALLEST] == 0.0140


def test_every_cycle_is_above_maasp_and_continues():
    rows = volumetric_table(800, 100, 50, 1.2, 889, [24, 20, 15, 9])
    # (cycle, hold psi, bleed bbl, total bbl, above MAASP, 15-min rise, gas at surface)
    assert [tuple(row) for row in rows] == [
        (1, 950, 1.2, 1.2, True, 24, False),        # 800 + 100 + 50 = 950 > 889 already
        (2, 1000, 1.2, 2.4, True, 20, False),
        (3, 1050, 1.2, 3.6, True, 15, False),
        (4, 1100, 1.2, 4.8, True, 9, True),         # gas at surface
    ]


def test_lubricate_and_bleed_pipe_in_the_hole():
    # 5" DP x 7" casing at surface: 0.5980 / 0.0140 = 42.7 psi per bbl
    rows = lubricate_and_bleed_table(959, 50, [3.0, 3.5, 4.0, 4.0, 4.5, 4.5], KILL_GRADIENT, 0.0140)
    # (cycle, pump to, bbl pumped, hydrostatic added, bleed to)
    assert [tuple(row) for row in rows] == [
        (1, 1009, 3.0, 128, 831),                   # 3.0 x 0.5980 / 0.0140 = 128.1 -> 128
        (2, 881, 3.5, 149, 682),
        (3, 732, 4.0, 170, 512),
        (4, 562, 4.0, 170, 342),
        (5, 392, 4.5, 192, 150),
        (6, 200, 4.5, 192, 0),                      # hydrostatic control regained
    ]


def test_lubricate_and_bleed_pipe_out_of_the_hole():
    # 7" casing at surface: 0.5980 / 0.0383 = 15.6 psi per bbl; 8 bbl -> 124.9 -> 124
    rows = lubricate_and_bleed_table(960, 50, [8.0, 9.0, 10.0, 10.0, 10.0, 11.0, 11.0], KILL_GRADIENT, 0.0383)
    assert [row.bleed_to_psi for row in rows] == [836, 696, 540, 384, 228, 57, 0]
