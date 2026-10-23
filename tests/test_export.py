"""Tests for kill sheet and schedule export functions (JSON, CSV, Markdown)."""

import json

from killsheet.export import schedule_to_csv, to_json, to_markdown_report
from killsheet.schedule import ScheduleRow


def test_to_json_serialization():
    data = {
        "title": "Test Well",
        "kmw_ppg": 11.5,
        "sections": [("5 in DP", 0.0178, 10000)],
        "schedule": [ScheduleRow(0, 0, 0, 1400, "start")],
    }
    json_str = to_json(data)
    parsed = json.loads(json_str)
    assert parsed["title"] == "Test Well"
    assert parsed["kmw_ppg"] == 11.5
    assert parsed["schedule"][0]["strokes"] == 0
    assert parsed["schedule"][0]["pressure_psi"] == 1400


def test_schedule_to_csv(tmp_path):
    rows = [
        ScheduleRow(0, 0, 0, 1400, "start"),
        ScheduleRow(100, 1000, 1000, 1350, "step 1"),
        ScheduleRow(1755, 11500, 11500, 829, "bit"),
    ]
    csv_str = schedule_to_csv(rows)
    lines = csv_str.strip().split("\r\n") if "\r\n" in csv_str else csv_str.strip().split("\n")
    assert lines[0] == "Strokes,MD_ft,TVD_ft,Drill_Pipe_Pressure_psi,Label"
    assert lines[1] == "0,0,0,1400,start"
    assert lines[3] == "1755,11500,11500,829,bit"

    # Test file write
    file_path = tmp_path / "schedule.csv"
    schedule_to_csv(rows, filepath=str(file_path))
    assert file_path.exists()
    assert "1755,11500,11500,829,bit" in file_path.read_text(encoding="utf-8")


def test_to_markdown_report():
    sheet = {
        "title": "Baseline Well Kill Sheet",
        "method": "Driller's method",
        "kill_mud_weight_ppg": 11.5,
        "icp_psi": 1400,
        "fcp_psi": 829,
        "max_allowable_mud_weight_ppg": 14.6,
        "maasp_original_psi": 1124,
        "surface_to_bit_strokes": 1627,
    }
    md = to_markdown_report(sheet)
    assert "# Baseline Well Kill Sheet" in md
    assert "11.5" in md
    assert "1,400" in md
    assert "1,627" in md
