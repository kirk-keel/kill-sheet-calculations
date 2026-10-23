"""Wellbore hydraulics, bit jet optimization, and ECD profiling example.

Demonstrates:
  - Bit nozzle Total Flow Area (TFA)
  - Nozzle jet exit velocity
  - Bit pressure drop and hydraulic horsepower (HHP / HSI)
  - Jet impact cleaning force (JIF)
  - Bingham Plastic annular friction pressure loss and circulating ECD

Run with:  python examples/example_wellbore_hydraulics.py
"""

from killsheet.hydraulics import (
    annular_pressure_loss_psi,
    bit_hydraulics_report,
    equivalent_circulating_density_ppg,
)

HYD_PARAMS = dict(
    mud_weight_ppg=10.5,
    flow_rate_gpm=450.0,
    bit_diameter_in=8.75,
    nozzle_sizes_in_32nds=[12, 12, 12],
)


def run_example():
    res = bit_hydraulics_report(**HYD_PARAMS)

    # Annular loss over 8,000 ft wellbore
    dp_ann = annular_pressure_loss_psi(
        mud_weight_ppg=10.5,
        plastic_viscosity_cp=16.0,
        yield_point_lbf_100sqft=12.0,
        flow_rate_gpm=450.0,
        hole_diameter_in=8.75,
        pipe_od_in=5.0,
        interval_length_ft=8000.0,
    )
    ecd = equivalent_circulating_density_ppg(10.5, dp_ann, 8000.0)

    print("WELLBORE HYDRAULICS & BIT JET OPTIMIZATION")
    print("=" * 64)
    print(f"Total Flow Area (TFA):       {res['tfa_sq_in']:>8.4f} sq in")
    print(f"Nozzle Fluid Velocity:       {res['nozzle_velocity_fps']:>8.1f} ft/s")
    print(f"Bit Pressure Drop:           {res['bit_pressure_drop_psi']:>8,} psi")
    print(f"Bit Hydraulic Horsepower:    {res['hydraulic_horsepower_hhp']:>8.1f} hp")
    print(f"Hydraulic Power Density:     {res['hsi_hp_per_sq_in']:>8.2f} hp/sq in")
    print(f"Jet Impact Force (JIF):      {res['jet_impact_force_lbf']:>8,} lbf")
    print(f"Annular Friction Loss:       {dp_ann:>8,} psi")
    print(f"Circulating ECD at Bit:      {ecd:>8.2f} ppg (+{ecd - 10.5:.2f} ppg)")


if __name__ == "__main__":
    run_example()
