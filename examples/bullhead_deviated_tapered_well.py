"""Bullhead sheet (drilling) - deviated (build-and-hold) well, tapered string.

The approved deviated well: KOP 3,000 ft, end of build 4,000 ft MD / 3,955 ft TVD,
9-5/8" shoe 5,380 ft MD / 5,150 ft TVD, bit 12,712 ft MD / 11,500 ft TVD, with
5" DP over 4" DP (crossover at 8,000 ft MD), 4" HWDP and 6-1/2" DC.
The annular is shut and kill fluid is pumped down the drill string AND the
backside at the same rate, at the same time.

Run it with:  python examples/bullhead_deviated_tapered_well.py
"""

from kill_sheet_printer import print_bullhead_sheet

print_bullhead_sheet(
    title="BULLHEAD - annular shut, down the string and the backside (deviated, tapered)",
    bit_md_ft=12_712,
    bit_tvd_ft=11_500,
    shoe_md_ft=5_380,
    shoe_tvd_ft=5_150,
    key_points=[("KOP", 3_000, 3_000), ("end of build", 4_000, 3_955)],
    original_mud_weight_ppg=10.4,
    # Leak-off test (formation limit)
    lot_pressure_psi=1_350,
    test_mud_weight_ppg=9.6,
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
        ('5" 19.5# DP', 0.0178, 8_000),
        ('4" 14# DP', 0.0108, 3_212),
        ('4" HWDP', 0.0064, 900),
        ('6-1/2" DC', 0.0077, 600),
    ],
    annulus_bottom_up=[                 # bottom up
        ('DC x 8-1/2" hole', 0.0291, 600),
        ('4" HWDP x 8-1/2" hole', 0.0546, 900),
        ('4" DP x 8-1/2" hole', 0.0546, 3_212),
        ('5" DP x 8-1/2" hole', 0.0459, 2_620),
        ('5" DP x 9-5/8" casing', 0.0489, 5_380),
    ],
)
