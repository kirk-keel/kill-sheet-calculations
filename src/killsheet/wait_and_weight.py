"""Wait and Weight method: one circulation, with kill mud, holding a SAFETY
MARGIN (SF, chosen by the team) on bottom.

  Weight up: with the well shut in, weight up the active system to KMW.
             RETAKE SIDPP (bump the float) and SICP just before the pump is
             started - gas may have migrated while weighting up.
  Start-up:  bring the pump up to the kill rate holding CASING pressure
             constant at the retaken SICP + SF.
  Check ICP: once at the kill rate the drill pipe should read ICP + SF
             (+/- 10 psi). If it reads HIGH, recalculate from the gauge
             reading. FCP is never recalculated LOWER - if anything it goes
             higher. A LOW reading is a complication, not a recalculation:
             keep the calculated ICP and FCP.
  Hold:      follow the step-down schedule + SF on the DRILL PIPE from
             ICP + SF to FCP + SF while kill mud goes surface to bit.
  Hold:      hold the DRILL PIPE at FCP + SF while kill mud goes bit to surface.
  Shut-down: slow the pump to 0 holding CASING pressure constant.
  End:       both gauges read the TRAPPED pressure (= SF). Bleed it off,
             check 0 (+/- 10 psi) - the well is dead - and flow check.
"""

from killsheet.formulas import final_circulating_pressure
from killsheet.kill_steps import (
    CHECK,
    GAUGE_TOLERANCE_PSI,
    HOLD,
    SHUT_DOWN,
    START_UP,
    WEIGHT_UP,
    KillStep,
    final_shut_in_steps,
)
from killsheet.rounding import round_to_whole_number

# What the ICP check found once the pump was at kill rate.
ICP_MATCHES = "matches"              # within +/- 10 psi: use the calculated ICP and FCP
ICP_RECALCULATED = "recalculated"    # reads high: ICP and FCP rebuilt from the reading
ICP_READS_LOW = "reads low"          # a complication: calculated ICP and FCP are kept


def actual_scr_pressure(observed_icp_psi, sidpp_at_start_psi, safety_margin_psi):
    """Actual SCR pressure (psi) from the drill pipe reading at kill rate.

        Actual SCR = Observed ICP - SF - Retaken SIDPP
    """
    return round_to_whole_number(observed_icp_psi - safety_margin_psi - sidpp_at_start_psi)


def trapped_pressure(safety_margin_psi, fcp_psi, kill_mud_friction_psi):
    """Pressure (psi) on both gauges at the final shut-in, kill mud to surface.

        Trapped = SF + (FCP used - Actual friction with kill mud), never below 0

    The step-down schedule ends on FCP + SF. FCP is the friction, so the
    trapped pressure is just the SF (baseline: 50 psi). Only when a high ICP
    recalculation kept the calculated FCP (higher than the actual friction)
    is it more.
    """
    return max(0, safety_margin_psi + fcp_psi - kill_mud_friction_psi)


def wait_and_weight_method(sicp_at_start_psi, icp_psi, fcp_psi, kill_mud_weight_ppg,
                           surface_to_bit_strokes, bit_to_surface_strokes, safety_margin_psi,
                           kill_mud_friction_psi=None):
    """Every step of a Wait and Weight kill, in order.

    sicp_at_start_psi:     the SICP RETAKEN just before the pump is started
    safety_margin_psi:     SF held on bottom, chosen by the team
    kill_mud_friction_psi: actual friction with kill mud at kill rate. Leave it
                           out unless the ICP was recalculated: it is then the
                           FCP. After a recalculation it is
                           Actual SCR x (KMW / OMW).
    The step-down schedule itself comes from schedule.pressure_schedule().
    """
    kill = "kill circulation (kill mud)"
    sf = safety_margin_psi
    friction = fcp_psi if kill_mud_friction_psi is None else kill_mud_friction_psi
    trapped = trapped_pressure(sf, fcp_psi, friction)
    return [
        KillStep(kill, WEIGHT_UP, "pits", None, None,
                 f"weight up the active system to {kill_mud_weight_ppg:.1f} ppg; "
                 "retake SIDPP (bump the float) and SICP just before pump start-up"),
        KillStep(kill, START_UP, "casing", sicp_at_start_psi + sf, None,
                 "bring pump to kill rate holding casing pressure constant at the retaken SICP + SF"),
        KillStep(kill, CHECK, "drill pipe", icp_psi + sf, None,
                 f"at kill rate the drill pipe must read ICP + SF (+/-{GAUGE_TOLERANCE_PSI} psi); "
                 "if high, recalculate (FCP never lower); if low, a complication"),
        KillStep(kill, HOLD, "drill pipe", icp_psi + sf, surface_to_bit_strokes,
                 f"follow the step-down schedule + SF from {icp_psi + sf:,} to {fcp_psi + sf:,} psi "
                 "- kill mud surface to bit"),
        KillStep(kill, HOLD, "drill pipe", fcp_psi + sf, bit_to_surface_strokes,
                 "hold FCP + SF - kill mud bit to surface"),
        KillStep(kill, SHUT_DOWN, "casing", None, None,
                 f"slow pump to 0 holding casing pressure constant (expect {trapped:,} psi)"),
    ] + final_shut_in_steps(kill, trapped)


def kill_pressures_at_kill_rate(calculated_icp_psi, calculated_fcp_psi, observed_icp_psi,
                                sidpp_at_start_psi, kill_mud_weight_ppg, original_mud_weight_ppg,
                                safety_margin_psi):
    """ICP and FCP to use once the pump is at kill rate.

    observed_icp_psi:   what the drill pipe reads at kill rate (it includes the SF)
    sidpp_at_start_psi: SIDPP retaken (float bumped) just before start-up

    The reading is compared with ICP + SF. Returns (icp_psi, fcp_psi, status)
    WITHOUT the SF (the steps add it back), where status is:
      ICP_MATCHES      - within +/- 10 psi: calculated ICP and FCP
      ICP_RECALCULATED - more than 10 psi HIGH:
                             Actual SCR = Observed ICP - SF - Retaken SIDPP
                             ICP        = Observed ICP - SF
                             FCP        = Actual SCR x (KMW / OMW), but never
                                          lower than the calculated FCP
      ICP_READS_LOW    - more than 10 psi LOW: a complication. Calculated ICP
                         and FCP are kept - they are never recalculated lower.
    """
    if sidpp_at_start_psi <= 0:
        raise ValueError(
            "Retaken SIDPP must be greater than 0 psi. If the drill pipe reads 0 with a "
            "float in the string, bump the float to determine the true SIDPP."
        )
    expected_psi = calculated_icp_psi + safety_margin_psi
    if abs(observed_icp_psi - expected_psi) <= GAUGE_TOLERANCE_PSI:
        return calculated_icp_psi, calculated_fcp_psi, ICP_MATCHES
    if observed_icp_psi < expected_psi:
        return calculated_icp_psi, calculated_fcp_psi, ICP_READS_LOW

    actual_scr_psi = actual_scr_pressure(observed_icp_psi, sidpp_at_start_psi, safety_margin_psi)
    fcp_psi = final_circulating_pressure(actual_scr_psi, kill_mud_weight_ppg, original_mud_weight_ppg)
    icp_psi = round_to_whole_number(observed_icp_psi - safety_margin_psi)
    return icp_psi, max(fcp_psi, calculated_fcp_psi), ICP_RECALCULATED
