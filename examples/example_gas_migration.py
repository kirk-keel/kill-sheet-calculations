"""Gas percolation velocity, bubble rise, and surface pressure accumulation example.

Demonstrates:
  - Hydrodynamic Harmathy single-bubble slip velocity
  - Inclination effect on gas migration along wellbore high side
  - Shut-in casing pressure rise rate (dP/dt)
  - Critical arrival time at casing shoe and surface BOP stack

Run with:  python examples/example_gas_migration.py
"""

from killsheet.gas_migration import evaluate_gas_migration

WELL_PARAMS = dict(
    mud_weight_ppg=11.5,
    bit_tvd_ft=12_000.0,
    shoe_tvd_ft=7_500.0,
    initial_sicp_psi=650.0,
    inclination_deg=35.0,
)


def run_example():
    res = evaluate_gas_migration(**WELL_PARAMS)
    print("GAS MIGRATION & SHUT-IN PRESSURE ACCUMULATION")
    print("=" * 64)
    print(f"Mud Weight:                  {WELL_PARAMS['mud_weight_ppg']:>8.1f} ppg")
    print(f"Wellbore Inclination:        {WELL_PARAMS['inclination_deg']:>8.1f}°")
    print(f"Migration Rise Velocity:     {res['migration_velocity_ft_per_hr']:>8.1f} ft/hr")
    print(f"Pressure Rise Rate (dP/dt):  {res['pressure_rise_rate_psi_per_hr']:>8,} psi/hr")
    print(f"Time to Casing Shoe:         {res['time_to_casing_shoe_hr']:>8.1f} hrs ({res['time_to_casing_shoe_min']:,} min)")
    print(f"Time to Surface BOP:         {res['time_to_surface_bop_hr']:>8.1f} hrs ({res['time_to_surface_bop_min']:,} min)")
    print(f"Initial SICP:                {res['initial_sicp_psi']:>8,} psi")
    print(f"Projected SICP at Shoe:      {res['projected_sicp_at_shoe_psi']:>8,} psi")


if __name__ == "__main__":
    run_example()
