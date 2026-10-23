"""Tubular stress, sinusoidal buckling, and helical lockup analysis example.

Demonstrates:
  - Moment of inertia and buoyancy factor calculations
  - Radial clearance in casing/open hole
  - Paslay-Dawson sinusoidal buckling load (threshold of snaking/waving)
  - Wu & Juvkam-Wold helical buckling load (threshold of lockup risk)
  - Operating safety margins under current axial load

Run with:  python examples/example_tubular_buckling.py
"""

from killsheet.buckling import evaluate_tubular_buckling

DRILLSTRING_PARAMS = dict(
    pipe_od_in=5.0,
    pipe_id_in=4.276,
    hole_id_in=8.5,
    pipe_weight_lb_per_ft=19.5,
    mud_weight_ppg=10.5,
    inclination_deg=75.0,
    current_axial_force_lbf=15_000.0,
)


def run_example():
    res = evaluate_tubular_buckling(**DRILLSTRING_PARAMS)
    print("TUBULAR BUCKLING & DIRECTIONAL STABILITY ANALYSIS")
    print("=" * 64)
    print(f"Wellbore Inclination:        {DRILLSTRING_PARAMS['inclination_deg']:>8.1f}°")
    print(f"Radial Clearance:            {res['radial_clearance_in']:>8.3f} in")
    print(f"Buoyancy Factor:             {res['buoyancy_factor']:>8.4f}")
    print(f"Area Moment of Inertia (I):  {res['moment_of_inertia_in4']:>8.2f} in^4")
    print(f"Sinusoidal Buckling Limit:   {res['sinusoidal_buckling_limit_lbf']:>8,} lbf")
    print(f"Helical Buckling Limit:      {res['helical_buckling_limit_lbf']:>8,} lbf")
    print(f"Current Compressive Load:    {int(res['axial_force_lbf']):>8,} lbf")
    print(f"Margin to Sinusoidal:        {res['margin_to_sinusoidal_lbf']:>8,} lbf")
    print(f"Current Tubular State:       {res['buckling_state']}")


if __name__ == "__main__":
    run_example()
