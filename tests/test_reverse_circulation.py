"""Tests for the reverse circulation kill - completion / workover / intervention (CWI) well.

Vertical completion: 2-7/8" 6.5# tubing, opened SSD at 9,900 ft above the packer at
9,950 ft, 5-1/2" 17# casing, perforations 10,100-10,200 ft, 8.6 ppg packer fluid.
Formation pressure 5,200 psi, SITP 1,800 psi, fracture gradient 0.75 psi/ft.
Kill weight fluid down the annulus (pump side), up the tubing (choke side).
Verified by a well control specialist before this test was written.
"""

import pytest

from killsheet.kill_steps import CHECK, HOLD, SHUT_DOWN, START_UP
from killsheet.reverse_circulation import (
    AT_SSD,
    STEP,
    TUBING_DISPLACED,
    bullhead_below_ssd_limits,
    final_circulating_pressure,
    fracture_pressure,
    kill_weight_fluid,
    max_annulus_pressure,
    pressure_at_ssd,
    reverse_circulation_steps,
    reverse_schedule,
    sicp_after_ssd_opened,
    sitp_after_ssd_opened,
    tubing_fluid_gradient,
    volume_below_ssd,
)

GRADIENT = 0.335
P_SSD = 5_116
KWF = 10.0
FRAC = 7_575


def test_tubing_gradient_and_pressure_at_the_ssd():
    # (5,200 - 1,800) / 10,150 = 0.33498 -> 0.3350 psi/ft
    assert tubing_fluid_gradient(5_200, 1_800, 10_150) == GRADIENT
    # 5,200 - 0.3350 x (10,150 - 9,900) = 5,116.25 -> 5,116 (formation fluid left below the SSD)
    assert pressure_at_ssd(5_200, GRADIENT, 10_150, 9_900) == P_SSD


def test_kill_weight_fluid_rule_1_and_optional_margin():
    # 5,116 / (0.052 x 9,900) = 9.938 -> UP -> 10.0 ppg
    assert kill_weight_fluid(P_SSD, 9_900) == 10.0
    # A margin is added BEFORE the round-up: 9.938 + 0.1 = 10.038 -> UP -> 10.1
    assert kill_weight_fluid(P_SSD, 9_900, margin_ppg=0.1) == 10.1


def test_pressures_once_the_ssd_is_open():
    # SICP = 5,116 - 8.6 x 0.052 x 9,900 (4,427.28) = 688.72 -> 689
    assert sicp_after_ssd_opened(P_SSD, 8.6, 9_900) == 689
    # SITP = 5,116 - 0.3350 x 9,900 (3,316.5) = 1,799.5 -> 1,800
    assert sitp_after_ssd_opened(P_SSD, GRADIENT, 9_900) == 1_800


def test_annulus_limits_packer_fluid_and_kill_fluid():
    assert fracture_pressure(0.75, 10_100) == FRAC                         # top perf
    # Packer fluid: 7,575 - (4,427.28 + 0.3350 x 200) = 3,080.72 -> 3,080
    assert max_annulus_pressure(FRAC, KWF, 8.6, 0, 9_900, GRADIENT, 10_100) == 3_080
    # Kill fluid:   7,575 - (5,148 + 67) = 2,360
    assert max_annulus_pressure(FRAC, KWF, 8.6, 9_900, 9_900, GRADIENT, 10_100) == 2_360


def test_fcp_from_the_observed_icp():
    # 900 - (10.0 - 8.6) x 0.052 x 9,900 = 900 - 720.72; drop rounded DOWN -> 900 - 720 = 180
    assert final_circulating_pressure(900, KWF, 8.6, 9_900) == (180, False)


@pytest.mark.parametrize("observed_icp", [700, 720])
def test_fcp_at_or_below_zero_is_floored_with_a_warning(observed_icp):
    # 700 - 720 = -20; 720 - 720 = 0: friction is less than the overbalance at the SSD
    assert final_circulating_pressure(observed_icp, KWF, 8.6, 9_900) == (0, True)


def test_steps_hold_tubing_at_start_up_and_shut_down():
    steps = reverse_circulation_steps(1_800, 900, 180, 3_010, 1_148)
    assert [(s.stage, s.gauge, s.hold_psi, s.strokes) for s in steps] == [
        (CHECK, "tubing and casing", None, None),           # open the SSD, record SITP and SICP
        (START_UP, "tubing", 1800, None),                   # hold TUBING at SITP - sides swapped
        (HOLD, "annulus", 900, 3010),                       # observed ICP, step down to FCP
        (HOLD, "annulus", 180, 1148),                       # hold FCP while the tubing is displaced
        (SHUT_DOWN, "tubing", None, None),                  # hold TUBING while bringing the pump off
        (CHECK, "tubing and casing", 0, None),              # both read 0 +/-10 psi
        (CHECK, "well", None, None),                        # flow check
    ]
    assert "flow check" in steps[-1].note
    assert "If the choke is wide open and pump pressure still climbs above FCP" in steps[3].note


def test_schedule():
    rows = reverse_schedule(900, KWF, 8.6, [(0.0152, 9_900)], [(0.0058, 9_900)], 0.0500, FRAC, GRADIENT,
                            10_100, 4_000)
    # (strokes, kill fluid MD, TVD, pump psi, max allowable psi, row)
    assert [tuple(row) for row in rows] == [
        (0, 0, 0, 900, 3080, STEP),
        (301, 993, 993, 828, 3008, STEP),          # 15.1 bbl: 1.4 x 0.052 x 993 = 72.3 -> 72
        (602, 1_980, 1_980, 756, 2936, STEP),
        (903, 2_973, 2_973, 684, 2864, STEP),
        (1204, 3_960, 3_960, 612, 2792, STEP),
        (1505, 4_953, 4_953, 540, 2720, STEP),
        (1806, 5_940, 5_940, 468, 2648, STEP),
        (2107, 6_933, 6_933, 396, 2575, STEP),
        (2408, 7_920, 7_920, 324, 2504, STEP),
        (2709, 8_913, 8_913, 252, 2431, STEP),
        (3010, 9_900, 9_900, 180, 2360, AT_SSD),               # 150.5 bbl / 0.05
        (4158, 9_900, 9_900, 180, 2360, TUBING_DISPLACED),     # + 57.4 bbl / 0.05 = 1,148
    ]


def test_schedule_never_goes_below_zero():
    rows = reverse_schedule(700, KWF, 8.6, [(0.0152, 9_900)], [(0.0058, 9_900)], 0.0500, FRAC, GRADIENT,
                            10_100, 4_000)
    assert min(row.pump_psi for row in rows) == 0


def test_equipment_limit_caps_the_schedule():
    rows = reverse_schedule(900, KWF, 8.6, [(0.0152, 9_900)], [(0.0058, 9_900)], 0.0500, FRAC, GRADIENT,
                            10_100, 2_500)
    assert rows[0].max_allowable_psi == 2_500       # formation 3,080, equipment 2,500
    assert rows[-1].max_allowable_psi == 2_360      # formation 2,360 is lower


def test_optional_bullhead_below_the_ssd():
    # Tubing SSD -> packer: 0.0058 x 50 = 0.29 -> 0.3; casing packer -> top perf: 0.0232 x 150 = 3.48 -> 3.5
    assert volume_below_ssd(0.0058, 50, 0.0232, 150) == 3.8
    # Initial 7,575 - (5,148 + 67) = 2,360; final 7,575 - 10.0 x 0.052 x 10,100 (5,252) = 2,323
    assert bullhead_below_ssd_limits(FRAC, KWF, 9_900, GRADIENT, 10_100) == (2_360, 2_323)
