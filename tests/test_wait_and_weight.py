"""Tests for the Wait and Weight method - vertical well, untapered string.

Baseline example well: KMW 11.5 ppg, SIDPP 650 psi, SICP 800 psi,
ICP 1,400 psi, FCP 829 psi, surface-to-bit 1,627 strokes,
bit-to-surface 4,557 strokes.

SF 0 is the regression baseline (the values before the safety margin).
SF 50 is the hand-worked example approved by the well control specialist.
"""

import pytest

from killsheet.kill_steps import BLEED, CHECK, FLOW_CHECK, HOLD, SHUT_DOWN, START_UP, WEIGHT_UP
from killsheet.formulas import final_circulating_pressure
from killsheet.schedule import BIT, CROSSOVER, STEP, pressure_schedule
from killsheet.wait_and_weight import (
    ICP_MATCHES,
    ICP_READS_LOW,
    ICP_RECALCULATED,
    actual_scr_pressure,
    kill_pressures_at_kill_rate,
    trapped_pressure,
    wait_and_weight_method,
)

KMW_PPG = 11.5
ORIGINAL_MUD_WEIGHT_PPG = 10.4
SIDPP_PSI = 650
ICP_PSI = 1400
FCP_PSI = 829
SURFACE_TO_BIT_STROKES = 1627
BIT_TO_SURFACE_STROKES = 4557


def kill_steps(sicp_at_start_psi=800, safety_margin_psi=0, icp_psi=ICP_PSI, kill_mud_friction_psi=None):
    return wait_and_weight_method(sicp_at_start_psi, icp_psi, FCP_PSI, KMW_PPG, SURFACE_TO_BIT_STROKES,
                                  BIT_TO_SURFACE_STROKES, safety_margin_psi, kill_mud_friction_psi)


def stages(steps):
    # (stage, gauge, hold psi, strokes) - None means "hold constant" / not stroke-based
    return [(s.stage, s.gauge, s.hold_psi, s.strokes) for s in steps]


def test_trapped_pressure():
    # SF + (FCP used - actual friction with kill mud), never below 0
    assert trapped_pressure(50, 829, 829) == 50      # the step-down ends on FCP + SF: trapped = SF
    assert trapped_pressure(0, 829, 829) == 0
    assert trapped_pressure(50, 829, 818) == 61      # high ICP, FCP kept at the calculated 829
    assert trapped_pressure(0, 829, 840) == 0        # a gauge can't read below 0


def test_wait_and_weight_steps_sf_0():
    assert stages(kill_steps(safety_margin_psi=0)) == [
        (WEIGHT_UP, "pits", None, None),                # weight up to KMW, retake SIDPP and SICP
        (START_UP, "casing", 800, None),                # hold casing at the retaken SICP
        (CHECK, "drill pipe", 1400, None),              # ICP check at kill rate
        (HOLD, "drill pipe", 1400, 1627),               # step down ICP -> FCP, surface to bit
        (HOLD, "drill pipe", 829, 4557),                # hold FCP, bit to surface
        (SHUT_DOWN, "casing", None, None),              # hold casing constant
        (CHECK, "drill pipe and casing", 0, None),      # trapped = SF = 0
        (BLEED, "choke", None, None),                   # if any pressure, bleed it off
        (CHECK, "drill pipe and casing", 0, None),      # both read 0 - well dead
        (FLOW_CHECK, "well", None, None),
    ]


def test_wait_and_weight_steps_sf_50():
    # The hand-worked example approved by the well control specialist.
    assert stages(kill_steps(safety_margin_psi=50)) == [
        (WEIGHT_UP, "pits", None, None),
        (START_UP, "casing", 850, None),                # retaken SICP + SF
        (CHECK, "drill pipe", 1450, None),              # ICP + SF
        (HOLD, "drill pipe", 1450, 1627),               # step-down + SF, 1,450 -> 879
        (HOLD, "drill pipe", 879, 4557),                # FCP + SF
        (SHUT_DOWN, "casing", None, None),              # expect 50
        (CHECK, "drill pipe and casing", 50, None),     # trapped = SF (NOT 42 as in Driller's)
        (BLEED, "choke", None, None),
        (CHECK, "drill pipe and casing", 0, None),      # well dead
        (FLOW_CHECK, "well", None, None),
    ]


def test_step_down_note_runs_from_icp_plus_sf_to_fcp_plus_sf():
    assert "from 1,450 to 879 psi" in kill_steps(safety_margin_psi=50)[3].note


def test_high_icp_recalculated_trapped_pressure_is_more_than_sf():
    # SF 50, SIDPP retaken at 680, drill pipe reads 1,470 at kill rate (ICP + SF = 1,450):
    #   actual SCR = 1,470 - 50 - 680 = 740; friction with kill mud = 740 x 11.5 / 10.4 = 818
    #   ICP = 1,470 - 50 = 1,420; FCP stays 829 (never lower than calculated)
    #   trapped = 50 + (829 - 818) = 61
    icp, fcp, status = at_kill_rate(1470, sidpp_at_start_psi=680, safety_margin_psi=50)
    assert (icp, fcp, status) == (1420, 829, ICP_RECALCULATED)
    friction = final_circulating_pressure(actual_scr_pressure(1470, 680, 50), KMW_PPG, ORIGINAL_MUD_WEIGHT_PPG)
    assert friction == 818
    steps = kill_steps(sicp_at_start_psi=830, safety_margin_psi=50, icp_psi=icp, kill_mud_friction_psi=friction)
    assert stages(steps) == [
        (WEIGHT_UP, "pits", None, None),
        (START_UP, "casing", 880, None),                # retaken SICP 830 + SF
        (CHECK, "drill pipe", 1470, None),              # recalculated ICP + SF = the reading
        (HOLD, "drill pipe", 1470, 1627),
        (HOLD, "drill pipe", 879, 4557),                # FCP + SF
        (SHUT_DOWN, "casing", None, None),
        (CHECK, "drill pipe and casing", 61, None),     # 50 + 829 - 818
        (BLEED, "choke", None, None),
        (CHECK, "drill pipe and casing", 0, None),
        (FLOW_CHECK, "well", None, None),
    ]


def test_weight_up_step_names_the_kill_mud_weight():
    steps = kill_steps()
    assert "11.5 ppg" in steps[0].note
    assert "retake SIDPP (bump the float) and SICP" in steps[0].note


def test_start_up_uses_the_retaken_sicp():
    # Gas migrated while weighting up: SICP retaken at 830 psi before start-up.
    steps = kill_steps(sicp_at_start_psi=830)
    assert (steps[1].stage, steps[1].gauge, steps[1].hold_psi) == (START_UP, "casing", 830)


def test_total_strokes_for_the_kill():
    # 1,627 + 4,557 = 6,184 strokes (Driller's method on the same well: 10,741)
    assert sum(s.strokes for s in kill_steps() if s.strokes) == 6184


def at_kill_rate(observed_icp_psi, sidpp_at_start_psi=SIDPP_PSI, safety_margin_psi=0):
    """ICP check for the baseline well: calculated ICP 1,400, FCP 829."""
    return kill_pressures_at_kill_rate(
        ICP_PSI, FCP_PSI, observed_icp_psi, sidpp_at_start_psi, KMW_PPG, ORIGINAL_MUD_WEIGHT_PPG,
        safety_margin_psi,
    )


@pytest.mark.parametrize(
    "observed_icp_psi, expected",
    [
        (1450, (1400, 829, ICP_MATCHES)),           # ICP + SF exactly
        (1460, (1400, 829, ICP_MATCHES)),           # within +/- 10 of ICP + SF
        (1439, (1400, 829, ICP_READS_LOW)),         # 11 psi low: a complication
        (1400, (1400, 829, ICP_READS_LOW)),         # reading ICP means the SF was not held
        # 1,500: actual SCR = 1,500 - 50 - 650 = 800 -> FCP 884.6 -> 885; ICP = 1,450
        (1500, (1450, 885, ICP_RECALCULATED)),
    ],
)
def test_icp_check_compares_with_icp_plus_sf(observed_icp_psi, expected):
    assert at_kill_rate(observed_icp_psi, safety_margin_psi=50) == expected


def test_actual_scr_pressure():
    assert actual_scr_pressure(1500, 650, 50) == 800      # observed - SF - retaken SIDPP
    assert actual_scr_pressure(1450, 650, 0) == 800


@pytest.mark.parametrize("observed_icp_psi", [1400, 1405, 1410, 1390])
def test_icp_within_10_psi_uses_calculated_values(observed_icp_psi):
    assert at_kill_rate(observed_icp_psi) == (1400, 829, ICP_MATCHES)


def test_recalculate_when_drill_pipe_reads_high():
    # Observed 1,450, retaken SIDPP 650: actual SCR = 1,450 - 650 = 800
    # FCP = 800 x (11.5 / 10.4) = 884.6 -> 885 (higher than 829, so it is used)
    assert at_kill_rate(1450) == (1450, 885, ICP_RECALCULATED)


def test_recalculate_uses_the_retaken_sidpp():
    # Gas migrated while weighting up: SIDPP retaken at 680 (float bumped).
    # Observed 1,430: actual SCR = 1,430 - 680 = 750 -> FCP = 829.3 -> 829
    assert at_kill_rate(1430, sidpp_at_start_psi=680) == (1430, 829, ICP_RECALCULATED)


def test_recalculated_fcp_is_never_lower_than_calculated():
    # Observed 1,420, retaken SIDPP 680: actual SCR = 740 -> 740 x 11.5 / 10.4 = 818.3 -> 818
    # 818 is LOWER than the calculated 829, so FCP stays at 829.
    assert at_kill_rate(1420, sidpp_at_start_psi=680) == (1420, 829, ICP_RECALCULATED)


@pytest.mark.parametrize("observed_icp_psi", [1389, 1380, 1300])
def test_drill_pipe_reading_low_is_never_recalculated_lower(observed_icp_psi):
    # More than 10 psi low is a complication: keep the calculated ICP and FCP.
    assert at_kill_rate(observed_icp_psi) == (1400, 829, ICP_READS_LOW)


def test_retaken_sidpp_of_zero_is_rejected():
    with pytest.raises(ValueError, match="bump the float"):
        at_kill_rate(1450, sidpp_at_start_psi=0)


def test_schedule_rebuilt_after_recalculation():
    # ICP 1,450, FCP 885 on the baseline string: drop to each row = 565 x MD / 11,500, rounded DOWN
    icp, fcp, _status = at_kill_rate(1450)
    baseline_string = [(0.0178, 10_000), (0.0087, 900), (0.0077, 600)]
    assert [tuple(row) for row in pressure_schedule(icp, fcp, baseline_string, 0.117)] == [
        (0, 0, 0, 1450, STEP),
        (163, 1_073, 1_073, 1398, STEP),
        (326, 2_140, 2_140, 1345, STEP),
        (489, 3_213, 3_213, 1293, STEP),
        (652, 4_287, 4_287, 1240, STEP),
        (815, 5_360, 5_360, 1187, STEP),
        (978, 6_427, 6_427, 1135, STEP),
        (1141, 7_500, 7_500, 1082, STEP),
        (1304, 8_573, 8_573, 1029, STEP),
        (1467, 9_640, 9_640, 977, STEP),
        (1521, 10_000, 10_000, 959, CROSSOVER),
        (1588, 10_900, 10_900, 915, CROSSOVER),
        (1627, 11_500, 11_500, 885, BIT),
    ]
