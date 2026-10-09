"""Bullheading while drilling - vertical well, tapered string.

The approved vertical tapered well: 5" DP over 3-1/2" DP, HWDP and DC, 7" 26# casing
to 9,500 ft, 6-1/8" hole to 11,500 ft. 10.4 ppg mud, kill fluid 11.5 ppg, MAMW 12.2 ppg.
Annular shut; the same rate down the string and the backside.
Verified by a well control specialist before this test was written.
"""

from killsheet.bullhead import (
    ANNULUS_AT_BOTTOM,
    ANNULUS_AT_SHOE,
    OVERDISPLACED,
    STEP,
    STRING_AT_BIT,
    STRING_CROSSOVER,
    bullhead_chart,
    bullhead_limits,
    minimum_spm_to_beat_gas_migration,
)
from killsheet.formulas import kill_mud_weight, max_allowable_mud_weight
from killsheet.strokes import surface_to_bit_strokes, total_volume

DRILL_STRING = [(0.0178, 7_000), (0.0074, 3_600), (0.0041, 600), (0.0049, 300)]
ANNULUS_BOTTOM_UP = [(0.0145, 300), (0.0245, 600), (0.0245, 1_100), (0.0264, 2_500), (0.0140, 7_000)]


def test_inputs():
    assert kill_mud_weight(650, 11_500, 10.4) == 11.5
    assert max_allowable_mud_weight(1_100, 9_500, 10.0) == 12.2
    assert (total_volume(DRILL_STRING), surface_to_bit_strokes(DRILL_STRING, 0.117)) == (155.2, 1326)
    annulus_top_down = list(reversed(ANNULUS_BOTTOM_UP))
    assert (total_volume(annulus_top_down), surface_to_bit_strokes(annulus_top_down, 0.117)) == (210.1, 1796)


def test_minimum_rate_with_the_largest_annulus():
    # (185 / 60) x 0.0264 / 0.117 = 0.70 -> rounded UP -> 1 spm
    assert minimum_spm_to_beat_gas_migration(185, 0.0264, 0.117) == 1


def test_limits_worked_by_hand():
    def limits(string_md, annulus_md):
        return bullhead_limits(string_md, annulus_md, 10.4, 11.5, 12.2, 9_500, 9_500, 11_500, [(11_500, 11_500)])

    assert limits(0, 0) == (889, 889)               # MAASP: (12.2 - 10.4) x 494 = 889.2
    # 900 stks: string 0.052 x [115,900 - (11.5 x 5,916 + 10.4 x 5,584) + 10.4 x 2,000] = 550.8
    #           annulus 0.052 x [115,900 - (11.5 x 7,277 + 10.4 x 2,223)] = 472.96
    assert limits(5_916, 7_277) == (550, 472)
    # String full, open hole still mud: 0.052 x [115,900 - 11.5 x 11,500 + 10.4 x 2,000] = 231.4
    assert limits(11_500, 9_500) == (231, 345)
    assert limits(11_500, 11_500) == (345, 345)     # (12.2 - 11.5) x 494 = 345.8


def test_bullhead_chart():
    rows = bullhead_chart(10.4, 11.5, 12.2, 9_500, DRILL_STRING, ANNULUS_BOTTOM_UP, 0.117, 3_000,
                          overdisplacement_bbl=5.0)
    # (strokes, string kill MD, annulus kill MD, string max, annulus max, row)
    assert [tuple(row) for row in rows] == [
        (0, 0, 0, 889, 889, STEP),
        (180, 1_185, 1_507, 821, 802, STEP),
        (360, 2_365, 3_007, 753, 717, STEP),
        (540, 3_551, 4_514, 686, 630, STEP),
        (720, 4_730, 6_014, 618, 545, STEP),
        (900, 5_916, 7_277, 550, 472, STEP),
        (1065, 7_000, 8_008, 488, 431, STRING_CROSSOVER),       # 5" / 3-1/2" DP
        (1080, 7_244, 8_076, 474, 427, STEP),
        (1260, 10_086, 8_871, 312, 381, STEP),
        (1292, 10_600, 9_015, 282, 373, STRING_CROSSOVER),      # DP / HWDP
        (1314, 11_200, 9_110, 248, 368, STRING_CROSSOVER),      # HWDP / DC
        (1326, 11_500, 9_163, 231, 365, STRING_AT_BIT),         # lowest string limit
        (1402, 11_500, 9_500, 231, 345, ANNULUS_AT_SHOE),
        (1440, 11_500, 9_683, 241, 345, STEP),
        (1620, 11_500, 10_539, 290, 345, STEP),
        (1796, 11_500, 11_500, 345, 345, ANNULUS_AT_BOTTOM),    # kill point
        (1839, 11_500, 11_500, 345, 345, OVERDISPLACED),        # + 5.0 bbl = 43 stks
    ]


def test_annulus_falls_faster_than_the_string_at_first():
    # The tight 5" DP x 7" casing annulus (0.0140) moves kill fluid down faster per
    # stroke than the 5" DP (0.0178), so the annulus limit drops first.
    rows = bullhead_chart(10.4, 11.5, 12.2, 9_500, DRILL_STRING, ANNULUS_BOTTOM_UP, 0.117, 3_000)
    first_step = rows[1]
    assert first_step.annulus_kill_md_ft > first_step.string_kill_md_ft
    assert first_step.annulus_max_psi < first_step.string_max_psi
