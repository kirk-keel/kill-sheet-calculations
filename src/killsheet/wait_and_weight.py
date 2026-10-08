"""Wait and Weight method: one circulation, with kill mud.

  Weight up: with the well shut in, weight up the active system to KMW.
             RETAKE SIDPP (bump the float) and SICP just before the pump is
             started - gas may have migrated while weighting up.
  Start-up:  bring the pump up to the kill rate holding CASING pressure
             constant at the retaken SICP.
  Check ICP: once at the kill rate the drill pipe should read ICP (+/- 10 psi).
             If it reads HIGH, recalculate from the gauge reading. FCP is
             never recalculated LOWER - if anything it goes higher. A LOW
             reading is a complication, not a recalculation: keep the
             calculated ICP and FCP.
  Hold:      follow the step-down schedule on the DRILL PIPE from ICP to
             FCP while kill mud goes surface to bit.
  Hold:      hold the DRILL PIPE at FCP while kill mud goes bit to surface.
  Shut-down: slow the pump to 0 holding CASING pressure constant.
  Check:     SIDPP and SICP must both read 0 (+/- 10 psi) - the well is dead.
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
)
from killsheet.rounding import round_to_whole_number

# What the ICP check found once the pump was at kill rate.
ICP_MATCHES = "matches"              # within +/- 10 psi: use the calculated ICP and FCP
ICP_RECALCULATED = "recalculated"    # reads high: ICP and FCP rebuilt from the reading
ICP_READS_LOW = "reads low"          # a complication: calculated ICP and FCP are kept


def wait_and_weight_method(sicp_at_start_psi, icp_psi, fcp_psi, kill_mud_weight_ppg,
                           surface_to_bit_strokes, bit_to_surface_strokes):
    """Every step of a Wait and Weight kill, in order.

    sicp_at_start_psi is the SICP RETAKEN just before the pump is started.
    The step-down schedule itself comes from schedule.pressure_schedule().
    """
    kill = "kill circulation (kill mud)"
    return [
        KillStep(kill, WEIGHT_UP, "pits", None, None,
                 f"weight up the active system to {kill_mud_weight_ppg:.1f} ppg; "
                 "retake SIDPP (bump the float) and SICP just before pump start-up"),
        KillStep(kill, START_UP, "casing", sicp_at_start_psi, None,
                 "bring pump to kill rate holding casing pressure constant at the retaken SICP"),
        KillStep(kill, HOLD, "drill pipe", icp_psi, surface_to_bit_strokes,
                 f"follow the step-down schedule from ICP {icp_psi:,} to FCP {fcp_psi:,} psi "
                 "- kill mud surface to bit"),
        KillStep(kill, HOLD, "drill pipe", fcp_psi, bit_to_surface_strokes,
                 "hold FCP - kill mud bit to surface"),
        KillStep(kill, SHUT_DOWN, "casing", None, None,
                 "slow pump to 0 holding casing pressure constant"),
        KillStep(kill, CHECK, "drill pipe and casing", 0, None,
                 f"both must read 0 psi (+/-{GAUGE_TOLERANCE_PSI} psi) - the well is dead"),
    ]


def kill_pressures_at_kill_rate(calculated_icp_psi, calculated_fcp_psi, observed_icp_psi,
                                sidpp_at_start_psi, kill_mud_weight_ppg, original_mud_weight_ppg):
    """ICP and FCP to use once the pump is at kill rate.

    observed_icp_psi:   what the drill pipe reads at kill rate
    sidpp_at_start_psi: SIDPP retaken (float bumped) just before start-up

    Returns (icp_psi, fcp_psi, status), where status is:
      ICP_MATCHES      - within +/- 10 psi: calculated ICP and FCP
      ICP_RECALCULATED - more than 10 psi HIGH:
                             Actual SCR = Observed ICP - Retaken SIDPP
                             ICP        = Observed ICP
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
    if abs(observed_icp_psi - calculated_icp_psi) <= GAUGE_TOLERANCE_PSI:
        return calculated_icp_psi, calculated_fcp_psi, ICP_MATCHES
    if observed_icp_psi < calculated_icp_psi:
        return calculated_icp_psi, calculated_fcp_psi, ICP_READS_LOW

    actual_scr_psi = round_to_whole_number(observed_icp_psi - sidpp_at_start_psi)
    fcp_psi = final_circulating_pressure(actual_scr_psi, kill_mud_weight_ppg, original_mud_weight_ppg)
    return round_to_whole_number(observed_icp_psi), max(fcp_psi, calculated_fcp_psi), ICP_RECALCULATED
