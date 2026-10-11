"""Volumetric method forecast: where the gas is, what BHP and the shoe see, and
what hold pressure keeps BHP at formation pressure + safety margin.

Single-bubble model (user-approved v1.3), the same physics as the kill plot:
POSITION by MD, PRESSURE by TVD, Boyle's law at the TOP of the bubble.

    Influx         Height = Pit gain / annulus capacity, from TD up (MD), then its TVD height
    Pf             SIDPP + Mud gradient x TD TVD when SIDPP is known; otherwise
                   ESTIMATED: SICP + Mud gradient x (TD TVD - h) + 0.1 x h
                   ("assumes influx at bottom, 0.1 psi/ft, no migration before the SICP reading")
    Gas gradient   from the gauges with SIDPP; 0.1 psi/ft otherwise (and always in a lateral)
    Boyle          P x V = P0 x Pit gain, P0 = pressure at the top of the bubble at shut-in
                   (Pf at the heel when the influx lies in the lateral)
    Gas position   with casing C and gas volume V (pit gain + bbl bled):
                       Gas top TVD = (P0 x Pit gain / V - C) / Mud gradient
                   gas bottom from the annulus capacities

Each cycle:
    Bleed      on the SMALLEST annulus the gas touches anywhere along its path, from
               the end of the last bleed (or shut-in) to the end of this one. The
               largest capacity that still satisfies that is used, so any error in
               the gas position is an under-bleed, never an over-bleed.
    Hold       Standard (IADC) = SICP + SF + n x Pw, RE-BASED after a shoe-limited cycle
               (tier 2-4) to the hold actually used + Pw, so the hold to use is never
               below the standard it sits next to unless the shoe limits it. The hold to
               use is raised (never lowered) until the forecast BHP through the coming
               bleed stays at or above Pf + SF - the gas gaining vertical height in a
               narrower annulus or the build section is the only thing that can pull it lower.
    Shoe       every hold is checked against the shoe limit = fracture - shoe margin
               (the team's choice, default 0 - a leak-off test isn't that precise):
               tier 0  standard hold, no correction, shoe below the limit
               tier 1  corrected hold, shoe below the limit
               tier 2  hold limited by the shoe, BHP still >= Pf + SF
               tier 3  hold limited by the shoe, BHP between Pf and Pf + SF (SF reduced)
               tier 4  the shoe-limited hold puts BHP below Pf: SUPERVISOR DECISION.
                       The BHP-keeping hold is printed (constant-BHP doctrine).
Gas reaches surface in a wait when its pressure is no more than the hold (the casing
rises only to it), or during a bleed once its pressure falls to the hold.

The forecast is a model: real gas usually arrives EARLIER (it disperses, or breaks
out of solution in oil-based mud). The crew's readings still drive the table.
"""

import math
from typing import NamedTuple

from killsheet.depths import tvd_at_md
from killsheet.rounding import round_down_to_tenth, round_to_4_places, round_to_tenth, round_to_whole_number

ANNULUS_AT_THE_GAS = "annulus at the gas"          # the default bleed capacity choice
LATERAL_GAS_GRADIENT_PSI_PER_FT = 0.1
EARLY_OR_LATE_GAS_PERCENT = 20

PF_ESTIMATED = "estimated: assumes influx at bottom, 0.1 psi/ft, no migration before the SICP reading"

TIER_STANDARD = 0
TIER_CORRECTED = 1
TIER_SHOE_LIMITED = 2
TIER_SF_REDUCED = 3
TIER_SUPERVISOR = 4
TIERS = ("Tier 0: standard hold, no correction. 1: raised for the gas gaining vertical height. "
         "2: limited by the shoe, BHP still >= Pf + SF. 3: limited by the shoe, SF reduced. "
         "4: supervisor decision.")


class Annulus:
    """The open annulus as the gas sees it: sections from the BOTTOM UP, and the well path."""

    def __init__(self, sections_bottom_up, td_md_ft, td_tvd_ft, shoe_md_ft, shoe_tvd_ft, key_points=()):
        self.sections_bottom_up = list(sections_bottom_up)            # (capacity bbl/ft, length ft MD)
        self.td_md, self.td_tvd = td_md_ft, td_tvd_ft
        self.shoe_md, self.shoe_tvd = shoe_md_ft, shoe_tvd_ft
        self.survey = tuple((md, tvd) for _name, md, tvd in key_points) + ((shoe_md_ft, shoe_tvd_ft),
                                                                          (td_md_ft, td_tvd_ft))
        self.deviated = bool(key_points) or td_md_ft != td_tvd_ft
        self.sections_top_down = []                                    # (top MD, bottom MD, capacity)
        md = td_md_ft
        for capacity, length in self.sections_bottom_up:
            self.sections_top_down.insert(0, (md - length, md, capacity))
            md -= length

    def tvd(self, md_ft):
        """TVD (whole ft) at an MD - the MD itself in a vertical well (depths: whole ft)."""
        if md_ft <= 0:
            return md_ft
        return tvd_at_md(md_ft, self.survey) if self.deviated else round_to_whole_number(md_ft)

    def md_at_tvd(self, tvd_ft):
        """The shallowest MD at a TVD: the heel for the TVD of a lateral."""
        points = sorted(set(self.survey) | {(0, 0)})
        for (md1, tvd1), (md2, tvd2) in zip(points, points[1:]):
            if tvd1 <= tvd_ft <= tvd2 and tvd2 > tvd1:
                return md1 + (tvd_ft - tvd1) * (md2 - md1) / (tvd2 - tvd1)
        return min(md for md, tvd in points if tvd == self.td_tvd)

    def gas_bottom(self, top_md_ft, gas_bbl):
        """MD of the bottom of a gas volume whose top is at top_md_ft (the capacities, going down)."""
        for top, bottom, capacity in self.sections_top_down:
            if top_md_ft < bottom:
                start = max(top_md_ft, top)
                if gas_bbl <= (bottom - start) * capacity:
                    return start + gas_bbl / capacity
                gas_bbl -= (bottom - start) * capacity
        return self.td_md

    def capacities_between(self, top_md_ft, bottom_md_ft):
        return [c for top, bottom, c in self.sections_top_down if top < bottom_md_ft and bottom > top_md_ft]

    def influx_height(self, pit_gain_bbl):
        """Influx height (whole ft MD) from TD up: pit gain / capacity, section by section."""
        height, bbl = 0, pit_gain_bbl
        for capacity, length in self.sections_bottom_up:
            if bbl <= capacity * length:
                return round_to_whole_number(height + bbl / capacity)
            bbl -= capacity * length
            height += length
        raise ValueError(f"A pit gain of {pit_gain_bbl} bbl is more than the whole annulus volume")


class Influx(NamedTuple):
    height_md_ft: int
    height_tvd_ft: int
    gradient_psi_per_ft: float
    formation_psi: int
    pf_estimated: bool
    top_pressure_psi: float          # P0: pressure at the top of the bubble at shut-in
    in_lateral: bool


def influx_at_shut_in(annulus, pit_gain_bbl, sicp_psi, sidpp_psi, mud_gradient_psi_per_ft):
    """The influx, its gradient and the formation pressure (from SIDPP, or estimated from SICP)."""
    if pit_gain_bbl is None or pit_gain_bbl <= 0:
        raise ValueError("Pit gain must be greater than 0 bbl - the volumetric forecast needs it.")
    mud = mud_gradient_psi_per_ft
    h_md = annulus.influx_height(pit_gain_bbl)
    h_tvd = annulus.td_tvd - annulus.tvd(annulus.td_md - h_md)
    lateral = h_tvd == 0
    if sidpp_psi is not None:
        pf = sidpp_psi + round_to_whole_number(mud * annulus.td_tvd)
        gradient = (LATERAL_GAS_GRADIENT_PSI_PER_FT if lateral
                    else round_to_4_places(mud - round_to_4_places((sicp_psi - sidpp_psi) / h_tvd)))
        estimated = False
    else:
        gradient = LATERAL_GAS_GRADIENT_PSI_PER_FT
        pf = round_to_whole_number(sicp_psi + mud * (annulus.td_tvd - h_tvd) + gradient * h_tvd)
        estimated = True
    return Influx(h_md, h_tvd, gradient, pf, estimated, pf - gradient * h_tvd, lateral)


class GasPosition(NamedTuple):
    top_md_ft: float
    bottom_md_ft: float
    top_tvd_ft: int
    bhp_psi: float
    shoe_psi: float


class Decision(NamedTuple):
    """Tier 4: the two holds and what each costs."""
    bhp_hold_psi: int
    bhp_vs_pf_psi: int               # BHP-keeping hold: lowest BHP vs Pf
    shoe_over_psi: int               # ... and how far it puts the shoe over fracture
    shoe_hold_psi: int
    shoe_hold_bhp_vs_pf_psi: int     # shoe-limited hold: lowest BHP vs Pf (negative = influx)


class ForecastCycle(NamedTuple):
    cycle: int
    standard_hold_psi: int
    hold_psi: int                    # the hold to use
    correction_psi: int              # raise for the gas gaining vertical height
    tier: int
    capacity_bbl_per_ft: float
    bleed_bbl: float
    total_bled_bbl: float
    gas_top_tvd_ft: int              # at the hold, before the bleed
    gas_below_shoe: bool
    lowest_bhp_vs_pf_psi: int        # through the bleed
    highest_shoe_psi: int
    decision: Decision | None
    bhp_at_hold_vs_pf_psi: int = 0   # BHP when casing reaches the hold (start of the bleed)
    bhp_after_bleed_vs_pf_psi: int = 0


class GasAtSurface(NamedTuple):
    cycle: int                       # the cycle it happens in (or the wait after it)
    during: str                      # "wait" or "bleed"
    casing_psi: int
    bled_bbl: float                  # total bled when the gas reaches surface
    gas_volume_bbl: float


class VolumetricModel:
    """The forecast for one well, kick and set of team choices."""

    def __init__(self, annulus, influx, mud_gradient_psi_per_ft, sicp_psi, safety_margin_psi,
                 working_pressure_psi, fracture_psi, pit_gain_bbl, fixed_capacity_bbl_per_ft=None,
                 shoe_margin_psi=0):
        self.annulus, self.influx, self.mud = annulus, influx, mud_gradient_psi_per_ft
        self.sicp, self.sf, self.pw = sicp_psi, safety_margin_psi, working_pressure_psi
        self.fracture, self.pit = fracture_psi, pit_gain_bbl
        self.shoe_limit = fracture_psi - shoe_margin_psi              # the shoe tiers use this
        self.fixed_capacity = fixed_capacity_bbl_per_ft
        self.boyle = influx.top_pressure_psi * pit_gain_bbl            # P x V of the bubble
        self.heel_md = annulus.md_at_tvd(annulus.td_tvd)
        self.capacities = sorted({c for c, _l in annulus.sections_bottom_up})

    def gas_pressure(self, gas_bbl):
        return self.boyle / gas_bbl

    def position(self, casing_psi, gas_bbl):
        """Where the gas is and what BHP / the shoe see - None once the gas is at surface."""
        a = self.annulus
        p = self.gas_pressure(gas_bbl)
        top_tvd = (p - casing_psi) / self.mud
        if top_tvd <= 0:
            return None
        gradient = self.influx.gradient_psi_per_ft * p / self.influx.top_pressure_psi
        top = self.heel_md if top_tvd >= a.td_tvd else a.md_at_tvd(top_tvd)
        bottom = a.gas_bottom(top, gas_bbl)
        layers = [(0, top, self.mud), (top, bottom, gradient), (bottom, a.td_md, self.mud)]

        def hydrostatic(down_to_md):
            return sum(g * (a.tvd(min(b, down_to_md)) - a.tvd(t)) for t, b, g in layers if t < down_to_md)

        return GasPosition(top, bottom, a.tvd(top), casing_psi + hydrostatic(a.td_md),
                           casing_psi + hydrostatic(a.shoe_md))

    def bleed(self, hold_psi, gas_bbl, previous_bottom_md):
        """(capacity, bbl) for a bleed at this hold - the path rule, or the team's fixed choice."""
        def bbl_for(capacity):
            return round_down_to_tenth(self.pw / self.mud * capacity)

        if self.fixed_capacity:
            return self.fixed_capacity, bbl_for(self.fixed_capacity)
        here = self.position(hold_psi, gas_bbl)
        pick = self.capacities[0]
        for capacity in self.capacities:
            end = self.position(hold_psi, round_to_tenth(gas_bbl + bbl_for(capacity)))
            path_top = end.top_md_ft if end else 0
            path_bottom = max(previous_bottom_md, here.bottom_md_ft, end.bottom_md_ft if end else 0)
            if min(self.annulus.capacities_between(path_top, path_bottom)) >= capacity:
                pick = capacity
        return pick, bbl_for(pick)

    def through_bleed(self, hold_psi, gas_bbl, bleed_bbl):
        """Lowest BHP and highest shoe pressure from the start to the end of a bleed (every 0.1 bbl)."""
        positions = [self.position(hold_psi, round_to_tenth(gas_bbl + step / 10))
                     for step in range(0, round_to_whole_number(bleed_bbl * 10) + 1)]
        positions = [p for p in positions if p]
        return min(p.bhp_psi for p in positions), max(p.shoe_psi for p in positions)

    def forecast(self, max_cycles=500):
        """Every cycle until the gas reaches surface: (list of ForecastCycle, GasAtSurface)."""
        pf, rows, bled, used = self.influx.formation_psi, [], 0.0, None
        # the gas path starts at the bubble: at TD, or at the heel when it lies in the lateral
        previous_bottom = (self.annulus.gas_bottom(self.heel_md, self.pit) if self.influx.in_lateral
                           else self.annulus.td_md)
        standard, rebase = None, False
        for n in range(1, max_cycles + 1):
            gas_bbl = round_to_tenth(self.pit + bled)
            base = self.sicp + self.sf + self.pw if used is None else used + self.pw
            standard = base if (standard is None or rebase) else standard + self.pw
            hold = base
            for _ in range(20):                       # raise until BHP stays >= Pf + SF through the bleed
                if self.gas_pressure(gas_bbl) <= hold:
                    break
                _c, b = self.bleed(hold, gas_bbl, previous_bottom)
                low, _high = self.through_bleed(hold, gas_bbl, b)
                short = math.ceil(round(pf + self.sf - low, 6))
                if short <= 0:
                    break
                hold += short
            if self.gas_pressure(gas_bbl) <= hold:    # the casing only rises to the gas pressure
                return rows, GasAtSurface(n - 1, "wait", round_to_whole_number(self.gas_pressure(gas_bbl)),
                                          bled, gas_bbl)
            corrected = hold
            capacity, b = self.bleed(hold, gas_bbl, previous_bottom)
            low, high = self.through_bleed(hold, gas_bbl, b)
            tier, decision = (TIER_CORRECTED if corrected > base else TIER_STANDARD), None
            if high > self.shoe_limit:
                limited, high_l = corrected, high
                for _ in range(20):                   # step down until the shoe is at the limit
                    limited -= math.ceil(round(high_l - self.shoe_limit, 6))
                    capacity_l, b_l = self.bleed(limited, gas_bbl, previous_bottom)
                    low_l, high_l = self.through_bleed(limited, gas_bbl, b_l)
                    if high_l <= self.shoe_limit:
                        break
                if low_l >= pf:
                    tier = TIER_SHOE_LIMITED if low_l >= pf + self.sf else TIER_SF_REDUCED
                    hold, capacity, b, low, high = limited, capacity_l, b_l, low_l, high_l
                else:
                    tier = TIER_SUPERVISOR
                    decision = Decision(corrected, round_to_whole_number(low - pf),
                                        round_to_whole_number(high - self.shoe_limit), limited,
                                        round_to_whole_number(low_l - pf))
            here = self.position(hold, gas_bbl)
            reaches_surface = self.gas_pressure(round_to_tenth(gas_bbl + b)) <= hold
            total = round_to_tenth(bled + b)
            after = self.position(hold, round_to_tenth(self.pit + total))
            rows.append(ForecastCycle(n, standard, hold, corrected - base, tier, capacity,
                                      b, total, here.top_tvd_ft, here.top_md_ft > self.annulus.shoe_md,
                                      round_to_whole_number(low - pf), round_to_whole_number(high), decision,
                                      round_to_whole_number(here.bhp_psi - pf),
                                      round_to_whole_number((after.bhp_psi if after else low) - pf)))
            if reaches_surface:
                return rows, GasAtSurface(n, "bleed", hold, round_to_tenth(self.boyle / hold - self.pit),
                                          round_to_tenth(self.boyle / hold))
            bled = total
            previous_bottom = self.position(hold, round_to_tenth(self.pit + bled)).bottom_md_ft
            used, rebase = hold, tier >= TIER_SHOE_LIMITED
        raise ValueError(f"The gas does not reach surface within {max_cycles} cycles")


# --- Sheet wording (user-approved) --------------------------------------------------

def precheck_warning(sicp_psi, safety_margin_psi, working_pressure_psi, maasp_psi, shoe_margin_psi=0):
    """Before starting: SF + Pw against the shoe margin at shut-in (MAASP - SICP - shoe margin)."""
    margin = maasp_psi - sicp_psi - shoe_margin_psi
    if safety_margin_psi + working_pressure_psi < margin:
        return None
    return (f"Shoe margin {margin:,} psi is less than SF + Pw {safety_margin_psi + working_pressure_psi:,}. "
            "Volumetric with these margins will exceed fracture. Reduce SF/Pw or consider bullheading.")


def correction_note(correction_psi):
    return (f"+{correction_psi:,} psi: gas will gain vertical height during this bleed "
            "(narrower annulus / build section).")


def tier_warning(row, safety_margin_psi, shoe_margin_psi=0):
    """Tier 3 and tier 4 lines; None otherwise."""
    limit = "fracture" if not shoe_margin_psi else f"the shoe limit (fracture - {shoe_margin_psi:,} psi)"
    if row.tier == TIER_SF_REDUCED:
        return (f"Cycle {row.cycle}: hold limited by the shoe. SF reduced from {safety_margin_psi:,} to "
                f"{row.lowest_bhp_vs_pf_psi:,} psi. BHP still above Pf.")
    if row.tier == TIER_SUPERVISOR:
        d = row.decision
        return (f"SUPERVISOR DECISION, cycle {row.cycle}: hold {d.bhp_hold_psi:,} psi keeps BHP >= Pf + "
                f"{d.bhp_vs_pf_psi:,} but puts the shoe {d.shoe_over_psi:,} psi over {limit}. Hold "
                f"{d.shoe_hold_psi:,} psi keeps the shoe at {limit} but BHP {-d.shoe_hold_bhp_vs_pf_psi:,} psi "
                f"under Pf (influx). Constant-BHP doctrine favors {d.bhp_hold_psi:,}.")
    return None


def maasp_label(hold_psi, maasp_psi, gas_below_shoe):
    """Above MAASP: what it means depends on where the gas is."""
    if hold_psi <= maasp_psi:
        return None
    if gas_below_shoe:
        return "ABOVE MAASP, gas below shoe, shoe overpressured"
    return "above MAASP, gas above shoe, MAASP no longer applies, continue"


def arrival_warning(readings_bbl, model_bbl, model_gas_top_tvd_ft=None):
    """Readings vs the model: gas at surface more than 20% earlier or later (bbl bled)."""
    if model_bbl <= 0 or abs(readings_bbl - model_bbl) / model_bbl * 100 <= EARLY_OR_LATE_GAS_PERCENT:
        return None
    if readings_bbl < model_bbl:
        where = f" (gas top at {model_gas_top_tvd_ft:,} ft)" if model_gas_top_tvd_ft else ""
        return (f"Readings show gas at surface at {readings_bbl:.1f} bbl bled; the single-bubble model predicts "
                f"{model_bbl:.1f} bbl{where}. Gas arriving early is common (dispersed or breaking out of "
                "solution). Check the pit gain and readings. L&B volumes follow the readings.")
    return (f"Readings show gas at surface at {readings_bbl:.1f} bbl bled; the model predicts {model_bbl:.1f} bbl. "
            "Gas arriving late suggests a larger influx than the pit gain entered, or gas in solution "
            "(oil-based mud). Check the pit gain and readings. L&B volumes follow the readings.")


LATERAL_NOTE = ("Gas lying in the lateral may not migrate, so casing can stay flat for a long time. "
                "Volumetric steps start when casing begins to rise.")
SHOE_AT_HEEL_NOTE = ("Shoe at the heel: shoe pressure = BHP. Kick tolerance is very small. "
                     "If the pre-check fires, consider bullheading before volumetric.")
