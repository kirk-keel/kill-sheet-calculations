"""Volumetric method, then lubricate and bleed - bit at 8,000 ft, above the influx, unable to strip back to bottom.

The baseline well with the string pulled up 3,500 ft: below the bit is open hole
with no pipe in it. A SWABBED kick: Pf is the 10.4 ppg hydrostatic (6,219 psi), SICP 62
comes from the gas column only, and the original 10.4 ppg mud is lubricated -
hydrostatic control is regained.
The 15-minute SICP rises are illustrative until the gas reaches surface; when that
happens, the SICP with gas at surface and the bbl pumped in lubricate and bleed come
from the single-bubble forecast (killsheet/volumetric_model.py), so the readings
and the forecast agree.

Run it with:  python examples/volumetric_pipe_above_influx_well.py
"""

from kill_sheet_printer import print_volumetric_sheet
from killsheet.volumetric import AVERAGE, LONGEST, SMALLEST  # noqa: F401
from killsheet.volumetric_model import ANNULUS_AT_THE_GAS

WELL = dict(
    title="VOLUMETRIC - pipe above the influx, unable to strip (vertical, untapered)",
    original_mud_weight_ppg=10.4,
    kill_mud_weight_ppg=10.4,           # mud lubricated in L&B (swabbed kick: original mud)
    # Shoe and leak-off test (for MAASP)
    shoe_tvd_ft=5_150,
    lot_pressure_psi=1_350,
    test_mud_weight_ppg=9.6,
    sicp_psi=62,
    pit_gain_bbl=10,                    # kick size - the forecast needs it
    # Where the pipe is (for the plot and schematic)
    pipe_bottom_md_ft=8_000,            # bit above the influx
    float_in_string=True,               # no drill pipe reading - casing only
    # Chosen by the team killing the well
    safety_margin_psi=100,
    working_pressure_psi=50,
    capacity_choice=ANNULUS_AT_THE_GAS, # default; or SMALLEST, AVERAGE, LONGEST
    annulus_bottom_up=[                 # (name, capacity bbl/ft, length ft)
        ('8-1/2" hole, no pipe', 0.0702, 3_500),
        ('DC x 8-1/2" hole', 0.0291, 600),
        ('HWDP x 8-1/2" hole', 0.0459, 900),
        ('DP x 8-1/2" hole', 0.0459, 1_350),
        ('DP x 9-5/8" casing', 0.0489, 5_150),
    ],
    # Readings: SICP rise over the 15 minute wait after each volumetric cycle
    # (illustrative until the gas reaches surface - the forecast decides when that is)
    sicp_rises_after_each_cycle=[
        30, 29, 27, 26, 24, 23, 22, 20, 19, 18, 16, 15, 13, 0,
    ],
    # Readings: SICP once the gas is at surface, and bbl pumped each L&B cycle
    sicp_gas_at_surface_psi=935,
    bbl_pumped_each_cycle=[
        3.4, 3.3, 3.3, 3.2, 3.2, 3.1, 3.0, 3.0, 2.9, 2.8, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0,
        1.9, 1.7, 1.6, 1.5, 1.3, 1.2, 1.1, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.4, 0.3, 0.3, 0.2, 0.2,
        0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
    ],
)

if __name__ == "__main__":
    print_volumetric_sheet(**WELL)
