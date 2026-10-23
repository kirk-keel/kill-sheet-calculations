"""Tests for tripping, slug volume, dry pipe, and fill-up calculations."""

import pytest

from killsheet.tripping import (
    dry_pipe_fill_volume,
    hydrostatic_loss_from_level_drop,
    level_drop_unfilled_hole,
    slug_length_in_pipe,
    slug_pit_gain,
    slug_volume_for_dry_pipe,
    trip_slug_summary,
    wet_pipe_fill_volume,
)


def test_slug_volume_and_pit_gain():
    # 250 ft dry pipe desired in 5" 19.5# DP (cap 0.0178 bbl/ft)
    # OMW = 10.0 ppg, Slug = 12.0 ppg
    # V_slug = (250 x 0.0178 x 10) / (12 - 10) = 44.5 / 2 = 22.25 -> 22.3 bbl
    slug_vol = slug_volume_for_dry_pipe(
        desired_dry_pipe_ft=250,
        dp_capacity_bbl_per_ft=0.0178,
        original_mud_weight_ppg=10.0,
        slug_weight_ppg=12.0,
    )
    assert slug_vol == 22.3

    # Pit gain: 22.3 x (12 - 10) / 10 = 4.46 -> 4.5 bbl
    gain = slug_pit_gain(slug_vol, 10.0, 12.0)
    assert gain == 4.5

    # Length in pipe: 22.3 / 0.0178 = 1252.8 -> 1253 ft
    length = slug_length_in_pipe(slug_vol, 0.0178)
    assert length == 1253


def test_dry_and_wet_pipe_fill_volumes():
    # 5 stands of pipe = 465 ft
    # Dry pull with steel displacement 0.0075 bbl/ft: 465 x 0.0075 = 3.4875 -> 3.5 bbl
    dry_fill = dry_pipe_fill_volume(465, 0.0075)
    assert dry_fill == 3.5

    # Wet pull with closed displacement 0.0243 bbl/ft: 465 x 0.0243 = 11.2995 -> 11.3 bbl
    wet_fill = wet_pipe_fill_volume(465, 0.0243)
    assert wet_fill == 11.3


def test_level_drop_and_hydrostatic_loss():
    # 5 stands pulled dry without filling: 3.5 bbl missing
    # Casing annulus capacity = 0.0500 bbl/ft
    # Level drop: 3.5 / 0.0500 = 70 ft
    drop = level_drop_unfilled_hole(3.5, 0.0500)
    assert drop == 70

    # Hydrostatic loss: 0.052 x 10.0 ppg x 70 ft = 36.4 -> 36 psi
    dp_loss = hydrostatic_loss_from_level_drop(drop, 10.0)
    assert dp_loss == 36


def test_trip_slug_summary():
    summary = trip_slug_summary(
        desired_dry_pipe_ft=250,
        dp_capacity_bbl_per_ft=0.0178,
        original_mud_weight_ppg=10.0,
        slug_weight_ppg=12.0,
        pump_output_bbl_per_stk=0.102,
    )
    assert summary["slug_volume_bbl"] == 22.3
    assert summary["pit_gain_bbl"] == 4.5
    assert summary["slug_length_ft"] == 1253
    # 22.3 / 0.102 = 218.6 -> 219 strokes
    assert summary["pump_strokes"] == 219


def test_tripping_input_validation():
    with pytest.raises(ValueError, match="must be > 0"):
        slug_volume_for_dry_pipe(0, 0.0178, 10.0, 12.0)

    with pytest.raises(ValueError, match="Slug weight .* must be greater"):
        slug_volume_for_dry_pipe(250, 0.0178, 10.0, 9.5)

    with pytest.raises(ValueError, match="Length pulled and steel displacement must be > 0"):
        dry_pipe_fill_volume(0, 0.0075)
