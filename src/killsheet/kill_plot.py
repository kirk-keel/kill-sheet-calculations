"""Kill plot: forecast drill pipe AND casing pressure against strokes.

Vertical wells (untapered or tapered string), surface BOP stack,
Driller's method and Wait and Weight. The web page only draws these numbers.

Constant bottomhole pressure with a SAFETY MARGIN (SF, chosen by the team):
  Shut in:    drill pipe reads SIDPP, casing reads SICP.
  Start-up:   casing is raised to SICP + SF; through the U-tube the drill pipe
              rises to SIDPP + SF. The pump is brought up holding casing at
              SICP + SF. At kill rate the drill pipe reads ICP + SF and the
              choke operator swaps to the drill pipe gauge.
              BHP = formation pressure + SF for the whole kill.
  End:        both gauges read the same TRAPPED pressure (the SF less any
              overbalance of the kill mud). If they don't match, something is
              wrong. Bleed it off in small steps through the choke, check 0
              (+/- 10 psi), then flow check. Pressure building back = not dead.

Single-bubble gas model (forecasts the casing line while gas is in the annulus):
  - The influx is one bubble at the bit; its volume is the PIT GAIN.
  - Its gradient comes from the gauges:
        Height   = Pit gain / annulus capacity at the bit (whole ft)
        Gradient = Mud gradient - (SICP - SIDPP) / Height
  - The bubble moves up with the mud, stroke by stroke. Boyle's law
    (IADC #32), P1 x V1 = P2 x V2, at the TOP of the bubble (conservative:
    more expansion, higher casing). The gas gradient grows and shrinks with
    the pressure.
  - Casing = BHP - hydrostatic of everything in the annulus (mud, gas, kill mud)
    Shoe     = Casing + hydrostatic from surface down to the shoe
LIMITS of the model are in MODEL_LIMITS - print them with the plot.

Rounding: forecast pressures only use academic rounding (rule 3), depths to a
whole foot, each pressure rounded once at the end. KMW still rounds UP
(rule 1) and maximums still round DOWN (rule 2) - those come in as inputs.
"""

from typing import NamedTuple

from killsheet.kill_steps import GAUGE_TOLERANCE_PSI
from killsheet.rounding import (
    round_down_to_whole_number,
    round_to_4_places,
    round_to_tenth,
    round_to_whole_number,
)
from killsheet.schedule import drill_pipe_pressure, pressure_schedule
from killsheet.strokes import (
    md_after_strokes,
    section_volume,
    strokes_for_volume,
    surface_to_bit_strokes,
    total_length,
    total_volume,
)

# Gas gradient used when the gauges don't make sense (psi/ft).
FALLBACK_GAS_GRADIENT_PSI_PER_FT = 0.1
# Above this the influx is probably not gas (psi/ft).
NOT_GAS_ABOVE_PSI_PER_FT = 0.25

MODEL_LIMITS = (
    "Single-bubble gas model: ignores temperature, gas compressibility (Z), "
    "dispersion and slip. NOT valid in oil-based mud (gas dissolves). "
    "It usually over-predicts the peak casing pressure (errs on the safe side)."
)


class GasInflux(NamedTuple):
    """The gas bubble at shut-in."""

    volume_bbl: float              # the pit gain
    height_ft: int
    gradient_psi_per_ft: float
    top_pressure_psi: float        # pressure at the top of the bubble at shut-in


class AnnulusWell(NamedTuple):
    """What the gas model needs to know about the annulus (vertical well)."""

    annulus_sections: list         # (capacity bbl/ft, length ft), listed from the bit UP
    shoe_tvd_ft: int
    pump_output_bbl_per_stk: float
    mud_gradient_psi_per_ft: float
    kill_mud_gradient_psi_per_ft: float


class AnnulusForecast(NamedTuple):
    """Forecast casing and shoe pressure after a number of strokes."""

    strokes: int
    casing_psi: int
    shoe_psi: int
    gas_top_ft: int | None         # None once the gas is out
    gas_bottom_ft: int | None
    gas_volume_bbl: float | None   # = pit gain while all the gas is in the well


class PlotPoint(NamedTuple):
    """One point on the kill plot (and one row of its table)."""

    strokes: int
    drill_pipe_psi: int
    casing_psi: int
    gas_volume_bbl: float | None
    label: str


class KillPlot(NamedTuple):
    points: list                   # PlotPoint, in stroke order
    peak_casing: AnnulusForecast
    max_shoe: AnnulusForecast
    fracture_at_shoe_psi: int
    trapped_drill_pipe_psi: int
    trapped_casing_psi: int
    warnings: list


# --- Gradients and the influx ---------------------------------------------------

def mud_gradient(mud_weight_ppg):
    """Mud gradient (psi/ft), 4 places.

        Gradient = 0.052 x Mud weight
    """
    return round_to_4_places(0.052 * mud_weight_ppg)


def height_above_bit(volume_bbl, annulus_sections):
    """Height (ft, not rounded) that a volume pumped fills in the annulus, from the bit up.

        Height = Full sections + Section length x (Volume left / Section volume)

    Uses each section's ROUNDED volume, like the stroke calculations, so the
    gas and kill mud pass each crossover on the crossover's strokes.
    A volume bigger than the whole annulus returns the whole annulus length.
    """
    height_ft = 0
    for capacity_bbl_per_ft, length_ft in annulus_sections:
        section_bbl = section_volume(capacity_bbl_per_ft, length_ft)
        if volume_bbl <= section_bbl:
            return height_ft + length_ft * volume_bbl / section_bbl
        volume_bbl -= section_bbl
        height_ft += length_ft
    return height_ft


def gas_column_height(start_ft, volume_bbl, annulus_sections):
    """Height (ft, not rounded) of a gas volume whose bottom is start_ft above
    the bit, or None if the gas would reach surface.

        Height = Volume / Annular capacity  (section by section, going up)

    Uses the CAPACITY (like the influx height on a kill sheet), not the
    rounded section volumes.
    """
    section_bottom_ft = 0
    for capacity_bbl_per_ft, length_ft in annulus_sections:
        section_top_ft = section_bottom_ft + length_ft
        if start_ft < section_top_ft:
            from_ft = max(start_ft, section_bottom_ft)
            room_bbl = (section_top_ft - from_ft) * capacity_bbl_per_ft
            if volume_bbl <= room_bbl:
                return from_ft + volume_bbl / capacity_bbl_per_ft - start_ft
            volume_bbl -= room_bbl
        section_bottom_ft = section_top_ft
    return None


def annulus_volume_above(start_ft, annulus_sections):
    """Annulus volume (bbl, not rounded) from start_ft above the bit up to surface.

        Volume = Annular capacity x Length  (section by section)
    """
    volume_bbl = 0
    section_bottom_ft = 0
    for capacity_bbl_per_ft, length_ft in annulus_sections:
        section_top_ft = section_bottom_ft + length_ft
        if start_ft < section_top_ft:
            volume_bbl += (section_top_ft - max(start_ft, section_bottom_ft)) * capacity_bbl_per_ft
        section_bottom_ft = section_top_ft
    return volume_bbl


def influx_height(pit_gain_bbl, annulus_sections):
    """Height of the influx (whole ft) at the bit.

        Height = Pit gain / Annular capacity

    If the influx is taller than the bottom section, the rest goes into the
    next section up, and so on.
    """
    height_ft = gas_column_height(0, pit_gain_bbl, annulus_sections)
    if height_ft is None:
        raise ValueError(f"A pit gain of {pit_gain_bbl} bbl is more than the whole annulus volume")
    return round_to_whole_number(height_ft)


def influx_gradient(sidpp_psi, sicp_psi, mud_gradient_psi_per_ft, influx_height_ft):
    """Influx gradient (psi/ft) from the shut-in gauges, and a warning (or None).

        Gradient = Mud gradient - (SICP - SIDPP) / Influx height

    If the answer is 0 or less, or as heavy as the mud, the gauges don't make
    sense: 0.1 psi/ft is used instead, with a warning. Above 0.25 psi/ft the
    influx is probably liquid, not gas - it is used, with a warning.
    """
    gradient = round_to_4_places(
        mud_gradient_psi_per_ft - round_to_4_places((sicp_psi - sidpp_psi) / influx_height_ft))
    if gradient <= 0 or gradient >= mud_gradient_psi_per_ft:
        return FALLBACK_GAS_GRADIENT_PSI_PER_FT, (
            f"WARNING: influx gradient from the gauges is {gradient:.4f} psi/ft - the gauges are "
            "inconsistent (bad gauges, or the influx isn't at the bottom). "
            f"Using {FALLBACK_GAS_GRADIENT_PSI_PER_FT} psi/ft.")
    if gradient > NOT_GAS_ABOVE_PSI_PER_FT:
        return gradient, (
            f"WARNING: influx gradient {gradient:.4f} psi/ft. Influx gradient suggests liquid, not gas. "
            "The plot assumes an expanding gas bubble, so casing and shoe peaks are overstated "
            "(conservative).")
    return gradient, None


def gas_influx(pit_gain_bbl, sidpp_psi, sicp_psi, mud_gradient_psi_per_ft, bit_tvd_ft, annulus_sections):
    """The gas bubble at shut-in, and a warning (or None).

        Formation pressure = SIDPP + Mud gradient x Bit TVD
        Top pressure       = Formation pressure - Gas gradient x Height
    """
    height_ft = influx_height(pit_gain_bbl, annulus_sections)
    gradient, warning = influx_gradient(sidpp_psi, sicp_psi, mud_gradient_psi_per_ft, height_ft)
    formation_psi = formation_pressure(sidpp_psi, mud_gradient_psi_per_ft, bit_tvd_ft)
    return GasInflux(pit_gain_bbl, height_ft, gradient, formation_psi - gradient * height_ft), warning


def formation_pressure(sidpp_psi, mud_gradient_psi_per_ft, bit_tvd_ft):
    """Formation pressure (psi), whole psi.

        Formation pressure = SIDPP + Mud gradient x Bit TVD
    """
    return sidpp_psi + round_to_whole_number(mud_gradient_psi_per_ft * bit_tvd_ft)


# --- What is in the annulus ----------------------------------------------------

def _mud_layers(top_ft, bottom_ft, kill_mud_top_ft, well):
    """Mud between two depths as (top, bottom, gradient): kill mud below kill_mud_top_ft."""
    layers = []
    if top_ft < min(bottom_ft, kill_mud_top_ft):
        layers.append((top_ft, min(bottom_ft, kill_mud_top_ft), well.mud_gradient_psi_per_ft))
    if max(top_ft, kill_mud_top_ft) < bottom_ft:
        layers.append((max(top_ft, kill_mud_top_ft), bottom_ft, well.kill_mud_gradient_psi_per_ft))
    return layers


def _hydrostatic(layers, down_to_ft):
    """Hydrostatic (psi, not rounded) of the layers from surface down to a depth."""
    return sum((min(bottom, down_to_ft) - top) * gradient
               for top, bottom, gradient in layers if top < down_to_ft)


def annulus_forecast(strokes, bhp_psi, well, gas=None, kill_mud_at_bit_strokes=None):
    """Forecast casing and shoe pressure after a number of strokes (vertical well).

    bhp_psi: held constant (formation pressure + safety margin).
    gas:     the GasInflux at shut-in, or None if there's no gas (2nd circulation).
    kill_mud_at_bit_strokes: strokes when kill mud reaches the bit, or None for
             original mud only (Driller's 1st circulation).

        Bottom of gas = annulus volume pumped (Strokes x Pump output) above the bit
        Top pressure  = BHP - mud below the gas - gas gradient x gas height
        Gas volume    = Volume at shut-in x Top pressure at shut-in / Top pressure
        Gas gradient  = Gradient at shut-in x Top pressure / Top pressure at shut-in
        Casing        = BHP - hydrostatic of mud, gas and kill mud in the annulus
        Shoe          = Casing + hydrostatic from surface to the shoe

    The top of the gas depends on its volume, which depends on its pressure,
    so the top is found by repeating the calculation until it stops moving.
    Once the gas reaches surface it is being produced: the top stays at
    surface and the gas left is the annulus volume above the bottom of the gas.
    The bottom of the gas and the kill mud front move with the ROUNDED section
    volumes (like the strokes); the gas column itself uses the capacity.
    """
    sections = well.annulus_sections
    bit_ft = total_length(sections)
    annulus_bbl = total_volume(sections)
    pumped_bbl = round_to_tenth(strokes * well.pump_output_bbl_per_stk)

    kill_mud_top_ft = bit_ft
    if kill_mud_at_bit_strokes is not None and strokes > kill_mud_at_bit_strokes:
        kill_mud_bbl = round_to_tenth((strokes - kill_mud_at_bit_strokes) * well.pump_output_bbl_per_stk)
        kill_mud_top_ft = round_to_whole_number(bit_ft - height_above_bit(kill_mud_bbl, sections))

    if gas is None or pumped_bbl >= annulus_bbl:
        layers = _mud_layers(0, bit_ft, kill_mud_top_ft, well)
        top_ft = bottom_ft = volume_bbl = None
    else:
        bottom_ft = round_to_whole_number(bit_ft - height_above_bit(pumped_bbl, sections))
        below_psi = _hydrostatic(_mud_layers(bottom_ft, bit_ft, kill_mud_top_ft, well), bit_ft)
        top_ft = round_to_whole_number(bottom_ft - gas.height_ft)
        gradient = gas.gradient_psi_per_ft
        for _ in range(50):
            top_pressure_psi = bhp_psi - below_psi - gradient * (bottom_ft - top_ft)
            volume_bbl = gas.volume_bbl * gas.top_pressure_psi / top_pressure_psi
            gradient = gas.gradient_psi_per_ft * top_pressure_psi / gas.top_pressure_psi
            height_ft = gas_column_height(bit_ft - bottom_ft, volume_bbl, sections)
            if height_ft is None:
                new_top_ft = 0                     # gas at surface, being produced
                volume_bbl = annulus_volume_above(bit_ft - bottom_ft, sections)
            else:
                new_top_ft = round_to_whole_number(bottom_ft - height_ft)
            if new_top_ft == top_ft:
                break
            top_ft = new_top_ft
        volume_bbl = round_to_tenth(volume_bbl)
        layers = (_mud_layers(0, top_ft, kill_mud_top_ft, well)
                  + [(top_ft, bottom_ft, gradient)]
                  + _mud_layers(bottom_ft, bit_ft, kill_mud_top_ft, well))

    casing_psi = bhp_psi - _hydrostatic(layers, bit_ft)
    shoe_psi = casing_psi + _hydrostatic(layers, well.shoe_tvd_ft)
    # A gauge can't read below 0: an overbalanced annulus reads 0 psi.
    return AnnulusForecast(strokes, max(0, round_to_whole_number(casing_psi)),
                           round_to_whole_number(shoe_psi), top_ft, bottom_ft, volume_bbl)


# --- Checks --------------------------------------------------------------------

def fracture_at_shoe(mamw_ppg, shoe_tvd_ft):
    """Fracture pressure at the shoe (psi), rounded DOWN (a maximum, rule 2).

        Fracture pressure = 0.052 x MAMW x Shoe TVD
    """
    return round_down_to_whole_number(0.052 * mamw_ppg * shoe_tvd_ft)


def trapped_pressure(sidpp_psi, safety_margin_psi, mud_gradient_psi_per_ft,
                     kill_mud_gradient_psi_per_ft, bit_tvd_ft):
    """Drill pipe pressure (psi) at the final shut-in, kill mud to surface.

        Trapped = SIDPP + SF - (KMW gradient - OMW gradient) x Bit TVD

    The casing must read the same. A gauge can't read below 0.
    """
    overbalance_psi = (kill_mud_gradient_psi_per_ft - mud_gradient_psi_per_ft) * bit_tvd_ft
    return max(0, round_to_whole_number(sidpp_psi + safety_margin_psi - overbalance_psi))


def trapped_pressures_match(drill_pipe_psi, casing_psi):
    """True if both gauges read the same trapped pressure (+/- 10 psi)."""
    return abs(drill_pipe_psi - casing_psi) <= GAUGE_TOLERANCE_PSI


def plot_warnings(peak, max_shoe, fracture_psi, maasp_psi, trapped_dp_psi, trapped_casing_psi):
    """Warnings for the peak casing pressure, the shoe and the trapped pressures."""
    warnings = []
    if max_shoe.shoe_psi > fracture_psi:
        warnings.append(f"WARNING: forecast shoe pressure {max_shoe.shoe_psi:,} psi at "
                        f"{max_shoe.strokes:,} strokes is ABOVE the fracture pressure {fracture_psi:,} psi.")
    if peak.casing_psi > maasp_psi:
        warnings.append(f"Peak casing {peak.casing_psi:,} psi at {peak.strokes:,} strokes is above MAASP "
                        f"{maasp_psi:,} psi. MAASP assumes mud below the shoe; with gas above the shoe "
                        f"the shoe pressure ({max_shoe.shoe_psi:,} psi max vs fracture {fracture_psi:,}) "
                        "is the real check.")
    if not trapped_pressures_match(trapped_dp_psi, trapped_casing_psi):
        warnings.append(f"WARNING: trapped pressures don't match (drill pipe {trapped_dp_psi:,}, "
                        f"casing {trapped_casing_psi:,} psi) - something is wrong.")
    return warnings


# --- The plots -----------------------------------------------------------------

def _forecasts(first_stroke, last_stroke, bhp_psi, well, gas, kill_mud_at_bit_strokes):
    """Annulus forecast for every stroke from first to last."""
    return [annulus_forecast(s, bhp_psi, well, gas, kill_mud_at_bit_strokes)
            for s in range(first_stroke, last_stroke + 1)]


def _events(forecasts, shoe_tvd_ft):
    """Strokes where the gas does something worth a row: {strokes: label}."""
    events = {}
    for before, after in zip(forecasts, forecasts[1:]):
        if before.gas_top_ft is not None and after.gas_top_ft is not None:
            if before.gas_top_ft > shoe_tvd_ft >= after.gas_top_ft:
                events[after.strokes] = "top of gas at the shoe"
            if before.gas_top_ft > 0 and after.gas_top_ft == 0:
                events[after.strokes] = "gas at surface"
        if before.gas_top_ft is not None and after.gas_top_ft is None:
            events[after.strokes] = "gas out"
    return events


def _stroke_marks(last_stroke, step_strokes):
    return list(range(step_strokes, last_stroke, step_strokes))


def drillers_kill_plot(sidpp_psi, sicp_psi, icp_psi, fcp_psi, safety_margin_psi, pit_gain_bbl,
                       original_mud_weight_ppg, kill_mud_weight_ppg, bit_tvd_ft, shoe_tvd_ft,
                       mamw_ppg, maasp_psi, drill_string_sections, annulus_sections,
                       pump_output_bbl_per_stk, surface_line_volume_bbl=0, step_strokes=100):
    """Kill plot for Driller's method, vertical well. Strokes run on through
    both circulations (the 2nd starts where the 1st ended).

    1st circulation: drill pipe held at ICP + SF; casing from the gas model.
    2nd circulation: casing held at SIDPP + SF while kill mud goes to the bit
    (drill pipe falls ICP + SF -> FCP + SF), then drill pipe held at FCP + SF
    while casing falls to the trapped pressure.
    annulus_sections: ALL of the annulus, listed from the bit UP.
    """
    sf = safety_margin_psi
    well = AnnulusWell(annulus_sections, shoe_tvd_ft, pump_output_bbl_per_stk,
                       mud_gradient(original_mud_weight_ppg), mud_gradient(kill_mud_weight_ppg))
    gas, gas_warning = gas_influx(pit_gain_bbl, sidpp_psi, sicp_psi, well.mud_gradient_psi_per_ft,
                                  bit_tvd_ft, annulus_sections)
    bhp_psi = formation_pressure(sidpp_psi, well.mud_gradient_psi_per_ft, bit_tvd_ft) + sf
    bottoms_up = strokes_for_volume(total_volume(annulus_sections), pump_output_bbl_per_stk)
    to_bit = surface_to_bit_strokes(drill_string_sections, pump_output_bbl_per_stk, surface_line_volume_bbl)

    # 1st circulation - original mud, gas out.
    first = _forecasts(0, bottoms_up, bhp_psi, well, gas, None)
    start_shoe = sicp_psi + sf + round_to_whole_number(well.mud_gradient_psi_per_ft * shoe_tvd_ft)
    first[0] = first[0]._replace(casing_psi=sicp_psi + sf, shoe_psi=start_shoe)  # the value held
    events = _events(first, shoe_tvd_ft)
    peak = max(first, key=lambda f: f.casing_psi)
    events.setdefault(peak.strokes, "peak casing")
    points = [
        PlotPoint(0, sidpp_psi, sicp_psi, pit_gain_bbl, "shut in"),
        PlotPoint(0, sidpp_psi + sf, sicp_psi + sf, first[0].gas_volume_bbl,
                  "start-up: casing held at SICP + SF"),
        PlotPoint(0, icp_psi + sf, sicp_psi + sf, first[0].gas_volume_bbl,
                  "at kill rate: swap to drill pipe, hold ICP + SF"),
    ]
    for s in sorted(set(_stroke_marks(bottoms_up, step_strokes)) | set(events)):
        f = first[s]
        points.append(PlotPoint(s, icp_psi + sf, f.casing_psi, f.gas_volume_bbl, events.get(s, "")))
    points.append(PlotPoint(bottoms_up, sidpp_psi + sf, first[bottoms_up].casing_psi, None,
                            "shut in: both read SIDPP + SF"))

    # 2nd circulation - kill mud. Strokes counted from its own start, then offset.
    second = _forecasts(0, to_bit + bottoms_up, bhp_psi, well, None, to_bit)
    offset = bottoms_up
    points.append(PlotPoint(offset, icp_psi + sf, sidpp_psi + sf, None,
                            "2nd circulation start-up: casing held at SIDPP + SF"))
    for row in pressure_schedule(icp_psi, fcp_psi, drill_string_sections, pump_output_bbl_per_stk,
                                 surface_line_volume_bbl):
        if row.strokes > 0:
            label = "kill mud at the bit" if row.strokes == to_bit else row.label
            points.append(PlotPoint(offset + row.strokes, row.pressure_psi + sf,
                                    second[row.strokes].casing_psi, None, label))
    for s in _stroke_marks(to_bit + bottoms_up, step_strokes):
        if s > to_bit:
            points.append(PlotPoint(offset + s, fcp_psi + sf, second[s].casing_psi, None, ""))
    trapped_dp = trapped_pressure(sidpp_psi, sf, well.mud_gradient_psi_per_ft,
                                  well.kill_mud_gradient_psi_per_ft, bit_tvd_ft)
    trapped_casing = second[-1].casing_psi
    end = offset + to_bit + bottoms_up
    points.append(PlotPoint(end, fcp_psi + sf, trapped_casing, None, "kill mud at surface"))
    points.append(PlotPoint(end, trapped_dp, trapped_casing, None,
                            "shut in: both read the trapped pressure - bleed to 0, check, flow check"))

    max_shoe = max(first + [s._replace(strokes=offset + s.strokes) for s in second],
                   key=lambda f: f.shoe_psi)
    fracture_psi = fracture_at_shoe(mamw_ppg, shoe_tvd_ft)
    warnings = ([gas_warning] if gas_warning else []) + plot_warnings(
        peak, max_shoe, fracture_psi, maasp_psi, trapped_dp, trapped_casing)
    return KillPlot(points, peak, max_shoe, fracture_psi, trapped_dp, trapped_casing, warnings)


def wait_and_weight_kill_plot(sidpp_psi, sicp_psi, icp_psi, fcp_psi, safety_margin_psi, pit_gain_bbl,
                              original_mud_weight_ppg, kill_mud_weight_ppg, bit_tvd_ft, shoe_tvd_ft,
                              mamw_ppg, maasp_psi, drill_string_sections, annulus_sections,
                              pump_output_bbl_per_stk, surface_line_volume_bbl=0, step_strokes=100):
    """Kill plot for Wait and Weight, vertical well. One circulation:
    from the first stroke kill mud goes down the drill pipe while the gas and
    original mud come up the annulus.

    Drill pipe: step-down chart + SF until kill mud is at the bit, then FCP + SF.
    Casing:     gas model, with kill mud filling the annulus from the bit up.
    sidpp_psi and sicp_psi are the values RETAKEN just before start-up.
    annulus_sections: ALL of the annulus, listed from the bit UP.
    """
    sf = safety_margin_psi
    well = AnnulusWell(annulus_sections, shoe_tvd_ft, pump_output_bbl_per_stk,
                       mud_gradient(original_mud_weight_ppg), mud_gradient(kill_mud_weight_ppg))
    gas, gas_warning = gas_influx(pit_gain_bbl, sidpp_psi, sicp_psi, well.mud_gradient_psi_per_ft,
                                  bit_tvd_ft, annulus_sections)
    bhp_psi = formation_pressure(sidpp_psi, well.mud_gradient_psi_per_ft, bit_tvd_ft) + sf
    bottoms_up = strokes_for_volume(total_volume(annulus_sections), pump_output_bbl_per_stk)
    to_bit = surface_to_bit_strokes(drill_string_sections, pump_output_bbl_per_stk, surface_line_volume_bbl)
    end = to_bit + bottoms_up
    bit_md_ft = total_length(drill_string_sections)

    def drill_pipe_at(strokes):
        """Step-down chart + SF until kill mud is at the bit, then FCP + SF."""
        if strokes >= to_bit:
            return fcp_psi + sf
        md_ft = md_after_strokes(strokes, drill_string_sections, pump_output_bbl_per_stk,
                                 surface_line_volume_bbl)
        return drill_pipe_pressure(icp_psi, fcp_psi, sidpp_psi, md_ft, md_ft, bit_md_ft, bit_md_ft) + sf

    forecasts = _forecasts(0, end, bhp_psi, well, gas, to_bit)
    start_shoe = sicp_psi + sf + round_to_whole_number(well.mud_gradient_psi_per_ft * shoe_tvd_ft)
    forecasts[0] = forecasts[0]._replace(casing_psi=sicp_psi + sf, shoe_psi=start_shoe)
    events = _events(forecasts, shoe_tvd_ft)
    peak = max(forecasts, key=lambda f: f.casing_psi)
    events.setdefault(peak.strokes, "peak casing")
    for row in pressure_schedule(icp_psi, fcp_psi, drill_string_sections, pump_output_bbl_per_stk,
                                 surface_line_volume_bbl):
        if row.strokes > 0:
            events.setdefault(row.strokes, "kill mud at the bit" if row.strokes == to_bit else row.label)

    points = [
        PlotPoint(0, sidpp_psi, sicp_psi, pit_gain_bbl, "shut in"),
        PlotPoint(0, sidpp_psi + sf, sicp_psi + sf, forecasts[0].gas_volume_bbl,
                  "start-up: casing held at SICP + SF"),
        PlotPoint(0, icp_psi + sf, sicp_psi + sf, forecasts[0].gas_volume_bbl,
                  "at kill rate: swap to drill pipe, follow the step-down chart + SF"),
    ]
    for s in sorted(set(_stroke_marks(end, step_strokes)) | set(events)):
        f = forecasts[s]
        points.append(PlotPoint(s, drill_pipe_at(s), f.casing_psi, f.gas_volume_bbl, events.get(s, "")))
    trapped_dp = trapped_pressure(sidpp_psi, sf, well.mud_gradient_psi_per_ft,
                                  well.kill_mud_gradient_psi_per_ft, bit_tvd_ft)
    trapped_casing = forecasts[end].casing_psi
    points.append(PlotPoint(end, fcp_psi + sf, trapped_casing, None, "kill mud at surface"))
    points.append(PlotPoint(end, trapped_dp, trapped_casing, None,
                            "shut in: both read the trapped pressure - bleed to 0, check, flow check"))

    max_shoe = max(forecasts, key=lambda f: f.shoe_psi)
    fracture_psi = fracture_at_shoe(mamw_ppg, shoe_tvd_ft)
    warnings = ([gas_warning] if gas_warning else []) + plot_warnings(
        peak, max_shoe, fracture_psi, maasp_psi, trapped_dp, trapped_casing)
    return KillPlot(points, peak, max_shoe, fracture_psi, trapped_dp, trapped_casing, warnings)
