"""Kick tolerance and casing seat drilling window engineering example.

Demonstrates:
  - Kick intensity calculation (ppg equivalent deficit)
  - Casing shoe MAASP and fracture pressure limit
  - Maximum allowable gas influx height (Hmax) at casing shoe
  - Maximum shut-in gas kick volume (Kick Tolerance) via Boyle's Law

Run with:  python examples/example_kick_tolerance.py
"""

from killsheet.kick_tolerance import kick_tolerance_summary

WELL_PARAMS = dict(
    mud_weight_ppg=12.5,
    tvd_ft=10_000,
    shoe_tvd_ft=5_000,
    lot_emw_ppg=14.5,
    sidpp_psi=350,
    annular_capacity_bbl_per_ft=0.0459,
)


def run_example():
    res = kick_tolerance_summary(**WELL_PARAMS)
    print("KICK TOLERANCE & CASING SEAT DRILLING WINDOW")
    print("=" * 64)
    print(f"Current Mud Weight:          {WELL_PARAMS['mud_weight_ppg']:>8.1f} ppg")
    print(f"Casing Shoe Depth (TVD):     {WELL_PARAMS['shoe_tvd_ft']:>8,} ft")
    print(f"Total Vertical Depth (TVD):  {WELL_PARAMS['tvd_ft']:>8,} ft")
    print(f"Kick Intensity:              {res['kick_intensity_ppg']:>8.1f} ppg")
    print(f"Equivalent Pore Pressure:    {res['equivalent_pore_pressure_ppg']:>8.1f} ppg")
    print(f"Formation Pore Pressure:     {res['formation_pressure_psi']:>8,} psi")
    print(f"Shoe Fracture Pressure:      {res['shoe_fracture_pressure_psi']:>8,} psi")
    print(f"Shoe MAASP:                  {res['shoe_maasp_psi']:>8,} psi")
    print(f"Max Gas Influx Height:       {res['max_gas_height_at_shoe_ft']:>8,} ft")
    print(f"Kick Tolerance (Bottomhole): {res['kick_tolerance_bottomhole_bbl']:>8.1f} bbl")


if __name__ == "__main__":
    run_example()
