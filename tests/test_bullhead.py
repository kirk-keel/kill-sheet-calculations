"""Tests for bullheading while drilling - vertical well, untapered string.

The baseline well: 10.4 ppg mud, kill fluid 11.5 ppg (rounded UP), MAMW 14.6 ppg,
shoe 5,150 ft, bit 11,500 ft. Annular shut; kill fluid pumped down the string
AND the backside at the SAME rate, at the same time, the whole way.
Influx treated as original mud. Limits rounded DOWN.
Verified by a well control specialist before this test was written.
"""

import pytest

from killsheet.bullhead import (
    ANNULUS_AT_BOTTOM,
    ANNULUS_AT_SHOE,
    OVERDISPLACED,
    STEP,
    STRING_AT_BIT,
    STRING_CROSSOVER,
    bullhead_chart,
    bullhead_limits,
    equipment_limit,
    gas_migration_rate,
    minimum_spm_to_beat_gas_migration,
)

OMW, KILL_FLUID, MAMW = 10.4, 11.5, 14.6
SHOE_FT, BIT_FT = 5_150, 11_500
VERTICAL = [(BIT_FT, BIT_FT)]
DRILL_STRING = [(0.0178, 10_000), (0.0087, 900), (0.0077, 600)]
ANNULUS_BOTTOM_UP = [(0.0291, 600), (0.0459, 900), (0.0459, 4_850), (0.0489, 5_150)]


def limits(string_md, annulus_md):
    return bullhead_limits(string_md, annulus_md, OMW, KILL_FLUID, MAMW, SHOE_FT, SHOE_FT, BIT_FT, VERTICAL)


def test_limits_before_and_after():
    # Nothing pumped: both sides = MAASP = (14.6 - 10.4) x 0.052 x 5,150 = 1,124.76 -> 1,124
    assert limits(0, 0) == (1124, 1124)
    # Both sides full of kill fluid: (14.6 - 11.5) x 0.052 x 5,150 = 830.18 -> 830
    assert limits(BIT_FT, BIT_FT) == (830, 830)


def test_string_limit_depends_on_both_columns():
    # String full of kill fluid, open-hole annulus still original mud:
    # 0.052 x [14.6 x 5,150 - 11.5 x 11,500 + 10.4 x 6,350] = 466.96 -> 466
    # The annulus formula would have given 830 - the string side must use both columns.
    assert limits(BIT_FT, SHOE_FT) == (466, 830)


def test_string_limit_at_the_dp_crossover_worked_by_hand():
    # Kill fluid 10,000 ft down the string, 3,641 ft down the annulus (above the shoe):
    # 0.052 x [75,190 - (11.5 x 10,000 + 10.4 x 1,500) + 10.4 x 6,350] = 552.76 -> 552
    assert limits(10_000, 3_641)[0] == 552


def test_equipment_limit_is_the_lowest_rating_or_test():
    ratings = [("BOP stack, tested", 3_500), ('9-5/8" casing, tested', 3_000), ("Pump lines, rated", 5_000)]
    assert equipment_limit(ratings) == ('9-5/8" casing, tested', 3_000)


def test_gas_migration_and_minimum_rate():
    # 100 psi/hr / 0.5408 psi/ft = 184.9 -> 185 ft/hr (IADC #34)
    assert gas_migration_rate(100, 0.5408) == 185
    # (185 / 60) x 0.0489 / 0.117 = 1.29 spm -> rounded UP -> 2 spm (IADC #13; a minimum)
    assert minimum_spm_to_beat_gas_migration(185, 0.0489, 0.117) == 2
    # An exact whole number stays put: 3.0 spm -> 3
    assert minimum_spm_to_beat_gas_migration(60, 0.351, 0.117) == 3


def chart(equipment_psi=3_000, overdisplacement_bbl=10.0):
    return [tuple(row) for row in bullhead_chart(OMW, KILL_FLUID, MAMW, SHOE_FT, DRILL_STRING, ANNULUS_BOTTOM_UP,
                                                 0.117, equipment_psi, overdisplacement_bbl)]


def test_bullhead_chart_same_rate_both_sides():
    # (strokes, string kill MD, annulus kill MD, string max, annulus max, row)
    assert chart() == [
        (0, 0, 0, 1124, 1124, STEP),
        (456, 3_000, 1_092, 953, 1062, STEP),
        (912, 5_994, 2_182, 781, 999, STEP),
        (1368, 8_994, 3_274, 610, 937, STEP),
        (1521, 10_000, 3_641, 552, 916, STRING_CROSSOVER),
        (1588, 10_900, 3_800, 501, 907, STRING_CROSSOVER),
        (1627, 11_500, 3_894, 466, 902, STRING_AT_BIT),         # lowest string limit
        (1824, 11_500, 4_365, 466, 875, STEP),
        (2152, 11_500, 5_150, 466, 830, ANNULUS_AT_SHOE),
        (2280, 11_500, 5_477, 485, 830, STEP),                  # string limit climbs back as kill
        (2736, 11_500, 6_638, 552, 830, STEP),                  # fluid fills the annulus below the shoe
        (3192, 11_500, 7_802, 618, 830, STEP),
        (3648, 11_500, 8_963, 685, 830, STEP),
        (4104, 11_500, 10_126, 751, 830, STEP),
        (4557, 11_500, 11_500, 830, 830, ANNULUS_AT_BOTTOM),    # kill point
        (4642, 11_500, 11_500, 830, 830, OVERDISPLACED),        # + 10.0 bbl = 85 stks
    ]


def test_equipment_limit_caps_the_chart():
    # With a 1,000 psi equipment limit, the first rows are capped at 1,000.
    rows = chart(equipment_psi=1_000)
    assert rows[0][3:5] == (1000, 1000)
    assert rows[1][3:5] == (953, 1000)      # string 953 is below it; annulus 1,062 is capped


def test_no_overdisplacement_row_when_none_is_chosen():
    assert chart(overdisplacement_bbl=0)[-1][5] == ANNULUS_AT_BOTTOM


@pytest.mark.parametrize("row", chart())
def test_never_above_the_formation_limit_at_the_start(row):
    # Pumping can only take the limits DOWN from MAASP (1,124) on either side.
    assert row[3] <= 1124 and row[4] <= 1124
