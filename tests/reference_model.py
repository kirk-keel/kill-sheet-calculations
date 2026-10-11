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
