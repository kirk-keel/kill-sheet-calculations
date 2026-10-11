"""The web page glue (web/app.py): every example well loads and gives the same
sheet in the browser as the printed example."""

import json
import runpy
import sys
from pathlib import Path

import pytest

from killsheet.kill_sheet import bullhead_sheet, kill_sheet, reverse_circulation_sheet, volumetric_sheet

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "examples"))          # in the browser they sit beside app.py
APP = runpy.run_path(str(ROOT / "web" / "app.py"))
WELLS = json.loads(APP["example_wells"]())


def test_every_example_is_offered():
    offered = {well["id"] for well in WELLS["wells"]}
    on_disk = {path.stem for path in (ROOT / "examples").glob("*_well.py")}
    assert offered == on_disk
    assert len(offered) == 36


@pytest.mark.parametrize("well", WELLS["wells"], ids=lambda well: well["id"])
def test_every_example_input_is_on_the_form(well):
    on_form = {field[0] for field in WELLS["forms"][well["kind"]]}
    assert set(well["inputs"]) <= on_form


@pytest.mark.parametrize("well", WELLS["wells"], ids=lambda well: well["id"])
def test_page_sheet_matches_the_printed_example(well):
    # Inputs travel to the page and back as JSON (tuples become lists).
    result = json.loads(APP["calculate"](well["kind"], json.dumps(well["inputs"])))
    module = __import__(well["id"])
    sheet = {"kill sheet": kill_sheet, "volumetric": volumetric_sheet, "bullhead": bullhead_sheet,
             "reverse circulation": reverse_circulation_sheet}[well["kind"]]
    direct = sheet(**module.WELL)
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


def test_baseline_bullhead_on_the_page():
    baseline = next(well for well in WELLS["wells"] if well["id"] == "bullhead_well")
    assert baseline["kind"] == "bullhead"
    sheet = json.loads(APP["calculate"]("bullhead", json.dumps(baseline["inputs"])))["sheet"]
    first, last = sheet["chart"][0], sheet["chart"][-1]
    assert (sheet["kill_fluid_ppg"], sheet["equipment_limit_psi"]) == (11.5, 3000)
    at_bit = next(row for row in sheet["chart"] if row["label"] == "kill fluid at the bit (string)")
    assert (first["string_max_psi"], first["annulus_max_psi"]) == (1124, 1124)
    assert at_bit["string_max_psi"] == 466              # the string side uses both columns
    assert last["label"] == "overdisplaced"


def test_bullhead_section_lengths_that_dont_add_up_are_refused():
    baseline = next(well for well in WELLS["wells"] if well["id"] == "bullhead_well")
    result = json.loads(APP["calculate"]("bullhead", json.dumps(dict(baseline["inputs"], bit_tvd_ft=12_000))))
    assert result["error"] == "Drill string sections add up to 11,500 ft MD but should be 12,000 ft"


def test_reverse_circulation_on_the_page():
    tapered = next(well for well in WELLS["wells"] if well["id"] == "reverse_circulation_horizontal_tapered_well")
    assert tapered["kind"] == "reverse circulation"
    sheet = json.loads(APP["calculate"]("reverse circulation", json.dumps(tapered["inputs"])))["sheet"]
    assert (sheet["kill_fluid_ppg"], sheet["sitp_psi"], sheet["sicp_psi"], sheet["fcp_psi"]) == (10.8, 1799, 990, 244)
    assert [row["pump_psi"] for row in sheet["schedule"]][-2:] == [244, 244]
    assert (sheet["volume_below_ssd_bbl"], sheet["bullhead_below_initial_psi"]) == (38.6, 1962)
    # The schematic's tubing runs on past the SSD to the packer.
    assert sheet["schematic"]["string"][-1] == {"name": "tubing, SSD to packer", "top_md_ft": 8800,
                                                 "bottom_md_ft": 8850, "volume_bbl": 0.3}


def test_reverse_circulation_before_the_icp_is_read():
    well = next(well for well in WELLS["wells"] if well["id"] == "reverse_circulation_well")
    inputs = {name: value for name, value in well["inputs"].items() if name != "observed_icp_psi"}
    sheet = json.loads(APP["calculate"]("reverse circulation", json.dumps(inputs)))["sheet"]
    assert (sheet["fcp_psi"], sheet["steps"], sheet["schedule"]) == (None, None, None)
    assert sheet["sicp_psi"] > 0
