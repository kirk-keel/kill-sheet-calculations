"""Export utilities for kill sheets and operational schedules.

Provides serialization to:
  - JSON (for SCADA / rig telemetry / web APIs)
  - CSV (for drill pipe pressure step-down schedules loaded onto console monitors)
  - Markdown (for Daily Drilling Reports and engineering documentation)
"""

import csv
import io
import json
from typing import Any, Iterable


def _sanitize_for_json(obj: Any) -> Any:
    """Recursively converts namedtuples, tuples, and sets to JSON-serializable structures."""
    if hasattr(obj, "_asdict"):
        return _sanitize_for_json(obj._asdict())
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize_for_json(item) for item in obj]
    return obj


def to_json(data: dict, indent: int = 2) -> str:
    """Converts a kill sheet or summary dictionary into formatted JSON."""
    clean_data = _sanitize_for_json(data)
    return json.dumps(clean_data, indent=indent)


def schedule_to_csv(schedule_rows: Iterable[Any], filepath: str = None) -> str:
    """Exports a Wait & Weight pressure step-down schedule to CSV format.

    Each row includes: Strokes, Measured Depth (ft), True Vertical Depth (ft),
    Drill Pipe Pressure (psi), and Stage / Crossover Label.
    If filepath is provided, writes to file. Returns CSV string.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Strokes", "MD_ft", "TVD_ft", "Drill_Pipe_Pressure_psi", "Label"])

    for row in schedule_rows:
        if hasattr(row, "_asdict"):
            d = row._asdict()
            writer.writerow([d["strokes"], d["md_ft"], d["tvd_ft"], d["pressure_psi"], d["label"]])
        elif isinstance(row, dict):
            writer.writerow([row["strokes"], row["md_ft"], row["tvd_ft"], row["pressure_psi"], row["label"]])
        elif isinstance(row, (list, tuple)) and len(row) >= 5:
            writer.writerow([row[0], row[1], row[2], row[3], row[4]])

    csv_text = output.getvalue()
    if filepath:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(csv_text)
    return csv_text


def _fmt(val: Any) -> str:
    """Format integers with commas, floats with 1 decimal, strings as-is."""
    if val is None:
        return "N/A"
    if isinstance(val, int):
        return f"{val:,}"
    if isinstance(val, float):
        return f"{val:.1f}"
    return str(val)


def to_markdown_report(sheet_dict: dict) -> str:
    """Generates a structured Markdown report from a kill sheet dictionary."""
    lines = [
        f"# {sheet_dict.get('title', 'WELL CONTROL KILL SHEET')}",
        f"**Method:** {sheet_dict.get('method', 'N/A')}  ",
        "",
        "## Key Kill Parameters",
        "| Parameter | Value | Unit |",
        "| :--- | :---: | :---: |",
        f"| Kill Mud Weight (KMW) | {_fmt(sheet_dict.get('kill_mud_weight_ppg'))} | ppg |",
        f"| Initial Circulating Pressure (ICP) | {_fmt(sheet_dict.get('icp_psi'))} | psi |",
        f"| Final Circulating Pressure (FCP) | {_fmt(sheet_dict.get('fcp_psi'))} | psi |",
        f"| Maximum Allowable Mud Weight (MAMW) | {_fmt(sheet_dict.get('max_allowable_mud_weight_ppg'))} | ppg |",
        f"| Initial MAASP | {_fmt(sheet_dict.get('maasp_original_psi'))} | psi |",
        f"| MAASP After Kill | {_fmt(sheet_dict.get('maasp_after_kill_psi'))} | psi |",
        f"| Safety Margin (SF) | {_fmt(sheet_dict.get('safety_margin_psi', 0))} | psi |",
        "",
        "## Circulation Volumes & Strokes",
        "| Section | Volume (bbl) | Strokes |",
        "| :--- | :---: | :---: |",
        f"| Surface to Bit | {_fmt(sheet_dict.get('surface_to_bit_volume_bbl'))} | {_fmt(sheet_dict.get('surface_to_bit_strokes'))} |",
        f"| Bit to Shoe | {_fmt(sheet_dict.get('bit_to_shoe_volume_bbl'))} | {_fmt(sheet_dict.get('bit_to_shoe_strokes'))} |",
        f"| Bit to Surface | {_fmt(sheet_dict.get('bit_to_surface_volume_bbl'))} | {_fmt(sheet_dict.get('bit_to_surface_strokes'))} |",
    ]
    return "\n".join(lines) + "\n"
