"""kill_plot.py checked against the independent reference model (tests/reference_model.py)
on every example well with a kill plot: vertical, tapered, deviated and horizontal,
untapered and tapered strings, Driller's and Wait and Weight.

Every point on the plot must match the reference: casing, drill pipe, the peak
casing and the max shoe pressure, to the psi and the stroke.
"""

import importlib
import sys
from pathlib import Path

import pytest

from killsheet.kill_sheet import DRILLERS, kill_sheet

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))                       # reference_model.py
sys.path.insert(0, str(HERE.parent / "examples"))   # the example wells
from reference_model import DRILLERS as REF_DRILLERS, WAIT_AND_WEIGHT as REF_WW, reference_plot  # noqa: E402

CASES = [
    "example_well", "tapered_well", "deviated_well", "deviated_tapered_well",
    "horizontal_well", "horizontal_tapered_well",
    "wait_and_weight_well", "wait_and_weight_tapered_well", "wait_and_weight_deviated_well",
    "wait_and_weight_deviated_tapered_well", "wait_and_weight_horizontal_well",
    "wait_and_weight_horizontal_tapered_well",
]


@pytest.fixture(scope="module", params=CASES)
def case(request):
    well = importlib.import_module(request.param).WELL
    method = REF_DRILLERS if well["method"] == DRILLERS else REF_WW
    return request.param, kill_sheet(**well)["plot"], reference_plot(well, method)


def test_every_plotted_casing_and_drill_pipe_matches_the_reference(case):
    name, plot, ref = case
    for point in plot["points"]:
        if point["label"].startswith(("shut in", "start-up", "at kill rate", "2nd circulation start-up")):
            continue                                    # held / shut-in values, not the forecast
        s = point["strokes"]
        assert (s, point["casing_psi"]) == (s, ref["casing"][s]), name
        assert (s, point["drill_pipe_psi"]) == (s, ref["drill_pipe"][s]), name


def test_peak_casing_matches_the_reference(case):
    name, plot, ref = case
    peak = plot["peak_casing"]
    assert (peak["strokes"], peak["casing_psi"], peak["gas_volume_bbl"]) == ref["peak"], name


def test_max_shoe_matches_the_reference(case):
    name, plot, ref = case
    assert (plot["max_shoe"]["strokes"], plot["max_shoe"]["shoe_psi"]) == ref["max_shoe"], name
    assert plot["fracture_at_shoe_psi"] == ref["fracture"], name


def test_end_casing_matches_the_reference(case):
    name, plot, ref = case
    assert plot["trapped_casing_psi"] == ref["end_casing"], name
