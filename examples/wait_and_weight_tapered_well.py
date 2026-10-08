"""Kill sheet for a tapered string in a vertical well, Wait and Weight method.

The approved vertical tapered well (5" DP over 3-1/2" DP, plus HWDP and drill
collars, in 7" casing and a 6-1/8" hole). The step-down schedule bends at every
crossover because it follows the depth of the kill mud.

Run it with:  python examples/wait_and_weight_tapered_well.py
"""

from kill_sheet_printer import WAIT_AND_WEIGHT, print_kill_sheet
from killsheet.schedule import EVERY_100_STROKES, TEN_STEPS  # noqa: F401

print_kill_sheet(
    title="KILL SHEET - vertical well, tapered string, surface BOP stack",
    method=WAIT_AND_WEIGHT,
    step_method=TEN_STEPS,              # default; or EVERY_100_STROKES
    # Well data
    bit_tvd_ft=11_500,
    shoe_tvd_ft=9_500,
    original_mud_weight_ppg=10.4,
    # Leak-off test
    lot_pressure_psi=1_100,
    test_mud_weight_ppg=10.0,
    # Kick data
    sidpp_psi=650,
    sicp_psi=800,
    scr_pressure_psi=750,               # at 30 spm
    # Wait and Weight: retake SIDPP (bump the float) and SICP just before
    # start-up, and the drill pipe reading once at kill rate
    # (leave observed_icp_psi as None until you have it)
    sidpp_at_start_psi=650,
    sicp_at_start_psi=800,
    observed_icp_psi=None,
    # Pump and volumes: (name, capacity bbl/ft, length ft)
    pump_output_bbl_per_stk=0.117,
    surface_line_volume_bbl=0,          # leave as 0 if unknown
    drill_string=[                      # top down
        ('5" 19.5# DP', 0.0178, 7_000),
        ('3-1/2" 13.3# DP', 0.0074, 3_600),
        ('3-1/2" HWDP', 0.0041, 600),
        ('4-3/4" DC', 0.0049, 300),
    ],
    open_hole_annulus=[                 # bit up
        ('DC x 6-1/8" hole', 0.0145, 300),
        ('HWDP x 6-1/8" hole', 0.0245, 600),
        ('3-1/2" DP x 6-1/8" hole', 0.0245, 1_100),
    ],
    cased_hole_annulus=[                # bit up
        ('3-1/2" DP x 7" casing', 0.0264, 2_500),
        ('5" DP x 7" casing', 0.0140, 7_000),
    ],
)
