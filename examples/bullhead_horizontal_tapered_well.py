"""Bullhead sheet (drilling) - horizontal well, tapered string.

The approved horizontal well: KOP 9,000 ft, heel and 9-5/8" shoe 9,900 ft MD /
9,573 ft TVD, 5,000 ft 8-1/2" lateral to the bit at 14,900 ft MD, with 5" DP over
4" DP (crossover 500 ft into the lateral), 4" HWDP and 6-1/2" DC. The lateral is
flat, so kill fluid there adds no hydrostatic: the string limit drops to its
final value as soon as kill fluid reaches the heel.

Run it with:  python examples/bullhead_horizontal_tapered_well.py
"""

from kill_sheet_printer import print_bullhead_sheet

print_bullhead_sheet(
    title="BULLHEAD - annular shut, down the string and the backside (horizontal, tapered)",
    bit_md_ft=14_900,
    bit_tvd_ft=9_573,
    shoe_md_ft=9_900,                   # casing set at the heel
    shoe_tvd_ft=9_573,
    key_points=[("KOP", 9_000, 9_000), ("heel", 9_900, 9_573)],
    original_mud_weight_ppg=10.4,
    # Leak-off test (formation limit)
    lot_pressure_psi=1_000,
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
        ('9-5/8" casing, tested', 3_000),
        ("Pump lines / standpipe, rated", 5_000),
    ],
    overdisplacement_bbl=10.0,          # team's choice
    drill_string=[                      # top down
        ('5" 19.5# DP', 0.0178, 10_400),
        ('4" 14# DP', 0.0108, 3_000),
        ('4" HWDP', 0.0064, 900),
        ('6-1/2" DC', 0.0077, 600),
    ],
    annulus_bottom_up=[                 # bottom up
        ('DC x 8-1/2" hole', 0.0291, 600),
        ('4" HWDP x 8-1/2" hole', 0.0546, 900),
        ('4" DP x 8-1/2" hole', 0.0546, 3_000),
        ('5" DP x 8-1/2" hole', 0.0459, 500),
        ('5" DP x 9-5/8" casing', 0.0489, 9_900),
    ],
)
