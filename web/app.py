"""Runs in the browser (Pyodide). Hands the web page the example wells and
works out the kill sheet with the real killsheet package - the page only
draws what comes back.

The well data is read straight from the example files (examples/*_well.py),
so the web page and the printed examples always start from the same wells.
"""

import importlib
import json

from killsheet.kill_sheet import DRILLERS, WAIT_AND_WEIGHT, kill_sheet, volumetric_sheet
from killsheet.schedule import EVERY_100_STROKES, TEN_STEPS
from killsheet.volumetric import AVERAGE, LONGEST, SMALLEST
from killsheet.volumetric_model import ANNULUS_AT_THE_GAS

KILL_SHEET = "kill sheet"
VOLUMETRIC = "volumetric"

# The example wells offered in the dropdown: (example file, label).
# Bullheading and reverse circulation come in a later web release.
EXAMPLE_WELLS = [
    ("example_well", "Driller's - vertical, untapered (baseline)"),
    ("tapered_well", "Driller's - vertical, tapered"),
    ("deviated_well", "Driller's - deviated, untapered"),
    ("deviated_tapered_well", "Driller's - deviated, tapered"),
    ("horizontal_well", "Driller's - horizontal, untapered"),
    ("horizontal_tapered_well", "Driller's - horizontal, tapered"),
    ("wait_and_weight_well", "Wait and Weight - vertical, untapered"),
    ("wait_and_weight_tapered_well", "Wait and Weight - vertical, tapered"),
    ("wait_and_weight_deviated_well", "Wait and Weight - deviated, untapered"),
    ("wait_and_weight_deviated_tapered_well", "Wait and Weight - deviated, tapered"),
    ("wait_and_weight_horizontal_well", "Wait and Weight - horizontal, untapered"),
    ("wait_and_weight_horizontal_tapered_well", "Wait and Weight - horizontal, tapered"),
    ("volumetric_pipe_on_bottom_well", "Volumetric + L&B - pipe on bottom, vertical, untapered"),
    ("volumetric_pipe_on_bottom_no_float_well", "Volumetric + L&B - pipe on bottom, NO float, vertical, untapered"),
    ("volumetric_pipe_above_influx_well", "Volumetric + L&B - pipe above the influx, vertical, untapered"),
    ("volumetric_pipe_out_of_hole_well", "Volumetric + L&B - pipe out of the hole, vertical"),
    ("volumetric_tapered_pipe_on_bottom_well", "Volumetric + L&B - pipe on bottom, vertical, tapered"),
    ("volumetric_tapered_shoe_at_risk_well", "Volumetric + L&B - tapered, 10 bbl, SHOE AT RISK at shut-in"),
    ("volumetric_tapered_pipe_above_influx_well", "Volumetric + L&B - pipe above the influx, vertical, tapered"),
    ("volumetric_tapered_pipe_out_of_hole_well", "Volumetric + L&B - pipe out of the hole, vertical, tapered"),
    ("volumetric_deviated_well", "Volumetric + L&B - deviated, pipe on bottom, untapered"),
    ("volumetric_deviated_tapered_well", "Volumetric + L&B - deviated, pipe on bottom, tapered"),
    ("volumetric_horizontal_well", "Volumetric + L&B - horizontal, pipe on bottom, untapered"),
    ("volumetric_horizontal_tapered_well", "Volumetric + L&B - horizontal, pipe on bottom, tapered"),
]

# The input form for each kind of sheet: (input name, label, type, optional).
# Types: text, number (with its unit), a list of choices, yesno, sections
# (name, capacity, length), points (name, MD, TVD) or numbers (a list of readings).
# Optional inputs may be left blank: a blank MD means a vertical well (MD = TVD).
WW = "Wait and Weight only"
FORMS = {
    KILL_SHEET: [
        ("title", "Title", "text", False),
        ("method", "Method", [DRILLERS, WAIT_AND_WEIGHT], False),
        ("step_method", "Step-down schedule", [TEN_STEPS, EVERY_100_STROKES], WW),
        ("bit_tvd_ft", "Bit TVD", "ft", False),
        ("bit_md_ft", "Bit MD (blank = vertical)", "ft", True),
        ("shoe_tvd_ft", "Shoe TVD", "ft", False),
        ("shoe_md_ft", "Shoe MD (blank = vertical)", "ft", True),
        ("original_mud_weight_ppg", "Original mud weight", "ppg", False),
        ("lot_pressure_psi", "Leak-off test pressure", "psi", False),
        ("test_mud_weight_ppg", "Leak-off test mud weight", "ppg", False),
        ("sidpp_psi", "SIDPP", "psi", False),
        ("sicp_psi", "SICP", "psi", False),
        ("pit_gain_bbl", "Pit gain (for the kill plot)", "bbl", True),
        ("scr_pressure_psi", "SCR pressure", "psi", False),
        ("safety_margin_psi", "Safety margin (SF), team's choice", "psi", False),
        ("pump_output_bbl_per_stk", "Pump output", "bbl/stk", False),
        ("surface_line_volume_bbl", "Surface line volume (0 if unknown)", "bbl", False),
        ("sidpp_at_start_psi", "SIDPP retaken before start-up", "psi", WW),
        ("sicp_at_start_psi", "SICP retaken before start-up", "psi", WW),
        ("observed_icp_psi", "Drill pipe reading at kill rate (blank until you have it)", "psi", WW),
        ("key_points", "Key points (KOP, end of build, heel)", "points", True),
        ("drill_string", "Drill string, top down", "sections", False),
        ("open_hole_annulus", "Open hole annulus, bit up", "sections", False),
        ("cased_hole_annulus", "Cased hole annulus, bit up", "sections", False),
    ],
    VOLUMETRIC: [
        ("title", "Title", "text", False),
        ("original_mud_weight_ppg", "Mud weight", "ppg", False),
        ("kill_mud_weight_ppg", "Mud lubricated in L&B (original mud for a swabbed kick)", "ppg", False),
        ("td_md_ft", "TD MD (blank = vertical)", "ft", True),
        ("td_tvd_ft", "TD TVD (blank = vertical)", "ft", True),
        ("shoe_tvd_ft", "Shoe TVD", "ft", False),
        ("shoe_md_ft", "Shoe MD (blank = vertical)", "ft", True),
        ("lot_pressure_psi", "Leak-off test pressure", "psi", False),
        ("test_mud_weight_ppg", "Leak-off test mud weight", "ppg", False),
        ("sicp_psi", "SICP", "psi", False),
        ("pit_gain_bbl", "Pit gain (the forecast needs it)", "bbl", False),
        ("pipe_bottom_md_ft", "Pipe bottom MD (blank = out of the hole, TD = on bottom)", "ft", True),
        ("float_in_string", "Float in the string", "yesno", False),
        ("sidpp_psi", "SIDPP (on bottom, no float - otherwise Pf is estimated)", "psi", True),
        ("safety_margin_psi", "Safety margin, team's choice", "psi", False),
        ("working_pressure_psi", "Working pressure, team's choice", "psi", False),
        ("shoe_margin_psi", "Shoe margin below fracture, team's choice (0 if none)", "psi", True),
        ("capacity_choice", "Bleed per cycle sized on", [ANNULUS_AT_THE_GAS, SMALLEST, AVERAGE, LONGEST], False),
        ("key_points", "Key points (KOP, end of build, heel)", "points", True),
        ("annulus_bottom_up", "Annulus, bottom up (include sections with no pipe)", "sections", False),
        ("sicp_rises_after_each_cycle", "Readings: SICP rise over the 15-minute wait, each cycle", "numbers", False),
        ("sicp_gas_at_surface_psi", "Reading: SICP with gas at surface", "psi", False),
        ("bbl_pumped_each_cycle", "Readings: bbl pumped, each lubricate and bleed cycle", "numbers", False),
    ],
}


def well_inputs(example):
    """The WELL data of one example file, with the kind of sheet it is."""
    well = importlib.import_module(example).WELL
    kind = VOLUMETRIC if "annulus_bottom_up" in well else KILL_SHEET
    return kind, well


def example_wells():
    """Every example well for the dropdown, with its inputs, as JSON."""
    wells = []
    for example, label in EXAMPLE_WELLS:
        kind, well = well_inputs(example)
        wells.append({"id": example, "label": label, "kind": kind, "inputs": well})
    return json.dumps({"wells": wells, "forms": FORMS})


def calculate(kind, inputs_json):
    """Work out the sheet from the page's inputs. Returns JSON: the sheet, or the error."""
    inputs = json.loads(inputs_json)
    try:
        sheet = volumetric_sheet(**inputs) if kind == VOLUMETRIC else kill_sheet(**inputs)
    except (ValueError, TypeError, KeyError, ZeroDivisionError, IndexError) as error:
        return json.dumps({"error": str(error)})
    return json.dumps({"kind": kind, "sheet": sheet})
