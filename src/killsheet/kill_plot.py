"""Kill plot: forecast drill pipe AND casing pressure against strokes.

Vertical, deviated and horizontal wells (untapered or tapered string), surface
BOP stack, Driller's method and Wait and Weight. The web page only draws these
numbers.

Deviated and horizontal wells: POSITION along the hole uses MD (the gas and the
kill mud move with the volume pumped), PRESSURE uses TVD (hydrostatic = gradient
x TVD height). Gas lying in a lateral has no vertical height: its pressure
doesn't change, it doesn't expand, and the casing stays flat until the gas
reaches the build.

Constant bottomhole pressure with a SAFETY MARGIN (SF, chosen by the team):
  Shut in:    drill pipe reads SIDPP, casing reads SICP.
  Start-up:   casing is raised to SICP + SF; through the U-tube the drill pipe
              rises to SIDPP + SF. The pump is brought up holding casing at
              SICP + SF. At kill rate the drill pipe reads ICP + SF and the
              choke operator swaps to the drill pipe gauge.
  Driller's:  BHP = formation pressure + SF for the whole kill. In the 2nd
              circulation the drill pipe falls to FCP + SIDPP + SF - kill mud
              overbalance (871 psi on the baseline, not FCP + SF = 879) and is
              held there. If the SF is smaller than the kill mud's extra
              overbalance, casing reaches 0 (choke fully open) and from then on
              BHP and the drill pipe rise a little (toward FCP).
  W&W:        the step-down chart uses SIDPP, but the kill mud (KMW rounded UP)
              adds a little more than SIDPP. BHP is worked back from the
              scheduled drill pipe pressure at every stroke:
                  BHP = Formation pressure + Scheduled DP - SIDPP
                        + Kill mud hydrostatic gain - Friction
              It ends at formation pressure + SF + (overbalance - SIDPP).
  End:        both gauges read the same TRAPPED pressure (Driller's:
              SIDPP + SF - overbalance; W&W: SF). If they don't match, something
              is wrong. Bleed it off in small steps through the choke, check 0
              (+/- 10 psi), then flow check. Pressure building back = not dead.

Single-bubble gas model (forecasts the casing line while gas is in the annulus):
  - The influx is one bubble at the bit; its volume is the PIT GAIN.
  - Its gradient comes from the gauges:
        Height   = Pit gain / annulus capacity at the bit (whole ft MD)
        Gradient = Mud gradient - (SICP - SIDPP) / TVD height of the influx
    An influx in the lateral (TVD height 0) can't give a gradient: 0.1 psi/ft
    is assumed (conservative), and SICP must read SIDPP (+/- 10 psi) or the
    casing forecast does not apply.
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

from functools import lru_cache
from typing import NamedTuple

from killsheet import drillers
from killsheet import wait_and_weight
from killsheet.depths import tvd_at_md
from killsheet.formulas import kill_mud_overbalance
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
# Below this the gauges don't describe real gas (psi/ft).
NOT_PHYSICAL_BELOW_PSI_PER_FT = 0.05

LATERAL_NOTE = ("Influx in the lateral: gas gradient 0.1 psi/ft assumed (can't be read from the gauges; "
                "conservative, over-predicts casing and shoe pressure).")

MODEL_LIMITS = (
    "Single-bubble gas model: ignores temperature, gas compressibility (Z), "
    "dispersion and slip. NOT valid in oil-based mud (gas dissolves). "
    "It usually over-predicts the peak casing pressure (errs on the safe side)."
)


class GasInflux(NamedTuple):
    """The gas bubble at shut-in."""

    volume_bbl: float              # the pit gain
    height_ft: int                 # MD
    gradient_psi_per_ft: float
    top_pressure_psi: float        # pressure at the top of the bubble at shut-in
    height_tvd_ft: int | None = None


class AnnulusWell(NamedTuple):
    """What the gas model needs to know about the annulus.

    Depths in the model are MD from surface; survey turns them into TVD for
    pressures. Vertical well: leave survey empty (TVD = MD) and shoe_md_ft None.
    """

    annulus_sections: list         # (capacity bbl/ft, length ft MD), listed from the bit UP
    shoe_tvd_ft: int
    pump_output_bbl_per_stk: float
    mud_gradient_psi_per_ft: float
    kill_mud_gradient_psi_per_ft: float
    survey: tuple = ()             # (MD, TVD) points: key points, shoe, bit
    shoe_md_ft: int | None = None


def _tvd(md_ft, well):
    """TVD (whole ft) at an MD of the well - the MD itself in a vertical well.

    A trial depth above surface (while the top of the gas is being found) is
    treated as vertical, as the top of every well is.
    """
    return _tvd_on_path(md_ft, well.survey) if well.survey and md_ft >= 0 else md_ft


@lru_cache(maxsize=100_000)
def _tvd_on_path(md_ft, survey):
    """tvd_at_md, remembered: the model asks for the same depths thousands of times."""
    return tvd_at_md(md_ft, survey)


def _shoe_md(well):
    return well.shoe_tvd_ft if well.shoe_md_ft is None else well.shoe_md_ft


class AnnulusForecast(NamedTuple):
    """Forecast casing and shoe pressure after a number of strokes."""

    strokes: int
    casing_psi: int
    shoe_psi: int
    gas_top_ft: int | None         # None once the gas is out
    gas_bottom_ft: int | None
    gas_volume_bbl: float | None   # = pit gain while all the gas is in the well
    bhp_psi: int                   # actual BHP: above the BHP held if casing would read below 0


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
    casing_forecast_valid: bool = True    # False: don't draw the casing line - drill pipe only
    notes: tuple = ()                     # information, not warnings (e.g. the lateral gradient)


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
    for (_capacity, length_ft), section_bbl in zip(annulus_sections, _section_volumes(tuple(annulus_sections))):
        if volume_bbl <= section_bbl:
            return height_ft + length_ft * volume_bbl / section_bbl
        volume_bbl -= section_bbl
        height_ft += length_ft
    return height_ft


@lru_cache(maxsize=64)
def _section_volumes(annulus_sections):
    """Each section's rounded volume - worked out once per well, not once per stroke."""
    return tuple(section_volume(capacity_bbl_per_ft, length_ft) for capacity_bbl_per_ft, length_ft in annulus_sections)


@lru_cache(maxsize=64)
def _annulus_volume(annulus_sections):
    return total_volume(annulus_sections)


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
    influx is probably liquid, not gas; below 0.05 psi/ft it isn't physical -
    either way it is used, with a warning.
    """
    gradient = round_to_4_places(
        mud_gradient_psi_per_ft - round_to_4_places((sicp_psi - sidpp_psi) / influx_height_ft))
    if gradient <= 0 or gradient >= mud_gradient_psi_per_ft:
        return FALLBACK_GAS_GRADIENT_PSI_PER_FT, (
            f"WARNING: influx gradient from the gauges is {gradient:.4f} psi/ft - the gauges are "
            "inconsistent (bad gauges, or the influx isn't at the bottom). "
            f"Using {FALLBACK_GAS_GRADIENT_PSI_PER_FT} psi/ft.")
    if gradient < NOT_PHYSICAL_BELOW_PSI_PER_FT:
        return gradient, (
            f"WARNING: influx gradient {gradient:.4f} psi/ft. Influx gradient below 0.05 psi/ft is not "
            "physical. Check SICP/SIDPP and the influx volume.")
    if gradient > NOT_GAS_ABOVE_PSI_PER_FT:
        return gradient, (
            f"WARNING: influx gradient {gradient:.4f} psi/ft. Influx gradient suggests liquid, not gas. "
            "The plot assumes an expanding gas bubble, so casing and shoe peaks are overstated "
            "(conservative).")
    return gradient, None


def gas_influx(pit_gain_bbl, sidpp_psi, sicp_psi, mud_gradient_psi_per_ft, bit_tvd_ft, annulus_sections,
               bit_md_ft=None, survey=()):
    """The gas bubble at shut-in, and a warning (or None).

        TVD height         = Bit TVD - TVD at (Bit MD - MD height)
        Formation pressure = SIDPP + Mud gradient x Bit TVD
        Top pressure       = Formation pressure - Gas gradient x TVD height

    In the lateral (TVD height 0) the gradient is assumed, not read from the
    gauges: see influx_in_the_lateral().
    """
    height_ft = influx_height(pit_gain_bbl, annulus_sections)
    bit_md_ft = bit_tvd_ft if bit_md_ft is None else bit_md_ft
    height_tvd_ft = bit_tvd_ft - (tvd_at_md(bit_md_ft - height_ft, survey) if survey else bit_md_ft - height_ft)
    if height_tvd_ft == 0:
        gradient, warning = FALLBACK_GAS_GRADIENT_PSI_PER_FT, None
    else:
        gradient, warning = influx_gradient(sidpp_psi, sicp_psi, mud_gradient_psi_per_ft, height_tvd_ft)
    formation_psi = formation_pressure(sidpp_psi, mud_gradient_psi_per_ft, bit_tvd_ft)
    return GasInflux(pit_gain_bbl, height_ft, gradient, formation_psi - gradient * height_tvd_ft,
                     height_tvd_ft), warning


def lateral_gauge_warning(sidpp_psi, sicp_psi):
    """With the influx in the lateral SICP must read SIDPP (+/- 10 psi), or the
    casing forecast does not apply. Returns the warning, or None."""
    if sicp_psi - sidpp_psi <= GAUGE_TOLERANCE_PSI:
        return None
    return (f"With the influx in the lateral, SICP should read the same as SIDPP (+/-{GAUGE_TOLERANCE_PSI} psi). "
            f"SICP is {sicp_psi - sidpp_psi:,} psi higher. Possible causes: gas already in the build (partly "
            "circulated before shut-in, or migrated), toe-up or undulating lateral, trapped pressure, or a "
            "gauge error. The casing forecast below assumes zero influx height and does not apply. "
            "Use the drill pipe schedule only.")


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


def _hydrostatic(layers, down_to_ft, well):
    """Hydrostatic (psi, not rounded) of the layers from surface down to an MD.

        Hydrostatic = sum of Gradient x TVD height of each layer
    """
    return sum((_tvd(min(bottom, down_to_ft), well) - _tvd(top, well)) * gradient
               for top, bottom, gradient in layers if top < down_to_ft)


def annulus_forecast(strokes, bhp_psi, well, gas=None, kill_mud_at_bit_strokes=None):
    """Forecast casing and shoe pressure after a number of strokes.

    bhp_psi: the BHP being held (formation pressure + safety margin).
    gas:     the GasInflux at shut-in, or None if there's no gas (2nd circulation).
    kill_mud_at_bit_strokes: strokes when kill mud reaches the bit, or None for
             original mud only (Driller's 1st circulation).

        Bottom of gas = annulus volume pumped (Strokes x Pump output) above the bit
        Top pressure  = BHP - mud below the gas - gas gradient x gas TVD height
        Gas volume    = Volume at shut-in x Top pressure at shut-in / Top pressure
        Gas gradient  = Gradient at shut-in x Top pressure / Top pressure at shut-in
        Casing        = BHP - hydrostatic of mud, gas and kill mud in the annulus
        Shoe          = Casing + hydrostatic from surface to the shoe

    Depths are MD; every hydrostatic uses the TVD height. The top of the gas
    depends on its volume, which depends on its pressure, so the top is found
    by repeating the calculation until it stops moving.
    Once the gas reaches surface it is being produced: the top stays at
    surface and the gas left is the annulus volume above the bottom of the gas.
    The bottom of the gas and the kill mud front move with the ROUNDED section
    volumes (like the strokes); the gas column itself uses the capacity.
    """
    sections = well.annulus_sections
    bit_ft = total_length(sections)
    annulus_bbl = _annulus_volume(tuple(sections))
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
        below_psi = _hydrostatic(_mud_layers(bottom_ft, bit_ft, kill_mud_top_ft, well), bit_ft, well)
        top_ft = round_to_whole_number(bottom_ft - gas.height_ft)
        gradient = gas.gradient_psi_per_ft
        for _ in range(50):
            top_pressure_psi = bhp_psi - below_psi - gradient * (_tvd(bottom_ft, well) - _tvd(top_ft, well))
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

    annulus_psi = _hydrostatic(layers, bit_ft, well)
    # A gauge can't read below 0: an overbalanced annulus reads 0 psi with the
    # choke fully open, and BHP is then the annulus hydrostatic (above bhp_psi).
    casing_psi = max(0, bhp_psi - annulus_psi)
    shoe_psi = casing_psi + _hydrostatic(layers, _shoe_md(well), well)
    return AnnulusForecast(strokes, round_to_whole_number(casing_psi), round_to_whole_number(shoe_psi),
                           top_ft, bottom_ft, volume_bbl, round_to_whole_number(casing_psi + annulus_psi))


# --- Checks --------------------------------------------------------------------

def fracture_at_shoe(mamw_ppg, shoe_tvd_ft):
    """Fracture pressure at the shoe (psi), rounded DOWN (a maximum, rule 2).

        Fracture pressure = 0.052 x MAMW x Shoe TVD
    """
    return round_down_to_whole_number(0.052 * mamw_ppg * shoe_tvd_ft)


def trapped_pressures_match(drill_pipe_psi, casing_psi):
    """True if both gauges read the same trapped pressure (+/- 10 psi)."""
    return abs(drill_pipe_psi - casing_psi) <= GAUGE_TOLERANCE_PSI


def plot_warnings(peak, max_shoe, fracture_psi, maasp_psi, trapped_dp_psi, trapped_casing_psi, shoe_md_ft=None):
    """Warnings for the peak casing pressure, the shoe and the trapped pressures.

    Peak casing above MAASP with the gas above the shoe is NOT a shoe exceedance:
    MAASP assumes mud from the shoe to surface. The shoe limit is the max shoe line.
    """
    warnings = []
    if max_shoe.shoe_psi > fracture_psi:
        warnings.append(f"WARNING: forecast shoe pressure {max_shoe.shoe_psi:,} psi at "
                        f"{max_shoe.strokes:,} strokes is ABOVE the fracture pressure {fracture_psi:,} psi.")
    if peak.casing_psi > maasp_psi:
        above = f"Peak casing {peak.casing_psi:,} psi at {peak.strokes:,} strokes is above MAASP {maasp_psi:,} psi"
        shoe = f"{max_shoe.shoe_psi:,} psi max vs fracture {fracture_psi:,} psi"
        gas_below_shoe = (shoe_md_ft is not None and peak.gas_top_ft is not None
                          and peak.gas_top_ft >= shoe_md_ft)
        if gas_below_shoe:
            warnings.append(f"WARNING: {above} with the gas still below the shoe - the shoe is at risk. "
                            f"Check the max shoe pressure ({shoe}).")
        else:
            warnings.append(f"{above}, with the gas above the shoe. This is NOT a shoe exceedance: MAASP "
                            "assumes mud from the shoe to surface. The shoe limit is the max shoe pressure "
                            f"({shoe}).")
    if not trapped_pressures_match(trapped_dp_psi, trapped_casing_psi):
        warnings.append(f"WARNING: trapped pressures don't match (drill pipe {trapped_dp_psi:,}, "
                        f"casing {trapped_casing_psi:,} psi) - something is wrong.")
    return warnings


# --- The plots -----------------------------------------------------------------

def _forecasts(first_stroke, last_stroke, bhp_psi, well, gas, kill_mud_at_bit_strokes):
    """Annulus forecast for every stroke from first to last.

    bhp_psi: a number (held constant) or a function of the strokes.
    """
    bhp_at = bhp_psi if callable(bhp_psi) else (lambda _strokes: bhp_psi)
    return [annulus_forecast(s, bhp_at(s), well, gas, kill_mud_at_bit_strokes)
            for s in range(first_stroke, last_stroke + 1)]


def _friction(scr_psi, kill_mud_friction_psi, kill_mud_md_ft, bit_md_ft):
    """Drill string friction (psi, not rounded) with kill mud down to an MD.

        Friction = SCR + (Kill mud friction - SCR) x (MD of kill mud / Bit MD)
    """
    return scr_psi + (kill_mud_friction_psi - scr_psi) * kill_mud_md_ft / bit_md_ft


def _hydrostatic_gain(overbalance_psi, kill_mud_tvd_ft, bit_tvd_ft):
    """Extra hydrostatic (psi, not rounded) of kill mud down to a TVD.

        Gain = Kill mud overbalance x (TVD of kill mud / Bit TVD)
    """
    return overbalance_psi * kill_mud_tvd_ft / bit_tvd_ft


def _events(forecasts, shoe_md_ft, heel_md_ft=None):
    """Strokes where the gas does something worth a row: {strokes: label}.

    heel_md_ft: start of the lateral (horizontal well), or None.
    """
    events = {}

    def add(strokes, label):
        events[strokes] = f"{events[strokes]} / {label}" if strokes in events else label

    for before, after in zip(forecasts, forecasts[1:]):
        if before.gas_top_ft is not None and after.gas_top_ft is not None:
            if heel_md_ft is not None and before.gas_top_ft > heel_md_ft >= after.gas_top_ft:
                add(after.strokes, "top of gas leaves the lateral - casing starts to rise")
            if before.gas_top_ft > shoe_md_ft >= after.gas_top_ft:
                add(after.strokes, "top of gas at the shoe")
            if before.gas_top_ft > 0 and after.gas_top_ft == 0:
                add(after.strokes, "gas at surface")
        if before.gas_top_ft is not None and after.gas_top_ft is None:
            add(after.strokes, "gas out")
    return events


def _survey(bit_md_ft, bit_tvd_ft, shoe_md_ft, shoe_tvd_ft, key_points):
    """(MD, TVD) points of the well path, or () for a vertical well."""
    if bit_md_ft == bit_tvd_ft and shoe_md_ft == shoe_tvd_ft and not key_points:
        return ()
    return tuple([(md, tvd) for _name, md, tvd in key_points] + [(shoe_md_ft, shoe_tvd_ft), (bit_md_ft, bit_tvd_ft)])


def _heel_md(survey, bit_md_ft, bit_tvd_ft):
    """MD where the lateral starts (shallowest point at bit TVD), or None if the bit isn't in a lateral."""
    flat = [md for md, tvd in survey if tvd == bit_tvd_ft and md < bit_md_ft]
    return min(flat) if flat else None


def _start(well, gas, sidpp_psi, sicp_psi, gas_warning, survey, bit_md_ft, bit_tvd_ft):
    """Shared set-up: notes, warnings, and whether the casing forecast applies."""
    notes, warnings, valid = [], [gas_warning] if gas_warning else [], True
    if gas.height_tvd_ft == 0:
        notes.append(LATERAL_NOTE)
        lateral = lateral_gauge_warning(sidpp_psi, sicp_psi)
        if lateral:
            warnings.append(lateral)
            valid = False
    return notes, warnings, valid, _heel_md(survey, bit_md_ft, bit_tvd_ft)


def shoe_margin_warning(wait_and_weight_plot, drillers_plot):
    """W&W shoe margin below the Driller's margin on the same well: a warning, or None.

        Shoe margin = Fracture at the shoe - Max shoe pressure
    """
    if not (wait_and_weight_plot.casing_forecast_valid and drillers_plot.casing_forecast_valid):
        return None
    ww = wait_and_weight_plot.fracture_at_shoe_psi - wait_and_weight_plot.max_shoe.shoe_psi
    dm = drillers_plot.fracture_at_shoe_psi - drillers_plot.max_shoe.shoe_psi
    if ww >= dm:
        return None
    return (f"W&W shoe margin {ww:,} psi is less than Driller's {dm:,} psi because of kill mud rounding. "
            "Consider a smaller SF, a finer KMW rounding, or Driller's method.")


def _stroke_marks(last_stroke, step_strokes):
    return list(range(step_strokes, last_stroke, step_strokes))


def drillers_kill_plot(sidpp_psi, sicp_psi, icp_psi, fcp_psi, safety_margin_psi, pit_gain_bbl,
                       original_mud_weight_ppg, kill_mud_weight_ppg, bit_tvd_ft, shoe_tvd_ft,
                       mamw_ppg, maasp_psi, drill_string_sections, annulus_sections,
                       pump_output_bbl_per_stk, surface_line_volume_bbl=0, step_strokes=100,
                       bit_md_ft=None, shoe_md_ft=None, key_points=()):
    """Kill plot for Driller's method. Strokes run on through both circulations
    (the 2nd starts where the 1st ended).

    1st circulation: drill pipe held at ICP + SF; casing from the gas model.
    2nd circulation: casing held at SIDPP + SF while kill mud goes to the bit:
        DP = SIDPP + SF - Kill mud hydrostatic gain + Friction
    (hydrostatic gain by the TVD of the kill mud, friction by its MD)
    which falls from ICP + SF to FCP + SIDPP + SF - overbalance. That reading
    is held while kill mud goes to surface and casing falls to the trapped
    pressure. If casing reaches 0 first (choke fully open), BHP goes above
    formation pressure + SF and the drill pipe rises by the same amount.
    annulus_sections: ALL of the annulus, listed from the bit UP.
    Deviated or horizontal well: give bit_md_ft, shoe_md_ft and key_points (name, MD, TVD).
    """
    sf = safety_margin_psi
    bit_md_ft = bit_tvd_ft if bit_md_ft is None else bit_md_ft
    shoe_md_ft = shoe_tvd_ft if shoe_md_ft is None else shoe_md_ft
    survey = _survey(bit_md_ft, bit_tvd_ft, shoe_md_ft, shoe_tvd_ft, key_points)
    well = AnnulusWell(annulus_sections, shoe_tvd_ft, pump_output_bbl_per_stk,
                       mud_gradient(original_mud_weight_ppg), mud_gradient(kill_mud_weight_ppg),
                       survey, shoe_md_ft)
    gas, gas_warning = gas_influx(pit_gain_bbl, sidpp_psi, sicp_psi, well.mud_gradient_psi_per_ft,
                                  bit_tvd_ft, annulus_sections, bit_md_ft, survey)
    notes, warnings, valid, heel_md = _start(well, gas, sidpp_psi, sicp_psi, gas_warning, survey,
                                             bit_md_ft, bit_tvd_ft)
    bhp_psi = formation_pressure(sidpp_psi, well.mud_gradient_psi_per_ft, bit_tvd_ft) + sf
    bottoms_up = strokes_for_volume(total_volume(annulus_sections), pump_output_bbl_per_stk)
    to_bit = surface_to_bit_strokes(drill_string_sections, pump_output_bbl_per_stk, surface_line_volume_bbl)
    overbalance_psi = kill_mud_overbalance(kill_mud_weight_ppg, original_mud_weight_ppg, bit_tvd_ft)
    scr_psi = icp_psi - sidpp_psi
    dp_at_bit = drillers.drill_pipe_with_kill_mud_at_bit(sidpp_psi, fcp_psi, sf, overbalance_psi)

    def drill_pipe_at(strokes):
        """2nd circulation drill pipe: hydrostatic gain by TVD, friction by MD of the kill mud."""
        if strokes >= to_bit:
            return dp_at_bit + max(0, second[strokes].bhp_psi - bhp_psi)
        md_ft = md_after_strokes(strokes, drill_string_sections, pump_output_bbl_per_stk,
                                 surface_line_volume_bbl)
        return round_to_whole_number(
            sidpp_psi + sf - _hydrostatic_gain(overbalance_psi, _tvd(md_ft, well), bit_tvd_ft)
            + _friction(scr_psi, fcp_psi, md_ft, bit_md_ft))

    # 1st circulation - original mud, gas out.
    first = _forecasts(0, bottoms_up, bhp_psi, well, gas, None)
    start_shoe = sicp_psi + sf + round_to_whole_number(well.mud_gradient_psi_per_ft * shoe_tvd_ft)
    first[0] = first[0]._replace(casing_psi=sicp_psi + sf, shoe_psi=start_shoe)  # the value held
    events = _events(first, shoe_md_ft, heel_md)
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
                                 surface_line_volume_bbl, sidpp_psi=sidpp_psi, bit_tvd_ft=bit_tvd_ft,
                                 key_points=key_points):
        if row.strokes > 0:
            label = "kill mud at the bit" if row.strokes == to_bit else row.label
            points.append(PlotPoint(offset + row.strokes, drill_pipe_at(row.strokes),
                                    second[row.strokes].casing_psi, None, label))
    for s in _stroke_marks(to_bit + bottoms_up, step_strokes):
        if s > to_bit:
            points.append(PlotPoint(offset + s, drill_pipe_at(s), second[s].casing_psi, None, ""))
    choke_open = next((s for s in range(to_bit, to_bit + bottoms_up + 1)
                       if second[s].bhp_psi > bhp_psi), None)
    if choke_open is not None:
        points.append(PlotPoint(offset + choke_open, drill_pipe_at(choke_open), 0, None,
                                "casing at 0, choke fully open - drill pipe rises toward FCP"))
        points.sort(key=lambda p: p.strokes)
    trapped_dp = drillers.trapped_pressure(sidpp_psi, sf, overbalance_psi)
    trapped_casing = second[-1].casing_psi
    end = offset + to_bit + bottoms_up
    points.append(PlotPoint(end, drill_pipe_at(to_bit + bottoms_up), trapped_casing, None,
                            "kill mud at surface"))
    points.append(PlotPoint(end, trapped_dp, trapped_casing, None,
                            "shut in: both read the trapped pressure - bleed to 0, check, flow check"))

    max_shoe = max(first + [s._replace(strokes=offset + s.strokes) for s in second],
                   key=lambda f: f.shoe_psi)
    fracture_psi = fracture_at_shoe(mamw_ppg, shoe_tvd_ft)
    warnings += _checks(valid, peak, max_shoe, fracture_psi, maasp_psi, trapped_dp, trapped_casing, shoe_md_ft)
    return KillPlot(points, peak, max_shoe, fracture_psi, trapped_dp, trapped_casing, warnings, valid,
                    tuple(notes))


def _checks(valid, peak, max_shoe, fracture_psi, maasp_psi, trapped_dp_psi, trapped_casing_psi, shoe_md_ft):
    """plot_warnings - but no peak casing / shoe checks when the casing forecast doesn't apply."""
    found = plot_warnings(peak, max_shoe, fracture_psi, maasp_psi, trapped_dp_psi, trapped_casing_psi, shoe_md_ft)
    if valid:
        return found
    return [w for w in found if "trapped" in w]


def wait_and_weight_kill_plot(sidpp_psi, sicp_psi, icp_psi, fcp_psi, safety_margin_psi, pit_gain_bbl,
                              original_mud_weight_ppg, kill_mud_weight_ppg, bit_tvd_ft, shoe_tvd_ft,
                              mamw_ppg, maasp_psi, drill_string_sections, annulus_sections,
                              pump_output_bbl_per_stk, surface_line_volume_bbl=0, step_strokes=100,
                              kill_mud_friction_psi=None, bit_md_ft=None, shoe_md_ft=None, key_points=()):
    """Kill plot for Wait and Weight. One circulation:
    from the first stroke kill mud goes down the drill pipe while the gas and
    original mud come up the annulus.

    Drill pipe: step-down chart + SF until kill mud is at the bit, then FCP + SF.
    BHP:        worked back from the scheduled drill pipe at every stroke:
                    BHP = Formation pressure + DP - SIDPP + Hydrostatic gain - Friction
                (hydrostatic gain by the TVD of the kill mud, friction by its MD)
    Casing:     gas model at that BHP, with kill mud filling the annulus from the bit up.
    sidpp_psi and sicp_psi are the values RETAKEN just before start-up.
    kill_mud_friction_psi: leave out unless the ICP was recalculated (then it
                    is Actual SCR x KMW / OMW); it defaults to the FCP.
    annulus_sections: ALL of the annulus, listed from the bit UP.
    Deviated or horizontal well: give bit_md_ft, shoe_md_ft and key_points (name, MD, TVD).
    """
    sf = safety_margin_psi
    bit_md_ft = bit_tvd_ft if bit_md_ft is None else bit_md_ft
    shoe_md_ft = shoe_tvd_ft if shoe_md_ft is None else shoe_md_ft
    survey = _survey(bit_md_ft, bit_tvd_ft, shoe_md_ft, shoe_tvd_ft, key_points)
    well = AnnulusWell(annulus_sections, shoe_tvd_ft, pump_output_bbl_per_stk,
                       mud_gradient(original_mud_weight_ppg), mud_gradient(kill_mud_weight_ppg),
                       survey, shoe_md_ft)
    gas, gas_warning = gas_influx(pit_gain_bbl, sidpp_psi, sicp_psi, well.mud_gradient_psi_per_ft,
                                  bit_tvd_ft, annulus_sections, bit_md_ft, survey)
    notes, warnings, valid, heel_md = _start(well, gas, sidpp_psi, sicp_psi, gas_warning, survey,
                                             bit_md_ft, bit_tvd_ft)
    formation_psi = formation_pressure(sidpp_psi, well.mud_gradient_psi_per_ft, bit_tvd_ft)
    bottoms_up = strokes_for_volume(total_volume(annulus_sections), pump_output_bbl_per_stk)
    to_bit = surface_to_bit_strokes(drill_string_sections, pump_output_bbl_per_stk, surface_line_volume_bbl)
    end = to_bit + bottoms_up
    overbalance_psi = kill_mud_overbalance(kill_mud_weight_ppg, original_mud_weight_ppg, bit_tvd_ft)
    scr_psi = icp_psi - sidpp_psi
    friction_with_kill_mud = fcp_psi if kill_mud_friction_psi is None else kill_mud_friction_psi

    def kill_mud_md(strokes):
        if strokes >= to_bit:
            return bit_md_ft
        return md_after_strokes(strokes, drill_string_sections, pump_output_bbl_per_stk,
                                surface_line_volume_bbl)

    def drill_pipe_at(strokes):
        """Step-down chart + SF until kill mud is at the bit, then FCP + SF."""
        if strokes >= to_bit:
            return fcp_psi + sf
        md_ft = kill_mud_md(strokes)
        return drill_pipe_pressure(icp_psi, fcp_psi, sidpp_psi, md_ft, _tvd(md_ft, well),
                                   bit_md_ft, bit_tvd_ft) + sf

    def bhp_at(strokes):
        """BHP worked back from the scheduled drill pipe."""
        md_ft = kill_mud_md(strokes)
        return (formation_psi + drill_pipe_at(strokes) - sidpp_psi
                + _hydrostatic_gain(overbalance_psi, _tvd(md_ft, well), bit_tvd_ft)
                - _friction(scr_psi, friction_with_kill_mud, md_ft, bit_md_ft))

    forecasts = _forecasts(0, end, bhp_at, well, gas, to_bit)
    start_shoe = sicp_psi + sf + round_to_whole_number(well.mud_gradient_psi_per_ft * shoe_tvd_ft)
    forecasts[0] = forecasts[0]._replace(casing_psi=sicp_psi + sf, shoe_psi=start_shoe)
    events = _events(forecasts, shoe_md_ft, heel_md)
    peak = max(forecasts, key=lambda f: f.casing_psi)
    events.setdefault(peak.strokes, "peak casing")
    for row in pressure_schedule(icp_psi, fcp_psi, drill_string_sections, pump_output_bbl_per_stk,
                                 surface_line_volume_bbl, sidpp_psi=sidpp_psi, bit_tvd_ft=bit_tvd_ft,
                                 key_points=key_points):
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
    trapped_dp = wait_and_weight.trapped_pressure(sf, fcp_psi, friction_with_kill_mud)
    trapped_casing = forecasts[end].casing_psi
    points.append(PlotPoint(end, fcp_psi + sf, trapped_casing, None, "kill mud at surface"))
    points.append(PlotPoint(end, trapped_dp, trapped_casing, None,
                            "shut in: both read the trapped pressure - bleed to 0, check, flow check"))

    max_shoe = max(forecasts, key=lambda f: f.shoe_psi)
    fracture_psi = fracture_at_shoe(mamw_ppg, shoe_tvd_ft)
    warnings += _checks(valid, peak, max_shoe, fracture_psi, maasp_psi, trapped_dp, trapped_casing, shoe_md_ft)
    return KillPlot(points, peak, max_shoe, fracture_psi, trapped_dp, trapped_casing, warnings, valid,
                    tuple(notes))
