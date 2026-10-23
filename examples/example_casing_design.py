"""Casing burst and tension-derated collapse analysis under well control loads.

Demonstrates:
  - API Barlow's internal yield burst pressure (with 87.5% wall tolerance)
  - API 5C3 biaxial ellipse collapse resistance derating under axial tension
  - Well control safety factors and burst/collapse integrity verification

Run with:  python examples/example_casing_design.py
"""

from killsheet.casing_design import evaluate_casing_well_control_integrity

CASING_PARAMS = dict(
    od_in=9.625,
    id_in=8.835,
    casing_grade="L-80",
    nominal_collapse_psi=3090.0,
    hanging_weight_lbf=220_000.0,
    anticipated_surface_sicp_psi=1800.0,
    external_fluid_collapse_psi=2100.0,
)


def run_example():
    res = evaluate_casing_well_control_integrity(**CASING_PARAMS)
    print("CASING INTEGRITY & TENSION-DERATED COLLAPSE/BURST")
    print("=" * 64)
    print(f"Casing Size & Grade:         {CASING_PARAMS['od_in']}\" {res['casing_grade']} ({res['yield_strength_psi']:,} psi)")
    print(f"Wall Thickness:              {res['wall_thickness_in']:>8.3f} in")
    print(f"Steel Cross-Section:         {res['cross_section_sq_in']:>8.2f} sq in")
    print(f"API Burst Rating (0.875):    {res['api_burst_rating_psi']:>8,} psi")
    print(f"Surface SICP Load:           {res['surface_sicp_psi']:>8,} psi")
    print(f"Burst Safety Factor:         {res['burst_safety_factor']:>8.2f} (Status: {'PASS' if res['burst_integrity_ok'] else 'FAIL'})")
    print(f"Nominal Collapse Rating:     {res['nominal_collapse_psi']:>8,} psi")
    print(f"Tension-Derated Collapse:    {res['tension_derated_collapse_psi']:>8,} psi")
    print(f"Collapse Safety Factor:      {res['collapse_safety_factor']:>8.2f} (Status: {'PASS' if res['collapse_integrity_ok'] else 'FAIL'})")


if __name__ == "__main__":
    run_example()
