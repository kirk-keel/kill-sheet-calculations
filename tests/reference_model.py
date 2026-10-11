"""Reference model for the kill plot - an independent second calculation.

Written separately from src/killsheet/kill_plot.py and never imports it. It
was used to work the deviated, horizontal and tapered hand examples, and it
reproduces the user-approved vertical hand example exactly. tests/
test_kill_plot_reference.py checks kill_plot.py against it on every case.

Only the approved kill sheet numbers come from the package (formulas, strokes):
KMW, ICP, FCP, MAMW, overbalance and the surface-to-bit / bottoms-up strokes.
Everything about the gas, the well path and the pressures is worked here:

    Position (gas, kill mud)  by MD, from the volume pumped
    Pressure                  by TVD: hydrostatic = gradient x TVD height
    Influx height             Pit gain / capacity at the bit (MD), then its TVD height
    Influx gradient           Mud gradient - (SICP - SIDPP) / TVD height
                              (0 TVD height - in the lateral: 0.1 psi/ft)
    Boyle's law               at the TOP of the bubble; gradient scales with pressure
    Casing                    BHP - everything in the annulus (never below 0)
    Shoe                      Casing + everything above the shoe
    Driller's                 BHP = formation + SF; 2nd circ DP = SIDPP + SF - gain(TVD) + friction(MD)
    Wait and Weight           BHP = formation + scheduled DP + SF - SIDPP + gain(TVD) - friction(MD)
"""

import math

from killsheet.formulas import (
    final_circulating_pressure,
    initial_circulating_pressure,
    kill_mud_overbalance,
    kill_mud_weight,
    max_allowable_mud_weight,
)
from killsheet.strokes import bit_to_surface_strokes, surface_to_bit_strokes

DRILLERS = "D"
WAIT_AND_WEIGHT = "W"


def whole(value):
    """Nearest whole number, .5 up (the project's academic rounding)."""
    return math.floor(round(value, 6) + 0.5)


def tenth(value):
    return math.floor(round(value * 10, 6) + 0.5) / 10


def four(value):
    return math.floor(round(value * 10_000, 6) + 0.5) / 10_000


class ReferenceWell:
    """One example well (its WELL dict) as the reference model sees it."""

    def __init__(self, well):
        self.bit_tvd = well["bit_tvd_ft"]
        self.bit_md = well.get("bit_md_ft") or self.bit_tvd
        self.shoe_tvd = well["shoe_tvd_ft"]
        self.shoe_md = well.get("shoe_md_ft") or self.shoe_tvd
        self.path = sorted({(0, 0), (self.shoe_md, self.shoe_tvd), (self.bit_md, self.bit_tvd)}
                           | {(md, tvd) for _name, md, tvd in well.get("key_points", ())})
        self.annulus = [(c, l) for _n, c, l in well["open_hole_annulus"] + well["cased_hole_annulus"]]
        self.string = [(c, l) for _n, c, l in well["drill_string"]]
        self.pump = well["pump_output_bbl_per_stk"]
        self.lines = well.get("surface_line_volume_bbl", 0)
        omw = well["original_mud_weight_ppg"]
        self.sidpp = well.get("sidpp_at_start_psi") or well["sidpp_psi"]
        self.sicp = well.get("sicp_at_start_psi") or well["sicp_psi"]
        self.sf = well["safety_margin_psi"]
        self.pit = well["pit_gain_bbl"]
        self.kmw = kill_mud_weight(well["sidpp_psi"], self.bit_tvd, omw)
        self.icp = initial_circulating_pressure(well["sidpp_psi"], well["scr_pressure_psi"])
        self.fcp = final_circulating_pressure(well["scr_pressure_psi"], self.kmw, omw)
        self.scr = self.icp - self.sidpp
        self.mud = four(0.052 * omw)
        self.kill_mud = four(0.052 * self.kmw)
        self.overbalance = kill_mud_overbalance(self.kmw, omw, self.bit_tvd)
        self.formation = self.sidpp + whole(self.mud * self.bit_tvd)
        mamw = max_allowable_mud_weight(well["lot_pressure_psi"], self.shoe_tvd, well["test_mud_weight_ppg"])
        self.fracture = math.floor(round(0.052 * mamw * self.shoe_tvd, 6))
        self.to_bit = surface_to_bit_strokes(self.string, self.pump, self.lines)
        self.bottoms_up = bit_to_surface_strokes(self.annulus, self.pump)

    # --- the well path ------------------------------------------------------------
    def tvd(self, md):
        """TVD by straight lines between the path points; above surface counts as vertical."""
        if md < 0:
            return md
        for (md1, tvd1), (md2, tvd2) in zip(self.path, self.path[1:]):
            if md1 <= md <= md2:
                return whole(tvd1 + (md - md1) * (tvd2 - tvd1) / (md2 - md1))
        raise ValueError(md)

    # --- the annulus: h = length above the bit along the hole -------------------------
    def height_for_volume(self, bbl):
        """Pumped volume -> length above the bit (rounded section volumes, like strokes)."""
        h = 0
        for c, l in self.annulus:
            section = tenth(c * l)
            if bbl <= section:
                return h + l * bbl / section
            bbl -= section
            h += l
        return h

    def gas_length(self, start_h, bbl):
        """Length a gas volume fills going up from start_h (capacity), or None past surface."""
        bottom = 0
        for c, l in self.annulus:
            top = bottom + l
            if start_h < top:
                frm = max(start_h, bottom)
                room = (top - frm) * c
                if bbl <= room:
                    return frm + bbl / c - start_h
                bbl -= room
            bottom = top
        return None

    def volume_above(self, start_h):
        bbl, bottom = 0, 0
        for c, l in self.annulus:
            top = bottom + l
            if start_h < top:
                bbl += (top - max(start_h, bottom)) * c
            bottom = top
        return bbl

    # --- the influx ----------------------------------------------------------------
    def influx(self):
        """(MD height, TVD height, gradient, pressure at the top at shut-in)."""
        h_md = whole(self.gas_length(0, self.pit))
        h_tvd = self.bit_tvd - self.tvd(self.bit_md - h_md)
        if h_tvd == 0:
            gradient = 0.1
        else:
            gradient = four(self.mud - four((self.sicp - self.sidpp) / h_tvd))
            if gradient <= 0 or gradient >= self.mud:
                gradient = 0.1
        return h_md, h_tvd, gradient, self.formation - gradient * h_tvd

    # --- one stroke -------------------------------------------------------------------
    def forecast(self, strokes, bhp, with_gas, kill_mud_at_bit=None):
        """(casing, shoe, gas top MD, gas volume, actual BHP) after a number of strokes."""
        pumped = tenth(strokes * self.pump)
        kill_top = self.bit_md
        if kill_mud_at_bit is not None and strokes > kill_mud_at_bit:
            kill_top = whole(self.bit_md - self.height_for_volume(tenth((strokes - kill_mud_at_bit) * self.pump)))

        def mud(top, bottom):
            layers = []
            if top < min(bottom, kill_top):
                layers.append((top, min(bottom, kill_top), self.mud))
            if max(top, kill_top) < bottom:
                layers.append((max(top, kill_top), bottom, self.kill_mud))
            return layers

        def hydrostatic(layers, down_to):
            return sum(g * (self.tvd(min(b, down_to)) - self.tvd(t)) for t, b, g in layers if t < down_to)

        top = volume = None
        if not with_gas or pumped >= sum(tenth(c * l) for c, l in self.annulus):
            layers = mud(0, self.bit_md)
        else:
            h_md, _h_tvd, g0, p0 = self.influx()
            bottom = whole(self.bit_md - self.height_for_volume(pumped))
            below = hydrostatic(mud(bottom, self.bit_md), self.bit_md)
            top, g = whole(bottom - h_md), g0
            for _ in range(50):
                p_top = bhp - below - g * (self.tvd(bottom) - self.tvd(top))
                volume = self.pit * p0 / p_top
                g = g0 * p_top / p0
                length = self.gas_length(self.bit_md - bottom, volume)
                if length is None:
                    new_top, volume = 0, self.volume_above(self.bit_md - bottom)
                else:
                    new_top = whole(bottom - length)
                if new_top == top:
                    break
                top = new_top
            volume = tenth(volume)
            layers = mud(0, top) + [(top, bottom, g)] + mud(bottom, self.bit_md)
        annulus = hydrostatic(layers, self.bit_md)
        casing = max(0, bhp - annulus)
        shoe = casing + hydrostatic(layers, self.shoe_md)
        return whole(casing), whole(shoe), top, volume, whole(casing + annulus)

    # --- the drill string ----------------------------------------------------------------
    def kill_mud_md(self, strokes):
        if strokes >= self.to_bit:
            return self.bit_md
        bbl = tenth(strokes * self.pump) - self.lines
        if bbl <= 0:
            return 0
        md, filled = 0, 0
        for c, l in self.string:
            section = tenth(c * l)
            if bbl <= filled + section:
                return whole(md + l * (bbl - filled) / section)
            filled = tenth(filled + section)
            md += l
        return md

    def gain(self, md):
        return self.overbalance * self.tvd(md) / self.bit_tvd

    def friction(self, md, kill_mud_friction):
        return self.scr + (kill_mud_friction - self.scr) * md / self.bit_md

    def schedule_dp(self, strokes):
        """W&W step-down chart (without the SF): drop rounded DOWN."""
        md = self.kill_mud_md(strokes)
        drop = self.sidpp * self.tvd(md) / self.bit_tvd - (self.fcp - self.scr) * md / self.bit_md
        return self.icp - math.floor(round(drop, 6))


def reference_plot(well, method):
    """Casing (and drill pipe) at every stroke, and the peak / max shoe.

    Returns a dict:
      casing[s], shoe[s]     - Driller's: 1st circulation then 2nd (strokes run on)
      drill_pipe[s]          - the drill pipe held / scheduled at that stroke (with SF)
      peak                   - (strokes, casing, gas bbl) - Driller's: 1st circulation
      max_shoe               - (strokes, shoe)
      end_casing             - casing with kill mud at surface
      influx                 - (MD height, TVD height, gradient, top pressure)
    Stroke 0 is the value HELD at start-up: casing SICP + SF (the user's rule).
    """
    w = ReferenceWell(well)
    bhp = w.formation + w.sf
    casing, shoe, gas_bbl, dp = {}, {}, {}, {}
    if method == DRILLERS:
        for s in range(0, w.bottoms_up + 1):
            c, sh, _top, v, _b = w.forecast(s, bhp, True)
            casing[s], shoe[s], gas_bbl[s], dp[s] = c, sh, v, w.icp + w.sf
        offset = w.bottoms_up
        dp_at_bit = w.fcp + w.sidpp + w.sf - w.overbalance
        for s in range(1, w.to_bit + w.bottoms_up + 1):
            c, sh, _top, _v, actual = w.forecast(s, bhp, False, w.to_bit)
            casing[offset + s], shoe[offset + s] = c, sh
            if s < w.to_bit:
                md = w.kill_mud_md(s)
                dp[offset + s] = whole(w.sidpp + w.sf - w.gain(md) + w.friction(md, w.fcp))
            else:
                dp[offset + s] = dp_at_bit + max(0, actual - bhp)
        first = range(0, w.bottoms_up + 1)
    else:
        def bhp_at(s):
            md = w.kill_mud_md(s)
            scheduled = w.fcp if s >= w.to_bit else w.schedule_dp(s)
            return w.formation + scheduled + w.sf - w.sidpp + w.gain(md) - w.friction(md, w.fcp)

        for s in range(0, w.to_bit + w.bottoms_up + 1):
            c, sh, _top, v, _b = w.forecast(s, bhp_at(s), True, w.to_bit)
            casing[s], shoe[s], gas_bbl[s] = c, sh, v
            dp[s] = (w.fcp if s >= w.to_bit else w.schedule_dp(s)) + w.sf
        first = range(0, w.to_bit + w.bottoms_up + 1)
    casing[0] = w.sicp + w.sf
    shoe[0] = w.sicp + w.sf + whole(w.mud * w.shoe_tvd)
    peak = max(first, key=lambda s: casing[s])
    max_shoe = max(shoe, key=lambda s: shoe[s])
    return {
        "casing": casing, "shoe": shoe, "drill_pipe": dp,
        "peak": (peak, casing[peak], gas_bbl[peak]),
        "max_shoe": (max_shoe, shoe[max_shoe]),
        "end_casing": casing[max(casing)],
        "influx": w.influx(),
        "fracture": w.fracture,
    }


# =============================================================================
# Volumetric method - reference (oracle) for killsheet.volumetric_model
# =============================================================================
#
# Worked out with the user, cycle by cycle (v1.3). Single bubble, Boyle at the
# TOP of the bubble, positions by MD, pressures by TVD:
#
#   Influx height      pit gain / capacity, from TD up (MD); then its TVD height
#   Pf                 SIDPP + mud x TD TVD when SIDPP is known; otherwise
#                      ESTIMATED: SICP + mud x (TD TVD - h) + 0.1 x h
#   Gas gradient       from the gauges with SIDPP; 0.1 psi/ft otherwise
#   K                  P0 x pit gain, P0 = Pf - gas gradient x h (Pf at the heel
#                      when the influx lies in the lateral)
#   Gas at casing C,   P = K / V (V = pit gain + bbl bled); gas top TVD =
#   volume V           (P - C) / mud gradient; bottom from the capacities
#   Bleed per cycle    on the SMALLEST annulus the gas touches anywhere along its
#                      path (end of the last bleed through the end of this one);
#                      the largest capacity that still satisfies that is used
#   Hold               standard = SICP + SF + n x Pw, RE-BASED after a shoe-limited
#                      cycle (tier 2-4) to the hold used + Pw; the hold to use is raised
#                      (never lowered) until the forecast BHP through the coming bleed
#                      is >= Pf + SF
#   Shoe limit         fracture - shoe margin (team's choice, default 0)
#   Shoe tiers         1 corrected hold keeps the shoe <= fracture
#                      2 shoe-limited hold keeps BHP >= Pf + SF
#                      3 shoe-limited hold keeps BHP between Pf and Pf + SF (SF reduced)
#                      4 shoe-limited hold puts BHP below Pf: SUPERVISOR DECISION,
#                        the BHP-keeping hold is printed (constant-BHP doctrine)
#   Gas at surface     in a wait when P <= the hold; in a bleed when P falls to it

LATERAL_GAS_GRADIENT = 0.1


def round_down_tenth(value):
    return math.floor(round(value * 10, 6)) / 10


class ReferenceVolumetric:
    """One volumetric example well (its WELL dict, plus pit gain / SIDPP)."""

    def __init__(self, well):
        self.annulus = [(c, l) for _n, c, l in well["annulus_bottom_up"]]          # bottom up
        self.td_md = well.get("td_md_ft") or sum(l for _c, l in self.annulus)
        self.td_tvd = well.get("td_tvd_ft") or self.td_md
        self.shoe_tvd = well["shoe_tvd_ft"]
        self.shoe_md = well.get("shoe_md_ft") or self.shoe_tvd
        self.path = sorted({(0, 0), (self.shoe_md, self.shoe_tvd), (self.td_md, self.td_tvd)}
                           | {(md, tvd) for _n, md, tvd in well.get("key_points", ())})
        self.mud = four(0.052 * well["original_mud_weight_ppg"])
        self.sicp, self.sidpp = well["sicp_psi"], well.get("sidpp_psi")
        self.sf, self.pw, self.pit = well["safety_margin_psi"], well["working_pressure_psi"], well["pit_gain_bbl"]
        mamw = max_allowable_mud_weight(well["lot_pressure_psi"], self.shoe_tvd, well["test_mud_weight_ppg"])
        self.fracture = math.floor(round(0.052 * mamw * self.shoe_tvd, 6))
        self.maasp = math.floor(round((mamw - well["original_mud_weight_ppg"]) * 0.052 * self.shoe_tvd, 6))
        self.shoe_margin = well.get("shoe_margin_psi", 0)
        self.limit = self.fracture - self.shoe_margin
        self.sections_down = []                      # (top MD, bottom MD, capacity), top down
        md = self.td_md
        for c, l in self.annulus:
            self.sections_down.insert(0, (md - l, md, c))
            md -= l

    def tvd(self, md):
        if md <= 0:
            return md
        for (md1, tvd1), (md2, tvd2) in zip(self.path, self.path[1:]):
            if md1 <= md <= md2:
                return whole(tvd1 + (md - md1) * (tvd2 - tvd1) / (md2 - md1))
        raise ValueError(md)

    def md_at_tvd(self, tvd):
        """Shallowest MD at a TVD (the heel, for the TVD of a lateral)."""
        for (md1, tvd1), (md2, tvd2) in zip(self.path, self.path[1:]):
            if tvd1 <= tvd <= tvd2 and tvd2 > tvd1:
                return md1 + (tvd - tvd1) * (md2 - md1) / (tvd2 - tvd1)
        return min(md for md, t in self.path if t == self.td_tvd)

    def bottom_of(self, top_md, bbl):
        for top, bottom, c in self.sections_down:
            if top_md < bottom:
                frm = max(top_md, top)
                if bbl <= (bottom - frm) * c:
                    return frm + bbl / c
                bbl -= (bottom - frm) * c
        return self.td_md

    def capacities(self, top_md, bottom_md):
        return [c for top, bottom, c in self.sections_down if top < bottom_md and bottom > top_md]


def reference_volumetric(well):
    """The forecast, cycle by cycle - see the notes above. Returns a dict."""
    w = ReferenceVolumetric(well)
    bbl, h = w.pit, 0.0                                         # influx at TD
    for c, l in w.annulus:
        if bbl <= c * l:
            h += bbl / c
            break
        bbl -= c * l
        h += l
    h_md = whole(h)
    h_tvd = w.td_tvd - w.tvd(w.td_md - h_md)
    lateral = h_tvd == 0
    if w.sidpp is not None:
        pf, estimated = w.sidpp + whole(w.mud * w.td_tvd), False
        g0 = LATERAL_GAS_GRADIENT if lateral else four(w.mud - four((w.sicp - w.sidpp) / h_tvd))
    else:
        g0, estimated = LATERAL_GAS_GRADIENT, True
        pf = whole(w.sicp + w.mud * (w.td_tvd - h_tvd) + g0 * h_tvd)
    p0 = pf - g0 * h_tvd
    k = p0 * w.pit
    heel = w.md_at_tvd(w.td_tvd)

    def state(casing, v):
        p = k / v
        top_tvd = (p - casing) / w.mud
        if top_tvd <= 0:
            return None
        g = g0 * p / p0
        top = heel if top_tvd >= w.td_tvd else w.md_at_tvd(top_tvd)
        bottom = w.bottom_of(top, v)
        layers = [(0, top, w.mud), (top, bottom, g), (bottom, w.td_md, w.mud)]

        def hydro(down_to):
            return sum(gr * (w.tvd(min(b, down_to)) - w.tvd(t)) for t, b, gr in layers if t < down_to)
        return {"top": top, "bottom": bottom, "top_tvd": w.tvd(top), "bhp": casing + hydro(w.td_md),
                "shoe": casing + hydro(w.shoe_md)}

    caps = sorted({c for c, _l in w.annulus})

    def bleed_at(hold, v, prev_bottom):
        here = state(hold, v)
        pick = caps[0]
        for c in caps:
            b = round_down_tenth(w.pw / w.mud * c)
            end = state(hold, tenth(v + b))
            lo = end["top"] if end else 0
            hi = max(prev_bottom, here["bottom"], end["bottom"] if end else 0)
            if min(w.capacities(lo, hi)) >= c:
                pick = c
        return pick, round_down_tenth(w.pw / w.mud * pick)

    def through(hold, v, b):
        """Lowest BHP and highest shoe from the start to the end of a bleed (every 0.1 bbl)."""
        states = [state(hold, tenth(v + x / 10)) for x in range(0, whole(b * 10) + 1)]
        states = [s for s in states if s]
        return min(s["bhp"] for s in states), max(s["shoe"] for s in states)

    # the path starts at the bubble: at TD, or at the heel when the influx lies in the lateral
    start_bottom = w.bottom_of(heel, w.pit) if lateral else w.td_md
    cycles, bled, prev_bottom, used, surface = [], 0.0, start_bottom, None, None
    standard, rebase = None, False
    n = 0
    while True:
        n += 1
        v = tenth(w.pit + bled)
        base = w.sicp + w.sf + w.pw if used is None else used + w.pw
        standard = base if (standard is None or rebase) else standard + w.pw
        if k / v <= base:                                       # gas reaches surface in the wait
            surface = {"cycle": n - 1, "during": "wait", "casing": whole(k / v), "bled": bled, "volume": tenth(v)}
            break
        hold = base
        for _ in range(20):                                     # raise to keep BHP >= Pf + SF
            if k / v <= hold or state(hold, v) is None:
                break
            _cap, b = bleed_at(hold, v, prev_bottom)
            low, _high = through(hold, v, b)
            short = math.ceil(round(pf + w.sf - low, 6))
            if short <= 0:
                break
            hold += short
        if k / v <= hold:
            surface = {"cycle": n - 1, "during": "wait", "casing": whole(k / v), "bled": bled, "volume": tenth(v)}
            break
        corrected = hold
        cap, b = bleed_at(corrected, v, prev_bottom)
        low, high = through(corrected, v, b)
        tier, decision = (1 if corrected > base else 0), None
        if high > w.limit:
            limited, high_l = corrected, high
            for _ in range(20):                                 # step down until the shoe is at the limit
                limited -= math.ceil(round(high_l - w.limit, 6))
                cap_l, b_l = bleed_at(limited, v, prev_bottom)
                low_l, high_l = through(limited, v, b_l)
                if high_l <= w.limit:
                    break
            if low_l >= pf + w.sf:
                tier, hold, cap, b, low, high = 2, limited, cap_l, b_l, low_l, high_l
            elif low_l >= pf:
                tier, hold, cap, b, low, high = 3, limited, cap_l, b_l, low_l, high_l
            else:
                tier = 4
                decision = {"bhp_hold": corrected, "bhp_low_vs_pf": whole(low - pf),
                            "shoe_over": whole(high - w.limit), "shoe_hold": limited,
                            "shoe_hold_bhp_vs_pf": whole(low_l - pf)}
        here = state(hold, v)
        row = {"cycle": n, "standard": standard, "hold": hold, "correction": corrected - base,
               "tier": tier, "capacity": cap, "bleed": b, "gas_top_tvd": here["top_tvd"],
               "gas_below_shoe": here["top"] > w.shoe_md, "low_bhp_vs_pf": whole(low - pf),
               "high_shoe": whole(high), "decision": decision}
        if k / tenth(v + b) <= hold:                            # gas reaches surface in this bleed
            row["total"] = tenth(bled + b)
            cycles.append(row)
            surface = {"cycle": n, "during": "bleed", "casing": hold, "bled": tenth(k / hold - w.pit),
                       "volume": tenth(k / hold)}
            break
        bled = tenth(bled + b)
        row["total"] = bled
        cycles.append(row)
        prev_bottom = state(hold, tenth(w.pit + bled))["bottom"]
        used, rebase = hold, tier >= 2
    return {"pf": pf, "pf_estimated": estimated, "influx_md": h_md, "influx_tvd": h_tvd, "gradient": g0,
            "cycles": cycles, "surface": surface, "fracture": w.fracture, "maasp": w.maasp,
            "precheck": w.sf + w.pw >= w.maasp - w.sicp - w.shoe_margin}
