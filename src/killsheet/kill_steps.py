"""Building blocks shared by every kill method: the steps of a kill and the
shut-in gauge checks.

Every circulation uses the same start-up and shut-down procedure:
  Start-up:  bring the pump up to the kill rate holding CASING pressure constant.
  Shut-down: slow the pump to 0 holding CASING pressure constant.
The pressures will only tell the truth if that procedure is followed.

Every kill holds a SAFETY MARGIN (SF, chosen by the team) on bottom, so at
the final shut-in both gauges read the same TRAPPED pressure. It is bled off
through the choke, then the well is checked dead and flow checked.
"""

from typing import NamedTuple

# Gauge readings within this many psi count as "the same".
GAUGE_TOLERANCE_PSI = 10

# Stages of a kill.
WEIGHT_UP = "weight up"
START_UP = "start-up"
HOLD = "hold"
SHUT_DOWN = "shut-down"
CHECK = "check"
BLEED = "bleed"
FLOW_CHECK = "flow check"


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


def gauges_read(expected_psi, sidpp_psi, sicp_psi):
    """True if BOTH shut-in gauges read the expected pressure, within the tolerance.

        |SIDPP - expected| <= 10 psi  and  |SICP - expected| <= 10 psi
    """
    return (abs(sidpp_psi - expected_psi) <= GAUGE_TOLERANCE_PSI
            and abs(sicp_psi - expected_psi) <= GAUGE_TOLERANCE_PSI)


def well_is_dead(sidpp_psi, sicp_psi):
    """After the kill: True if both shut-in gauges read 0 (+/- 10 psi)."""
    return gauges_read(0, sidpp_psi, sicp_psi)


def final_shut_in_steps(circulation, trapped_psi):
    """The end of every kill: trapped pressure check, bleed off, dead-well check, flow check.

    trapped_psi: what BOTH gauges should read at the final shut-in.
    """
    return [
        KillStep(circulation, CHECK, "drill pipe and casing", trapped_psi, None,
                 f"both must read the same trapped pressure (+/-{GAUGE_TOLERANCE_PSI} psi); "
                 "if they don't match, something is wrong"),
        KillStep(circulation, BLEED, "choke", None, None,
                 "if any pressure on either gauge, bleed in small increments through the choke, "
                 "shutting in between; record volume bled; more than a few gallons or pressure "
                 "building back = well not dead"),
        KillStep(circulation, CHECK, "drill pipe and casing", 0, None,
                 f"both must read 0 psi (+/-{GAUGE_TOLERANCE_PSI} psi) - the well is dead"),
        KillStep(circulation, FLOW_CHECK, "well", None, None,
                 "flow check before opening the well"),
    ]
