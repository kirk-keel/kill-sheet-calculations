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
from killsheet.kill_plot import MODEL_LIMITS, drillers_kill_plot, wait_and_weight_kill_plot
from killsheet.lubricate_and_bleed import cycles_past_kop, kill_mud_column_ft, lubricate_and_bleed_table
from killsheet.schedule import TEN_STEPS, pressure_schedule
from killsheet.strokes import (
    bit_to_shoe_strokes,
    bit_to_surface_strokes,
    check_section_lengths,
    strokes_to_length,
    surface_to_bit_strokes,
)
from killsheet.volumetric import (
    SMALLEST,
    angle_corrected_volume_to_bleed,
    annular_capacity_choices,
    mud_gradient,
    volume_to_bleed_per_cycle,
    volumetric_table,
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
PLOT_VERTICAL_ONLY = ("Kill plot for deviated and horizontal wells is coming in a later release "
                      "(vertical wells only for now).")


def without_names(sections):
    """(name, capacity, length) -> (capacity, length), for the calculator."""
    return [(capacity, length) for _name, capacity, length in sections]


def depth_rows(rows, survey):
    """Group (name, MD) rows by MD - names at the same MD are joined - and add TVD."""
    by_md = {}
    for name, md_ft in rows:
        by_md.setdefault(md_ft, []).append(name)
    return [(" / ".join(names), md_ft, tvd_at_md(md_ft, survey)) for md_ft, names in by_md.items()]


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
                  out for no plot. Vertical wells only for now.

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
    }
    btsurf = sheet["bit_to_surface_strokes"]

    if pit_gain_bbl is not None and pit_gain_bbl <= 0:
        raise ValueError("Pit gain must be greater than 0 bbl.")
    vertical = bit_md_ft == bit_tvd_ft and shoe_md_ft == shoe_tvd_ft and not key_points
    plot_inputs = dict(
        original_mud_weight_ppg=original_mud_weight_ppg, kill_mud_weight_ppg=kmw, bit_tvd_ft=bit_tvd_ft,
        shoe_tvd_ft=shoe_tvd_ft, mamw_ppg=mamw, maasp_psi=sheet["maasp_original_psi"],
        drill_string_sections=string, annulus_sections=annulus, pump_output_bbl_per_stk=pump,
        surface_line_volume_bbl=surface_line_volume_bbl, safety_margin_psi=sf, pit_gain_bbl=pit_gain_bbl,
    )
    plot = None

    if method == DRILLERS:
        overbalance = kill_mud_overbalance(kmw, original_mud_weight_ppg, bit_tvd_ft)
        steps = drillers_method(sidpp_psi, sicp_psi, icp, fcp, stb, btsurf, sf, overbalance)
        if pit_gain_bbl is not None and vertical:
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
        if pit_gain_bbl is not None and vertical:
            plot = wait_and_weight_kill_plot(sidpp_psi=sidpp_at_start, sicp_psi=sicp_at_start, icp_psi=icp,
                                             fcp_psi=fcp, kill_mud_friction_psi=friction, **plot_inputs)
        sheet["step_method"] = step_method
        sheet["schedule"] = [
            {"strokes": row.strokes, "md_ft": row.md_ft, "tvd_ft": row.tvd_ft,
             "pressure_psi": row.pressure_psi, "pressure_plus_sf_psi": row.pressure_psi + sf, "label": row.label}
            for row in schedule
        ]
    sheet["steps"] = [step._asdict() for step in steps]
    if pit_gain_bbl is None:
        sheet["plot"] = {"unavailable": PLOT_NEEDS_PIT_GAIN}
    elif not vertical:
        sheet["plot"] = {"unavailable": PLOT_VERTICAL_ONLY}
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
    capacity_choice=SMALLEST,
    td_md_ft=None,
    td_tvd_ft=None,
    shoe_md_ft=None,
    key_points=(),
):
    """Volumetric method, then lubricate and bleed, for any situation.

    annulus_bottom_up: (name, capacity bbl/ft, length ft MD) from the BOTTOM UP,
    including sections with no pipe in them. The top section is the annulus
    at surface, used for lubricate and bleed.

    Vertical well: leave out td_md_ft, td_tvd_ft, shoe_md_ft and key_points.
    Deviated or horizontal well: give the TD and shoe MD/TVD and the key points
    as (name, MD, TVD). The bleed used stays the vertical (IADC #35) volume; the
    angle-corrected volume for each section is shown for information.
    """
    annulus = without_names(annulus_bottom_up)
    gradient = mud_gradient(original_mud_weight_ppg)
    kill_gradient = mud_gradient(kill_mud_weight_ppg)
    maasp_psi = maasp(max_allowable_mud_weight(lot_pressure_psi, shoe_tvd_ft, test_mud_weight_ppg),
                      original_mud_weight_ppg, shoe_tvd_ft)
    choices = annular_capacity_choices(annulus)
    bleed_bbl = volume_to_bleed_per_cycle(working_pressure_psi, gradient, choices[capacity_choice])

    td_md = td_md_ft if td_md_ft is not None else sum(length for _name, _cap, length in annulus_bottom_up)
    td_tvd = td_tvd_ft if td_tvd_ft is not None else td_md
    shoe_md = shoe_md_ft if shoe_md_ft is not None else shoe_tvd_ft
    vertical = td_md == td_tvd and not key_points
    sections = []
    horizontal = False
    if vertical:
        sections = [{"name": name, "capacity_bbl_per_ft": capacity, "length_ft": length}
                    for name, capacity, length in annulus_bottom_up]
    else:
        survey = [(md, tvd) for _name, md, tvd in key_points] + [(shoe_md, shoe_tvd_ft), (td_md, td_tvd)]
        bottom_md = td_md
        for name, capacity, length in annulus_bottom_up:
            top_md = bottom_md - length
            section_tvd = tvd_at_md(bottom_md, survey) - tvd_at_md(top_md, survey)
            corrected = angle_corrected_volume_to_bleed(working_pressure_psi, gradient, capacity, length, section_tvd)
            horizontal = horizontal or corrected is None
            sections.append({"name": name, "capacity_bbl_per_ft": capacity, "length_ft": length,
                             "tvd_ft": section_tvd, "tvd_over_md": section_tvd / length,
                             "angle_corrected_bleed_bbl": corrected})
            bottom_md = top_md

    surface_capacity = annulus[-1][0]
    # KOP: the deepest key point that is still vertical (TVD = MD).
    vertical_points = [md for _name, md, tvd in key_points if md == tvd]
    kop_md = max(vertical_points) if vertical_points else None
    lube = lubricate_and_bleed_table(sicp_gas_at_surface_psi, working_pressure_psi, bbl_pumped_each_cycle,
                                     kill_gradient, surface_capacity)
    past_kop = cycles_past_kop(lube, surface_capacity, kop_md)
    return {
        "title": title,
        "mud_weight_ppg": original_mud_weight_ppg,
        "mud_gradient_psi_per_ft": gradient,
        "kill_mud_weight_ppg": kill_mud_weight_ppg,
        "kill_mud_gradient_psi_per_ft": kill_gradient,
        "maasp_psi": maasp_psi,
        "safety_margin_psi": safety_margin_psi,
        "working_pressure_psi": working_pressure_psi,
        "vertical": vertical,
        "sections": sections,
        "horizontal_note": horizontal,
        "capacity_choices": [
            {"choice": choice, "capacity_bbl_per_ft": capacity, "used": choice == capacity_choice,
             "bleed_bbl": volume_to_bleed_per_cycle(working_pressure_psi, gradient, capacity)}
            for choice, capacity in choices.items()
        ],
        "sicp_psi": sicp_psi,
        "first_hold_psi": sicp_psi + safety_margin_psi + working_pressure_psi,
        "volumetric": [row._asdict() for row in volumetric_table(
            sicp_psi, safety_margin_psi, working_pressure_psi, bleed_bbl, maasp_psi, sicp_rises_after_each_cycle)],
        "surface_capacity_bbl_per_ft": surface_capacity,
        "lubricate_and_bleed": [dict(row._asdict(), past_kop=row.cycle in past_kop) for row in lube],
        "kop_md_ft": kop_md,
        "kill_mud_column_ft": (kill_mud_column_ft(sum(row.bbl_pumped for row in lube), surface_capacity)
                               if kop_md is not None else None),
        "passed_kop": bool(past_kop),
    }
