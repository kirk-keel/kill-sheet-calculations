"""Tests for the volumetric method - vertical well, untapered string, all three situations.

Baseline well: 10.4 ppg mud (0.5408 psi/ft), 8-1/2" hole, 9-5/8" 47# casing
(ID 8.681") at 5,150 ft, TD 11,500 ft, MAASP 1,124 psi, SICP 800 psi.
Safety margin 100 psi and working pressure 50 psi, chosen by the team.
The expected answers were worked by hand and verified by a well control specialist.
"""

import pytest

from killsheet.volumetric import (
    AVERAGE,
    LONGEST,
    SMALLEST,
    annular_capacity_choices,
    gas_at_surface,
    mud_gradient,
    volume_to_bleed_per_cycle,
    volumetric_table,
)

GRADIENT = 0.5408
WORKING_PSI = 50

# Annulus from the BOTTOM UP, including sections with no pipe in them.
PIPE_ON_BOTTOM = [(0.0291, 600), (0.0459, 900), (0.0459, 4_850), (0.0489, 5_150)]
PIPE_ABOVE_INFLUX = [(0.0702, 3_500), (0.0291, 600), (0.0459, 900), (0.0459, 1_350), (0.0489, 5_150)]
PIPE_OUT_OF_HOLE = [(0.0702, 6_350), (0.0732, 5_150)]


def test_mud_gradient():
    assert mud_gradient(10.4) == 0.5408      # 10.4 x 0.052
    assert mud_gradient(11.5) == 0.598       # 11.5 x 0.052


@pytest.mark.parametrize(
    "annulus, expected",
    [
        (PIPE_ON_BOTTOM, {SMALLEST: 0.0291, AVERAGE: 0.0464, LONGEST: 0.0489}),       # 533.2 / 11,500
        (PIPE_ABOVE_INFLUX, {SMALLEST: 0.0291, AVERAGE: 0.0538, LONGEST: 0.0489}),    # 618.3 / 11,500
        (PIPE_OUT_OF_HOLE, {SMALLEST: 0.0702, AVERAGE: 0.0715, LONGEST: 0.0702}),     # 822.8 / 11,500
    ],
)
def test_annular_capacity_choices(annulus, expected):
    assert annular_capacity_choices(annulus) == expected


@pytest.mark.parametrize(
    "capacity, expected_bbl",
    [
        (0.0291, 2.6),      # (50 / 0.5408) x 0.0291 = 2.69 -> DOWN -> 2.6  (smallest, the default)
        (0.0464, 4.2),      # 4.29 -> 4.2  (average)
        (0.0489, 4.5),      # 4.52 -> 4.5  (longest)
        (0.0702, 6.4),      # 6.49 -> 6.4  (pipe out of the hole)
    ],
)
def test_volume_to_bleed_per_cycle_is_rounded_down(capacity, expected_bbl):
    assert volume_to_bleed_per_cycle(WORKING_PSI, GRADIENT, capacity) == expected_bbl


@pytest.mark.parametrize("rise_psi, expected", [(0, True), (4, True), (10, True), (11, False), (30, False)])
def test_gas_at_surface_after_15_minutes(rise_psi, expected):
    assert gas_at_surface(rise_psi) is expected


def test_volumetric_table_pipe_on_bottom():
    rows = volumetric_table(800, 100, WORKING_PSI, 2.6, 1124, [30, 28, 25, 22, 20, 14, 4])
    # (cycle, hold psi, bleed bbl, total bbl, above MAASP, 15-min rise, gas at surface)
    assert [tuple(row) for row in rows] == [
        (1, 950, 2.6, 2.6, False, 30, False),       # 800 + 100 + 50
        (2, 1000, 2.6, 5.2, False, 28, False),
        (3, 1050, 2.6, 7.8, False, 25, False),
        (4, 1100, 2.6, 10.4, False, 22, False),
        (5, 1150, 2.6, 13.0, True, 20, False),      # above MAASP 1,124 - warn and continue
        (6, 1200, 2.6, 15.6, True, 14, False),
        (7, 1250, 2.6, 18.2, True, 4, True),        # rise of 4 psi in 15 min: gas at surface
    ]


def test_volumetric_table_stops_at_gas_at_surface():
    # Readings after the gas-at-surface reading are not used.
    rows = volumetric_table(800, 100, WORKING_PSI, 6.4, 1124, [32, 27, 21, 15, 8, 30, 30])
    assert len(rows) == 5
    assert rows[-1].gas_at_surface
    assert (rows[-1].hold_psi, rows[-1].total_bled_bbl) == (1150, 32.0)


def test_volumetric_table_waits_for_the_next_reading():
    # Gas not at surface yet: the table stops where the readings stop.
    rows = volumetric_table(800, 100, WORKING_PSI, 2.6, 1124, [30, 28])
    assert [row.hold_psi for row in rows] == [950, 1000]
    assert not rows[-1].gas_at_surface
