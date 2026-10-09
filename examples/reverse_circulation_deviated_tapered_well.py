"""Reverse circulation kill - CWI well, deviated (build and hold), tapered tubing.

3-1/2" 9.3# tubing to 5,000 ft MD over 2-7/8" 6.5# tubing, in 5-1/2" 17# casing, along the deviated well path: KOP 3,000 ft,
end of build 4,000 ft MD / 3,955 ft TVD, then a 30 deg tangent. Opened SSD at
11,000 ft MD (10,017 ft TVD), packer at 11,050 ft MD, perforations 11,200-11,300 ft
MD (10,190-10,277 ft TVD). Pressures use TVD; volumes and strokes use MD.
The observed ICP is an example reading.

Run it with:  python examples/reverse_circulation_deviated_tapered_well.py
"""

from kill_sheet_printer import print_reverse_circulation_sheet

print_reverse_circulation_sheet(
    title="REVERSE CIRCULATION - CWI well, opened SSD above the packer (deviated, tapered tubing)",
    formation_pressure_psi=5_200,
    sitp_psi=1_800,
    top_perf_md_ft=11_200,
    top_perf_tvd_ft=10_190,
    bottom_perf_tvd_ft=10_277,
    ssd_md_ft=11_000,
    ssd_tvd_ft=10_017,
    packer_md_ft=11_050,
    packer_tvd_ft=10_060,
    key_points=[("KOP", 3_000, 3_000), ("end of build", 4_000, 3_955)],
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
        ('2-7/8" tubing x 5-1/2" 17# casing', 0.0152, 6_000),
    ],
    tubing_sections=[
        ('3-1/2" 9.3# tubing', 0.0087, 5_000),
        ('2-7/8" 6.5# tubing', 0.0058, 6_000),
    ],
    casing_capacity_bbl_per_ft=0.0232,  # 5-1/2" 17# casing, packer to perfs
    # Reading: annulus pressure once at kill rate (None until you have it)
    observed_icp_psi=900,
)
