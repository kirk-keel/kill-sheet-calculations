"""Balanced cement plug and spacer placement calculation example.

Demonstrates:
  - Slurry volume sizing for target plug length
  - Balanced plug height with workstring in place
  - Spacer volume behind workstring to prevent U-tubing
  - Mud displacement volume to plug top
  - Dry cement sack count and mix water requirement

Run with:  python examples/example_cement_plug.py
"""

from killsheet.cementing import balanced_cement_plug_summary

PLUG_PARAMS = dict(
    plug_top_md_ft=7200.0,
    plug_bottom_md_ft=7800.0,
    hole_capacity_bbl_per_ft=0.0459,
    pipe_capacity_bbl_per_ft=0.0178,
    annular_capacity_bbl_per_ft=0.0400,
    spacer_ahead_bbl=25.0,
    excess_percent=15.0,
    slurry_yield_cu_ft_per_sk=1.18,
    mix_water_gal_per_sk=5.0,
)


def run_example():
    res = balanced_cement_plug_summary(**PLUG_PARAMS)
    print("BALANCED CEMENT PLUG & SPACER PLACEMENT")
    print("=" * 64)
    print(f"Target Plug Length:          {res['plug_length_ft']:>8,} ft ({PLUG_PARAMS['plug_top_md_ft']:,} - {PLUG_PARAMS['plug_bottom_md_ft']:,} ft)")
    print(f"Slurry Volume (15% excess):  {res['slurry_volume_bbl']:>8.1f} bbl")
    print(f"Balanced Plug Height (Pipe): {res['balanced_plug_height_with_pipe_ft']:>8.1f} ft")
    print(f"Top of Cement (with Pipe):   {res['top_of_cement_with_pipe_md_ft']:>8,} ft MD")
    print(f"Spacer Ahead:                {res['spacer_ahead_bbl']:>8.1f} bbl")
    print(f"Balanced Spacer Behind:      {res['balanced_spacer_behind_bbl']:>8.1f} bbl (U-tube balance)")
    print(f"Mud Displacement Volume:     {res['displacement_volume_bbl']:>8.1f} bbl")
    print(f"Cement Sacks Required:       {res['sacks_cement']:>8,} sacks")
    print(f"Mix Water Required:          {res['mix_water_bbl']:>8.1f} bbl")


if __name__ == "__main__":
    run_example()
