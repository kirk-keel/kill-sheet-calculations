"""Tests for the Wait and Weight method - vertical well, untapered string.

Baseline example well: KMW 11.5 ppg, SIDPP 650 psi, SICP 800 psi,
ICP 1,400 psi, FCP 829 psi, surface-to-bit 1,627 strokes,
bit-to-surface 4,557 strokes.
"""

import pytest

from killsheet.kill_steps import CHECK, HOLD, SHUT_DOWN, START_UP, WEIGHT_UP
from killsheet.schedule import BIT, CROSSOVER, STEP, pressure_schedule
from killsheet.wait_and_weight import (
    ICP_MATCHES,
    ICP_READS_LOW,
    ICP_RECALCULATED,
    kill_pressures_at_kill_rate,
    wait_and_weight_method,
)

KMW_PPG = 11.5
ORIGINAL_MUD_WEIGHT_PPG = 10.4
SIDPP_PSI = 650
ICP_PSI = 1400
FCP_PSI = 829
SURFACE_TO_BIT_STROKES = 1627
BIT_TO_SURFACE_STROKES = 4557


def test_wait_and_weight_steps():
    steps = wait_and_weight_method(800, ICP_PSI, FCP_PSI, KMW_PPG, SURFACE_TO_BIT_STROKES, BIT_TO_SURFACE_STROKES)
    # (stage, gauge, hold psi, strokes) - None means "hold constant" / not stroke-based
    assert [(s.stage, s.gauge, s.hold_psi, s.strokes) for s in steps] == [
        (WEIGHT_UP, "pits", None, None),                # weight up to KMW, retake SIDPP and SICP
        (START_UP, "casing", 800, None),                # hold casing at the retaken SICP
        (HOLD, "drill pipe", 1400, 1627),               # step down ICP -> FCP, surface to bit
        (HOLD, "drill pipe", 829, 4557),                # hold FCP, bit to surface
        (SHUT_DOWN, "casing", None, None),              # hold casing constant
        (CHECK, "drill pipe and casing", 0, None),      # both read 0 - well dead
    ]


def test_weight_up_step_names_the_kill_mud_weight():
    steps = wait_and_weight_method(800, ICP_PSI, FCP_PSI, KMW_PPG, SURFACE_TO_BIT_STROKES, BIT_TO_SURFACE_STROKES)
    assert "11.5 ppg" in steps[0].note
    assert "retake SIDPP (bump the float) and SICP" in steps[0].note


def test_start_up_uses_the_retaken_sicp():
    # Gas migrated while weighting up: SICP retaken at 830 psi before start-up.
    steps = wait_and_weight_method(830, ICP_PSI, FCP_PSI, KMW_PPG, SURFACE_TO_BIT_STROKES, BIT_TO_SURFACE_STROKES)
    assert (steps[1].stage, steps[1].gauge, steps[1].hold_psi) == (START_UP, "casing", 830)


def test_total_strokes_for_the_kill():
    # 1,627 + 4,557 = 6,184 strokes (Driller's method on the same well: 10,741)
    steps = wait_and_weight_method(800, ICP_PSI, FCP_PSI, KMW_PPG, SURFACE_TO_BIT_STROKES, BIT_TO_SURFACE_STROKES)
    assert sum(s.strokes for s in steps if s.strokes) == 6184


def at_kill_rate(observed_icp_psi, sidpp_at_start_psi=SIDPP_PSI):
    """ICP check for the baseline well: calculated ICP 1,400, FCP 829."""
    return kill_pressures_at_kill_rate(
        ICP_PSI, FCP_PSI, observed_icp_psi, sidpp_at_start_psi, KMW_PPG, ORIGINAL_MUD_WEIGHT_PPG
    )


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
