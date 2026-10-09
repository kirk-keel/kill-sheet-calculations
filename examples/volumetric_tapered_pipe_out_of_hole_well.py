"""Volumetric method, then lubricate and bleed - pipe out of the hole.

The approved vertical tapered well: 5" DP over 3-1/2" DP, HWDP and DC, 7" 26#
casing (ID 6.276") to 9,500 ft, 6-1/8" hole to 11,500 ft. MAASP is 889 psi, so
with a 100 psi safety margin and 50 psi working pressure every hold pressure is
above MAASP from the first cycle - the sheet warns and continues.
The 15-minute SICP rises and the bbl pumped are example readings.

Run it with:  python examples/volumetric_tapered_pipe_out_of_hole_well.py
"""

from kill_sheet_printer import print_volumetric_sheet
from killsheet.volumetric import AVERAGE, LONGEST, SMALLEST  # noqa: F401

print_volumetric_sheet(
    title="VOLUMETRIC - pipe out of the hole (vertical, tapered)",
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
        ('6-1/8" hole, no pipe', 0.0364, 2_000),
        ('7" casing, no pipe', 0.0383, 9_500),
    ],
    # Readings: SICP rise over the 15 minute wait after each volumetric cycle
    sicp_rises_after_each_cycle=[28, 22, 16, 10],
    # Readings: SICP once the gas is at surface, and bbl pumped each L&B cycle
    sicp_gas_at_surface_psi=960,
    bbl_pumped_each_cycle=[8.0, 9.0, 10.0, 10.0, 10.0, 11.0, 11.0],
)
