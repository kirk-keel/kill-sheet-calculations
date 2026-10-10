"""Tests for the Driller's method - the simplest kill.

Baseline example well: SIDPP 650 psi, SICP 800 psi, ICP 1,400 psi, FCP 829 psi,
surface-to-bit 1,627 strokes, bit-to-surface 4,557 strokes.
Kill mud overbalance: (11.5 - 10.4) x 0.052 x 11,500 = 657.8 -> 658 psi.

SF 0 is the regression baseline (the values before the safety margin, with
the 2nd circulation hold corrected from 829 to 821). SF 50 is the hand-worked
example approved by the well control specialist.
"""

import pytest

from killsheet.drillers import (
    CHECK,
    HOLD,
    SHUT_DOWN,
    START_UP,
    drill_pipe_with_kill_mud_at_bit,
    drillers_method,
    gas_is_out,
    trapped_pressure,
    well_is_dead,
)
from killsheet.kill_steps import BLEED, FLOW_CHECK

SIDPP_PSI = 650
SICP_PSI = 800
ICP_PSI = 1400
FCP_PSI = 829
SURFACE_TO_BIT_STROKES = 1627
BIT_TO_SURFACE_STROKES = 4557
OVERBALANCE_PSI = 658


def kill_steps(safety_margin_psi=0):
    return drillers_method(
        SIDPP_PSI, SICP_PSI, ICP_PSI, FCP_PSI, SURFACE_TO_BIT_STROKES, BIT_TO_SURFACE_STROKES,
        safety_margin_psi, OVERBALANCE_PSI,
    )


def test_drill_pipe_with_kill_mud_at_bit():
    # FCP + SIDPP + SF - overbalance
    assert drill_pipe_with_kill_mud_at_bit(650, 829, 50, 658) == 871     # not FCP + SF = 879
    assert drill_pipe_with_kill_mud_at_bit(650, 829, 0, 658) == 821      # not FCP = 829


def test_trapped_pressure():
    assert trapped_pressure(650, 50, 658) == 42      # 650 + 50 - 658
    assert trapped_pressure(650, 0, 658) == 0        # -8: a gauge can't read below 0


def test_drillers_method_steps_sf_0():
    # (stage, gauge, hold psi, strokes) - None means "hold constant" / not stroke-based
    assert [(s.stage, s.gauge, s.hold_psi, s.strokes) for s in kill_steps(0)] == [
        # 1st circulation - original mud
        (START_UP, "casing", 800, None),                    # hold casing at SICP
        (HOLD, "drill pipe", 1400, 4557),                   # ICP, minimum one bottoms up
        (SHUT_DOWN, "casing", None, None),                  # hold casing constant
        (CHECK, "drill pipe and casing", 650, None),        # both read original SIDPP
        # 2nd circulation - kill mud
        (START_UP, "casing", 650, None),                    # hold casing at SIDPP value
        (HOLD, "casing", 650, 1627),                        # kill mud surface to bit
        (HOLD, "drill pipe", 821, 4557),                    # 829 + 650 + 0 - 658, bit to surface
        (SHUT_DOWN, "casing", None, None),                  # hold casing constant
        (CHECK, "drill pipe and casing", 0, None),          # trapped: -8 reads 0
        (BLEED, "choke", None, None),                       # if any pressure, bleed it off
        (CHECK, "drill pipe and casing", 0, None),          # both read 0 - well dead
        (FLOW_CHECK, "well", None, None),
    ]


def test_drillers_method_steps_sf_50():
    # The hand-worked example approved by the well control specialist.
    assert [(s.stage, s.gauge, s.hold_psi, s.strokes) for s in kill_steps(50)] == [
        # 1st circulation - original mud
        (START_UP, "casing", 850, None),                    # SICP + SF
        (HOLD, "drill pipe", 1450, 4557),                   # ICP + SF, minimum one bottoms up
        (SHUT_DOWN, "casing", None, None),
        (CHECK, "drill pipe and casing", 700, None),        # SIDPP + SF: gas is out
        # 2nd circulation - kill mud
        (START_UP, "casing", 700, None),                    # SIDPP + SF
        (HOLD, "casing", 700, 1627),                        # drill pipe falls 1,450 -> 871
        (HOLD, "drill pipe", 871, 4557),                    # 829 + 650 + 50 - 658, NOT 879
        (SHUT_DOWN, "casing", None, None),                  # expect 42
        (CHECK, "drill pipe and casing", 42, None),         # trapped: 650 + 50 - 658
        (BLEED, "choke", None, None),
        (CHECK, "drill pipe and casing", 0, None),          # well dead
        (FLOW_CHECK, "well", None, None),
    ]


def test_drill_pipe_falls_to_the_reading_at_the_bit():
    note = kill_steps(50)[5].note
    assert "drill pipe falls from 1,450 to 871 psi" in note


def test_sf_below_kill_mud_overbalance_warns_casing_will_reach_0():
    # SF 0: SIDPP + SF (650) is less than the overbalance (658) - casing reaches 0
    # before kill mud reaches surface, then drill pipe rises toward FCP.
    note = kill_steps(0)[6].note
    assert ("If casing reaches 0 with the choke fully open, drill pipe will rise toward FCP "
            "(829 here). Expected; BHP ends slightly over formation pressure. Continue to surface.") in note


def test_sf_above_kill_mud_overbalance_has_no_casing_at_0_note():
    assert "casing reaches 0" not in kill_steps(50)[6].note
    assert "casing reaches 0" not in kill_steps(8)[6].note     # 650 + 8 = 658: exactly 0 at surface


def test_first_circulation_bottoms_up_is_a_minimum():
    first_hold = kill_steps()[1]
    assert "minimum" in first_hold.note


@pytest.mark.parametrize(
    "sidpp_psi, sicp_psi, expected",
    [
        (650, 650, True),       # both equal original SIDPP: gas is out
        (645, 658, True),       # within +/-10 psi
        (640, 660, True),       # exactly 10 psi off counts
        (650, 661, False),      # SICP 11 psi high: strung-out gas, keep circulating
        (650, 720, False),      # SICP well above SIDPP: gas still in the annulus
        (638, 650, False),      # SIDPP 12 psi low: not a clean reading
    ],
)
def test_gas_is_out(sidpp_psi, sicp_psi, expected):
    assert gas_is_out(SIDPP_PSI, sidpp_psi, sicp_psi, 0) is expected


@pytest.mark.parametrize(
    "sidpp_psi, sicp_psi, expected",
    [
        (700, 700, True),       # both read SIDPP + SF: gas is out
        (650, 650, False),      # 50 psi below SIDPP + SF: the SF was not held
        (700, 711, False),      # SICP 11 psi high: gas still in the annulus
    ],
)
def test_gas_is_out_with_sf_50(sidpp_psi, sicp_psi, expected):
    assert gas_is_out(SIDPP_PSI, sidpp_psi, sicp_psi, 50) is expected


@pytest.mark.parametrize(
    "sidpp_psi, sicp_psi, expected",
    [
        (0, 0, True),
        (5, 10, True),          # within +/-10 psi
        (0, 11, False),         # casing still reading pressure
        (25, 0, False),         # drill pipe still reading pressure
    ],
)
def test_well_is_dead(sidpp_psi, sicp_psi, expected):
    assert well_is_dead(sidpp_psi, sicp_psi) is expected
