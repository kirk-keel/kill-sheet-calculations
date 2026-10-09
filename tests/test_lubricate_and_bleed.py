"""Tests for lubricate and bleed - kill weight mud, annulus at surface.

Kill mud 11.5 ppg (0.5980 psi/ft). Working pressure 50 psi, chosen by the team.
    Pump to  = casing pressure before pumping + working pressure
    Bleed to = casing pressure before pumping - (bbl x 0.5980 / surface capacity), rounded DOWN
The expected answers were worked by hand and verified by a well control specialist.
"""

from killsheet.lubricate_and_bleed import hydrostatic_added, lubricate_and_bleed_table

KILL_GRADIENT = 0.598
DP_X_CASING = 0.0489        # pipe in the hole
CASING_ONLY = 0.0732        # pipe out of the hole


def test_hydrostatic_added_is_rounded_down():
    assert hydrostatic_added(3.0, KILL_GRADIENT, DP_X_CASING) == 36     # 36.7 -> 36
    assert hydrostatic_added(3.2, KILL_GRADIENT, DP_X_CASING) == 39     # 39.1 -> 39
    assert hydrostatic_added(3.5, KILL_GRADIENT, DP_X_CASING) == 42     # 42.8 -> 42
    assert hydrostatic_added(18.0, KILL_GRADIENT, CASING_ONLY) == 147   # 147.05 -> 147


def test_first_three_cycles_worked_by_hand():
    rows = lubricate_and_bleed_table(1100, 50, [3.0, 3.2, 3.5], KILL_GRADIENT, DP_X_CASING)
    # (cycle, pump to, bbl pumped, hydrostatic added, bleed to)
    assert [tuple(row) for row in rows] == [
        (1, 1150, 3.0, 36, 1064),
        (2, 1114, 3.2, 39, 1025),
        (3, 1075, 3.5, 42, 983),
    ]


def test_runs_until_hydrostatic_control_is_regained():
    measured = [6.0, 7.0, 8.0, 9.0, 10.0, 10.0, 11.0, 11.0, 12.0, 12.0, 12.0, 12.0]
    rows = lubricate_and_bleed_table(1254, 50, measured, KILL_GRADIENT, DP_X_CASING)
    assert [row.bleed_to_psi for row in rows] == [1181, 1096, 999, 889, 767, 645, 511, 377, 231, 85, 0]
    # The last reading isn't needed: casing pressure is already 0 after cycle 11.
    assert len(rows) == 11


def test_bleed_to_never_goes_below_zero():
    # 85 psi left, 146 psi of hydrostatic lubricated: bleed to 0, not -61.
    rows = lubricate_and_bleed_table(85, 50, [12.0], KILL_GRADIENT, DP_X_CASING)
    assert rows[0].bleed_to_psi == 0


def test_pipe_out_of_the_hole_uses_the_casing():
    rows = lubricate_and_bleed_table(1158, 50, [15.0, 16.0, 17.0], KILL_GRADIENT, CASING_ONLY)
    assert [(row.hydrostatic_added_psi, row.bleed_to_psi) for row in rows] == [(122, 1036), (130, 906), (138, 768)]
