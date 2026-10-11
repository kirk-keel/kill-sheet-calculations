"""The web page glue (web/app.py): every example well loads and gives the same
sheet in the browser as the printed example."""

import json
import runpy
import sys
from pathlib import Path

import pytest

from killsheet.kill_sheet import kill_sheet, volumetric_sheet

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "examples"))          # in the browser they sit beside app.py
APP = runpy.run_path(str(ROOT / "web" / "app.py"))
WELLS = json.loads(APP["example_wells"]())


def test_every_drillers_ww_and_volumetric_example_is_offered():
    offered = {well["id"] for well in WELLS["wells"]}
    on_disk = {path.stem for path in (ROOT / "examples").glob("*_well.py")
               if not path.stem.startswith(("bullhead", "reverse_circulation"))}
    assert offered == on_disk
    assert len(offered) == 24


@pytest.mark.parametrize("well", WELLS["wells"], ids=lambda well: well["id"])
def test_every_example_input_is_on_the_form(well):
    on_form = {field[0] for field in WELLS["forms"][well["kind"]]}
    assert set(well["inputs"]) <= on_form


@pytest.mark.parametrize("well", WELLS["wells"], ids=lambda well: well["id"])
def test_page_sheet_matches_the_printed_example(well):
    # Inputs travel to the page and back as JSON (tuples become lists).
    result = json.loads(APP["calculate"](well["kind"], json.dumps(well["inputs"])))
    module = __import__(well["id"])
    direct = volumetric_sheet(**module.WELL) if well["kind"] == "volumetric" else kill_sheet(**module.WELL)
    assert result["sheet"] == json.loads(json.dumps(direct))


def test_baseline_drillers_on_the_page():
    baseline = next(well for well in WELLS["wells"] if well["id"] == "example_well")
    sheet = json.loads(APP["calculate"]("kill sheet", json.dumps(baseline["inputs"])))["sheet"]
    assert (sheet["kill_mud_weight_ppg"], sheet["icp_psi"], sheet["fcp_psi"]) == (11.5, 1400, 829)
    assert [step["hold_psi"] for step in sheet["steps"]] == [850, 1450, None, 700, 700, 700, 871, None, 42, None, 0, None]


def test_bad_input_shows_the_calculators_message():
    baseline = next(well for well in WELLS["wells"] if well["id"] == "example_well")
    inputs = dict(baseline["inputs"], sidpp_psi=0)
    result = json.loads(APP["calculate"]("kill sheet", json.dumps(inputs)))
    assert "float" in result["error"]                   # SIDPP 0: bump the float


def test_section_lengths_that_dont_add_up_are_refused():
    baseline = next(well for well in WELLS["wells"] if well["id"] == "example_well")
    inputs = dict(baseline["inputs"], bit_tvd_ft=12_000)
    assert "error" in json.loads(APP["calculate"]("kill sheet", json.dumps(inputs)))
