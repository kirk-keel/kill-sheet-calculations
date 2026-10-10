"""Tests for the kill plot - single-bubble gas model, vertical well, untapered string.

Baseline example well, hand-worked example (user-approved):
SIDPP 650, SICP 800, OMW 10.4 ppg (0.5408 psi/ft), KMW 11.5 ppg (0.5980 psi/ft),
bit 11,500 ft, shoe 5,150 ft, MAMW 14.6 ppg, MAASP 1,124 psi, ICP 1,400, FCP 829,
pump 0.117 bbl/stk, pit gain 10 bbl, safety margin (SF) 50 psi.

  Influx height   = 10 / 0.0291 = 344 ft
  Gas gradient    = 0.5408 - 150 / 344 = 0.5408 - 0.4360 = 0.1048 psi/ft
  Formation       = 650 + 0.5408 x 11,500 = 6,869 psi;  BHP = 6,869 + 50 = 6,919 psi
  Fracture (shoe) = 0.052 x 14.6 x 5,150 = 3,909 psi (rounded DOWN)
  Overbalance     = (11.5 - 10.4) x 0.052 x 11,500 = 657.8 -> 658 psi (8 more than SIDPP)
  Driller's       = DP with kill mud at the bit 829 + 650 + 50 - 658 = 871 (held to surface);
                    trapped = 650 + 50 - 658 = 42 psi
  W&W             = step-down ends on FCP + SF = 879; the kill mud adds 8 psi more than
                    the SIDPP the chart takes off, so BHP ends at 6,919 + 8 = 6,927;
                    trapped = SF = 50 psi

Every pressure matches the hand example. The module rounds the pumped volume
to 0.1 bbl (as the stroke calculations do), so some events land a stroke or two
from the hand example. W&W max shoe: the shoe pressure sits at 3,647-3,648 psi
from about 1,600 to 1,631 strokes (a flat top), so the stroke it is first
reached moves with rounding.
"""

from killsheet.kill_plot import (
    FALLBACK_GAS_GRADIENT_PSI_PER_FT,
    AnnulusWell,
    annulus_forecast,
    drillers_kill_plot,
    fracture_at_shoe,
    formation_pressure,
    gas_influx,
    influx_height,
    influx_gradient,
    mud_gradient,
    plot_warnings,
    trapped_pressures_match,
    wait_and_weight_kill_plot,
)
from killsheet.schedule import pressure_schedule

DRILL_STRING = [(0.0178, 10_000), (0.0087, 900), (0.0077, 600)]                   # top down
ANNULUS = [(0.0291, 600), (0.0459, 900), (0.0459, 4_850), (0.0489, 5_150)]       # bit up
SF_PSI = 50

WELL = dict(sidpp_psi=650, sicp_psi=800, icp_psi=1400, fcp_psi=829, safety_margin_psi=SF_PSI,
            pit_gain_bbl=10, original_mud_weight_ppg=10.4, kill_mud_weight_ppg=11.5,
            bit_tvd_ft=11_500, shoe_tvd_ft=5_150, mamw_ppg=14.6, maasp_psi=1124,
            drill_string_sections=DRILL_STRING, annulus_sections=ANNULUS,
            pump_output_bbl_per_stk=0.117)

# Each plot works out every stroke - build them once.
DRILLERS = drillers_kill_plot(**WELL)
WAIT_AND_WEIGHT = wait_and_weight_kill_plot(**WELL)


# --- The influx -----------------------------------------------------------------

def test_mud_gradients():
    assert mud_gradient(10.4) == 0.5408
    assert mud_gradient(11.5) == 0.5980


def test_influx_height_in_the_collar_annulus():
    # 10 / 0.0291 = 343.6 -> 344 ft
    assert influx_height(10, ANNULUS) == 344


def test_influx_height_runs_into_the_next_section():
    # 600 ft x 0.0291 = 17.46 bbl in the DC annulus; 2.54 / 0.0459 = 55 ft of HWDP annulus
    assert influx_height(20, ANNULUS) == 655


def test_influx_gradient_from_the_gauges():
    assert influx_gradient(650, 800, 0.5408, 344) == (0.1048, None)


def test_influx_gradient_suggests_liquid():
    # 0.5408 - 150 / 654 = 0.3114 psi/ft - used, with a warning
    gradient, warning = influx_gradient(650, 800, 0.5408, 654)
    assert gradient == 0.3114
    assert "Influx gradient suggests liquid, not gas" in warning
    assert "overstated (conservative)" in warning


def test_influx_gradient_heavier_than_mud_falls_back():
    # SICP below SIDPP: gradient would be heavier than the mud
    gradient, warning = influx_gradient(650, 600, 0.5408, 344)
    assert gradient == FALLBACK_GAS_GRADIENT_PSI_PER_FT
    assert "inconsistent" in warning


def test_influx_gradient_below_zero_falls_back():
    # 0.5408 - 250 / 344 = -0.1859
    gradient, warning = influx_gradient(650, 900, 0.5408, 344)
    assert gradient == FALLBACK_GAS_GRADIENT_PSI_PER_FT
    assert "inconsistent" in warning


def test_gas_influx_at_shut_in():
    gas, warning = gas_influx(10, 650, 800, 0.5408, 11_500, ANNULUS)
    assert warning is None
    assert (gas.volume_bbl, gas.height_ft, gas.gradient_psi_per_ft) == (10, 344, 0.1048)
    # 6,869 - 0.1048 x 344 = 6,832.95 psi at the top of the bubble
    assert round(gas.top_pressure_psi, 2) == 6832.95


def test_formation_pressure():
    assert formation_pressure(650, 0.5408, 11_500) == 6869


# --- The annulus forecast --------------------------------------------------------

ANNULUS_WELL = AnnulusWell(ANNULUS, 5_150, 0.117, 0.5408, 0.5980)


def test_forecast_at_shut_in_reads_sicp():
    gas, _ = gas_influx(10, 650, 800, 0.5408, 11_500, ANNULUS)
    forecast = annulus_forecast(0, 6869, ANNULUS_WELL, gas)
    assert forecast.casing_psi == 800
    assert (forecast.gas_top_ft, forecast.gas_bottom_ft, forecast.gas_volume_bbl) == (11_156, 11_500, 10.0)


def test_forecast_no_gas_original_mud_reads_sidpp_plus_sf():
    assert annulus_forecast(0, 6919, ANNULUS_WELL).casing_psi == 700


def test_forecast_kill_mud_to_surface_reads_trapped_pressure():
    # 6,919 - 0.5980 x 11,500 = 42 psi
    assert annulus_forecast(4557 + 1627, 6919, ANNULUS_WELL, None, 1627).casing_psi == 42


def test_forecast_never_reads_below_zero():
    # No safety margin: kill mud overbalances by 8 psi - the gauge reads 0, the
    # choke is fully open and BHP is the kill mud hydrostatic, 8 psi over formation.
    forecast = annulus_forecast(4557 + 1627, 6869, ANNULUS_WELL, None, 1627)
    assert (forecast.casing_psi, forecast.bhp_psi) == (0, 6877)
    assert forecast.shoe_psi == 3080                        # 0 + 0.5980 x 5,150 (not 8 psi less)


def test_forecast_bhp_is_the_bhp_held():
    assert annulus_forecast(0, 6919, ANNULUS_WELL).bhp_psi == 6919


# --- Checks ----------------------------------------------------------------------

def test_fracture_at_shoe():
    assert fracture_at_shoe(14.6, 5_150) == 3909          # 3,909.9 rounded DOWN


def test_trapped_pressures_match():
    assert trapped_pressures_match(42, 42)
    assert trapped_pressures_match(42, 52)
    assert not trapped_pressures_match(42, 53)


# --- Driller's method -------------------------------------------------------------

def test_drillers_start_up():
    points = DRILLERS.points
    assert [(p.strokes, p.drill_pipe_psi, p.casing_psi) for p in points[:3]] == [
        (0, 650, 800),      # shut in
        (0, 700, 850),      # casing raised to SICP + SF; drill pipe rises with it (U-tube)
        (0, 1450, 850),     # at kill rate: drill pipe reads ICP + SF - swap to it
    ]


def test_drillers_peak_casing_as_gas_reaches_surface():
    peak = DRILLERS.peak_casing
    assert (peak.casing_psi, peak.gas_volume_bbl) == (1272, 53.6)
    assert abs(peak.strokes - 4097) <= 10


def test_drillers_max_shoe_pressure():
    plot = DRILLERS
    assert plot.max_shoe.shoe_psi == 3681
    assert abs(plot.max_shoe.strokes - 2241) <= 10
    assert plot.fracture_at_shoe_psi == 3909


def test_drillers_drill_pipe_held_at_icp_plus_sf_in_the_1st_circulation():
    points = DRILLERS.points
    first_circulation = [p for p in points[2:] if p.strokes < 4557]
    assert {p.drill_pipe_psi for p in first_circulation} == {1450}


def test_drillers_events_in_the_1st_circulation():
    labelled = {p.label: (p.strokes, p.casing_psi) for p in DRILLERS.points}
    # Gas events depend on rounding: pressure exact, stroke within a window
    assert labelled["top of gas at the shoe"][1] == 895
    assert abs(labelled["top of gas at the shoe"][0] - 2247) <= 10
    assert labelled["gas at surface"][1] == 1272
    assert abs(labelled["gas at surface"][0] - 4098) <= 10
    assert labelled["gas out"] == (4557, 700)
    assert labelled["shut in: both read SIDPP + SF"] == (4557, 700)


def test_drillers_2nd_circulation_drill_pipe_falls_to_871():
    # Casing held at SIDPP + SF: DP = SIDPP + SF - 658 x MD / 11,500 + 750 + 79 x MD / 11,500
    # e.g. 1,073 ft: 700 - 61.39 + 750 + 7.37 = 1,395.98 -> 1,396
    second = [(p.strokes - 4557, p.drill_pipe_psi, p.casing_psi)
              for p in DRILLERS.points if 4557 < p.strokes <= 4557 + 1627]
    assert second == [
        (163, 1396, 700), (326, 1342, 700), (489, 1288, 700), (652, 1234, 700),
        (815, 1180, 700), (978, 1126, 700), (1141, 1072, 700), (1304, 1018, 700),
        (1467, 965, 700),
        (1521, 947, 700),       # DP / HWDP crossover
        (1588, 901, 700),       # HWDP / DC crossover
        (1627, 871, 700),       # kill mud at the bit: 829 + 650 + 50 - 658 (NOT 879)
    ]


def test_drillers_drill_pipe_held_at_871_to_surface():
    bit_to_surface = [p for p in DRILLERS.points if 4557 + 1627 <= p.strokes and p.label != SHUT_IN_TRAPPED]
    assert {p.drill_pipe_psi for p in bit_to_surface} == {871}


def test_drillers_sf_below_overbalance_casing_reaches_0_and_drill_pipe_rises():
    # SF 0: casing would have to end at 650 - 658 = -8. It reaches 0 (choke fully
    # open) near the end and the drill pipe rises from 821 toward FCP 829.
    plot = drillers_kill_plot(**{**WELL, "safety_margin_psi": 0})
    labelled = {p.label: (p.strokes, p.drill_pipe_psi, p.casing_psi) for p in plot.points}
    assert labelled["kill mud at the bit"] == (4557 + 1627, 821, 650)
    choke_open = labelled["casing at 0, choke fully open - drill pipe rises toward FCP"]
    assert choke_open[1:] == (822, 0)
    assert abs(choke_open[0] - 10_687) <= 10
    assert labelled["kill mud at surface"] == (10_741, 829, 0)
    assert (plot.trapped_drill_pipe_psi, plot.trapped_casing_psi) == (0, 0)
    after = [p for p in plot.points if p.strokes >= choke_open[0] and p.label != SHUT_IN_TRAPPED]
    assert all(p.casing_psi == 0 for p in after)
    assert [p.drill_pipe_psi for p in after] == sorted(p.drill_pipe_psi for p in after)   # only rises


def test_drillers_sf_above_overbalance_choke_never_fully_open():
    assert not any("choke fully open" in p.label for p in DRILLERS.points)


SHUT_IN_TRAPPED = "shut in: both read the trapped pressure - bleed to 0, check, flow check"


def test_drillers_end_trapped_pressure():
    plot = DRILLERS
    assert (plot.trapped_drill_pipe_psi, plot.trapped_casing_psi) == (42, 42)
    last = plot.points[-1]
    assert (last.strokes, last.drill_pipe_psi, last.casing_psi) == (4557 + 1627 + 4557, 42, 42)


def test_drillers_warns_casing_over_maasp_but_shoe_is_the_check():
    warnings = DRILLERS.warnings
    assert len(warnings) == 1
    assert "above MAASP" in warnings[0] and "real check" in warnings[0]


def test_drillers_warns_shoe_above_fracture():
    # MAMW 13.0: fracture = 0.052 x 13.0 x 5,150 = 3,481 psi
    warnings = drillers_kill_plot(**{**WELL, "mamw_ppg": 13.0}).warnings
    assert any("ABOVE the fracture pressure 3,481" in w for w in warnings)


# --- Wait and Weight --------------------------------------------------------------

def test_wait_and_weight_peak_casing():
    peak = WAIT_AND_WEIGHT.peak_casing
    assert (peak.casing_psi, peak.gas_volume_bbl) == (1048, 65.1)
    assert abs(peak.strokes - 4000) <= 10


def test_wait_and_weight_max_shoe_is_not_at_top_of_gas_at_shoe():
    # Max as kill mud reaches the bit (casing is about to fall), not when the gas passes the shoe
    plot = WAIT_AND_WEIGHT
    assert plot.max_shoe.shoe_psi == 3648
    assert abs(plot.max_shoe.strokes - 1618) <= 30            # a plateau at 3,647-3,648
    labelled = {p.label: p.strokes for p in plot.points}
    assert abs(labelled["top of gas at the shoe"] - 2243) <= 10


def test_wait_and_weight_drill_pipe_follows_the_schedule_plus_sf():
    points = {p.strokes: p for p in WAIT_AND_WEIGHT.points[3:]}
    for row in pressure_schedule(1400, 829, DRILL_STRING, 0.117)[1:]:
        assert points[row.strokes].drill_pipe_psi == row.pressure_psi + SF_PSI
    assert points[1627].drill_pipe_psi == 879                  # FCP + SF at the bit


def test_wait_and_weight_casing_line():
    points = WAIT_AND_WEIGHT.points
    labelled = {p.label: (p.strokes, p.drill_pipe_psi, p.casing_psi) for p in points}
    assert labelled["kill mud at the bit"] == (1627, 879, 862)
    assert labelled["gas out"] == (4557, 879, 273)
    assert labelled["kill mud at surface"] == (6184, 879, 50)


def test_wait_and_weight_end_trapped_pressure():
    plot = WAIT_AND_WEIGHT
    assert (plot.trapped_drill_pipe_psi, plot.trapped_casing_psi) == (50, 50)    # SF, NOT 42
    assert plot.warnings == []                                 # peak 1,048 is under MAASP


def test_wait_and_weight_sf_0_ends_at_0():
    plot = wait_and_weight_kill_plot(**{**WELL, "safety_margin_psi": 0})
    labelled = {p.label: (p.strokes, p.drill_pipe_psi, p.casing_psi) for p in plot.points}
    assert labelled["kill mud at the bit"][1] == 829           # FCP
    assert labelled["kill mud at surface"] == (6184, 829, 0)
    assert (plot.trapped_drill_pipe_psi, plot.trapped_casing_psi) == (0, 0)


def test_wait_and_weight_high_icp_trapped_pressure():
    # SIDPP retaken 680, SICP 830, drill pipe reads 1,470 with SF 50:
    # ICP 1,420, FCP kept at 829, actual friction with kill mud 818
    # trapped = 50 + (829 - 818) = 61 - and the casing line ends on it.
    plot = wait_and_weight_kill_plot(**{**WELL, "sidpp_psi": 680, "sicp_psi": 830, "icp_psi": 1420,
                                        "kill_mud_friction_psi": 818})
    assert (plot.trapped_drill_pipe_psi, plot.trapped_casing_psi) == (61, 61)


# --- Warnings ---------------------------------------------------------------------

def test_warning_inconsistent_gauges_falls_back_to_0_1():
    # SICP below SIDPP - the influx can't be lighter than nothing
    plot = drillers_kill_plot(**{**WELL, "sicp_psi": 600})
    assert any("inconsistent" in w and "Using 0.1 psi/ft" in w for w in plot.warnings)


def test_warning_influx_suggests_liquid():
    # 20 bbl pit gain with the same gauges: 0.5408 - 150 / 655 = 0.3118 psi/ft
    plot = drillers_kill_plot(**{**WELL, "pit_gain_bbl": 20})
    assert any("suggests liquid, not gas" in w for w in plot.warnings)


def test_warning_trapped_pressures_dont_match():
    peak, shoe = DRILLERS.peak_casing, DRILLERS.max_shoe
    assert plot_warnings(peak, shoe, 3909, 1124, 42, 52) == plot_warnings(peak, shoe, 3909, 1124, 42, 42)
    warnings = plot_warnings(peak, shoe, 3909, 1124, 42, 53)                # 11 psi apart
    assert any("trapped pressures don't match" in w for w in warnings)


def test_warning_shoe_above_fracture():
    peak, shoe = DRILLERS.peak_casing, DRILLERS.max_shoe
    warnings = plot_warnings(peak, shoe, 3680, 1124, 42, 42)                # 3,681 > 3,680
    assert any("ABOVE the fracture pressure 3,680" in w for w in warnings)
    assert not any("ABOVE the fracture" in w for w in plot_warnings(peak, shoe, 3681, 1124, 42, 42))
