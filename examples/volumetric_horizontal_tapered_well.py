"""Volumetric method, then lubricate and bleed - horizontal well, tapered string, pipe on bottom.

The approved horizontal well with the tapered string (5" DP over 4" DP,
4" HWDP and 6-1/2" DC): KOP 9,000 ft, heel and 9-5/8"
shoe at 9,900 ft MD / 9,573 ft TVD, 5,000 ft lateral to TD at 14,900 ft MD.
Gas in the lateral doesn't migrate the way it does vertically - the
volumetric method applies once the gas is in the build or vertical section.
The 15-minute SICP rises and the bbl pumped are example readings.

Run it with:  python examples/volumetric_horizontal_tapered_well.py
"""

from kill_sheet_printer import print_volumetric_sheet
from killsheet.volumetric import AVERAGE, LONGEST, SMALLEST  # noqa: F401

print_volumetric_sheet(
    title="VOLUMETRIC - horizontal well, pipe on bottom, unable to pump (tapered)",
    original_mud_weight_ppg=10.4,
    kill_mud_weight_ppg=11.8,
    # Well path
    td_md_ft=14_900,
    td_tvd_ft=9_573,
    shoe_md_ft=9_900,
    key_points=[("KOP", 9_000, 9_000), ("heel", 9_900, 9_573)],
    # Shoe and leak-off test (for MAASP)
    shoe_tvd_ft=9_573,
    lot_pressure_psi=1_000,
    test_mud_weight_ppg=10.0,
    sicp_psi=700,
    # Chosen by the team killing the well
    safety_margin_psi=100,
    working_pressure_psi=50,
    capacity_choice=SMALLEST,           # default; or AVERAGE, LONGEST
    annulus_bottom_up=[                 # (name, capacity bbl/ft, length ft MD)
        ('DC x 8-1/2" hole', 0.0291, 600),
        ('4" HWDP x 8-1/2" hole', 0.0546, 900),
        ('4" DP x 8-1/2" hole', 0.0546, 3_000),
        ('5" DP x 8-1/2" hole', 0.0459, 500),
        ('5" DP x 9-5/8" casing', 0.0489, 9_900),
    ],
    # Readings: SICP rise over the 15 minute wait after each volumetric cycle
    sicp_rises_after_each_cycle=[26, 22, 18, 13, 8],
    # Readings: SICP once the gas is at surface, and bbl pumped each L&B cycle
    sicp_gas_at_surface_psi=1_058,
    bbl_pumped_each_cycle=[8.0, 9.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0],
)
