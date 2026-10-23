"""Tripping and slug pumping example.

Demonstrates:
  - Heavy slug volume required for desired dry pipe height
  - Pit volume gain after U-tube displacement
  - Fill-up volumes when pulling dry vs wet pipe
  - Hydrostatic pressure drop if the hole is pulled without filling

Run with:  python examples/tripping_slug_well.py
"""

from killsheet.tripping import (
    dry_pipe_fill_volume,
    hydrostatic_loss_from_level_drop,
    level_drop_unfilled_hole,
    trip_slug_summary,
    wet_pipe_fill_volume,
)

TRIP_DATA = dict(
    desired_dry_pipe_ft=250,
    dp_capacity_bbl_per_ft=0.0178,
    dp_steel_disp_bbl_per_ft=0.0075,
    dp_closed_disp_bbl_per_ft=0.0243,
    casing_annulus_cap_bbl_per_ft=0.0489,
    original_mud_weight_ppg=10.4,
    slug_weight_ppg=12.4,
    pump_output_bbl_per_stk=0.117,
    stands_pulled=5,
    stand_length_ft=93,
)


def print_tripping_operations():
    slug = trip_slug_summary(
        desired_dry_pipe_ft=TRIP_DATA["desired_dry_pipe_ft"],
        dp_capacity_bbl_per_ft=TRIP_DATA["dp_capacity_bbl_per_ft"],
        original_mud_weight_ppg=TRIP_DATA["original_mud_weight_ppg"],
        slug_weight_ppg=TRIP_DATA["slug_weight_ppg"],
        pump_output_bbl_per_stk=TRIP_DATA["pump_output_bbl_per_stk"],
    )

    length_pulled = TRIP_DATA["stands_pulled"] * TRIP_DATA["stand_length_ft"]
    dry_fill = dry_pipe_fill_volume(length_pulled, TRIP_DATA["dp_steel_disp_bbl_per_ft"])
    wet_fill = wet_pipe_fill_volume(length_pulled, TRIP_DATA["dp_closed_disp_bbl_per_ft"])
    drop_unfilled = level_drop_unfilled_hole(dry_fill, TRIP_DATA["casing_annulus_cap_bbl_per_ft"])
    hyd_loss = hydrostatic_loss_from_level_drop(drop_unfilled, TRIP_DATA["original_mud_weight_ppg"])

    print("TRIPPING & SLUG CALCULATIONS - Rig-Floor Worksheet")
    print("=" * 64)
    print(f"Target dry pipe height       {slug['desired_dry_pipe_ft']:>8,} ft")
    print(f"Original mud weight          {slug['original_mud_weight_ppg']:>8.1f} ppg")
    print(f"Heavy slug weight            {slug['slug_weight_ppg']:>8.1f} ppg")
    print(f"Slug volume to pump          {slug['slug_volume_bbl']:>8.1f} bbl")
    print(f"Slug length inside string    {slug['slug_length_ft']:>8,} ft")
    print(f"Pump strokes required        {slug['pump_strokes']:>8,} stks")
    print(f"Pit gain from U-tubing       {slug['pit_gain_bbl']:>8.1f} bbl")
    print()
    print(f"Tripping: {TRIP_DATA['stands_pulled']} stands pulled ({length_pulled} ft):")
    print(f"  Dry pipe fill-up required  {dry_fill:>8.1f} bbl")
    print(f"  Wet pipe fill-up required  {wet_fill:>8.1f} bbl")
    print(f"  Level drop if unfilled     {drop_unfilled:>8,} ft")
    print(f"  Hydrostatic loss unfilled  {hyd_loss:>8,} psi")


if __name__ == "__main__":
    print_tripping_operations()
