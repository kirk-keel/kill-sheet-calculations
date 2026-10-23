"""Unit tests for balanced cement plugs, spacer balance, and displacement calculations."""

import pytest

from killsheet.cementing import (
    balanced_cement_plug_summary,
    balanced_plug_height_ft,
    balanced_spacer_behind_bbl,
    calculate_cement_sacks_and_water,
    cement_slurry_volume_bbl,
    displacement_volume_to_plug_top_bbl,
)


def test_slurry_volume():
    # 500 ft plug in 0.05 bbl/ft hole with 10% excess
    # Base = 25 bbl, +10% = 27.5 bbl
    vol = cement_slurry_volume_bbl(500.0, 0.05, excess_percent=10.0)
    assert vol == 27.5


def test_balanced_plug_height():
    # 30 bbl slurry, pipe cap = 0.0178 bbl/ft, ann cap = 0.0450 bbl/ft
    # Total cap = 0.0628 bbl/ft -> h = 30 / 0.0628 = 477.7 ft
    h = balanced_plug_height_ft(30.0, 0.0178, 0.0450)
    assert 475 <= h <= 480


def test_spacer_behind_balance():
    # Spacer ahead = 20 bbl, pipe cap = 0.0178, ann cap = 0.0450
    # Ratio = 0.0178 / 0.0450 = 0.3956 -> V_behind = 7.9 bbl
    v_behind = balanced_spacer_behind_bbl(20.0, 0.0178, 0.0450)
    assert v_behind == 7.9


def test_displacement_volume():
    # Bottom = 8000 ft, h_balanced = 500 ft -> top = 7500 ft
    # C_pipe = 0.0178 bbl/ft -> V_disp = 7500 * 0.0178 = 133.5 bbl
    v_disp = displacement_volume_to_plug_top_bbl(8000.0, 500.0, 0.0178)
    assert v_disp == 133.5


def test_cement_sacks_and_water():
    res = calculate_cement_sacks_and_water(30.0, slurry_yield_cu_ft_per_sk=1.18, mix_water_gal_per_sk=5.0)
    assert res["sacks_cement"] > 100
    assert res["mix_water_bbl"] > 15


def test_balanced_cement_plug_summary():
    rep = balanced_cement_plug_summary(
        plug_top_md_ft=7500.0,
        plug_bottom_md_ft=8000.0,
        hole_capacity_bbl_per_ft=0.0459,
        pipe_capacity_bbl_per_ft=0.0178,
        annular_capacity_bbl_per_ft=0.0400,
        spacer_ahead_bbl=20.0,
    )
    assert rep["plug_length_ft"] == 500.0
    assert rep["slurry_volume_bbl"] > 20.0
    assert rep["balanced_plug_height_with_pipe_ft"] > 350.0
    assert rep["balanced_spacer_behind_bbl"] > 0
    assert rep["displacement_volume_bbl"] > 100.0
    assert rep["sacks_cement"] > 0
