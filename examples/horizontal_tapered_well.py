"""Kill sheet for a horizontal well, tapered string, Driller's method.

The approved horizontal well (KOP 9,000 ft, build 10 deg/100 ft to 90 deg, heel
and 9-5/8" shoe at 9,900 ft MD / 9,573 ft TVD, 5,000 ft 8-1/2" lateral) with
5" DP over 4" DP, 4" HWDP and 6-1/2" DC. The 5" x 4" crossover is 500 ft
into the lateral.

Run it with:  python examples/horizontal_tapered_well.py
"""

from kill_sheet_printer import DRILLERS, print_kill_sheet

print_kill_sheet(
    title="KILL SHEET - horizontal well, tapered string, surface BOP stack",
    method=DRILLERS,
    # Well path: bit, shoe and key points have MD and TVD
    bit_md_ft=14_900,
    bit_tvd_ft=9_573,
    shoe_md_ft=9_900,                   # casing set at the heel
    shoe_tvd_ft=9_573,
    key_points=[                        # (name, MD ft, TVD ft)
        ("KOP", 9_000, 9_000),
        ("heel", 9_900, 9_573),
    ],
    original_mud_weight_ppg=10.4,
    # Leak-off test
    lot_pressure_psi=1_000,
    test_mud_weight_ppg=10.0,
    # Kick data
    sidpp_psi=650,
    sicp_psi=700,
    scr_pressure_psi=750,               # at 30 spm
    safety_margin_psi=50,               # held on bottom, chosen by the team
    # Pump and volumes: (name, capacity bbl/ft, length ft MD)
    pump_output_bbl_per_stk=0.117,
    surface_line_volume_bbl=0,          # leave as 0 if unknown
    drill_string=[                      # top down
        ('5" 19.5# DP', 0.0178, 10_400),
        ('4" 14# DP', 0.0108, 3_000),
        ('4" HWDP', 0.0064, 900),
        ('6-1/2" DC', 0.0077, 600),
    ],
    open_hole_annulus=[                 # bit up (the lateral)
        ('DC x 8-1/2" hole', 0.0291, 600),
        ('4" HWDP x 8-1/2" hole', 0.0546, 900),
        ('4" DP x 8-1/2" hole', 0.0546, 3_000),
        ('5" DP x 8-1/2" hole', 0.0459, 500),
    ],
    cased_hole_annulus=[                # bit up
        ('5" DP x 9-5/8" casing', 0.0489, 9_900),
    ],
)
