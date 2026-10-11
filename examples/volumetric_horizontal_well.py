"""Volumetric method, then lubricate and bleed - horizontal well, pipe on bottom, unable to pump.

The approved horizontal well, untapered string: KOP 9,000 ft, heel and 9-5/8"
shoe at 9,900 ft MD / 9,573 ft TVD, 5,000 ft lateral to TD at 14,900 ft MD.
The influx lies in the lateral (SICP = SIDPP = 650). Shoe at the heel: shoe pressure
= BHP and the kick tolerance is very small - with SF 100 / Pw 50 the pre-check fires
and every hold is limited by the shoe. The honest answer for this well: consider
bullheading before volumetric.
The 15-minute SICP rises are illustrative until the gas reaches surface; when that
happens, the SICP with gas at surface and the bbl pumped in lubricate and bleed come
from the single-bubble forecast (killsheet/volumetric_model.py), so the readings
and the forecast agree.

Run it with:  python examples/volumetric_horizontal_well.py
"""

from kill_sheet_printer import print_volumetric_sheet
from killsheet.volumetric import AVERAGE, LONGEST, SMALLEST  # noqa: F401
from killsheet.volumetric_model import ANNULUS_AT_THE_GAS

WELL = dict(
    title="VOLUMETRIC - horizontal well, pipe on bottom, unable to pump (untapered)",
    original_mud_weight_ppg=10.4,
    kill_mud_weight_ppg=11.8,           # mud lubricated in L&B
    # Well path
    td_md_ft=14_900,
    td_tvd_ft=9_573,
    shoe_md_ft=9_900,
    key_points=[("KOP", 9_000, 9_000), ("heel", 9_900, 9_573)],
    # Shoe and leak-off test (for MAASP)
    shoe_tvd_ft=9_573,
    lot_pressure_psi=1_000,
    test_mud_weight_ppg=10.0,
    sicp_psi=650,                       # 0.1 psi/ft gas: SIDPP + (0.5408 - 0.1) x influx height
    pit_gain_bbl=10,                    # kick size - the forecast needs it
    # Where the pipe is (for the plot and schematic)
    pipe_bottom_md_ft=14_900,           # on bottom (TD)
    float_in_string=True,               # no drill pipe reading - casing only
    # Chosen by the team killing the well
    safety_margin_psi=100,
    working_pressure_psi=50,
    capacity_choice=ANNULUS_AT_THE_GAS, # default; or SMALLEST, AVERAGE, LONGEST
    annulus_bottom_up=[                 # (name, capacity bbl/ft, length ft MD)
        ('DC x 8-1/2" hole', 0.0291, 600),
        ('HWDP x 8-1/2" hole', 0.0459, 900),
        ('DP x 8-1/2" hole', 0.0459, 3_500),
        ('DP x 9-5/8" casing', 0.0489, 9_900),
    ],
    # Readings: SICP rise over the 15 minute wait after each volumetric cycle
    # (illustrative until the gas reaches surface - the forecast decides when that is)
    sicp_rises_after_each_cycle=[
        30, 27, 25, 22, 20, 17, 15, 10,
    ],
    # Readings: SICP once the gas is at surface, and bbl pumped each L&B cycle
    sicp_gas_at_surface_psi=1_275,
    bbl_pumped_each_cycle=[
        1.7, 1.7, 1.6, 1.6, 1.6, 1.5, 1.5, 1.5, 1.4, 1.4, 1.3, 1.3, 1.3, 1.2, 1.2, 1.1, 1.1, 1.1,
        1.0, 1.0, 0.9, 0.9, 0.9, 0.8, 0.8, 0.8, 0.7, 0.7, 0.7, 0.6, 0.6, 0.6, 0.5, 0.5, 0.5, 0.5,
        0.4, 0.4, 0.4, 0.4, 0.4, 0.3, 0.3, 0.3, 0.3, 0.3, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
        0.2, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
        0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
    ],
)

if __name__ == "__main__":
    print_volumetric_sheet(**WELL)
