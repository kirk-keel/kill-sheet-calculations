"""Tests for the Driller's method - the simplest kill.

Baseline example well: SIDPP 650 psi, ICP 1,400 psi, FCP 829 psi,
surface-to-bit 1,627 strokes, bit-to-surface 4,557 strokes.
"""

from killsheet.drillers import KillStep, drillers_method

SIDPP_PSI = 650
ICP_PSI = 1400
FCP_PSI = 829
SURFACE_TO_BIT_STROKES = 1627
BIT_TO_SURFACE_STROKES = 4557


def test_drillers_method_steps():
    steps = drillers_method(SIDPP_PSI, ICP_PSI, FCP_PSI, SURFACE_TO_BIT_STROKES, BIT_TO_SURFACE_STROKES)
    assert steps == [
        # 1st circulation: original mud, hold drill pipe at ICP for bottoms up
        KillStep("1st circulation (original mud)", "drill pipe", 1400, 4557),
        # 2nd circulation: kill mud to the bit, hold casing at the SIDPP value
        KillStep("2nd circulation (kill mud), surface to bit", "casing", 650, 1627),
        # 2nd circulation: kill mud bit to surface, hold drill pipe at FCP
        KillStep("2nd circulation (kill mud), bit to surface", "drill pipe", 829, 4557),
    ]


def test_total_strokes_for_the_kill():
    # 4,557 + 1,627 + 4,557 = 10,741 strokes over both circulations
    steps = drillers_method(SIDPP_PSI, ICP_PSI, FCP_PSI, SURFACE_TO_BIT_STROKES, BIT_TO_SURFACE_STROKES)
    assert sum(step.strokes for step in steps) == 10741
