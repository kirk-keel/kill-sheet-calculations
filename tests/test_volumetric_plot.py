"""Volumetric and lubricate and bleed plots (v1.3).

The volumetric chart comes from the volumetric sheet rows: the hold to use (with any
geometry correction), the standard IADC hold as a second layer, and annotations.
Baseline well, pipe on bottom, 10 bbl: holds 950 ... 1,400 (no correction needed),
bleeds on the annulus at the gas (2.6, 4.2, 4.5 bbl), gas at surface at 38.8 bbl bled
during cycle 10 at 1,400 psi; lubricate and bleed stops at 48.8 bbl.
"""

import importlib
import sys
from pathlib import Path

import pytest

from killsheet.kill_sheet import volumetric_sheet
from killsheet.lubricate_and_bleed import lubricate_and_bleed_table
from killsheet.volumetric_plot import (
    NO_READING_FLOAT,
    NOT_A_BHP_INDICATOR,
    OFF_BOTTOM,
    ON_BOTTOM,
    OUT_OF_HOLE,
    PIPE_OUT_OF_HOLE,
    drill_pipe_reading,
    lubricate_and_bleed_points,
    pipe_note,
    pipe_position,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "examples"))
BASELINE = importlib.import_module("volumetric_pipe_on_bottom_well").WELL
NO_FLOAT = importlib.import_module("volumetric_pipe_on_bottom_no_float_well").WELL


def test_pipe_position():
    assert pipe_position(11_500, 11_500) == ON_BOTTOM
    assert pipe_position(8_000, 11_500) == OFF_BOTTOM
    assert pipe_position(None, 11_500) == OUT_OF_HOLE
    with pytest.raises(ValueError, match="below TD"):
        pipe_position(12_000, 11_500)


@pytest.mark.parametrize("position, float_in_string, label", [
    (ON_BOTTOM, False, None),                       # readable: a line is drawn
    (ON_BOTTOM, True, NO_READING_FLOAT),             # user: no line
    (OFF_BOTTOM, True, NO_READING_FLOAT),
    (OFF_BOTTOM, False, NOT_A_BHP_INDICATOR),
    (OUT_OF_HOLE, False, PIPE_OUT_OF_HOLE),
    (OUT_OF_HOLE, True, PIPE_OUT_OF_HOLE),
])
def test_drill_pipe_reading(position, float_in_string, label):
    assert drill_pipe_reading(position, float_in_string) == label


def test_off_bottom_no_float_label():
    assert NOT_A_BHP_INDICATOR == "not a BHP indicator - gas may enter the string"


def test_pipe_note_on_bottom_no_float_says_use_the_drill_pipe_pressure_method():
    assert pipe_note(ON_BOTTOM, False, 11_500) == (
        "Pipe on bottom, no float: DP readable - use drill pipe pressure method "
        "(bleed holding SIDPP + safety margin constant). Drill pipe pressure method valid only if the string is "
        "open. If the string or bit is plugged, the drill pipe gauge is not a BHP indicator. "
        "Use volumetric on casing.")
    assert pipe_note(OFF_BOTTOM, True, 8_000) == (
        "Pipe off bottom at 8,000 ft MD, float in the string: no drill pipe reading - casing only.")


def test_volumetric_casing_staircase():
    plot = volumetric_sheet(**BASELINE)["plot"]["volumetric"]
    totals = [2.6, 6.8, 11.0, 15.5, 20.0, 24.5, 29.0, 33.5, 38.0, 38.8]
    expected = [(0, 800)]
    before = 0
    for n, total in enumerate(totals):
        hold = 950 + 50 * n
        expected += [(before, hold), (total, hold)]     # wait up to the hold, bleed holding it
        before = total
    expected.append((38.8, 1400))                       # gas at surface (during the last bleed)
    assert [(p["bbl"], p["casing_psi"]) for p in plot["points"]] == expected
    assert all(p["standard_psi"] == p["casing_psi"] for p in plot["points"])   # no correction on this well
    assert plot["maasp_until_bbl"] == 11.0              # the gas top passes the shoe before cycle 4


def test_volumetric_drill_pipe_mirrors_the_forecast_bhp():
    points = volumetric_sheet(**NO_FLOAT)["plot"]["volumetric"]["points"]
    # DP = SIDPP 650 + (BHP - Pf): up at each hold, down after each bleed
    assert [p["drill_pipe_psi"] for p in points[:6]] == [650, 806, 824, 875, 825, 875]


def test_volumetric_no_drill_pipe_line_without_a_reading():
    points = volumetric_sheet(**BASELINE)["plot"]["volumetric"]["points"]
    assert {p["drill_pipe_psi"] for p in points} == {None}


def test_lubricate_and_bleed_casing():
    lube = lubricate_and_bleed_table(1254, 50, [6.0, 7.0], 0.5980, 0.0489)
    points = [(p["bbl"], p["casing_psi"]) for p in lubricate_and_bleed_points(1254, lube)]
    assert points == [(0, 1254), (6.0, 1304), (6.0, 1181), (13.0, 1231), (13.0, 1096)]


def test_lubricate_and_bleed_plot_ends_at_the_stopping_volume():
    points = volumetric_sheet(**BASELINE)["plot"]["lubricate_and_bleed"]
    assert [(p["bbl"], p["casing_psi"]) for p in points[:5]] == [(0, 1400), (1.7, 1450), (1.7, 1380), (3.3, 1430),
                                                                  (3.3, 1361)]
    assert (points[-1]["bbl"], points[-1]["casing_psi"]) == (48.8, 839)


def test_sheet_plot_on_bottom_with_float():
    s = volumetric_sheet(**BASELINE)
    assert s["pipe_note"] == "Pipe on bottom, float in the string: no drill pipe reading - casing only."
    assert s["plot"]["drill_pipe_label"] == NO_READING_FLOAT
    assert s["schematic"]["string"] == [{"name": "pipe", "top_md_ft": 0, "bottom_md_ft": 11_500, "volume_bbl": None}]
    assert s["schematic"]["pipe_on_bottom"] is True


def test_sheet_on_bottom_no_float_needs_the_sidpp():
    with pytest.raises(ValueError, match="enter the SIDPP"):
        volumetric_sheet(**dict(NO_FLOAT, sidpp_psi=None))
    assert volumetric_sheet(**NO_FLOAT)["plot"]["drill_pipe_label"] is None


def test_sheet_out_of_the_hole():
    s = volumetric_sheet(**dict(BASELINE, pipe_bottom_md_ft=None))
    assert s["plot"]["drill_pipe_label"] == PIPE_OUT_OF_HOLE
    assert s["schematic"]["string"] == [] and s["schematic"]["pipe_bottom_tvd_ft"] is None
