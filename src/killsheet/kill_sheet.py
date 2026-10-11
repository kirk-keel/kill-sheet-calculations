"""The whole kill sheet in one place: every number the printed sheet and the
web page show, worked out once with the calculator's own functions.

Nothing new is calculated here - this module only calls the tested formulas,
strokes, schedule and kill step functions in the right order and collects the
answers. The printer (examples/kill_sheet_printer.py) and the web page
(web/app.py) both draw from it, so they can never disagree.

Sections are (name, capacity bbl/ft, length ft MD) - the name is only for
display. Key points are (name, MD ft, TVD ft). Results are plain dicts and
lists so the web page can read them as JSON.
"""

from killsheet.depths import tvd_at_md
from killsheet.drillers import drillers_method
from killsheet.formulas import (
    final_circulating_pressure,
    initial_circulating_pressure,
    kill_mud_overbalance,
    kill_mud_weight,
    maasp,
    max_allowable_mud_weight,
)
from killsheet.formulas import PSI_PER_FT_PER_PPG
from killsheet.kill_plot import LATERAL_NOTE as LATERAL_GRADIENT_NOTE
from killsheet.kill_plot import (
    MODEL_LIMITS,
    drillers_kill_plot,
    fracture_at_shoe,
    shoe_margin_warning,
    wait_and_weight_kill_plot,
)
from killsheet.rounding import round_to_tenth
from killsheet.lubricate_and_bleed import (
    cycles_past_kop,
    end_of_lubricate_and_bleed,
    kill_mud_column_ft,
    lubricate_and_bleed_to_volume,
    remaining_underbalance,
)
from killsheet.schedule import TEN_STEPS, pressure_schedule
from killsheet.strokes import (
    bit_to_shoe_strokes,
    bit_to_surface_strokes,
    check_section_lengths,
    section_volume,
    strokes_for_volume,
    strokes_to_length,
    surface_to_bit_strokes,
    total_volume,
)
from killsheet.volumetric import (
    angle_corrected_volume_to_bleed,
    annular_capacity_choices,
    gas_at_surface,
    mud_gradient,
    volume_to_bleed_per_cycle,
)
from killsheet.volumetric_model import (
    ANNULUS_AT_THE_GAS,
    LATERAL_NOTE,
    PF_ESTIMATED,
    SHOE_AT_HEEL_NOTE,
    TIERS,
    Annulus,
    VolumetricModel,
    arrival_warning,
    correction_note,
    influx_at_shut_in,
    maasp_label,
    precheck_warning,
    tier_warning,
)
from killsheet.volumetric_plot import (
    ON_BOTTOM,
    drill_pipe_reading,
    lubricate_and_bleed_points,
    pipe_note,
    pipe_position,
    volumetric_points,
)
from killsheet.wait_and_weight import (
    ICP_MATCHES,
    ICP_RECALCULATED,
    actual_scr_pressure,
    kill_pressures_at_kill_rate,
    wait_and_weight_method,
)

DRILLERS = "Driller's method"
WAIT_AND_WEIGHT = "Wait and Weight"

PLOT_NEEDS_PIT_GAIN = "Enter the pit gain to forecast the kill plot."


def kill_mud_rounding_note(sidpp_psi, bit_tvd_ft, original_mud_weight_ppg, kill_mud_weight_ppg, overbalance_psi):
    """Wait and Weight: what rounding the kill mud UP adds to BHP during the step-down.

        Exact KMW = OMW + SIDPP / (0.052 x Bit TVD)   (shown to 3 places, for information)
        Added     = Kill mud overbalance - SIDPP
    The schedule takes off SIDPP; the kill mud adds the whole overbalance.
    """
    exact = original_mud_weight_ppg + sidpp_psi / (PSI_PER_FT_PER_PPG * bit_tvd_ft)
    return (f"Kill mud rounding ({exact:.3f} -> {kill_mud_weight_ppg:.1f} ppg) adds "
            f"{overbalance_psi - sidpp_psi:,} psi to BHP during the step-down.")


def without_names(sections):
    """(name, capacity, length) -> (capacity, length), for the calculator."""
    return [(capacity, length) for _name, capacity, length in sections]


def depth_rows(rows, survey):
    """Group (name, MD) rows by MD - names at the same MD are joined - and add TVD."""
    by_md = {}
    for name, md_ft in rows:
        by_md.setdefault(md_ft, []).append(name)
    return [(" / ".join(names), md_ft, tvd_at_md(md_ft, survey)) for md_ft, names in by_md.items()]


def section_depths(sections, top_md_ft=0, down=True):
    """Each section's name, top and bottom MD (ft) and rounded volume (bbl), for the schematic.

    down=True: listed top down from top_md_ft (drill string).
    down=False: listed bottom up from top_md_ft, here the BOTTOM (annulus from the bit up).
    """
    rows = []
    md_ft = top_md_ft
    for name, capacity, length in sections:
        top, bottom = (md_ft, md_ft + length) if down else (md_ft - length, md_ft)
        rows.append({"name": name, "top_md_ft": top, "bottom_md_ft": bottom,
                     "volume_bbl": section_volume(capacity, length)})
        md_ft = bottom if down else top
    return rows


def volume_table(string, open_hole, cased_hole, pump_output_bbl_per_stk, surface_line_volume_bbl,
                 surface_to_bit_stks, bit_to_shoe_stks, bit_to_surface_stks):
    """Volumes (bbl, rounded to 0.1) and strokes for page 1 of the kill sheet.

        Volume  = sum of each section's rounded volume
        Strokes = Volume / Pump output (whole strokes)
    The total well system follows the same rule (user rule: a stroke can't be split), so
    it can be a stroke off Surface to bit + Bit to surface (baseline 6,185 vs 6,184).
    """
    string_bbl = total_volume(string)
    surface_to_bit_bbl = round_to_tenth(surface_line_volume_bbl + string_bbl)
    open_hole_bbl = total_volume(open_hole)
    cased_hole_bbl = total_volume(cased_hole)
    annulus_bbl = total_volume(open_hole + cased_hole)
    total_bbl = round_to_tenth(surface_to_bit_bbl + annulus_bbl)
    rows = []
    if surface_line_volume_bbl:
        rows.append(("Surface lines", surface_line_volume_bbl,
                     strokes_for_volume(surface_line_volume_bbl, pump_output_bbl_per_stk)))
        rows.append(("Drill string", string_bbl, strokes_for_volume(string_bbl, pump_output_bbl_per_stk)))
    rows += [
        ("Surface to bit", surface_to_bit_bbl, surface_to_bit_stks),
        ("Open hole annulus (bit to shoe)", open_hole_bbl, bit_to_shoe_stks),
        ("Cased hole annulus (shoe to surface)", cased_hole_bbl,
         strokes_for_volume(cased_hole_bbl, pump_output_bbl_per_stk)),
        ("Total annulus (bit to surface)", annulus_bbl, bit_to_surface_stks),
        ("Total well system", total_bbl, strokes_for_volume(total_bbl, pump_output_bbl_per_stk)),
    ]
    return [{"name": name, "volume_bbl": bbl, "strokes": stks} for name, bbl, stks in rows]


def kill_sheet(
    title,
    bit_tvd_ft,
    shoe_tvd_ft,
    original_mud_weight_ppg,
    lot_pressure_psi,
    test_mud_weight_ppg,
    sidpp_psi,
    sicp_psi,
    scr_pressure_psi,
    safety_margin_psi,
    pump_output_bbl_per_stk,
    drill_string,
    open_hole_annulus,
    cased_hole_annulus,
    bit_md_ft=None,
    shoe_md_ft=None,
    key_points=(),
    surface_line_volume_bbl=0,
    method=DRILLERS,
    step_method=TEN_STEPS,
    sidpp_at_start_psi=None,
    sicp_at_start_psi=None,
    observed_icp_psi=None,
    pit_gain_bbl=None,
):
    """The Driller's or Wait and Weight kill sheet.

    Vertical well: leave out bit_md_ft, shoe_md_ft and key_points (MD = TVD).
    Deviated or horizontal well: give the bit and shoe MD, and key points
    such as KOP, end of build and the heel as (name, MD, TVD).

    safety_margin_psi: SF held on bottom for the whole kill, chosen by the team.
    pit_gain_bbl: the kick size, for the kill plot (killsheet.kill_plot). Leave
                  out for no plot.

    Wait and Weight only:
      sidpp_at_start_psi - SIDPP retaken (float bumped) just before pump start-up
                           (defaults to sidpp_psi)
      sicp_at_start_psi  - SICP retaken just before pump start-up (defaults to sicp_psi)
      observed_icp_psi   - drill pipe reading once at kill rate (ICP + SF); if it reads
                           more than 10 psi HIGH, ICP/FCP are recalculated (FCP never lower)
    """
    if method not in (DRILLERS, WAIT_AND_WEIGHT):
        raise ValueError(f"method must be {DRILLERS!r} or {WAIT_AND_WEIGHT!r}")
    bit_md_ft = bit_tvd_ft if bit_md_ft is None else bit_md_ft
    shoe_md_ft = shoe_tvd_ft if shoe_md_ft is None else shoe_md_ft
    survey = [(md, tvd) for _name, md, tvd in key_points]
    survey += [(shoe_md_ft, shoe_tvd_ft), (bit_md_ft, bit_tvd_ft)]

    string = without_names(drill_string)
    open_hole = without_names(open_hole_annulus)
    annulus = without_names(open_hole_annulus + cased_hole_annulus)
    pump = pump_output_bbl_per_stk
    check_section_lengths(string, open_hole, without_names(cased_hole_annulus), bit_md_ft, shoe_md_ft)

    kmw = kill_mud_weight(sidpp_psi, bit_tvd_ft, original_mud_weight_ppg)
    icp = initial_circulating_pressure(sidpp_psi, scr_pressure_psi)
    fcp = final_circulating_pressure(scr_pressure_psi, kmw, original_mud_weight_ppg)
    mamw = max_allowable_mud_weight(lot_pressure_psi, shoe_tvd_ft, test_mud_weight_ppg)
    stb = surface_to_bit_strokes(string, pump, surface_line_volume_bbl)
    sf = safety_margin_psi

    # Drill string, top down: key points and the bottom of each section.
    rows = [(name, md) for name, md, _tvd in key_points]
    md_ft = 0
    for name, _capacity, length in drill_string:
        md_ft += length
        rows.append((f"bottom of {name}", md_ft))
    rows[-1] = ("bit", bit_md_ft)
    string_depths = [
        {"name": name, "md_ft": md, "tvd_ft": tvd,
         "strokes": strokes_to_length(string, md, pump, surface_line_volume_bbl)}
        for name, md, tvd in sorted(depth_rows(rows, survey), key=lambda row: row[1])
    ]

    # Annulus, bit up: key points, the shoe and the top of each section.
    rows = [(name, md) for name, md, _tvd in key_points if md < bit_md_ft]
    rows.append(("shoe", shoe_md_ft))
    md_ft = bit_md_ft
    for name, _capacity, length in open_hole_annulus + cased_hole_annulus:
        md_ft -= length
        rows.append((f"top of {name}", md_ft))
    rows[-1] = ("surface", 0)
    annulus_depths = [
        {"name": name, "md_ft": md, "tvd_ft": tvd, "strokes": strokes_to_length(annulus, bit_md_ft - md, pump)}
        for name, md, tvd in sorted(depth_rows(rows, survey), key=lambda row: -row[1])
    ]

    sheet = {
        "title": title,
        "method": method,
        "kill_mud_weight_ppg": kmw,
        "icp_psi": icp,
        "fcp_psi": fcp,
        "max_allowable_mud_weight_ppg": mamw,
        "maasp_original_psi": maasp(mamw, original_mud_weight_ppg, shoe_tvd_ft),
        "maasp_after_kill_psi": maasp(mamw, kmw, shoe_tvd_ft),
        "surface_to_bit_strokes": stb,
        "bit_to_shoe_strokes": bit_to_shoe_strokes(open_hole, pump),
        "bit_to_surface_strokes": bit_to_surface_strokes(annulus, pump),
        "string_depths": string_depths,
        "annulus_depths": annulus_depths,
        "safety_margin_psi": sf,
        "icp_check": None,
        "step_method": None,
        "schedule": None,
        "kill_mud_rounding_note": None,
    }
    btsurf = sheet["bit_to_surface_strokes"]
    sheet["volumes"] = volume_table(string, open_hole, without_names(cased_hole_annulus), pump,
                                    surface_line_volume_bbl, stb, sheet["bit_to_shoe_strokes"], btsurf)
    sheet["schematic"] = {
        "bit_md_ft": bit_md_ft, "bit_tvd_ft": bit_tvd_ft, "shoe_md_ft": shoe_md_ft, "shoe_tvd_ft": shoe_tvd_ft,
        "key_points": [{"name": name, "md_ft": md, "tvd_ft": tvd} for name, md, tvd in key_points],
        "string": section_depths(drill_string),
        "annulus": section_depths(open_hole_annulus + cased_hole_annulus, bit_md_ft, down=False),
    }

    if pit_gain_bbl is not None and pit_gain_bbl <= 0:
        raise ValueError("Pit gain must be greater than 0 bbl.")
    plot_inputs = dict(
        original_mud_weight_ppg=original_mud_weight_ppg, kill_mud_weight_ppg=kmw, bit_tvd_ft=bit_tvd_ft,
        shoe_tvd_ft=shoe_tvd_ft, mamw_ppg=mamw, maasp_psi=sheet["maasp_original_psi"],
        drill_string_sections=string, annulus_sections=annulus, pump_output_bbl_per_stk=pump,
        surface_line_volume_bbl=surface_line_volume_bbl, safety_margin_psi=sf, pit_gain_bbl=pit_gain_bbl,
        bit_md_ft=bit_md_ft, shoe_md_ft=shoe_md_ft, key_points=key_points,
    )
    plot = None

    if method == DRILLERS:
        overbalance = kill_mud_overbalance(kmw, original_mud_weight_ppg, bit_tvd_ft)
        steps = drillers_method(sidpp_psi, sicp_psi, icp, fcp, stb, btsurf, sf, overbalance)
        if pit_gain_bbl is not None:
            plot = drillers_kill_plot(sidpp_psi=sidpp_psi, sicp_psi=sicp_psi, icp_psi=icp, fcp_psi=fcp,
                                      **plot_inputs)
    else:
        sidpp_at_start = sidpp_psi if sidpp_at_start_psi is None else sidpp_at_start_psi
        sicp_at_start = sicp_psi if sicp_at_start_psi is None else sicp_at_start_psi
        friction = None
        if observed_icp_psi is not None:
            check = {"icp_plus_sf_psi": icp + sf, "observed_psi": observed_icp_psi}
            icp, fcp, status = kill_pressures_at_kill_rate(
                icp, fcp, observed_icp_psi, sidpp_at_start, kmw, original_mud_weight_ppg, sf
            )
            if status == ICP_MATCHES:
                check["message"] = "within +/-10 psi - use the calculated ICP and FCP"
            elif status == ICP_RECALCULATED:
                check["message"] = (f"more than 10 psi high - RECALCULATED from retaken SIDPP "
                                    f"{sidpp_at_start:,} psi: ICP {icp:,} psi, FCP {fcp:,} psi "
                                    "(FCP is never lower than calculated)")
                friction = final_circulating_pressure(
                    actual_scr_pressure(observed_icp_psi, sidpp_at_start, sf), kmw, original_mud_weight_ppg)
            else:
                check["message"] = ("more than 10 psi low - a complication; calculated ICP and FCP "
                                    "are kept (never recalculated lower)")
            check["status"] = status
            sheet["icp_check"] = check
        steps = wait_and_weight_method(sicp_at_start, icp, fcp, kmw, stb, btsurf, sf, friction)
        schedule = pressure_schedule(icp, fcp, string, pump, surface_line_volume_bbl, step_method,
                                     sidpp_psi=sidpp_at_start, bit_tvd_ft=bit_tvd_ft, key_points=key_points)
        sheet["kill_mud_rounding_note"] = kill_mud_rounding_note(
            sidpp_psi, bit_tvd_ft, original_mud_weight_ppg, kmw,
            kill_mud_overbalance(kmw, original_mud_weight_ppg, bit_tvd_ft))
        if pit_gain_bbl is not None:
            plot = wait_and_weight_kill_plot(sidpp_psi=sidpp_at_start, sicp_psi=sicp_at_start, icp_psi=icp,
                                             fcp_psi=fcp, kill_mud_friction_psi=friction, **plot_inputs)
            # Same well, same gauges, Driller's method: is W&W worse at the shoe?
            compare = drillers_kill_plot(sidpp_psi=sidpp_at_start, sicp_psi=sicp_at_start, icp_psi=icp,
                                         fcp_psi=fcp, **plot_inputs)
            margin = shoe_margin_warning(plot, compare)
            if margin:
                plot = plot._replace(warnings=plot.warnings + [margin])
        sheet["step_method"] = step_method
        sheet["schedule"] = [
            {"strokes": row.strokes, "md_ft": row.md_ft, "tvd_ft": row.tvd_ft,
             "pressure_psi": row.pressure_psi, "pressure_plus_sf_psi": row.pressure_psi + sf, "label": row.label}
            for row in schedule
        ]
    sheet["steps"] = [step._asdict() for step in steps]
    if pit_gain_bbl is None:
        sheet["plot"] = {"unavailable": PLOT_NEEDS_PIT_GAIN}
    else:
        sheet["plot"] = {
            "pit_gain_bbl": pit_gain_bbl,
            "points": [point._asdict() for point in plot.points],
            "peak_casing": plot.peak_casing._asdict(),
            "max_shoe": plot.max_shoe._asdict(),
            "fracture_at_shoe_psi": plot.fracture_at_shoe_psi,
            "maasp_psi": sheet["maasp_original_psi"],
            "trapped_drill_pipe_psi": plot.trapped_drill_pipe_psi,
            "trapped_casing_psi": plot.trapped_casing_psi,
            "warnings": plot.warnings,
            "notes": list(plot.notes),
            "casing_forecast_valid": plot.casing_forecast_valid,
            "model_limits": MODEL_LIMITS,
        }
    return sheet


def volumetric_sheet(
    title,
    original_mud_weight_ppg,
    kill_mud_weight_ppg,
    shoe_tvd_ft,
    lot_pressure_psi,
    test_mud_weight_ppg,
    sicp_psi,
    safety_margin_psi,
    working_pressure_psi,
    annulus_bottom_up,
    sicp_rises_after_each_cycle,
    sicp_gas_at_surface_psi,
    bbl_pumped_each_cycle,
    pit_gain_bbl,
    capacity_choice=ANNULUS_AT_THE_GAS,
    td_md_ft=None,
    td_tvd_ft=None,
    shoe_md_ft=None,
    key_points=(),
    pipe_bottom_md_ft=None,
    float_in_string=False,
    sidpp_psi=None,
    shoe_margin_psi=0,
):
    """Volumetric method, then lubricate and bleed, for any situation.

    annulus_bottom_up: (name, capacity bbl/ft, length ft MD) from the BOTTOM UP,
    including sections with no pipe in them. The top section is the annulus
    at surface, used for lubricate and bleed.
    kill_mud_weight_ppg: the mud LUBRICATED (kill mud; original mud for a swabbed kick).
    pit_gain_bbl: the kick size - the forecast (volumetric_model.py) needs it.
    capacity_choice: ANNULUS_AT_THE_GAS (default: the forecast picks the annulus the
    gas is in, conservatively), or the team's fixed SMALLEST / AVERAGE / LONGEST.

    Vertical well: leave out td_md_ft, td_tvd_ft, shoe_md_ft and key_points.
    Deviated or horizontal well: give the TD and shoe MD/TVD and the key points
    as (name, MD, TVD). The angle-corrected volume for each section is shown for information.

    Where the pipe is (for the plot and the schematic):
      pipe_bottom_md_ft - blank = out of the hole; TD = on bottom; shallower = off bottom
      float_in_string   - True: no drill pipe reading
      sidpp_psi         - on bottom with no float (the drill pipe is readable); it also
                          gives Pf - without it Pf is estimated from SICP

    shoe_margin_psi: the team's margin below fracture at the shoe (default 0) - the shoe
                     tiers and the pre-check use fracture - shoe margin.

    The crew's readings drive the table: SICP rise over each 15 minute wait (gas at
    surface at 10 psi or less), SICP with the gas at surface, bbl pumped each L&B cycle.
    """
    annulus = without_names(annulus_bottom_up)
    gradient = mud_gradient(original_mud_weight_ppg)
    lubricated_gradient = mud_gradient(kill_mud_weight_ppg)
    mamw = max_allowable_mud_weight(lot_pressure_psi, shoe_tvd_ft, test_mud_weight_ppg)
    maasp_psi = maasp(mamw, original_mud_weight_ppg, shoe_tvd_ft)
    fracture_psi = fracture_at_shoe(mamw, shoe_tvd_ft)
    choices = annular_capacity_choices(annulus)
    sf, pw = safety_margin_psi, working_pressure_psi

    td_md = td_md_ft if td_md_ft is not None else sum(length for _name, _cap, length in annulus_bottom_up)
    td_tvd = td_tvd_ft if td_tvd_ft is not None else td_md
    shoe_md = shoe_md_ft if shoe_md_ft is not None else shoe_tvd_ft
    vertical = td_md == td_tvd and not key_points
    survey = [(md, tvd) for _name, md, tvd in key_points] + [(shoe_md, shoe_tvd_ft), (td_md, td_tvd)]
    sections, horizontal = [], False
    if vertical:
        sections = [{"name": name, "capacity_bbl_per_ft": capacity, "length_ft": length}
                    for name, capacity, length in annulus_bottom_up]
    else:
        bottom_md = td_md
        for name, capacity, length in annulus_bottom_up:
            top_md = bottom_md - length
            section_tvd = tvd_at_md(bottom_md, survey) - tvd_at_md(top_md, survey)
            corrected = angle_corrected_volume_to_bleed(pw, gradient, capacity, length, section_tvd)
            horizontal = horizontal or corrected is None
            sections.append({"name": name, "capacity_bbl_per_ft": capacity, "length_ft": length,
                             "tvd_ft": section_tvd, "tvd_over_md": section_tvd / length,
                             "angle_corrected_bleed_bbl": corrected})
            bottom_md = top_md

    position = pipe_position(pipe_bottom_md_ft, td_md)
    no_line = drill_pipe_reading(position, float_in_string)
    if no_line is None and sidpp_psi is None:
        raise ValueError("Pipe on bottom with no float: the drill pipe is readable - enter the SIDPP.")

    # The forecast: where the gas is, the hold to use, the shoe.
    well = Annulus(annulus, td_md, td_tvd, shoe_md, shoe_tvd_ft, key_points)
    influx = influx_at_shut_in(well, pit_gain_bbl, sicp_psi, sidpp_psi, gradient)
    fixed = None if capacity_choice == ANNULUS_AT_THE_GAS else choices[capacity_choice]
    model = VolumetricModel(well, influx, gradient, sicp_psi, sf, pw, fracture_psi, pit_gain_bbl, fixed,
                            shoe_margin_psi)
    forecast, model_surface = model.forecast()

    # The table: the readings decide when the gas is at surface; the forecast gives each hold.
    rows, total, hold, standard, last = [], 0.0, sicp_psi + sf, sicp_psi + sf, None
    for cycle, rise in enumerate(sicp_rises_after_each_cycle, start=1):
        f = forecast[cycle - 1] if cycle <= len(forecast) else None
        if f:
            hold, bleed_bbl, capacity = f.hold_psi, f.bleed_bbl, f.capacity_bbl_per_ft
            if cycle == model_surface.cycle and model_surface.during == "bleed":
                bleed_bbl = round_to_tenth(model_surface.bled_bbl - total)   # gas at the choke: stop bleeding
            standard = f.standard_hold_psi
        else:                                     # beyond the forecast: the standard step
            hold, bleed_bbl, capacity = hold + pw, last["bleed_bbl"], last["capacity_bbl_per_ft"]
            standard += pw
        total = round_to_tenth(total + bleed_bbl)
        row = {
            "cycle": cycle, "standard_hold_psi": standard, "hold_psi": hold,
            "correction_psi": f.correction_psi if f else 0, "tier": f.tier if f else None,
            "capacity_bbl_per_ft": capacity, "bleed_bbl": bleed_bbl, "total_bled_bbl": total,
            "sicp_rise_psi": rise, "gas_at_surface": gas_at_surface(rise),
            "gas_below_shoe": f.gas_below_shoe if f else None,
            "gas_top_tvd_ft": f.gas_top_tvd_ft if f else None,
            "lowest_bhp_vs_pf_psi": f.lowest_bhp_vs_pf_psi if f else None,
            "highest_shoe_psi": f.highest_shoe_psi if f else None,
            "bhp_at_hold_vs_pf_psi": f.bhp_at_hold_vs_pf_psi if f else None,
            "bhp_after_bleed_vs_pf_psi": f.bhp_after_bleed_vs_pf_psi if f else None,
        }
        reasons = []
        if last and last["tier"] in (2, 3, 4):
            reasons.append(f"Standard re-based after shoe-limited cycle {last['cycle']}: previous hold used + Pw.")
        if row["correction_psi"]:
            reasons.append(correction_note(row["correction_psi"]))
            if row["tier"] in (0, 1) and hold - standard != row["correction_psi"]:
                reasons.append(f"Hold to use is {hold - standard:,} psi above the standard (corrections so far).")
        row["warning"] = tier_warning(f, sf, shoe_margin_psi) if f else None
        if row["warning"]:
            reasons.append(row["warning"])
        label = maasp_label(hold, maasp_psi, row["gas_below_shoe"]) if f else None
        if label:
            reasons.append(label)
        if not f:
            reasons.append("beyond the forecast (the model has the gas at surface): standard step")
        row["reasons"] = reasons
        rows.append(row)
        last = row
        if row["gas_at_surface"]:
            break

    # Gas at surface: readings vs the model.
    readings_bbl = rows[-1]["total_bled_bbl"] if rows and rows[-1]["gas_at_surface"] else None
    arrival = None
    if readings_bbl is not None:
        where = model.position(rows[-1]["hold_psi"], round_to_tenth(pit_gain_bbl + readings_bbl))
        arrival = arrival_warning(readings_bbl, model_surface.bled_bbl, where.top_tvd_ft if where else None)

    # Lubricate and bleed: until the bbl lubricated = the gas volume at surface (from the readings).
    stopping_bbl = round_to_tenth(pit_gain_bbl + (readings_bbl or 0))
    surface_capacity = annulus[-1][0]
    lube = lubricate_and_bleed_to_volume(sicp_gas_at_surface_psi, pw, bbl_pumped_each_cycle,
                                         lubricated_gradient, surface_capacity, stopping_bbl)
    lubricated = round_to_tenth(sum(row.bbl_pumped for row in lube))
    end_casing = lube[-1].bleed_to_psi if lube else sicp_gas_at_surface_psi
    underbalance = remaining_underbalance(influx.formation_psi, lubricated, lubricated_gradient, gradient,
                                          td_tvd, surface_capacity, well.tvd)
    vertical_points = [md for _name, md, tvd in key_points if md == tvd]
    kop_md = max(vertical_points) if vertical_points else None
    past_kop = cycles_past_kop(lube, surface_capacity, kop_md)

    # What the sheet says before the tables.
    notes = [pipe_note(position, float_in_string, pipe_bottom_md_ft)]
    if influx.in_lateral:
        notes += [LATERAL_NOTE, LATERAL_GRADIENT_NOTE]
    if shoe_tvd_ft == td_tvd:
        notes.append(SHOE_AT_HEEL_NOTE)
    bleeds = []
    for row in forecast:
        if not bleeds or bleeds[-1]["capacity_bbl_per_ft"] != row.capacity_bbl_per_ft:
            bleeds.append({"capacity_bbl_per_ft": row.capacity_bbl_per_ft, "bleed_bbl": row.bleed_bbl,
                           "from_cycle": row.cycle, "bled_before_bbl": round_to_tenth(row.total_bled_bbl - row.bleed_bbl)})
    pipe = ([] if pipe_bottom_md_ft is None else
            [{"name": "pipe", "top_md_ft": 0, "bottom_md_ft": pipe_bottom_md_ft, "volume_bbl": None}])
    return {
        "title": title,
        "mud_weight_ppg": original_mud_weight_ppg,
        "mud_gradient_psi_per_ft": gradient,
        "kill_mud_weight_ppg": kill_mud_weight_ppg,
        "kill_mud_gradient_psi_per_ft": lubricated_gradient,
        "maasp_psi": maasp_psi,
        "fracture_psi": fracture_psi,
        "shoe_margin_psi": shoe_margin_psi,
        "tiers": TIERS,
        "safety_margin_psi": sf,
        "working_pressure_psi": pw,
        "pit_gain_bbl": pit_gain_bbl,
        "influx": {"height_md_ft": influx.height_md_ft, "height_tvd_ft": influx.height_tvd_ft,
                   "gradient_psi_per_ft": influx.gradient_psi_per_ft, "formation_psi": influx.formation_psi,
                   "pf_note": PF_ESTIMATED if influx.pf_estimated else f"from SIDPP {sidpp_psi:,} psi"},
        "precheck": precheck_warning(sicp_psi, sf, pw, maasp_psi, shoe_margin_psi),
        "notes": notes,
        "vertical": vertical,
        "sections": sections,
        "horizontal_note": horizontal,
        "capacity_choices": [
            {"choice": choice, "capacity_bbl_per_ft": capacity, "used": choice == capacity_choice,
             "bleed_bbl": volume_to_bleed_per_cycle(pw, gradient, capacity)}
            for choice, capacity in choices.items()
        ],
        "capacity_choice": capacity_choice,
        "bleed_by_annulus": bleeds,
        "sicp_psi": sicp_psi,
        "volumetric": rows,
        "model_gas_at_surface": model_surface._asdict(),
        "readings_gas_at_surface_bbl": readings_bbl,
        "arrival_warning": arrival,
        "surface_capacity_bbl_per_ft": surface_capacity,
        "stopping_volume_bbl": stopping_bbl,
        "model_gas_volume_bbl": model_surface.gas_volume_bbl,
        "lubricate_and_bleed": [dict(row._asdict(), past_kop=row.cycle in past_kop) for row in lube],
        "lubricated_bbl": lubricated,
        "end_casing_psi": end_casing,
        "remaining_underbalance_psi": underbalance,
        "end_message": end_of_lubricate_and_bleed(end_casing, underbalance, sf),
        "kop_md_ft": kop_md,
        "kill_mud_column_ft": kill_mud_column_ft(lubricated, surface_capacity) if kop_md is not None else None,
        "passed_kop": bool(past_kop),
        "pipe_position": position,
        "pipe_note": notes[0],
        "plot": {
            "volumetric": volumetric_points(rows, sicp_psi, sicp_gas_at_surface_psi,
                                            sidpp_psi if no_line is None else None),
            "lubricate_and_bleed": lubricate_and_bleed_points(sicp_gas_at_surface_psi, lube),
            "drill_pipe_label": no_line,
            "maasp_psi": maasp_psi,
        },
        "schematic": {
            "bit_md_ft": td_md, "bit_tvd_ft": td_tvd, "bottom_name": "TD",
            "shoe_md_ft": shoe_md, "shoe_tvd_ft": shoe_tvd_ft,
            "key_points": [{"name": name, "md_ft": md, "tvd_ft": tvd} for name, md, tvd in key_points],
            "string": pipe,
            "pipe_bottom_tvd_ft": None if pipe_bottom_md_ft is None else tvd_at_md(pipe_bottom_md_ft, survey),
            "pipe_on_bottom": position == ON_BOTTOM,
        },
    }
