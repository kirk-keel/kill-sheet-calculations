"""Volumetric method, then lubricate and bleed - pipe out of the hole.

The baseline well with no pipe in it: open hole and casing only.

Run it with:  python examples/volumetric_pipe_out_of_hole_well.py
"""

from kill_sheet_printer import print_volumetric_sheet
from killsheet.volumetric import AVERAGE, LONGEST, SMALLEST  # noqa: F401

print_volumetric_sheet(
    title="VOLUMETRIC - pipe out of the hole (vertical)",
    original_mud_weight_ppg=10.4,
    kill_mud_weight_ppg=11.5,
    # Shoe and leak-off test (for MAASP)
    shoe_tvd_ft=5_150,
    lot_pressure_psi=1_350,
    test_mud_weight_ppg=9.6,
    sicp_psi=800,
    # Chosen by the team killing the well
    safety_margin_psi=100,
    working_pressure_psi=50,
    capacity_choice=SMALLEST,           # default; or AVERAGE, LONGEST
    annulus_bottom_up=[                 # (name, capacity bbl/ft, length ft)
        ('8-1/2" hole, no pipe', 0.0702, 6_350),
        ('9-5/8" casing, no pipe', 0.0732, 5_150),
    ],
    # Readings: SICP rise over the 15 minute wait after each volumetric cycle
    sicp_rises_after_each_cycle=[32, 27, 21, 15, 8],
    # Readings: SICP once the gas is at surface, and bbl pumped each L&B cycle
    sicp_gas_at_surface_psi=1_158,
    bbl_pumped_each_cycle=[15.0, 16.0, 17.0, 18.0, 18.0, 18.0, 18.0, 18.0, 18.0],
)
