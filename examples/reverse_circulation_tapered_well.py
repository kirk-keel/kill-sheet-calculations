"""Reverse circulation kill - CWI well with a tapered tubing string.

Vertical completion: 3-1/2" 9.3# tubing to 5,000 ft over 2-7/8" 6.5# tubing, opened SSD at 9,900 ft above the
production packer at 9,950 ft, 5-1/2" 17# casing, perforations 10,100-10,200 ft.
Kill weight fluid down the annulus, up the tubing through the choke.
The observed ICP is an example reading - the crew enters what they read at
kill rate.

Run it with:  python examples/reverse_circulation_tapered_well.py
"""

from kill_sheet_printer import print_reverse_circulation_sheet

print_reverse_circulation_sheet(
    title="REVERSE CIRCULATION - CWI well, tapered tubing, opened SSD above the packer (vertical)",
    formation_pressure_psi=5_200,
    sitp_psi=1_800,
    top_perf_tvd_ft=10_100,
    bottom_perf_tvd_ft=10_200,
    ssd_tvd_ft=9_900,
    packer_tvd_ft=9_950,
    packer_fluid_ppg=8.6,
    fracture_gradient_psi_per_ft=0.75,
    margin_ppg=0,                       # optional; added before the rule-1 round-up
    # Pump
    pump_output_bbl_per_stk=0.0500,
    pump_rate_bbl_per_min=2.0,
    # Equipment limit: the lowest rating or tested value
    equipment_ratings=[
        ("Tree, rated", 5_000),
        ('5-1/2" casing, tested', 4_000),
    ],
    # Volumes, surface to the SSD: (name, capacity bbl/ft, length ft MD)
    annulus_sections=[
        ('3-1/2" tubing x 5-1/2" 17# casing', 0.0113, 5_000),
        ('2-7/8" tubing x 5-1/2" 17# casing', 0.0152, 4_900),
    ],
    tubing_sections=[
        ('3-1/2" 9.3# tubing', 0.0087, 5_000),
        ('2-7/8" 6.5# tubing', 0.0058, 4_900),
    ],
    casing_capacity_bbl_per_ft=0.0232,  # 5-1/2" 17# casing, packer to perfs
    # Reading: annulus pressure once at kill rate (None until you have it)
    observed_icp_psi=900,
)
