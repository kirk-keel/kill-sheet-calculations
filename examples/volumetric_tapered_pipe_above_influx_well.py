"""Volumetric method, then lubricate and bleed - bit at 10,000 ft, above the influx, unable to strip back to bottom.

The approved vertical tapered well: 5" DP over 3-1/2" DP, HWDP and DC, 7" 26#
casing (ID 6.276") to 9,500 ft, 6-1/8" hole to 11,500 ft, MAASP 889 psi.
The HWDP is across the shoe: 200 ft in open hole, 400 ft in casing. A 3 bbl
SWABBED kick (SICP 36), SF 50 / Pw 50; the original mud is lubricated.
The 15-minute SICP rises are illustrative until the gas reaches surface; when that
happens, the SICP with gas at surface and the bbl pumped in lubricate and bleed come
from the single-bubble forecast (killsheet/volumetric_model.py), so the readings
and the forecast agree.

Run it with:  python examples/volumetric_tapered_pipe_above_influx_well.py
"""

from kill_sheet_printer import print_volumetric_sheet
from killsheet.volumetric import AVERAGE, LONGEST, SMALLEST  # noqa: F401
from killsheet.volumetric_model import ANNULUS_AT_THE_GAS

WELL = dict(
    title="VOLUMETRIC - pipe above the influx, unable to strip (vertical, tapered)",
    original_mud_weight_ppg=10.4,
    kill_mud_weight_ppg=10.4,           # mud lubricated in L&B (swabbed kick: original mud)
    # Shoe and leak-off test (for MAASP)
    shoe_tvd_ft=9_500,
    lot_pressure_psi=1_100,
    test_mud_weight_ppg=10.0,
    sicp_psi=36,
    pit_gain_bbl=3,                     # kick size - the forecast needs it
    # Where the pipe is (for the plot and schematic)
    pipe_bottom_md_ft=10_000,           # bit above the influx
    float_in_string=True,               # no drill pipe reading - casing only
    # Chosen by the team killing the well
    safety_margin_psi=50,
    working_pressure_psi=50,
    capacity_choice=ANNULUS_AT_THE_GAS, # default; or SMALLEST, AVERAGE, LONGEST
    annulus_bottom_up=[                 # (name, capacity bbl/ft, length ft)
        ('6-1/8" hole, no pipe', 0.0364, 1_500),
        ('DC x 6-1/8" hole', 0.0145, 300),
        ('HWDP x 6-1/8" hole', 0.0245, 200),
        ('HWDP x 7" casing', 0.0264, 400),
        ('3-1/2" DP x 7" casing', 0.0264, 2_100),
        ('5" DP x 7" casing', 0.0140, 7_000),
    ],
    # Readings: SICP rise over the 15 minute wait after each volumetric cycle
    # (illustrative until the gas reaches surface - the forecast decides when that is)
    sicp_rises_after_each_cycle=[
        30, 29, 27, 26, 25, 24, 22, 21, 20, 18, 17, 16, 15, 13, 0,
    ],
    # Readings: SICP once the gas is at surface, and bbl pumped each L&B cycle
    sicp_gas_at_surface_psi=891,
    bbl_pumped_each_cycle=[
        1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9, 0.9, 0.9, 0.8, 0.8, 0.7, 0.7,
        0.6, 0.6, 0.5, 0.4, 0.4, 0.3, 0.2, 0.2, 0.1, 0.1, 0.1, 0.1,
    ],
)

if __name__ == "__main__":
    print_volumetric_sheet(**WELL)
