"""Driller's method: the simplest kill (vertical well, untapered string).

A constant bottomhole pressure kill in two circulations at the kill rate.
Every circulation uses the same start-up and shut-down procedure:

  Start-up:  bring the pump up to the kill rate holding CASING pressure constant.
  Shut-down: slow the pump to 0 holding CASING pressure constant.

1st circulation - ORIGINAL mud, circulate the gas out:
    Start-up holding casing at SICP, then hold DRILL PIPE at ICP.
    One bottoms up (bit-to-surface strokes) is the MINIMUM - keep
    circulating until the gas is out. Shut down and check: SIDPP and SICP
    must both read the original SIDPP. If SICP is higher, strung-out gas
    is still in the annulus - continue circulating.

2nd circulation - KILL mud:
    Start-up holding casing at the SIDPP value, then:
      a) hold CASING constant while kill mud goes surface to bit
      b) hold DRILL PIPE at FCP while kill mud goes bit to surface
    Shut down and check: SIDPP and SICP must both read 0 - the well is dead.

The pressures will only tell the truth if the start-up and shut-down
procedure is followed.
"""

from typing import NamedTuple

# Gauge readings within this many psi count as "the same".
GAUGE_TOLERANCE_PSI = 10

# Stages of each circulation.
START_UP = "start-up"
HOLD = "hold"
SHUT_DOWN = "shut-down"
CHECK = "check"


class KillStep(NamedTuple):
    """One step of the kill.

    hold_psi is None when the gauge is held at whatever it reads ("constant").
    strokes is None for steps that aren't measured in strokes.
    """

    circulation: str
    stage: str
    gauge: str
    hold_psi: int | None
    strokes: int | None
    note: str


def drillers_method(sidpp_psi, sicp_psi, icp_psi, fcp_psi, surface_to_bit_strokes, bit_to_surface_strokes):
    """Every step of a Driller's method kill, in order, including start-up,
    shut-down and the shut-in check after each circulation.
    """
    first = "1st circulation (original mud)"
    second = "2nd circulation (kill mud)"
    return [
        KillStep(first, START_UP, "casing", sicp_psi, None,
                 "bring pump to kill rate holding casing pressure constant"),
        KillStep(first, HOLD, "drill pipe", icp_psi, bit_to_surface_strokes,
                 "minimum - one bottoms up; continue until the gas is out"),
        KillStep(first, SHUT_DOWN, "casing", None, None,
                 "slow pump to 0 holding casing pressure constant"),
        KillStep(first, CHECK, "drill pipe and casing", sidpp_psi, None,
                 f"both must read the original SIDPP (+/-{GAUGE_TOLERANCE_PSI} psi); "
                 "if SICP is higher, gas is still in the annulus - continue circulating"),
        KillStep(second, START_UP, "casing", sidpp_psi, None,
                 "bring pump to kill rate holding casing pressure constant"),
        KillStep(second, HOLD, "casing", sidpp_psi, surface_to_bit_strokes,
                 "kill mud surface to bit"),
        KillStep(second, HOLD, "drill pipe", fcp_psi, bit_to_surface_strokes,
                 "kill mud bit to surface"),
        KillStep(second, SHUT_DOWN, "casing", None, None,
                 "slow pump to 0 holding casing pressure constant"),
        KillStep(second, CHECK, "drill pipe and casing", 0, None,
                 f"both must read 0 psi (+/-{GAUGE_TOLERANCE_PSI} psi) - the well is dead"),
    ]


def gauges_read(expected_psi, sidpp_psi, sicp_psi):
    """True if BOTH shut-in gauges read the expected pressure, within the tolerance.

        |SIDPP - expected| <= 10 psi  and  |SICP - expected| <= 10 psi
    """
    return (abs(sidpp_psi - expected_psi) <= GAUGE_TOLERANCE_PSI
            and abs(sicp_psi - expected_psi) <= GAUGE_TOLERANCE_PSI)


def gas_is_out(original_sidpp_psi, sidpp_psi, sicp_psi):
    """After the 1st circulation: True if the gas is out of the annulus.

    Both shut-in gauges must read the original SIDPP (+/- 10 psi). If SICP
    reads higher, strung-out gas is still in the annulus - keep circulating.
    """
    return gauges_read(original_sidpp_psi, sidpp_psi, sicp_psi)


def well_is_dead(sidpp_psi, sicp_psi):
    """After the 2nd circulation: True if both shut-in gauges read 0 (+/- 10 psi)."""
    return gauges_read(0, sidpp_psi, sicp_psi)
