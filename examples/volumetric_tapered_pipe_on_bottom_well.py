"""Volumetric method, then lubricate and bleed - pipe on bottom, unable to pump.

The approved vertical tapered well: 5" DP over 3-1/2" DP, HWDP and DC, 7" 26#
casing (ID 6.276") to 9,500 ft, 6-1/8" hole to 11,500 ft. MAASP is 889 psi, so
with a 100 psi safety margin and 50 psi working pressure every hold pressure is
above MAASP from the first cycle - the sheet warns and continues.
The smallest annulus is the 5" DP inside the 7" casing, near surface.
The 15-minute SICP rises and the bbl pumped are example readings.

Run it with:  python examples/volumetric_tapered_pipe_on_bottom_well.py
"""

from kill_sheet_printer import print_volumetric_sheet
from killsheet.volumetric import AVERAGE, LONGEST, SMALLEST  # noqa: F401

print_volumetric_sheet(
    title="VOLUMETRIC - pipe on bottom, unable to pump (vertical, tapered)",
    original_mud_weight_ppg=10.4,
    kill_mud_weight_ppg=11.5,
    # Shoe and leak-off test (for MAASP)
    shoe_tvd_ft=9_500,
    lot_pressure_psi=1_100,
    test_mud_weight_ppg=10.0,
    sicp_psi=800,
    # Chosen by the team killing the well
    safety_margin_psi=100,
    working_pressure_psi=50,
    capacity_choice=SMALLEST,           # default; or AVERAGE, LONGEST
    annulus_bottom_up=[                 # (name, capacity bbl/ft, length ft)
        ('DC x 6-1/8" hole', 0.0145, 300),
        ('HWDP x 6-1/8" hole', 0.0245, 600),
        ('3-1/2" DP x 6-1/8" hole', 0.0245, 1_100),
        ('3-1/2" DP x 7" casing', 0.0264, 2_500),
        ('5" DP x 7" casing', 0.0140, 7_000),
    ],
    # Readings: SICP rise over the 15 minute wait after each volumetric cycle
    sicp_rises_after_each_cycle=[24, 20, 15, 9],
    # Readings: SICP once the gas is at surface, and bbl pumped each L&B cycle
    sicp_gas_at_surface_psi=959,
    bbl_pumped_each_cycle=[3.0, 3.5, 4.0, 4.0, 4.5, 4.5],
)
