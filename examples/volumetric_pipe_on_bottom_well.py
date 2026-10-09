"""Volumetric method, then lubricate and bleed - pipe on bottom, unable to pump.

The baseline well: vertical, untapered string, surface BOP stack.
The 15-minute SICP rises and the bbl pumped are what the crew reads - the
tables run until the gas is at surface, and until casing pressure is 0.

Run it with:  python examples/volumetric_pipe_on_bottom_well.py
"""

from kill_sheet_printer import print_volumetric_sheet
from killsheet.volumetric import AVERAGE, LONGEST, SMALLEST  # noqa: F401

print_volumetric_sheet(
    title="VOLUMETRIC - pipe on bottom, unable to pump (vertical, untapered)",
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
        ('DC x 8-1/2" hole', 0.0291, 600),
        ('HWDP x 8-1/2" hole', 0.0459, 900),
        ('DP x 8-1/2" hole', 0.0459, 4_850),
        ('DP x 9-5/8" casing', 0.0489, 5_150),
    ],
    # Readings: SICP rise over the 15 minute wait after each volumetric cycle
    sicp_rises_after_each_cycle=[30, 28, 25, 22, 20, 14, 4],
    # Readings: SICP once the gas is at surface, and bbl pumped each L&B cycle
    sicp_gas_at_surface_psi=1_254,
    bbl_pumped_each_cycle=[6.0, 7.0, 8.0, 9.0, 10.0, 10.0, 11.0, 11.0, 12.0, 12.0, 12.0],
)
