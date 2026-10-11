"""Runs in the browser (Pyodide). Calculates the kill sheet with the real
killsheet package and hands the numbers to the page as JSON - the page only
draws them.

W1 (plumbing): the baseline well, Driller's method. The well data moves to a
tested module with the other example wells in W2.
"""

import json

from killsheet.drillers import drillers_method
from killsheet.formulas import (
    final_circulating_pressure,
    initial_circulating_pressure,
    kill_mud_overbalance,
    kill_mud_weight,
    maasp,
    max_allowable_mud_weight,
)
from killsheet.strokes import bit_to_shoe_strokes, bit_to_surface_strokes, surface_to_bit_strokes

# Baseline example well - same data as examples/example_well.py
BIT_TVD_FT = 11_500
SHOE_TVD_FT = 5_150
ORIGINAL_MUD_WEIGHT_PPG = 10.4
LOT_PRESSURE_PSI = 1_350
TEST_MUD_WEIGHT_PPG = 9.6
SIDPP_PSI = 650
SICP_PSI = 800
SCR_PRESSURE_PSI = 750
SAFETY_MARGIN_PSI = 50
PUMP_OUTPUT_BBL_PER_STK = 0.117
DRILL_STRING = [(0.0178, 10_000), (0.0087, 900), (0.0077, 600)]          # top down
OPEN_HOLE_ANNULUS = [(0.0291, 600), (0.0459, 900), (0.0459, 4_850)]      # bit up
CASED_HOLE_ANNULUS = [(0.0489, 5_150)]                                   # bit up


def baseline_drillers_sheet():
    """The baseline well's kill sheet, Driller's method, as JSON for the page."""
    kmw = kill_mud_weight(SIDPP_PSI, BIT_TVD_FT, ORIGINAL_MUD_WEIGHT_PPG)
    icp = initial_circulating_pressure(SIDPP_PSI, SCR_PRESSURE_PSI)
    fcp = final_circulating_pressure(SCR_PRESSURE_PSI, kmw, ORIGINAL_MUD_WEIGHT_PPG)
    mamw = max_allowable_mud_weight(LOT_PRESSURE_PSI, SHOE_TVD_FT, TEST_MUD_WEIGHT_PPG)
    pump = PUMP_OUTPUT_BBL_PER_STK
    stb = surface_to_bit_strokes(DRILL_STRING, pump)
    bts = bit_to_shoe_strokes(OPEN_HOLE_ANNULUS, pump)
    btsurf = bit_to_surface_strokes(OPEN_HOLE_ANNULUS + CASED_HOLE_ANNULUS, pump)
    overbalance = kill_mud_overbalance(kmw, ORIGINAL_MUD_WEIGHT_PPG, BIT_TVD_FT)
    steps = drillers_method(SIDPP_PSI, SICP_PSI, icp, fcp, stb, btsurf, SAFETY_MARGIN_PSI, overbalance)
    return json.dumps({
        "title": "Baseline well - vertical, untapered string, surface BOP stack",
        "method": "Driller's method",
        "summary": [
            ["Kill mud weight", f"{kmw:.1f}", "ppg"],
            ["Initial circulating pressure", f"{icp:,}", "psi"],
            ["Final circulating pressure", f"{fcp:,}", "psi"],
            ["Max allowable mud weight", f"{mamw:.1f}", "ppg"],
            ["MAASP (original mud)", f"{maasp(mamw, ORIGINAL_MUD_WEIGHT_PPG, SHOE_TVD_FT):,}", "psi"],
            ["MAASP (after kill)", f"{maasp(mamw, kmw, SHOE_TVD_FT):,}", "psi"],
            ["Surface to bit", f"{stb:,}", "stks"],
            ["Bit to shoe", f"{bts:,}", "stks"],
            ["Bit to surface", f"{btsurf:,}", "stks"],
            ["Safety margin (SF)", f"{SAFETY_MARGIN_PSI:,}", "psi"],
        ],
        "steps": [step._asdict() for step in steps],
    })
