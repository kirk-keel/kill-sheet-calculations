"""Volumetric method, then lubricate and bleed - pipe out of the hole.

The baseline well with no pipe in it: open hole and casing only. A SWABBED kick
(SICP 62, Pf = the 10.4 ppg hydrostatic); the original mud is lubricated.
The 15-minute SICP rises are illustrative until the gas reaches surface; when that
happens, the SICP with gas at surface and the bbl pumped in lubricate and bleed come
from the single-bubble forecast (killsheet/volumetric_model.py), so the readings
and the forecast agree.

Run it with:  python examples/volumetric_pipe_out_of_hole_well.py
"""

from kill_sheet_printer import print_volumetric_sheet
from killsheet.volumetric import AVERAGE, LONGEST, SMALLEST  # noqa: F401
from killsheet.volumetric_model import ANNULUS_AT_THE_GAS

WELL = dict(
    title="VOLUMETRIC - pipe out of the hole (vertical)",
    original_mud_weight_ppg=10.4,
    kill_mud_weight_ppg=10.4,           # mud lubricated in L&B (swabbed kick: original mud)
    # Shoe and leak-off test (for MAASP)
    shoe_tvd_ft=5_150,
    lot_pressure_psi=1_350,
    test_mud_weight_ppg=9.6,
    sicp_psi=62,
    pit_gain_bbl=10,                    # kick size - the forecast needs it
    # Where the pipe is (for the plot and schematic)
    pipe_bottom_md_ft=None,             # out of the hole
    # Chosen by the team killing the well
    safety_margin_psi=100,
    working_pressure_psi=50,
    capacity_choice=ANNULUS_AT_THE_GAS, # default; or SMALLEST, AVERAGE, LONGEST
    annulus_bottom_up=[                 # (name, capacity bbl/ft, length ft)
        ('8-1/2" hole, no pipe', 0.0702, 6_350),
        ('9-5/8" casing, no pipe', 0.0732, 5_150),
    ],
    # Readings: SICP rise over the 15 minute wait after each volumetric cycle
    # (illustrative until the gas reaches surface - the forecast decides when that is)
    sicp_rises_after_each_cycle=[
        30, 28, 26, 25, 23, 21, 19, 17, 16, 14, 10,
    ],
    # Readings: SICP once the gas is at surface, and bbl pumped each L&B cycle
    sicp_gas_at_surface_psi=747,
    bbl_pumped_each_cycle=[
        5.2, 5.1, 5.0, 4.9, 4.8, 4.7, 4.6, 4.5, 4.3, 4.1, 4.0, 3.8, 3.5, 3.3, 3.1, 2.8, 2.5, 2.2,
        2.0, 1.7, 1.4, 1.2, 1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
    ],
)

if __name__ == "__main__":
    print_volumetric_sheet(**WELL)
