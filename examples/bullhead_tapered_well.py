"""Bullhead sheet (drilling) - vertical well, tapered string.

The approved vertical tapered well: 5" DP over 3-1/2" DP, HWDP and DC, 7" 26#
casing (ID 6.276") to 9,500 ft, 6-1/8" hole to 11,500 ft. MAASP is 889 psi.
The annular is shut and kill fluid is pumped down the drill string AND the
backside at the same rate, at the same time.

Run it with:  python examples/bullhead_tapered_well.py
"""

from kill_sheet_printer import print_bullhead_sheet

print_bullhead_sheet(
    title="BULLHEAD - annular shut, down the string and the backside (vertical, tapered)",
    bit_tvd_ft=11_500,
    shoe_tvd_ft=9_500,
    original_mud_weight_ppg=10.4,
    # Leak-off test (formation limit)
    lot_pressure_psi=1_100,
    test_mud_weight_ppg=10.0,
    # Kick data
    sidpp_psi=650,
    sicp_increase_psi_per_hr=100,       # for the gas migration rate
    # Pump - the same rate down both sides
    pump_output_bbl_per_stk=0.117,
    pump_rate_bbl_per_min=3.0,
    # Equipment limit: the lowest rating or tested value
    equipment_ratings=[
        ("BOP stack, tested", 3_500),
        ('7" casing, tested', 3_000),
        ("Pump lines / standpipe, rated", 5_000),
    ],
    overdisplacement_bbl=5.0,           # team's choice
    drill_string=[                      # top down
        ('5" 19.5# DP', 0.0178, 7_000),
        ('3-1/2" 13.3# DP', 0.0074, 3_600),
        ('3-1/2" HWDP', 0.0041, 600),
        ('4-3/4" DC', 0.0049, 300),
    ],
    annulus_bottom_up=[                 # bottom up
        ('DC x 6-1/8" hole', 0.0145, 300),
        ('HWDP x 6-1/8" hole', 0.0245, 600),
        ('3-1/2" DP x 6-1/8" hole', 0.0245, 1_100),
        ('3-1/2" DP x 7" casing', 0.0264, 2_500),
        ('5" DP x 7" casing', 0.0140, 7_000),
    ],
)
