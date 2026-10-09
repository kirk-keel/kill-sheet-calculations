"""Volumetric method, then lubricate and bleed - deviated well, pipe on bottom, unable to pump.

The approved deviated (build-and-hold) well, untapered string: KOP 3,000 ft,
end of build 4,000 ft MD / 3,955 ft TVD, 30 deg tangent to TD at 12,712 ft MD /
11,500 ft TVD. The volume bled is the vertical IADC #35 volume; the
angle-corrected volume for each section is printed for information.
The 15-minute SICP rises and the bbl pumped are example readings.

Run it with:  python examples/volumetric_deviated_well.py
"""

from kill_sheet_printer import print_volumetric_sheet
from killsheet.volumetric import AVERAGE, LONGEST, SMALLEST  # noqa: F401

print_volumetric_sheet(
    title="VOLUMETRIC - deviated well, pipe on bottom, unable to pump (untapered)",
    original_mud_weight_ppg=10.4,
    kill_mud_weight_ppg=11.5,
    # Well path
    td_md_ft=12_712,
    td_tvd_ft=11_500,
    shoe_md_ft=5_380,
    key_points=[("KOP", 3_000, 3_000), ("end of build", 4_000, 3_955)],
    # Shoe and leak-off test (for MAASP)
    shoe_tvd_ft=5_150,
    lot_pressure_psi=1_350,
    test_mud_weight_ppg=9.6,
    sicp_psi=800,
    # Chosen by the team killing the well
    safety_margin_psi=100,
    working_pressure_psi=50,
    capacity_choice=SMALLEST,           # default; or AVERAGE, LONGEST
    annulus_bottom_up=[                 # (name, capacity bbl/ft, length ft MD)
        ('DC x 8-1/2" hole', 0.0291, 600),
        ('HWDP x 8-1/2" hole', 0.0459, 900),
        ('DP x 8-1/2" hole', 0.0459, 5_832),
        ('DP x 9-5/8" casing', 0.0489, 5_380),
    ],
    # Readings: SICP rise over the 15 minute wait after each volumetric cycle
    sicp_rises_after_each_cycle=[30, 28, 25, 22, 20, 14, 4],
    # Readings: SICP once the gas is at surface, and bbl pumped each L&B cycle
    sicp_gas_at_surface_psi=1_254,
    bbl_pumped_each_cycle=[6.0, 7.0, 8.0, 9.0, 10.0, 10.0, 11.0, 11.0, 12.0, 12.0, 12.0],
)
