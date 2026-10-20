"""Drilling: one-page printable kill form (doghouse copy).

Every value is pulled live from the Kill Sheet / Well Data - nothing is
entered here. Print setup: portrait, fit to one page.
"""
from openpyxl.styles import Font
from openpyxl.worksheet.properties import PageSetupProperties

from .. import style as S
from ..builder import SheetBuilder
from . import kill_sheet

KS = "'Kill Sheet'"

F_BIG = Font(name="Calibri", size=12)
F_BIGB = Font(name="Calibri", size=12, bold=True)
F_HDR = Font(name="Calibri", size=13, bold=True, color="1F3864")


def build(wb):
    ws = wb.create_sheet("Kill Form")
    ws.sheet_properties.tabColor = S.TAB_COLORS["drilling"]
    ws.sheet_view.showGridLines = False
    SheetBuilder.registry.append(
        ("Kill Form", "drilling",
         "One-page printable kill sheet (all values pulled live from Kill Sheet / Well Data)"))
    R = kill_sheet.REFS
    for col, w in {"A": 26, "B": 13, "C": 8, "D": 4, "E": 14, "F": 13}.items():
        ws.column_dimensions[col].width = w

    ws.merge_cells("A1:F1")
    t = ws.cell(row=1, column=1, value="WELL KILL SHEET - SURFACE BOP")
    t.font = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
    t.fill = S.FILL_TITLE
    ws.row_dimensions[1].height = 24

    def pair(row, col, label, formula, fmt="#,##0", unit=""):
        a = ws.cell(row=row, column=col, value=label)
        a.font = F_BIG
        b = ws.cell(row=row, column=col + 1, value=formula)
        b.font = F_BIGB
        b.number_format = fmt
        b.border = S.BORDER_BOX
        b.alignment = S.AL_RIGHT
        if unit:
            u = ws.cell(row=row, column=col + 2, value=unit)
            u.font = S.F_UNIT

    def header(row, text):
        h = ws.cell(row=row, column=1, value=text)
        h.font = F_HDR
        h.fill = S.FILL_SECTION
        for cc in range(1, 4):
            ws.cell(row=row, column=cc).fill = S.FILL_SECTION

    r = 3
    pair(r, 1, "Well", "=WD_Well", "@")
    pair(r, 4, "Date", "=WD_Date", "@")
    r += 1
    pair(r, 1, "Rig", "=WD_Rig", "@")
    pair(r, 4, "Engineer", "=WD_Engineer", "@")
    r += 2

    header(r, "PRE-RECORDED DATA")
    r += 1
    for label, key, fmt, unit in [
            ("Current mud weight", "omw", "0.0", "ppg"),
            ("MD / TVD at bit", "md", "#,##0", "ft"),
            ("Shoe MD / TVD", "shoe_md", "#,##0", "ft"),
            ("LOT EMW", "lot", "0.0", "ppg"),
            ("SCR pressure", "scr", "#,##0", "psi"),
            ("Pump output", "spr", "0.0000", "bbl/stk"),
            ("Kill rate", "krate", "#,##0", "spm"),
            ("MAASP (initial)", "maasp", "#,##0", "psi")]:
        pair(r, 1, label, f"={KS}!{R[key]}", fmt, unit)
        r += 1
    # second value on the paired depth rows
    pair(r - 7, 4, "", f"={KS}!{R['tvd']}", "#,##0", "ft TVD")
    pair(r - 6, 4, "", f"={KS}!{R['shoe_tvd']}", "#,##0", "ft TVD")
    r += 1

    header(r, "VOLUMES & STROKES")
    r += 1
    for label, key, fmt, unit in [
            ("Drill string volume", "str_vol", "0.0", "bbl"),
            ("Strokes surface to bit", "stb", "#,##0", "stk"),
            ("Annulus volume", "ann_vol", "0.0", "bbl"),
            ("Strokes bit to surface", "bts", "#,##0", "stk"),
            ("Total circulation", "tot", "#,##0", "stk")]:
        pair(r, 1, label, f"={KS}!{R[key]}", fmt, unit)
        r += 1
    r += 1

    header(r, "KICK DATA")
    r += 1
    for label, key, fmt, unit in [
            ("SIDPP", "sidpp", "#,##0", "psi"),
            ("SICP", "sicp", "#,##0", "psi"),
            ("Pit gain", "gain", "0.0", "bbl")]:
        pair(r, 1, label, f"={KS}!{R[key]}", fmt, unit)
        r += 1
    r += 1

    header(r, "KILL DATA")
    r += 1
    for label, key, fmt, unit in [
            ("Kill mud weight (rounded up)", "kmw", "0.0", "ppg"),
            ("ICP", "icp", "#,##0", "psi"),
            ("FCP", "fcp", "#,##0", "psi"),
            ("psi per 100 strokes (rounded down)", "drop", "#,##0", "psi"),
            ("Formation pressure", "fp", "#,##0", "psi"),
            ("MAASP after kill", "maasp_k", "#,##0", "psi")]:
        pair(r, 1, label, f"={KS}!{R[key]}", fmt, unit)
        r += 1

    # schedule on the right side
    sr = 8
    h = ws.cell(row=sr, column=5, value="STROKES")
    h.font = F_BIGB
    h2 = ws.cell(row=sr, column=6, value="DP PSI")
    h2.font = F_BIGB
    for cc in (5, 6):
        ws.cell(row=sr, column=cc).border = S.BORDER_BOX
    for i in range(21):
        row = sr + 1 + i
        src = R["sched_first"] + i
        b = ws.cell(row=row, column=5, value=f"={KS}!$B{src}")
        p = ws.cell(row=row, column=6, value=f"={KS}!$E{src}")
        for cell in (b, p):
            cell.font = F_BIG
            cell.number_format = "#,##0"
            cell.border = S.BORDER_BOX
            cell.alignment = S.AL_RIGHT
    note = ws.cell(row=sr + 22, column=5, value="Survey-driven schedule")
    note.font = S.F_NOTE

    last = max(r + 2, sr + 24)
    for label, col in (("Driller:", 1), ("Toolpusher:", 3), ("Company rep:", 5)):
        cell = ws.cell(row=last, column=col, value=label + " ____________")
        cell.font = F_BIG
    last += 2
    ws.cell(row=last, column=1,
            value="Generated from the live Kill Sheet - values update automatically. "
                  "Verify against stabilised shut-in pressures before pumping.").font = S.F_NOTE

    ws.print_area = f"A1:F{last}"
    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
