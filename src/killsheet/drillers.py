"""Driller's method: the simplest kill (vertical well, untapered string).

A constant bottomhole pressure kill in two circulations at the kill rate,
holding a SAFETY MARGIN (SF, chosen by the team) on bottom the whole way.
Every circulation uses the same start-up and shut-down procedure:

  Start-up:  bring the pump up to the kill rate holding CASING pressure constant.
  Shut-down: slow the pump to 0 holding CASING pressure constant.

1st circulation - ORIGINAL mud, circulate the gas out:
    Start-up holding casing at SICP + SF, then hold DRILL PIPE at ICP + SF.
    One bottoms up (bit-to-surface strokes) is the MINIMUM - keep
    circulating until the gas is out. Shut down and check: SIDPP and SICP
    must both read SIDPP + SF. If SICP is higher, strung-out gas is still
    in the annulus - continue circulating.

2nd circulation - KILL mud:
    Start-up holding casing at SIDPP + SF, then:
      a) hold CASING constant while kill mud goes surface to bit
      b) hold the DRILL PIPE at its reading with kill mud at the bit while
         kill mud goes bit to surface. That reading is a little below
         FCP + SF, because the kill mud (rounded UP) overbalances SIDPP.
    Shut down: both gauges read the TRAPPED pressure. Bleed it off, check
    0 psi - the well is dead - and flow check.

The pressures will only tell the truth if the start-up and shut-down
procedure is followed.
"""

from killsheet.kill_steps import (  # noqa: F401  (well_is_dead re-exported for callers)
    CHECK,
    GAUGE_TOLERANCE_PSI,
    HOLD,
    SHUT_DOWN,
    START_UP,
    KillStep,
    final_shut_in_steps,
    gauges_read,
    well_is_dead,
)


def drill_pipe_with_kill_mud_at_bit(sidpp_psi, fcp_psi, safety_margin_psi, kill_mud_overbalance_psi):
    """Drill pipe reading (psi) in the 2nd circulation when kill mud reaches the bit.

        DP at bit = FCP + SIDPP + SF - Kill mud overbalance

    Casing is held at SIDPP + SF while the kill mud goes down, so BHP stays at
    formation pressure + SF. Baseline: 829 + 650 + 50 - 658 = 871 psi
    (not FCP + SF = 879). This is the pressure held from the bit to surface.
    """
    return fcp_psi + sidpp_psi + safety_margin_psi - kill_mud_overbalance_psi


def trapped_pressure(sidpp_psi, safety_margin_psi, kill_mud_overbalance_psi):
    """Pressure (psi) on both gauges at the final shut-in, kill mud to surface.

        Trapped = SIDPP + SF - Kill mud overbalance, never below 0

    Baseline: 650 + 50 - 658 = 42 psi. A gauge can't read below 0.
    """
    return max(0, sidpp_psi + safety_margin_psi - kill_mud_overbalance_psi)


def drillers_method(sidpp_psi, sicp_psi, icp_psi, fcp_psi, surface_to_bit_strokes, bit_to_surface_strokes,
                    safety_margin_psi, kill_mud_overbalance_psi):
    """Every step of a Driller's method kill, in order, including start-up,
    shut-down, the shut-in check after each circulation, the trapped pressure
    bleed-off and the flow check.

    safety_margin_psi:        SF held on bottom, chosen by the team
    kill_mud_overbalance_psi: from formulas.kill_mud_overbalance()
    """
    first = "1st circulation (original mud)"
    second = "2nd circulation (kill mud)"
    sf = safety_margin_psi
    dp_at_bit = drill_pipe_with_kill_mud_at_bit(sidpp_psi, fcp_psi, sf, kill_mud_overbalance_psi)
    trapped = trapped_pressure(sidpp_psi, sf, kill_mud_overbalance_psi)

    hold_to_surface_note = "kill mud bit to surface - hold the drill pipe reading with kill mud at the bit"
    if sidpp_psi + sf < kill_mud_overbalance_psi:
        # The SF is less than the kill mud's extra overbalance: casing reaches 0 early.
        hold_to_surface_note += (
            f". If casing reaches 0 with the choke fully open, drill pipe will rise toward FCP "
            f"({fcp_psi:,} here). Expected; BHP ends slightly over formation pressure. "
            "Continue to surface.")

    return [
        KillStep(first, START_UP, "casing", sicp_psi + sf, None,
                 "bring pump to kill rate holding casing pressure constant at SICP + SF"),
        KillStep(first, HOLD, "drill pipe", icp_psi + sf, bit_to_surface_strokes,
                 "ICP + SF; minimum - one bottoms up; continue until the gas is out"),
        KillStep(first, SHUT_DOWN, "casing", None, None,
                 "slow pump to 0 holding casing pressure constant"),
        KillStep(first, CHECK, "drill pipe and casing", sidpp_psi + sf, None,
                 f"both must read SIDPP + SF (+/-{GAUGE_TOLERANCE_PSI} psi); "
                 "if SICP is higher, gas is still in the annulus - continue circulating"),
        KillStep(second, START_UP, "casing", sidpp_psi + sf, None,
                 "bring pump to kill rate holding casing pressure constant at SIDPP + SF"),
        KillStep(second, HOLD, "casing", sidpp_psi + sf, surface_to_bit_strokes,
                 f"kill mud surface to bit; drill pipe falls from {icp_psi + sf:,} to {dp_at_bit:,} psi"),
        KillStep(second, HOLD, "drill pipe", dp_at_bit, bit_to_surface_strokes, hold_to_surface_note),
        KillStep(second, SHUT_DOWN, "casing", None, None,
                 f"slow pump to 0 holding casing pressure constant (expect {trapped:,} psi)"),
    ] + final_shut_in_steps(second, trapped)


def gas_is_out(original_sidpp_psi, sidpp_psi, sicp_psi, safety_margin_psi):
    """After the 1st circulation: True if the gas is out of the annulus.

    Both shut-in gauges must read the original SIDPP + SF (+/- 10 psi). If
    SICP reads higher, strung-out gas is still in the annulus - keep circulating.
    """
    return gauges_read(original_sidpp_psi + safety_margin_psi, sidpp_psi, sicp_psi)
