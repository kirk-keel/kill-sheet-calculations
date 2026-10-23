"""Kick influx characterization and fluid identification example.

Demonstrates:
  - Annular influx bubble height calculation
  - Influx pressure gradient and equivalent density
  - Automated fluid classification (Gas, Condensate, Oil, Saltwater)
  - Natural gas deviation factor (Z-factor) and formation volume factor (Bg)

Run with:  python examples/example_influx_identification.py
"""

from killsheet.influx import characterize_kick

INFLUX_PARAMS = dict(
    sidpp_psi=450.0,
    sicp_psi=680.0,
    pit_gain_bbl=25.0,
    annular_capacity_bbl_per_ft=0.0500,
    original_mud_weight_ppg=11.0,
    bit_tvd_ft=10_000.0,
    temperature_deg_f=160.0,
)


def run_example():
    res = characterize_kick(**INFLUX_PARAMS)
    print("INFLUX CHARACTERIZATION & FLUID IDENTIFICATION")
    print("=" * 64)
    print(f"Influx Bubble Height:        {res['influx_height_ft']:>8.1f} ft")
    print(f"Influx Pressure Gradient:    {res['influx_gradient_psi_per_ft']:>8.3f} psi/ft")
    print(f"Equivalent Influx Density:   {res['influx_density_ppg']:>8.2f} ppg")
    print(f"Fluid Classification:        {res['fluid_type']:>8}")
    print(f"Reservoir Pore Pressure:     {res['formation_pressure_psi']:>8,} psi")
    print(f"Gas Compressibility (Z):     {res['z_factor']:>8.4f}")
    print(f"Formation Volume Factor Bg:  {res['bg_bbl_per_mscf']:>8.4f} bbl/Mscf")


if __name__ == "__main__":
    run_example()
