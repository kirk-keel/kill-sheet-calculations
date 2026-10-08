"""Kill sheet for a tapered string in a vertical well, Driller's method.

5" drill pipe over 3-1/2" drill pipe, plus HWDP and drill collars,
in 7" casing and a 6-1/8" hole.

Run it with:  python examples/tapered_well.py
"""

from kill_sheet_printer import DRILLERS, WAIT_AND_WEIGHT, print_kill_sheet  # noqa: F401

print_kill_sheet(
    title="KILL SHEET - vertical well, tapered string, surface BOP stack",
    method=DRILLERS,
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
