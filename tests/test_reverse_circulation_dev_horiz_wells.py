"""Reverse circulation kill - deviated and horizontal CWI wells, untapered tubing.

2-7/8" 6.5# tubing in 5-1/2" 17# casing, 8.6 ppg packer fluid, formation pressure
5,200 psi, SITP 1,800 psi, fracture gradient 0.75 psi/ft, casing tested to 4,000 psi.
Pressures use TVD; volumes and strokes use MD.
Verified by a well control specialist before this test was written.
"""

from killsheet.reverse_circulation import (
    AT_SSD,
    STEP,
    TUBING_DISPLACED,
    bullhead_below_ssd_limits,
    final_circulating_pressure,
    fracture_pressure,
    kill_weight_fluid,
    max_annulus_pressure,
    pressure_at_ssd,
    reverse_schedule,
    sicp_after_ssd_opened,
    sitp_after_ssd_opened,
    tubing_fluid_gradient,
    volume_below_ssd,
)

# --- Deviated: SSD 11,000 MD / 10,017 TVD; perfs 11,200-11,300 MD / 10,190-10,277 TVD ----
DEVIATED_KEY_POINTS = [("KOP", 3_000, 3_000), ("end of build", 4_000, 3_955)]

# --- Horizontal: SSD 8,800 / packer 8,850 above KOP; perfs in the lateral at the heel TVD --
HORIZONTAL_KEY_POINTS = [("KOP", 9_000, 9_000), ("heel", 9_900, 9_573)]


def test_deviated_kill_weight_and_pressures():
    gradient = tubing_fluid_gradient(5_200, 1_800, 10_234)          # mid-perf (10,190 + 10,277) / 2
    assert gradient == 0.3322
    p_ssd = pressure_at_ssd(5_200, gradient, 10_234, 10_017)         # 5,200 - 0.3322 x 217 = 5,127.9
    assert p_ssd == 5_128
    assert kill_weight_fluid(p_ssd, 10_017) == 9.9                    # 9.845 -> UP
    assert sitp_after_ssd_opened(p_ssd, gradient, 10_017) == 1_800
    assert sicp_after_ssd_opened(p_ssd, 8.6, 10_017) == 648
    frac = fracture_pressure(0.75, 10_190)                             # top perf TVD
    assert frac == 7_642
    assert max_annulus_pressure(frac, 9.9, 8.6, 0, 10_017, gradient, 10_190) == 3_104
    assert max_annulus_pressure(frac, 9.9, 8.6, 10_017, 10_017, gradient, 10_190) == 2_427
    # 900 - 1.3 x 0.052 x 10,017 (677.1 -> 677) = 223
    assert final_circulating_pressure(900, 9.9, 8.6, 10_017) == (223, False)


def test_deviated_schedule_follows_tvd():
    rows = reverse_schedule(900, 9.9, 8.6, [(0.0152, 11_000)], [(0.0058, 11_000)], 0.05, 7_642, 0.3322,
                            10_190, 4_000, ssd_tvd_ft=10_017, key_points=DEVIATED_KEY_POINTS)
    # (strokes, kill fluid MD, TVD, pump psi, max allowable psi, row)
    assert [tuple(row) for row in rows] == [
        (0, 0, 0, 900, 3104, STEP),
        (334, 1_099, 1_099, 826, 3030, STEP),
        (668, 2_197, 2_197, 752, 2956, STEP),
        (1002, 3_296, 3_283, 679, 2882, STEP),          # in the build
        (1336, 4_395, 4_297, 610, 2814, STEP),
        (1670, 5_493, 5_248, 546, 2750, STEP),
        (2004, 6_592, 6_200, 481, 2685, STEP),
        (2338, 7_691, 7_151, 417, 2621, STEP),
        (2672, 8_789, 8_102, 353, 2557, STEP),
        (3006, 9_888, 9_054, 288, 2492, STEP),
        (3344, 11_000, 10_017, 223, 2427, AT_SSD),      # 167.2 bbl / 0.05
        (4620, 11_000, 10_017, 223, 2427, TUBING_DISPLACED),   # + 63.8 bbl = 1,276 stks
    ]


def test_deviated_volume_below_ssd():
    assert volume_below_ssd(0.0058, 50, 0.0232, 150) == 3.8
    assert bullhead_below_ssd_limits(7_642, 9.9, 10_017, 0.3322, 10_190) == (2_427, 2_396)


def test_horizontal_kill_weight_and_pressures():
    gradient = tubing_fluid_gradient(5_200, 1_800, 9_573)            # heel TVD as mid-perf
    assert gradient == 0.3552
    p_ssd = pressure_at_ssd(5_200, gradient, 9_573, 8_800)           # 5,200 - 0.3552 x 773 = 4,925.4
    assert p_ssd == 4_925
    # The SSD is 773 ft TVD above the perfs: balanced at a shallower depth -> heavier KWF
    assert kill_weight_fluid(p_ssd, 8_800) == 10.8                    # 10.763 -> UP
    assert sitp_after_ssd_opened(p_ssd, gradient, 8_800) == 1_799     # 4-place gradient rounding
    assert sicp_after_ssd_opened(p_ssd, 8.6, 8_800) == 990
    frac = fracture_pressure(0.75, 9_573)                              # heel TVD as top perf
    assert frac == 7_179
    assert max_annulus_pressure(frac, 10.8, 8.6, 0, 8_800, gradient, 9_573) == 2_969
    assert max_annulus_pressure(frac, 10.8, 8.6, 8_800, 8_800, gradient, 9_573) == 1_962
    # Observed ICP must be above SICP (990): 1,250 - 2.2 x 0.052 x 8,800 (1,006.7 -> 1,006) = 244
    assert final_circulating_pressure(1_250, 10.8, 8.6, 8_800) == (244, False)


def test_horizontal_schedule():
    rows = reverse_schedule(1_250, 10.8, 8.6, [(0.0152, 8_800)], [(0.0058, 8_800)], 0.05, 7_179, 0.3552,
                            9_573, 4_000, ssd_tvd_ft=8_800, key_points=HORIZONTAL_KEY_POINTS)
    assert [(row.strokes, row.pump_psi, row.max_allowable_psi) for row in rows] == [
        (0, 1250, 2969), (268, 1150, 2868), (536, 1049, 2767), (804, 948, 2666), (1072, 847, 2565),
        (1340, 746, 2464), (1608, 646, 2364), (1876, 545, 2263), (2144, 444, 2162), (2412, 343, 2061),
        (2676, 244, 1962),      # kill fluid at the SSD (133.8 bbl)
        (3696, 244, 1962),      # tubing displaced (+ 51.0 bbl = 1,020 stks)
    ]


def test_horizontal_volume_below_ssd_is_much_larger():
    # Tubing SSD -> packer 0.3 bbl + casing packer -> first perf in the lateral (1,650 ft) 38.3 bbl
    assert volume_below_ssd(0.0058, 50, 0.0232, 10_500 - 8_850) == 38.6
    # Max tubing pressure at the start: 7,179 - (10.8 x 0.052 x 8,800 + 0.3552 x 773)
    #   = 7,179 - (4,942.1 + 274.6) = 1,962.3 -> 1,962
    # Once displaced to the top perf: 7,179 - 10.8 x 0.052 x 9,573 (5,376.2) = 1,802.8 -> 1,802
    assert bullhead_below_ssd_limits(7_179, 10.8, 8_800, 0.3552, 9_573) == (1_962, 1_802)
