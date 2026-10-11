"""Volumetric method, then lubricate and bleed - pipe out of the hole (tapered well).

The approved vertical tapered well: 5" DP over 3-1/2" DP, HWDP and DC, 7" 26#
casing (ID 6.276") to 9,500 ft, 6-1/8" hole to 11,500 ft, MAASP 889 psi.
A 3 bbl SWABBED kick (SICP 36), SF 50 / Pw 50; the original mud is lubricated.
The 15-minute SICP rises are illustrative until the gas reaches surface; when that
happens, the SICP with gas at surface and the bbl pumped in lubricate and bleed come
from the single-bubble forecast (killsheet/volumetric_model.py), so the readings
and the forecast agree.

Run it with:  python examples/volumetric_tapered_pipe_out_of_hole_well.py
"""

from kill_sheet_printer import print_volumetric_sheet
from killsheet.volumetric import AVERAGE, LONGEST, SMALLEST  # noqa: F401
from killsheet.volumetric_model import ANNULUS_AT_THE_GAS

WELL = dict(
    title="VOLUMETRIC - pipe out of the hole (vertical, tapered)",
    original_mud_weight_ppg=10.4,
    kill_mud_weight_ppg=10.4,           # mud lubricated in L&B (swabbed kick: original mud)
    # Shoe and leak-off test (for MAASP)
    shoe_tvd_ft=9_500,
    lot_pressure_psi=1_100,
    test_mud_weight_ppg=10.0,
    sicp_psi=36,
    pit_gain_bbl=3,                     # kick size - the forecast needs it
    # Where the pipe is (for the plot and schematic)
    pipe_bottom_md_ft=None,             # out of the hole
    # Chosen by the team killing the well
    safety_margin_psi=50,
    working_pressure_psi=50,
    capacity_choice=ANNULUS_AT_THE_GAS, # default; or SMALLEST, AVERAGE, LONGEST
    annulus_bottom_up=[                 # (name, capacity bbl/ft, length ft)
        ('6-1/8" hole, no pipe', 0.0364, 2_000),
        ('7" casing, no pipe', 0.0383, 9_500),
    ],
    # Readings: SICP rise over the 15 minute wait after each volumetric cycle
    # (illustrative until the gas reaches surface - the forecast decides when that is)
    sicp_rises_after_each_cycle=[
        30, 28, 26, 23, 21, 19, 16, 14, 7,
    ],
    # Readings: SICP once the gas is at surface, and bbl pumped each L&B cycle
    sicp_gas_at_surface_psi=543,
    bbl_pumped_each_cycle=[
        2.9, 2.8, 2.8, 2.7, 2.6, 2.6, 2.5, 2.3, 2.2, 2.0, 1.9, 1.6, 1.4, 1.2, 0.9, 0.7, 0.4, 0.3,
        0.2, 0.1, 0.1, 0.1,
    ],
)

if __name__ == "__main__":
    print_volumetric_sheet(**WELL)
