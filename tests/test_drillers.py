"""Tests for the Driller's method - the simplest kill.

Baseline example well: SIDPP 650 psi, SICP 800 psi, ICP 1,400 psi, FCP 829 psi,
surface-to-bit 1,627 strokes, bit-to-surface 4,557 strokes.
"""

import pytest

from killsheet.drillers import (
    CHECK,
    HOLD,
    SHUT_DOWN,
    START_UP,
    drillers_method,
    gas_is_out,
    well_is_dead,
)

SIDPP_PSI = 650
SICP_PSI = 800
ICP_PSI = 1400
FCP_PSI = 829
SURFACE_TO_BIT_STROKES = 1627
BIT_TO_SURFACE_STROKES = 4557


def kill_steps():
    return drillers_method(
        SIDPP_PSI, SICP_PSI, ICP_PSI, FCP_PSI, SURFACE_TO_BIT_STROKES, BIT_TO_SURFACE_STROKES
    )


def test_drillers_method_steps():
    # (stage, gauge, hold psi, strokes) - None means "hold constant" / not stroke-based
    assert [(s.stage, s.gauge, s.hold_psi, s.strokes) for s in kill_steps()] == [
        # 1st circulation - original mud
        (START_UP, "casing", 800, None),                    # hold casing at SICP
        (HOLD, "drill pipe", 1400, 4557),                   # ICP, minimum one bottoms up
        (SHUT_DOWN, "casing", None, None),                  # hold casing constant
        (CHECK, "drill pipe and casing", 650, None),        # both read original SIDPP
        # 2nd circulation - kill mud
        (START_UP, "casing", 650, None),                    # hold casing at SIDPP value
        (HOLD, "casing", 650, 1627),                        # kill mud surface to bit
        (HOLD, "drill pipe", 829, 4557),                    # FCP, kill mud bit to surface
        (SHUT_DOWN, "casing", None, None),                  # hold casing constant
        (CHECK, "drill pipe and casing", 0, None),          # both read 0 - well dead
    ]


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
    assert gas_is_out(SIDPP_PSI, sidpp_psi, sicp_psi) is expected


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
