"""Bullhead sheet (drilling) - the baseline well: vertical, untapered string.

The kick is too large to handle at surface: the annular is shut and kill
fluid is pumped down the drill string AND the backside at the same rate, at
the same time, to push the influx back where it came from.

Run it with:  python examples/bullhead_well.py
"""

from kill_sheet_printer import print_bullhead_sheet

print_bullhead_sheet(
    title="BULLHEAD - annular shut, down the string and the backside (vertical, untapered)",
    bit_tvd_ft=11_500,
    shoe_tvd_ft=5_150,
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
        ('5" 19.5# DP', 0.0178, 10_000),
        ('5" HWDP', 0.0087, 900),
        ('6-1/2" DC', 0.0077, 600),
    ],
    annulus_bottom_up=[                 # bottom up
        ('DC x 8-1/2" hole', 0.0291, 600),
        ('HWDP x 8-1/2" hole', 0.0459, 900),
        ('DP x 8-1/2" hole', 0.0459, 4_850),
        ('DP x 9-5/8" casing', 0.0489, 5_150),
    ],
)
