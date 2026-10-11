"""The web page glue (web/app.py) gives the same baseline numbers as the kill sheet."""

import json
import runpy
from pathlib import Path

APP = runpy.run_path(str(Path(__file__).resolve().parent.parent / "web" / "app.py"))


def test_baseline_drillers_sheet_summary():
    sheet = json.loads(APP["baseline_drillers_sheet"]())
    assert sheet["summary"] == [
        ["Kill mud weight", "11.5", "ppg"],
        ["Initial circulating pressure", "1,400", "psi"],
        ["Final circulating pressure", "829", "psi"],
        ["Max allowable mud weight", "14.6", "ppg"],
        ["MAASP (original mud)", "1,124", "psi"],
        ["MAASP (after kill)", "830", "psi"],
        ["Surface to bit", "1,627", "stks"],
        ["Bit to shoe", "2,405", "stks"],
        ["Bit to surface", "4,557", "stks"],
        ["Safety margin (SF)", "50", "psi"],
    ]


def test_baseline_drillers_sheet_steps():
    sheet = json.loads(APP["baseline_drillers_sheet"]())
    assert [(s["stage"], s["hold_psi"], s["strokes"]) for s in sheet["steps"]] == [
        ("start-up", 850, None), ("hold", 1450, 4557), ("shut-down", None, None), ("check", 700, None),
        ("start-up", 700, None), ("hold", 700, 1627), ("hold", 871, 4557), ("shut-down", None, None),
        ("check", 42, None), ("bleed", None, None), ("check", 0, None), ("flow check", None, None),
    ]
