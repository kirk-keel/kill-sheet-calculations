"""Tests for the core kill sheet formulas.

The expected answers were worked by hand and verified by a well control
specialist before these tests were written.
"""

import pytest

from killsheet.formulas import (
    final_circulating_pressure,
    initial_circulating_pressure,
    kill_mud_weight,
    maasp,
    max_allowable_mud_weight,
)

# ---------------------------------------------------------------------------
# Hand-worked example well
# ---------------------------------------------------------------------------
TVD_FT = 11_500
ORIGINAL_MUD_WEIGHT_PPG = 10.4
SIDPP_PSI = 650
SCR_PRESSURE_PSI = 750          # at 30 spm
SHOE_TVD_FT = 5_150
LOT_PRESSURE_PSI = 1_350        # surface leak-off pressure
TEST_MUD_WEIGHT_PPG = 9.6       # mud weight during the leak-off test


def test_kill_mud_weight():
    # 10.4 + 650 / (0.052 x 11,500) = 11.487 -> round UP -> 11.5
    assert kill_mud_weight(SIDPP_PSI, TVD_FT, ORIGINAL_MUD_WEIGHT_PPG) == 11.5


def test_initial_circulating_pressure():
    # 650 + 750 = 1,400
    assert initial_circulating_pressure(SIDPP_PSI, SCR_PRESSURE_PSI) == 1400


def test_final_circulating_pressure():
    # 750 x (11.5 / 10.4) = 829.33 -> nearest -> 829
    assert final_circulating_pressure(SCR_PRESSURE_PSI, 11.5, ORIGINAL_MUD_WEIGHT_PPG) == 829


def test_max_allowable_mud_weight():
    # 9.6 + 1,350 / (0.052 x 5,150) = 14.641 -> round DOWN -> 14.6
    assert max_allowable_mud_weight(LOT_PRESSURE_PSI, SHOE_TVD_FT, TEST_MUD_WEIGHT_PPG) == 14.6


def test_maasp_with_original_mud():
    # (14.6 - 10.4) x 0.052 x 5,150 = 1,124.76 -> round DOWN -> 1,124
    # (academic rounding would give 1,125, so this proves rule 2 is applied)
    assert maasp(14.6, ORIGINAL_MUD_WEIGHT_PPG, SHOE_TVD_FT) == 1124


def test_maasp_after_kill():
    # (14.6 - 11.5) x 0.052 x 5,150 = 830.18 -> round DOWN -> 830
    assert maasp(14.6, 11.5, SHOE_TVD_FT) == 830


def test_full_example_carries_rounded_values_forward():
    # Chain the functions the way a kill sheet is filled in.
    kmw = kill_mud_weight(SIDPP_PSI, TVD_FT, ORIGINAL_MUD_WEIGHT_PPG)
    mamw = max_allowable_mud_weight(LOT_PRESSURE_PSI, SHOE_TVD_FT, TEST_MUD_WEIGHT_PPG)

    assert kmw == 11.5
    assert initial_circulating_pressure(SIDPP_PSI, SCR_PRESSURE_PSI) == 1400
    assert final_circulating_pressure(SCR_PRESSURE_PSI, kmw, ORIGINAL_MUD_WEIGHT_PPG) == 829
    assert mamw == 14.6
    assert maasp(mamw, ORIGINAL_MUD_WEIGHT_PPG, SHOE_TVD_FT) == 1124
    assert maasp(mamw, kmw, SHOE_TVD_FT) == 830


# ---------------------------------------------------------------------------
# Kill mud weight safety factor and SIDPP checks
# ---------------------------------------------------------------------------
def test_exact_kill_mud_weight_still_goes_up():
    # 10.0 + 520 / (0.052 x 10,000) = 11.0 exactly.
    # An exact KMW only balances the formation, so it goes up to 11.1.
    kmw = kill_mud_weight(520, 10_000, 10.0)
    assert kmw == 11.1
    # 800 x (11.1 / 10.0) = 888
    assert final_circulating_pressure(800, kmw, 10.0) == 888


@pytest.mark.parametrize("sidpp_psi", [0, -50])
def test_kill_mud_weight_rejects_zero_or_negative_sidpp(sidpp_psi):
    # A zero SIDPP with a float in the string is not a true reading:
    # the float must be bumped first.
    with pytest.raises(ValueError, match="bump the float"):
        kill_mud_weight(sidpp_psi, 10_000, 10.0)
