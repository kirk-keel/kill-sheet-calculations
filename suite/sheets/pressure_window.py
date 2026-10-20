"""Drilling: pore/frac gradient estimation (Eaton) and the drilling window plot.

Eaton pore pressure from a sonic/resistivity trend ratio, Eaton and
Hubbert & Willis fracture gradients with an LOT calibration check, a 15-row
depth table of pore/frac EMW vs current MW and ECD, and a kick-tolerance
margin at the current shoe.

Depth table geometry:
  A=TVD  B=pore EMW  C=frac EMW  (yellow inputs)
  D=MW   E=ECD       (computed)
  G..K = NA()-guarded numeric helpers for the Drilling Window chart
"""
from openpyxl.chart import Reference, ScatterChart, Series

from .. import style as S
from ..builder import UNLOCKED, SheetBuilder

# (TVD ft, pore EMW ppg, frac EMW ppg) - normal pressure to ~4000 ft, then a
# transition ramping to the reservoir at 5573 ft (matches WD_ResP ~14.2 ppg EMW)
DEFAULT_WINDOW = [
    (1000, 8.9, 12.0),
    (1500, 8.9, 12.4),
    (2000, 8.9, 12.8),
    (2500, 8.9, 13.1),
    (3000, 9.0, 13.4),
    (3500, 9.2, 13.7),
    (4000, 9.6, 14.0),
    (4250, 10.2, 14.2),
    (4500, 11.0, 14.4),
    (4750, 11.8, 14.6),
    (5000, 12.6, 14.8),
    (5200, 13.2, 15.0),
    (5400, 13.7, 15.1),
    (5500, 14.0, 15.15),
    (5573, 14.2, 15.2),
]
N_ROWS = 15


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
        wb, "Pressure Window", "drilling",
        "Pore & Fracture Pressure - Drilling Window",
        "Eaton pore pressure, Eaton / Hubbert & Willis fracture gradient with LOT "
        "calibration, depth-table drilling window plot and shoe kick tolerance",
        description="Eaton pore pressure, frac gradient (Eaton, Hubbert & Willis), LOT "
                    "calibration check, pore/frac/MW/ECD window plot, shoe kick margin",
    )
    ws = sb.ws
    for col, w in {"G": 10, "H": 10, "I": 10, "J": 10, "K": 10}.items():
        ws.column_dimensions[col].width = w

    sb.section("Overburden & Eaton Pore Pressure")

    c = sb.calc("Eaton Pore Pressure from Trend Ratio",
                eq="PP_grad = OBG - (OBG - PN) x R^n",
                note="R = dt_normal/dt_observed (sonic form) or R_observed/R_normal "
                     "(resistivity form) - both arranged so R < 1 means overpressure. "
                     "n = 3.0 is the classic Eaton exponent for both forms (use ~1.2 "
                     "for the d-exponent form).")
    tvd = c.link("Depth of interest TVD", "WD_TVD", "ft", fmt="#,##0")
    obg = c.inp("Overburden gradient (OBG)", 1.0, "psi/ft", fmt="0.000",
                note="1.0 psi/ft is a common onshore default; integrate density logs offshore.")
    pn = c.inp("Normal pore gradient (PN)", 0.465, "psi/ft", fmt="0.000")
    ex = c.inp("Eaton exponent (n)", 3.0, None, fmt="0.0")
    ratio = c.inp("Observed/normal trend ratio (R)", 0.9, None, fmt="0.00")
    ppgrad = c.out("Pore pressure gradient", f"{obg}-({obg}-{pn})*{ratio}^{ex}",
                   "psi/ft", fmt="0.000")
    c.out("Pore pressure at depth", f"{ppgrad}*{tvd}", "psi", fmt="#,##0")
    ppemw = c.out("Pore pressure EMW", f"{ppgrad}/0.052", "ppg", fmt="0.00")

    sb.section("Fracture Gradient")

    c = sb.calc("Fracture Gradient (Eaton / Hubbert & Willis)",
                eq="Eaton: FG = (PR/(1-PR)) x (OBG - PP_grad) + PP_grad;   "
                   "H&W minimum: FG_min = (OBG + 2 x PP_grad)/3",
                note="Both are estimates - always calibrate against LOT/FIT or minifrac "
                     "data from the actual area before relying on the window.")
    pratio = c.inp("Poisson ratio (PR)", 0.25, None, fmt="0.00",
                   note="Typical 0.20-0.30 for shale; higher for unconsolidated sediments.")
    fge = c.out("Eaton fracture gradient", f"({pratio}/(1-{pratio}))*({obg}-{ppgrad})+{ppgrad}",
                "psi/ft", fmt="0.000")
    fgemw = c.out("Eaton fracture EMW", f"{fge}/0.052", "ppg", fmt="0.00")
    fghw = c.out("Hubbert & Willis minimum FG", f"({obg}+2*{ppgrad})/3",
                 "psi/ft", fmt="0.000")
    c.out("Hubbert & Willis minimum EMW", f"{fghw}/0.052", "ppg", fmt="0.00")
    lot = c.link("LOT / FIT EMW (measured)", "WD_LOT", "ppg")
    c.out("Calibration check",
          f'IF(ABS({lot}-{fgemw})<=0.5,"OK - matches LOT within 0.5 ppg",'
          f'"CHECK: calibrate to LOT/minifrac")',
          None, fmt="@")

    sb.section("Drilling Window vs Depth")

    c = sb.calc("Current Mud & ECD (for the window plot)",
                eq="ECD = MW + APL / (0.052 x TVD)",
                note="APL at full circulating rate. A constant APL overstates ECD at "
                     "shallow depths - refine per-section on the Hydraulics sheet.")
    mw = c.link("Current mud weight (MW)", "WD_OMW", "ppg")
    apl = c.inp("Annular pressure loss (APL)", 200, "psi", fmt="#,##0")

    # ------------------------------------------------------------ depth table
    sb.row += 1
    band_row = sb.row
    ws.merge_cells(start_row=band_row, start_column=1, end_row=band_row, end_column=6)
    band = ws.cell(row=band_row, column=1,
                   value="Depth Table - enter TVD / pore EMW / frac EMW per row (yellow); "
                         "MW and ECD compute from the block above")
    band.font = S.F_SECTION
    band.fill = S.FILL_SECTION
    for col in range(1, 7):
        ws.cell(row=band_row, column=col).fill = S.FILL_SECTION
    sb.row += 1

    hdr_row = sb.row
    headers = ["TVD (ft)", "Pore EMW (ppg)", "Frac EMW (ppg)", "MW (ppg)", "ECD (ppg)",
               "", "TVDh*", "POREh*", "FRACh*", "MWh*", "ECDh*"]
    for i, h in enumerate(headers, start=1):
        if not h:
            continue
        hc = ws.cell(row=hdr_row, column=i, value=h)
        hc.font = S.F_HEADER
        hc.border = S.BORDER_BOX
        hc.alignment = S.AL_RIGHT if i > 1 else S.AL_LEFT
    sb.row += 1

    first = sb.row
    last = first + N_ROWS - 1
    for i in range(N_ROWS):
        r = first + i
        t, p, f = DEFAULT_WINDOW[i] if i < len(DEFAULT_WINDOW) else (None, None, None)
        _cell(ws, r, 1, t, fmt="#,##0", is_input=True)
        _cell(ws, r, 2, p, fmt="0.00", is_input=True)
        _cell(ws, r, 3, f, fmt="0.00", is_input=True)
        _cell(ws, r, 4, f'=IF($A{r}="","",{mw})', fmt="0.00")
        _cell(ws, r, 5, f'=IF($A{r}="","",{mw}+{apl}/(0.052*$A{r}))', fmt="0.00")
        # NA()-guarded numeric helpers for the chart
        helpers = (
            (7, f'=IF($A{r}="",NA(),$A{r})'),
            (8, f'=IF(OR($A{r}="",$B{r}=""),NA(),$B{r})'),
            (9, f'=IF(OR($A{r}="",$C{r}=""),NA(),$C{r})'),
            (10, f'=IF($A{r}="",NA(),D{r})'),
            (11, f'=IF($A{r}="",NA(),E{r})'),
        )
        for col, formula in helpers:
            hcell = ws.cell(row=r, column=col, value=formula)
            hcell.font = S.F_NOTE
            hcell.number_format = "0.00"
            hcell.alignment = S.AL_RIGHT
    sb.row = last + 1
    note = ws.cell(row=sb.row, column=1,
                   value="* helper columns G-K feed the Drilling Window chart - do not edit. "
                         "They show #N/A on unused rows by design (chart gaps).")
    note.font = S.F_NOTE
    sb.row += 1

    sb.section("Kick Tolerance at Current Shoe")

    c = sb.calc("Kick Margin at the Shoe",
                eq="Margin EMW = LOT EMW - MAX(pore EMW at TD, current MW)",
                note="Simple shoe-strength margin: what the shoe can hold above the "
                     "heavier of the pore pressure EMW and the current mud. For a full "
                     "kick-volume tolerance use the Well Control sheet.")
    lot2 = c.link("LOT / FIT EMW at shoe", "WD_LOT", "ppg")
    omw2 = c.link("Current mud weight", "WD_OMW", "ppg")
    shoe = c.link("Casing shoe TVD", "WD_ShoeTVD", "ft", fmt="#,##0")
    tvd2 = c.link("Well TD TVD", "WD_TVD", "ft", fmt="#,##0")
    poretd = c.inp("Pore pressure EMW at TD", 14.3, "ppg", fmt="0.00",
                   note="Use the Eaton estimate above, calibrated to any kicks/connection gas.")
    c.out("Open hole below shoe (TVD)", f"{tvd2}-{shoe}", "ft", fmt="#,##0",
          note="0 ft is normal for a horizontal well with the shoe at reservoir TVD.")
    marg = c.out("Kick margin EMW at shoe", f"{lot2}-MAX({poretd},{omw2})", "ppg", fmt="0.00")
    c.out("Margin as pressure at shoe", f"0.052*{marg}*{shoe}", "psi", fmt="#,##0")
    c.out("Status",
          f'IF({marg}>=0.5,"OK - kick margin adequate",'
          f'IF({marg}>0,"MARGINAL - thin kick margin at shoe",'
          f'"CHECK: no kick margin - shoe cannot hold a kick on this mud"))',
          None, fmt="@")

    # ------------------------------------------------------------ chart
    chart = ScatterChart()
    chart.varyColors = False
    chart.title = "Drilling Window"
    chart.x_axis.title = "EMW (ppg)"
    chart.y_axis.title = "TVD (ft)"
    chart.y_axis.scaling.orientation = "maxMin"
    for ax in (chart.x_axis, chart.y_axis):
        ax.delete = False
        ax.tickLblPos = "nextTo"
    chart.height = 13
    chart.width = 16
    yref = Reference(ws, min_col=7, min_row=first, max_row=last)
    for col, name in ((8, "Pore EMW"), (9, "Frac EMW"), (10, "Mud weight"), (11, "ECD")):
        xref = Reference(ws, min_col=col, min_row=first, max_row=last)
        s = Series(yref, xref, title=name)
        s.marker.symbol = "circle"
        s.marker.size = 4
        chart.series.append(s)
    ws.add_chart(chart, "M6")
