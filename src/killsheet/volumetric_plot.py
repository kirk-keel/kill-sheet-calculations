"""Volumetric and lubricate and bleed plots: pressure against bbl bled / pumped.

No new calculations: every point comes from the volumetric sheet rows (the
holds come from volumetric_model.py) and the lubricate and bleed table. Two
charts, because their x-axes differ:

Volumetric (x = total bbl bled):
  Casing is a staircase. Flat while bleeding (casing held at the hold to use),
  straight up while shut in and waiting (the gas migrates):
      Shut in          SICP
      Each wait        up to the hold to use (standard + any geometry correction)
      Each bleed       flat at that hold, for the bleed volume
      Gas at surface   the SICP read once the gas is at surface
  A second, dashed layer shows the standard IADC hold (SICP + SF + n x Pw), and
  each correction / shoe-limited hold / supervisor decision is an annotation.
  The MAASP line stops where the gas top passes the shoe (MAASP no longer applies).
  Drill pipe (user rules) depends on where the pipe is:
      On bottom, no float   readable: it mirrors the forecast BHP -
                            DP = SIDPP + (BHP - Pf), up each wait, down each
                            bleed. The sheet says to use the drill pipe
                            pressure method instead.
      On bottom, float      no line - "no reading - float"
      Off bottom, float     no line - "no reading - float"
      Off bottom, no float  no line - "not a BHP indicator - gas may enter the string"
      Out of the hole       no line - "pipe out of hole"
  Never plot 0 unless the gauge reads 0 (user rule).

Lubricate and bleed (x = total bbl pumped), casing only (user):
      Pump      casing rises to the pump-to pressure as the bbl go in
      Bleed     casing falls (straight down) to the bleed-to pressure
"""

from killsheet.rounding import round_to_tenth

ON_BOTTOM = "on bottom"
OFF_BOTTOM = "off bottom"
OUT_OF_HOLE = "out of the hole"

NO_READING_FLOAT = "no reading - float"
NOT_A_BHP_INDICATOR = "not a BHP indicator - gas may enter the string"
PIPE_OUT_OF_HOLE = "pipe out of hole"
DP_READABLE = ("DP readable - use drill pipe pressure method "
               "(bleed holding SIDPP + safety margin constant).")


def pipe_position(pipe_bottom_md_ft, td_md_ft):
    """Where the pipe is: on bottom (at TD), off bottom, or out of the hole (no pipe)."""
    if pipe_bottom_md_ft is None:
        return OUT_OF_HOLE
    if pipe_bottom_md_ft > td_md_ft:
        raise ValueError(f"Pipe bottom ({pipe_bottom_md_ft:,} ft MD) can't be below TD ({td_md_ft:,} ft MD)")
    return ON_BOTTOM if pipe_bottom_md_ft == td_md_ft else OFF_BOTTOM


def drill_pipe_reading(position, float_in_string):
    """What the drill pipe line shows: None (a line is drawn) or the label used instead of a line."""
    if position == OUT_OF_HOLE:
        return PIPE_OUT_OF_HOLE
    if float_in_string:
        return NO_READING_FLOAT
    if position == OFF_BOTTOM:
        return NOT_A_BHP_INDICATOR
    return None                                    # on bottom, no float: readable


def pipe_note(position, float_in_string, pipe_bottom_md_ft):
    """One line for the sheet: where the pipe is and what that means for the drill pipe gauge."""
    if position == OUT_OF_HOLE:
        return "Pipe out of the hole: casing only."
    where = "on bottom" if position == ON_BOTTOM else f"off bottom at {pipe_bottom_md_ft:,} ft MD"
    if float_in_string:
        return f"Pipe {where}, float in the string: no drill pipe reading - casing only."
    if position == OFF_BOTTOM:
        return (f"Pipe {where}, no float: the drill pipe is not a BHP indicator "
                "(gas below the bit; gas may enter the string) - casing only.")
    return (f"Pipe {where}, no float: {DP_READABLE} Drill pipe pressure method valid only if the string is "
            "open. If the string or bit is plugged, the drill pipe gauge is not a BHP indicator. "
            "Use volumetric on casing.")


def volumetric_points(rows, sicp_psi, sicp_gas_at_surface_psi, sidpp_psi=None):
    """The volumetric chart: {"points": [...], "annotations": [...], "maasp_until_bbl": x or None}.

    rows: the volumetric sheet rows (dicts) - hold_psi, standard_hold_psi, bleed_bbl,
          total_bled_bbl, gas_at_surface, correction_psi, tier, warning, gas_below_shoe,
          bhp_at_hold_vs_pf_psi, bhp_after_bleed_vs_pf_psi (None beyond the forecast).
    sidpp_psi: only when the drill pipe is readable (on bottom, no float).
    Each point: {bbl, casing_psi, standard_psi, drill_pipe_psi, label}.
    """
    def dp(bhp_vs_pf):
        return None if sidpp_psi is None or bhp_vs_pf is None else sidpp_psi + bhp_vs_pf

    points = [{"bbl": 0, "casing_psi": sicp_psi, "standard_psi": sicp_psi, "drill_pipe_psi": dp(0),
               "label": "shut in"}]
    annotations, maasp_until, before = [], None, 0
    for row in rows:
        points.append({"bbl": before, "casing_psi": row["hold_psi"], "standard_psi": row["standard_hold_psi"],
                       "drill_pipe_psi": dp(row["bhp_at_hold_vs_pf_psi"]),
                       "label": f"wait: casing rises to {row['hold_psi']:,} psi"})
        points.append({"bbl": row["total_bled_bbl"], "casing_psi": row["hold_psi"],
                       "standard_psi": row["standard_hold_psi"], "drill_pipe_psi": dp(row["bhp_after_bleed_vs_pf_psi"]),
                       "label": f"cycle {row['cycle']}: bleed {row['bleed_bbl']:.1f} bbl holding {row['hold_psi']:,} psi"})
        if row["correction_psi"]:
            annotations.append({"bbl": before, "psi": row["hold_psi"], "kind": "correction",
                                 "text": f"c{row['cycle']} +{row['correction_psi']:,} psi (gas gaining vertical height)"})
        if row["tier"] in (2, 3, 4):
            kind = "supervisor" if row["tier"] == 4 else "shoe"
            annotations.append({"bbl": before, "psi": row["hold_psi"], "kind": kind, "text": row["warning"]
                                or f"c{row['cycle']} hold limited by the shoe"})
        if maasp_until is None and row["gas_below_shoe"] is False:
            maasp_until = before
            annotations.append({"bbl": before, "psi": None, "kind": "shoe passed",
                                "text": "gas top passes the shoe - MAASP no longer applies"})
        before = row["total_bled_bbl"]
        if row["gas_at_surface"]:
            last = rows[-1]["bhp_after_bleed_vs_pf_psi"]
            points.append({"bbl": before, "casing_psi": sicp_gas_at_surface_psi,
                           "standard_psi": sicp_gas_at_surface_psi,
                           "drill_pipe_psi": dp(None if last is None else last + sicp_gas_at_surface_psi - row["hold_psi"]),
                           "label": "gas at surface"})
    return {"points": points, "annotations": annotations, "maasp_until_bbl": maasp_until}


def lubricate_and_bleed_points(sicp_gas_at_surface_psi, lubricate_rows):
    """The lubricate and bleed chart (casing only): list of dicts {bbl, casing_psi, label}.

    lubricate_rows: from lubricate_and_bleed.lubricate_and_bleed_table.
    """
    points = [{"bbl": 0, "casing_psi": sicp_gas_at_surface_psi, "label": "gas at surface"}]
    total_bbl = 0
    for row in lubricate_rows:
        total_bbl = round_to_tenth(total_bbl + row.bbl_pumped)
        points.append({"bbl": total_bbl, "casing_psi": row.pump_to_psi,
                       "label": f"cycle {row.cycle}: pump {row.bbl_pumped:.1f} bbl"})
        points.append({"bbl": total_bbl, "casing_psi": row.bleed_to_psi,
                       "label": "hydrostatic control regained" if row.bleed_to_psi == 0 else "bleed gas"})
    return points
