"""Interventions: surface treating-iron / Chiksan rig-up builder.

Catalog of FMC/Weir-style figure-1502 treating iron (RU_Names / RU_Table
named ranges), plus an ordered rig-up builder table where the row order IS
the flow path from the pump discharge to the wellhead. Tallies give total
iron footage, line volume (for line tests, displacement and pump-down
volumes), the minimum ID (restriction) and the minimum pressure rating in
the path, checked against the planned line test pressure.
"""
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation

from .. import style as S
from ..builder import UNLOCKED, SheetBuilder

SHEET = "Surface Rig-Up"

N_ROWS = 24  # rows in the rig-up builder table

# (name, length ft, ID in, rating CWP psi, category)
# figure-1502 wing unions unless noted; lengths are typical make-up lengths
CATALOG = [
    ("2in 1502 pup 2ft", 2, 1.75, 15000, "pup"),
    ("2in 1502 pup 4ft", 4, 1.75, 15000, "pup"),
    ("2in 1502 pup 6ft", 6, 1.75, 15000, "pup"),
    ("2in 1502 pup 8ft", 8, 1.75, 15000, "pup"),
    ("2in 1502 pup 10ft", 10, 1.75, 15000, "pup"),
    ("2in 1502 straight 10ft", 10, 1.75, 15000, "straight"),
    ("2in Chiksan style 50 swivel", 2.2, 1.75, 15000, "swivel"),
    ("2in Chiksan style 10 swivel", 1.5, 1.75, 15000, "swivel"),
    ("2in 1502 plug valve", 1.6, 1.69, 15000, "valve"),
    ("2in 1502 check valve", 1.6, 1.69, 15000, "valve"),
    ("2in 1502 tee", 1.3, 1.75, 15000, "fitting"),
    ("2in 1502 cross", 1.3, 1.75, 15000, "fitting"),
    ("2in 1502 lateral (wye)", 1.5, 1.75, 15000, "fitting"),
    ("3in 1502 pup 10ft", 10, 2.75, 15000, "pup"),
    ("3in 1502 straight 10ft", 10, 2.75, 15000, "straight"),
    ("3in Chiksan style 50 swivel", 2.6, 2.75, 15000, "swivel"),
    ("3in 1502 plug valve", 1.9, 2.62, 15000, "valve"),
    ("3in x 2in 1502 crossover", 1.0, 1.75, 15000, "fitting"),
    ("2in 1502 x 2in hammer hose 20ft", 20, 1.75, 10000, "hose"),
    ("Low-torque relief valve 2in", 1.6, 1.69, 15000, "valve"),
]

# example rig-up: (catalog name, qty) - THE ORDER IS THE FLOW PATH,
# pump discharge first, wellhead connection last
RIGUP_DEFAULTS = [
    ("2in 1502 pup 10ft", 2),
    ("2in Chiksan style 50 swivel", 3),
    ("2in 1502 straight 10ft", 4),
    ("2in 1502 check valve", 1),
    ("2in 1502 plug valve", 2),
    ("2in Chiksan style 50 swivel", 3),
    ("2in 1502 pup 6ft", 1),
]

BIG = "9.99E+9"  # blank-row stand-in so MIN tallies never hit "" text


def _table_header(ws, row, headers):
    for i, h in enumerate(headers, start=1):
        c = ws.cell(row=row, column=i, value=h)
        c.font = S.F_HEADER
        c.border = S.BORDER_BOX
        c.alignment = S.AL_RIGHT if i > 1 else S.AL_LEFT


def _cell(ws, row, col, value, fmt="#,##0.00", is_input=False, is_output=False):
    c = ws.cell(row=row, column=col, value=value)
    c.number_format = fmt
    c.border = S.BORDER_BOX
    c.alignment = S.AL_RIGHT
    if is_input:
        c.fill = S.FILL_INPUT
        c.font = S.F_INPUT
        c.protection = UNLOCKED
    elif is_output:
        c.fill = S.FILL_OUTPUT
        c.font = S.F_OUTPUT
    else:
        c.font = S.F_LABEL
    return c


def build(wb):
    sb = SheetBuilder(
        wb, SHEET, "interventions",
        "Surface Rig-Up - Treating Iron / Chiksan Line Builder",
        "Ordered component list from pump to wellhead: footage, line volume, "
        "minimum ID and minimum pressure rating for line tests and displacements",
        description="Treating-iron catalog (RU_Names/RU_Table named ranges) and an "
                    "ordered flow-path builder with footage, volume, restriction and "
                    "rating tallies plus a line-test check",
    )
    ws = sb.ws
    ws.column_dimensions["B"].width = 30  # long component names in the builder table

    # --------------------------------------------------------------- catalog
    sb.section("1. Treating Iron Catalog")
    ws.cell(row=sb.row, column=1,
            value="FMC/Weir-style treating iron, figure-1502 wing unions unless noted. "
                  "Lengths are typical make-up (assembled) lengths. CWP = cold working "
                  "pressure. The hammer hose is rated 10,000 psi CWP and governs the "
                  "line rating whenever it is in the path.").font = S.F_NOTE
    sb.row += 1
    hdr = sb.row
    headers = ["Name", "Length (ft)", "ID (in)", "Rating CWP (psi)", "Category",
               "Capacity (bbl/ft)", "Capacity (gal/ft)"]
    for i, h in enumerate(headers, start=1):
        cell = ws.cell(row=hdr, column=i, value=h)
        cell.font = S.F_HEADER
        cell.border = S.BORDER_BOX
    cfirst = hdr + 1
    for i, (name, ln, idd, cwp, cat) in enumerate(CATALOG):
        r = cfirst + i
        ws.cell(row=r, column=1, value=name).border = S.BORDER_BOX
        for col, v, fmt in ((2, ln, "0.0"), (3, idd, "0.00"), (4, cwp, "#,##0")):
            cell = ws.cell(row=r, column=col, value=v)
            cell.number_format = fmt
            cell.border = S.BORDER_BOX
        cc = ws.cell(row=r, column=5, value=cat)
        cc.border = S.BORDER_BOX
        cc.font = S.F_SI
        for col, f in ((6, f"=$C{r}^2/1029.4"), (7, f"=$C{r}^2/1029.4*42")):
            cell = ws.cell(row=r, column=col, value=f)
            cell.number_format = "0.00000" if col == 6 else "0.0000"
            cell.border = S.BORDER_BOX
            cell.font = S.F_SI
    clast = cfirst + len(CATALOG) - 1
    sb.row = clast + 1

    wb.defined_names["RU_Names"] = DefinedName(
        "RU_Names", attr_text=f"'{SHEET}'!$A${cfirst}:$A${clast}")
    wb.defined_names["RU_Table"] = DefinedName(
        "RU_Table", attr_text=f"'{SHEET}'!$A${cfirst}:$E${clast}")

    # -------------------------------------------------------- rig-up builder
    sb.section("2. Rig-Up Builder (row order = flow path, pump to wellhead)")
    ws.cell(row=sb.row, column=1,
            value="Pick components from the dropdown IN FLOW ORDER from the pump "
                  "discharge to the wellhead - the sequence is the line walk-down. "
                  "Qty repeats identical items back-to-back. Unused rows stay blank. "
                  "Columns I-M are numeric helpers for the tallies - leave them alone.").font = S.F_NOTE
    sb.row += 1
    hdr = sb.row
    _table_header(ws, hdr, ["Seq #", "Component", "Qty", "Unit len (ft)",
                            "Line len (ft)", "ID (in)", "Rating (psi)", "Volume (bbl)"])
    for col, h in ((9, "len 0"), (10, "vol 0"), (11, "ID big"), (12, "rate big"),
                   (13, "qty 0")):
        c = ws.cell(row=hdr, column=col, value=h)
        c.font = S.F_SI
        c.border = S.BORDER_BOX
        c.alignment = S.AL_RIGHT
    first = hdr + 1
    for i in range(N_ROWS):
        r = first + i
        name, qty = RIGUP_DEFAULTS[i] if i < len(RIGUP_DEFAULTS) else ("", None)
        # A: sequence number (auto, blank when the row is unused)
        _cell(ws, r, 1, f'=IF($B{r}="","",{i + 1})', "0")
        # B: component (dropdown from the catalog)
        nc = ws.cell(row=r, column=2, value=name)
        nc.fill = S.FILL_INPUT
        nc.border = S.BORDER_BOX
        nc.font = S.F_INPUT
        nc.alignment = S.AL_LEFT
        nc.protection = UNLOCKED
        # C: quantity
        _cell(ws, r, 3, qty, "0", is_input=True)
        # D-H: VLOOKUP auto-fill, blank rows show ""
        _cell(ws, r, 4, f'=IF($B{r}="","",IFERROR(VLOOKUP($B{r},RU_Table,2,FALSE),""))',
              "0.0")
        _cell(ws, r, 5, f'=IF(OR($B{r}="",$C{r}="",$D{r}=""),"",$D{r}*$C{r})', "0.0")
        _cell(ws, r, 6, f'=IF($B{r}="","",IFERROR(VLOOKUP($B{r},RU_Table,3,FALSE),""))',
              "0.00")
        _cell(ws, r, 7, f'=IF($B{r}="","",IFERROR(VLOOKUP($B{r},RU_Table,4,FALSE),""))',
              "#,##0")
        _cell(ws, r, 8, f'=IF(OR($E{r}="",$F{r}=""),"",$F{r}^2/1029.4*$E{r})',
              "0.0000", is_output=True)
        # I-M: numeric helpers so SUM/MIN tallies never hit "" text
        helpers = ((9, f"$E{r}", "0"), (10, f"$H{r}", "0"), (11, f"$F{r}", BIG),
                   (12, f"$G{r}", BIG), (13, f"$C{r}", "0"))
        for col, ref, blank in helpers:
            c = ws.cell(row=r, column=col,
                        value=f"=IF(ISNUMBER({ref}),{ref},{blank})")
            c.font = S.F_SI
            c.border = S.BORDER_BOX
            c.alignment = S.AL_RIGHT
            c.number_format = "0.###"
    last = first + N_ROWS - 1
    dv = DataValidation(type="list", formula1="=RU_Names", allow_blank=True,
                        showErrorMessage=False)
    ws.add_data_validation(dv)
    dv.add(f"B{first}:B{last}")
    sb.row = last + 1

    # ----------------------------------------------------------------- tally
    sb.section("3. Line Tally & Test Check")
    c = sb.calc("Rig-Up Tally",
                eq="Volume = ID^2/1029.4 x length [bbl];  restriction = MIN(ID); "
                   "rating = MIN(CWP)",
                note="The minimum ID sets ball/dart/plug sizes and pump-down "
                     "restrictions; the minimum rating sets the line test limit.")
    ftg = c.out("Total iron footage", f"SUM($I${first}:$I${last})", "ft", fmt="0.0")
    vol = c.out("Total line volume", f"SUM($J${first}:$J${last})", "bbl", fmt="0.000")
    c.out("Total line volume", f"{vol}*42", "gal", fmt="0.0")
    minid = c.out("Minimum ID (restriction)", f"MIN($K${first}:$K${last})", "in",
                  fmt="0.00")
    minrat = c.out("Minimum rating in path", f"MIN($L${first}:$L${last})", "psi",
                   fmt="#,##0")
    c.out("Swivel count in path",
          f'IFERROR(SUMPRODUCT(ISNUMBER(SEARCH("swivel",$B${first}:$B${last}))'
          f"*$M${first}:$M${last}),0)", None, fmt="0",
          note="Chiksan swivels in the path - see minimum-count guidance below.")

    c = sb.calc("Line Test vs Component Ratings",
                eq="Test pressure = max anticipated x test factor",
                note="Test the line against a CLOSED VALVE at the wellhead before "
                     "pumping. The hammer hose (10,000 psi CWP) governs the line "
                     "rating whenever it is in the path.")
    antic = c.inp("Max anticipated treating pressure", 9500, "psi", fmt="#,##0")
    fac = c.inp("Line test factor", 1.1, None, fmt="0.00",
                note="Typical 1.1 x max anticipated, never above the lowest CWP.")
    test = c.out("Line test pressure", f"{antic}*{fac}", "psi", fmt="#,##0")
    c.out("Line test status",
          f'IF({test}<={minrat},"OK - test below lowest-rated component",'
          f'IF({antic}<={minrat},"MARGINAL - test EXCEEDS a component rating - '
          f'retest plan needed",'
          f'"CHECK: anticipated EXCEEDS lowest component rating - DO NOT pump"))',
          None, fmt="@")

    # ---------------------------------------------------------- displacement
    sb.section("4. Displacement & Safety Notes")
    c = sb.calc("Displacement",
                note="Add the pump-to-wellhead line volume above to every "
                     "displacement and pump-down calculation - the wellbore only "
                     "sees fluid after the line is full.")
    c.txt("Line volume adds to displacement",
          "Surface line volume (Total line volume above) is dead volume between "
          "the pump stroke counter and the wellhead: add it to spot, displacement "
          "and pump-down volumes on the Kill Sheet and Well Kill Operations "
          "sheets, and subtract it when flow-checking returns.")
    c.txt("Hammer-union safety",
          "Verify matched wing/thread halves on every hammer union - a 1502 wing "
          "on a 602 thread will make up but WILL part under pressure. No "
          "1502 x 602 mismatches anywhere in the line.")
    c.txt("Line restraint",
          "Restrain the line at every change of direction and at the wellhead - "
          "whip checks / restraint slings sized for the line, anchored to fixed "
          "points, with personnel excluded from the line path while pressurized.")
    c.txt("Swivel minimum count",
          "Use at least three swivel planes between pump and wellhead so the "
          "line can absorb thermal growth, vibration and rig-up misalignment "
          "without side-loading the unions.")
    c.txt("Test against the wellhead valve",
          "Pressure test against a closed valve at the wellhead (crown or master "
          "per the barrier plan) - never against the swab valve alone, and never "
          "test into the well.")
