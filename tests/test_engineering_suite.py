"""Tests for the 45-module Drilling, Completion & Well Intervention (CWI) Suite.

Skipped when ``openpyxl`` is not installed so the core ``killsheet`` test suite
remains runnable with zero third-party packages.
"""

from __future__ import annotations

import importlib

import pytest

openpyxl = pytest.importorskip("openpyxl")

import build  # noqa: E402
import spot_check  # noqa: E402
from suite.sheets import cover  # noqa: E402


@pytest.fixture(scope="module")
def built_workbook():
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for mod_name in build.SHEET_MODULES:
        mod = importlib.import_module(f"suite.sheets.{mod_name}")
        mod.build(wb)
    cover.build(wb)
    for ws in wb.worksheets:
        build.add_status_formatting(ws)
    return wb


def test_all_45_engineering_sheets_build_cleanly(built_workbook):
    # 45 domain sheets in SHEET_MODULES + 1 Cover sheet = 46 total sheets
    assert len(build.SHEET_MODULES) == 45
    assert len(built_workbook.sheetnames) == 46
    assert built_workbook.sheetnames[0] == "Cover"


def test_cwi_intervention_and_completion_sheets_present(built_workbook):
    names = set(built_workbook.sheetnames)
    expected_cwi_and_drilling = {
        "Kill Sheet",
        "Kill Sheet - Subsea",
        "Well Control",
        "Coiled Tubing",
        "Wireline",
        "Snubbing & Hydraulic Workover",
        "Well Kill - Interventions",
        "Surface Rig-Up",
        "Fishing & Stuck Pipe",
        "Tubing Stress Analysis",
        "Tubing & Packer Forces",
        "Completion Fluids & Brines",
        "Perforating",
        "Stimulation & Fracturing",
        "ESP Design",
        "Gas Lift Design",
        "Rod Pump Design",
        "Production Chemistry",
    }
    assert expected_cwi_and_drilling <= names


@pytest.mark.parametrize("sheet,label,expected,tol", spot_check.CHECKS)
def test_spot_check_labels_and_formulas_exist(built_workbook, sheet, label, expected, tol):
    assert sheet in built_workbook.sheetnames
    ws = built_workbook[sheet]
    found_row = None
    for row in ws.iter_rows(min_col=1, max_col=2):
        if row[0].value == label:
            found_row = row[0].row
            val = row[1].value
            assert val is not None
            break
    assert found_row is not None, f"Missing {label!r} on sheet {sheet!r}"
