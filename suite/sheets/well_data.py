"""Reference: master Well Data sheet - enter the well once.

Every field gets a workbook-level defined name (WD_*). Other sheets link to
these names via light-blue linked cells (overwrite locally if a calc needs a
different value). Keep this sheet first stop when setting up a new well.
"""
from openpyxl.workbook.defined_name import DefinedName

from ..builder import SheetBuilder

SHEET = "Well Data"


def build(wb):
    sb = SheetBuilder(
        wb, SHEET, "reference",
        "Well Data - Master Inputs",
        "Enter the well once; light-blue cells across the workbook pull from here "
        "(overwrite them locally when a calc needs a different value)",
        description="Single source of well inputs (WD_* named cells) feeding the linked "
                    "light-blue cells on other sheets",
    )

    def named(c, name, label, value, unit=None, note="", fmt="#,##0.00"):
        ref = c.inp(label, value, unit, note=note, fmt=fmt)
        wb.defined_names[name] = DefinedName(name, attr_text=f"'{SHEET}'!{ref}")
        return ref

    sb.section("Well Identification")
    c = sb.calc("Identification", note="Free text - appears on the printable Kill Form.")
    named(c, "WD_Well", "Well name", "EXAMPLE 1-H", fmt="@")
    named(c, "WD_Field", "Field / lease", "EXAMPLE FIELD", fmt="@")
    named(c, "WD_Rig", "Rig", "RIG 00", fmt="@")
    named(c, "WD_Engineer", "Engineer", "K. Keel", fmt="@")
    named(c, "WD_Date", "Date", "2026-08-18", fmt="@")

    sb.section("Depths & Geometry")
    c = sb.calc("Depths & Geometry",
                note="TVDs from the Directional Survey sheet (TVD at TD cell).")
    named(c, "WD_MD", "Bit / TD measured depth", 10500, "ft", fmt="#,##0")
    named(c, "WD_TVD", "Bit / TD true vertical depth", 5573, "ft", fmt="#,##0")
    named(c, "WD_ShoeMD", "Casing shoe MD", 5900, "ft", fmt="#,##0")
    named(c, "WD_ShoeTVD", "Casing shoe TVD", 5573, "ft", fmt="#,##0")
    named(c, "WD_HoleDiam", "Open hole diameter", 8.5, "in", fmt="0.000")
    named(c, "WD_CsgID", "Last casing ID", 8.681, "in", fmt="0.000")
    named(c, "WD_PerfTVD", "Perforation / reservoir TVD", 5573, "ft", fmt="#,##0")

    sb.section("Mud & Formation Pressures")
    c = sb.calc("Mud & Pressures")
    named(c, "WD_OMW", "Current mud / fluid weight", 12.5, "ppg")
    named(c, "WD_PV", "Plastic viscosity (PV)", 15, "cP", note="mPa-s in SI", fmt="0.0")
    named(c, "WD_YP", "Yield point (YP)", 12, None, note="lb/100ft2", fmt="0.0")
    named(c, "WD_LOT", "LOT / FIT equivalent mud weight", 15.2, "ppg")
    named(c, "WD_FracGrad", "Fracture gradient (at TD/perfs)", 0.79, "psi/ft", fmt="0.000")
    named(c, "WD_ResP", "Reservoir / formation pressure", 4122, "psi", fmt="#,##0")

    sb.section("Pumps & Kill Parameters")
    c = sb.calc("Pumps & Kill")
    named(c, "WD_SCR", "Slow circulating rate pressure (SCR)", 750, "psi", fmt="#,##0")
    named(c, "WD_SPR", "Pump output", 0.102, "bbl/stk", fmt="0.0000")
    named(c, "WD_KillRate", "Kill rate", 30, None, note="strokes per minute", fmt="#,##0")

    sb.section("Rig & Drill String (for Torque & Drag)")
    c = sb.calc("Rig & String")
    named(c, "WD_BlockWt", "Travelling block + top drive weight", 85, "klbf", fmt="#,##0")
    named(c, "WD_WOB", "Weight on bit (slack-off case)", 15, "klbf", fmt="0.0")
    named(c, "WD_BitTq", "Bit torque", 4000, "ft-lbf", fmt="#,##0")
    named(c, "WD_TJOD", "Tool joint OD", 6.625, "in", fmt="0.000")
    named(c, "WD_DPWt", "Drill pipe adjusted weight", 20.9, "lb/ft", fmt="0.00",
          note="Nominal weight + tool joints (approx nominal x 1.07).")
    named(c, "WD_BHAWt", "BHA weight per foot", 92.0, "lb/ft", fmt="0.00")
    named(c, "WD_BHALen", "BHA length", 300, "ft", fmt="#,##0")
    named(c, "WD_MuCased", "Friction factor - cased hole", 0.25, None, fmt="0.00",
          note="Typical 0.15-0.25 in WBM, lower in OBM.")
    named(c, "WD_MuOpen", "Friction factor - open hole", 0.30, None, fmt="0.00",
          note="Typical 0.25-0.40 in WBM.")

    sb.section("Subsea (leave 0 for land / surface BOP)")
    c = sb.calc("Subsea")
    named(c, "WD_WaterDepth", "Water depth", 0, "ft", fmt="#,##0")
    named(c, "WD_AirGap", "Air gap (RKB to sea level)", 0, "ft", fmt="#,##0")
    named(c, "WD_SWGrad", "Seawater gradient", 0.445, "psi/ft", fmt="0.000")
    named(c, "WD_CLF", "Choke line friction at kill rate", 0, "psi", fmt="#,##0")

    sb.section("Completion / Intervention Tubulars")
    c = sb.calc("Tubing")
    named(c, "WD_TbgOD", "Tubing OD", 3.5, "in", fmt="0.000")
    named(c, "WD_TbgID", "Tubing ID", 2.992, "in", fmt="0.000")
