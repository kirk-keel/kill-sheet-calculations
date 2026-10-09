"""Reverse circulation kill - CWI well, horizontal, untapered tubing.

2-7/8" 6.5# tubing in 5-1/2" 17# casing. Opened SSD at 8,800 ft and packer at
8,850 ft, both in the vertical section above KOP (9,000 ft); heel at 9,900 ft MD /
9,573 ft TVD; perforations along the lateral, 10,500-14,500 ft MD. The whole lateral
is at the heel TVD, so the heel TVD is used for the top and mid perf.
The observed ICP is an example reading (it must be above the SICP of 990 psi).

Run it with:  python examples/reverse_circulation_horizontal_well.py
"""

from kill_sheet_printer import print_reverse_circulation_sheet

print_reverse_circulation_sheet(
    title="REVERSE CIRCULATION - CWI well, opened SSD above the packer (horizontal)",
    formation_pressure_psi=5_200,
    sitp_psi=1_800,
    top_perf_md_ft=10_500,
    top_perf_tvd_ft=9_573,              # heel TVD - the lateral is flat
    bottom_perf_tvd_ft=9_573,
    ssd_md_ft=8_800,
    ssd_tvd_ft=8_800,
    packer_md_ft=8_850,
    packer_tvd_ft=8_850,
    key_points=[("KOP", 9_000, 9_000), ("heel", 9_900, 9_573)],
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
        ('2-7/8" tubing x 5-1/2" 17# casing', 0.0152, 8_800),
    ],
    tubing_sections=[
        ('2-7/8" 6.5# tubing', 0.0058, 8_800),
    ],
    casing_capacity_bbl_per_ft=0.0232,  # 5-1/2" 17# casing, packer to perfs
    # Reading: annulus pressure once at kill rate (None until you have it)
    observed_icp_psi=1_250,
)
