"""Kill sheet for a deviated (build-and-hold) well, tapered string, Driller's method.

The approved deviated well (KOP 3,000 ft, build 3 deg/100 ft to 30 deg, 30 deg
tangent to TD) with 5" DP over 4" DP, 4" HWDP and 6-1/2" DC.

Run it with:  python examples/deviated_tapered_well.py
"""

from kill_sheet_printer import DRILLERS, print_kill_sheet

print_kill_sheet(
    title="KILL SHEET - deviated well, tapered string, surface BOP stack",
    method=DRILLERS,
    # Well path: bit, shoe and key points have MD and TVD
    bit_md_ft=12_712,
    bit_tvd_ft=11_500,
    shoe_md_ft=5_380,
    shoe_tvd_ft=5_150,
    key_points=[                        # (name, MD ft, TVD ft)
        ("KOP", 3_000, 3_000),
        ("end of build", 4_000, 3_955),
    ],
    original_mud_weight_ppg=10.4,
    # Leak-off test
    lot_pressure_psi=1_350,
    test_mud_weight_ppg=9.6,
    # Kick data
    sidpp_psi=650,
    sicp_psi=800,
    scr_pressure_psi=750,               # at 30 spm
    safety_margin_psi=50,               # held on bottom, chosen by the team
    # Pump and volumes: (name, capacity bbl/ft, length ft MD)
    pump_output_bbl_per_stk=0.117,
    surface_line_volume_bbl=0,          # leave as 0 if unknown
    drill_string=[                      # top down
        ('5" 19.5# DP', 0.0178, 8_000),
        ('4" 14# DP', 0.0108, 3_212),
        ('4" HWDP', 0.0064, 900),
        ('6-1/2" DC', 0.0077, 600),
    ],
    open_hole_annulus=[                 # bit up
        ('DC x 8-1/2" hole', 0.0291, 600),
        ('4" HWDP x 8-1/2" hole', 0.0546, 900),
        ('4" DP x 8-1/2" hole', 0.0546, 3_212),
        ('5" DP x 8-1/2" hole', 0.0459, 2_620),
    ],
    cased_hole_annulus=[                # bit up
        ('5" DP x 9-5/8" casing', 0.0489, 5_380),
    ],
)
