"""Volumetric method, then lubricate and bleed - bit at 8,000 ft, above the influx,
unable to strip back to bottom.

The baseline well with the string pulled up 3,500 ft: below the bit is open
hole with no pipe in it.

Run it with:  python examples/volumetric_pipe_above_influx_well.py
"""

from kill_sheet_printer import print_volumetric_sheet
from killsheet.volumetric import AVERAGE, LONGEST, SMALLEST  # noqa: F401

print_volumetric_sheet(
    title="VOLUMETRIC - pipe above the influx, unable to strip (vertical, untapered)",
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
        ('8-1/2" hole, no pipe', 0.0702, 3_500),
        ('DC x 8-1/2" hole', 0.0291, 600),
        ('HWDP x 8-1/2" hole', 0.0459, 900),
        ('DP x 8-1/2" hole', 0.0459, 1_350),
        ('DP x 9-5/8" casing', 0.0489, 5_150),
    ],
    # Readings: SICP rise over the 15 minute wait after each volumetric cycle
    sicp_rises_after_each_cycle=[26, 21, 17, 12, 7],
    # Readings: SICP once the gas is at surface, and bbl pumped each L&B cycle
    sicp_gas_at_surface_psi=1_157,
    bbl_pumped_each_cycle=[10.0] * 10,
)
