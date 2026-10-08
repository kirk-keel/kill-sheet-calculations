"""Kill sheet for a horizontal well, untapered string, Wait and Weight.

Vertical to KOP at 9,000 ft, build at 10 deg/100 ft to 90 deg, land the heel
at 9,900 ft MD / 9,573 ft TVD with 9-5/8" casing, then a 5,000 ft 8-1/2" lateral.

The drill pipe pressure bottoms out at the heel, then climbs back to FCP
along the lateral - follow the schedule up to FCP.

Run it with:  python examples/wait_and_weight_horizontal_well.py
"""

from kill_sheet_printer import WAIT_AND_WEIGHT, print_kill_sheet
from killsheet.schedule import EVERY_100_STROKES, TEN_STEPS  # noqa: F401

print_kill_sheet(
    title="KILL SHEET - horizontal well, untapered string, surface BOP stack",
    method=WAIT_AND_WEIGHT,
    step_method=TEN_STEPS,              # default; or EVERY_100_STROKES
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
    # Wait and Weight: retake SIDPP (bump the float) and SICP just before
    # start-up, and the drill pipe reading once at kill rate
    # (leave observed_icp_psi as None until you have it)
    sidpp_at_start_psi=650,
    sicp_at_start_psi=700,
    observed_icp_psi=None,
    # Pump and volumes: (name, capacity bbl/ft, length ft MD)
    pump_output_bbl_per_stk=0.117,
    surface_line_volume_bbl=0,          # leave as 0 if unknown
    drill_string=[                      # top down
        ('5" 19.5# DP', 0.0178, 13_400),
        ('5" HWDP', 0.0087, 900),
        ('6-1/2" DC', 0.0077, 600),
    ],
    open_hole_annulus=[                 # bit up (the lateral)
        ('DC x 8-1/2" hole', 0.0291, 600),
        ('HWDP x 8-1/2" hole', 0.0459, 900),
        ('DP x 8-1/2" hole', 0.0459, 3_500),
    ],
    cased_hole_annulus=[                # bit up
        ('DP x 9-5/8" casing', 0.0489, 9_900),
    ],
)
