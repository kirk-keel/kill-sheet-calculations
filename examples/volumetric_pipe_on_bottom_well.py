"""Volumetric method, then lubricate and bleed - pipe on bottom, unable to pump (float).

The baseline well. Drilling kick that can't be circulated: SIDPP 650 / SICP 800, 10 bbl.
With a float there is no SIDPP reading, so Pf is ESTIMATED from SICP. The well ends
underbalanced: lubricate and bleed removes the gas, but a kill is still required.
The 15-minute SICP rises are illustrative until the gas reaches surface; when that
happens, the SICP with gas at surface and the bbl pumped in lubricate and bleed come
from the single-bubble forecast (killsheet/volumetric_model.py), so the readings
and the forecast agree.

Run it with:  python examples/volumetric_pipe_on_bottom_well.py
"""

from kill_sheet_printer import print_volumetric_sheet
from killsheet.volumetric import AVERAGE, LONGEST, SMALLEST  # noqa: F401
from killsheet.volumetric_model import ANNULUS_AT_THE_GAS

WELL = dict(
    title="VOLUMETRIC - pipe on bottom, unable to pump (vertical, untapered)",
    original_mud_weight_ppg=10.4,
    kill_mud_weight_ppg=11.5,           # mud lubricated in L&B
    # Shoe and leak-off test (for MAASP)
    shoe_tvd_ft=5_150,
    lot_pressure_psi=1_350,
    test_mud_weight_ppg=9.6,
    sicp_psi=800,                       # 0.1 psi/ft gas: SIDPP + (0.5408 - 0.1) x influx height
    pit_gain_bbl=10,                    # kick size - the forecast needs it
    # Where the pipe is (for the plot and schematic)
    pipe_bottom_md_ft=11_500,           # on bottom (TD)
    float_in_string=True,               # no drill pipe reading - casing only
    # Chosen by the team killing the well
    safety_margin_psi=100,
    working_pressure_psi=50,
    capacity_choice=ANNULUS_AT_THE_GAS, # default; or SMALLEST, AVERAGE, LONGEST
    annulus_bottom_up=[                 # (name, capacity bbl/ft, length ft)
        ('DC x 8-1/2" hole', 0.0291, 600),
        ('HWDP x 8-1/2" hole', 0.0459, 900),
        ('DP x 8-1/2" hole', 0.0459, 4_850),
        ('DP x 9-5/8" casing', 0.0489, 5_150),
    ],
    # Readings: SICP rise over the 15 minute wait after each volumetric cycle
    # (illustrative until the gas reaches surface - the forecast decides when that is)
    sicp_rises_after_each_cycle=[
        30, 28, 26, 24, 22, 20, 18, 16, 14, 0,
    ],
    # Readings: SICP once the gas is at surface, and bbl pumped each L&B cycle
    sicp_gas_at_surface_psi=1_400,
    bbl_pumped_each_cycle=[
        1.7, 1.6, 1.6, 1.6, 1.5, 1.5, 1.5, 1.4, 1.4, 1.4, 1.3, 1.3, 1.3, 1.2, 1.2, 1.1, 1.1, 1.1,
        1.0, 1.0, 1.0, 0.9, 0.9, 0.9, 0.8, 0.8, 0.8, 0.8, 0.7, 0.7, 0.7, 0.6, 0.6, 0.6, 0.6, 0.5,
        0.5, 0.5, 0.5, 0.4, 0.4, 0.4, 0.4, 0.4, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.2, 0.2, 0.2,
        0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
        0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
    ],
)

if __name__ == "__main__":
    print_volumetric_sheet(**WELL)
