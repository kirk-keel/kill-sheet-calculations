"""Drilling: IWCF-style surface BOP kill sheet, valid for vertical, deviated
and horizontal wells.

String and annulus volumes come from component tables (drill pipe, HWDP,
drill collars, ...). The kill schedule tracks the kill-mud front through the
tapered string by pumped volume, interpolates the front's TVD from the
Directional Survey sheet, and computes drill pipe pressure as

    P = SIDPP - 0.052 x (KMW - OMW) x TVD(front) + SCR + (FCP - SCR) x s

where s is the fraction of string volume pumped. Hydrostatic follows TVD,
friction follows pumped volume - correct on horizontal wells where the
classic linear ICP->FCP ramp holds BHP too high through the build.
A kill plot (DP pressure vs strokes) is generated automatically.
"""
from openpyxl.chart import Reference, ScatterChart, Series
from openpyxl.worksheet.datavalidation import DataValidation

from .. import style as S
from ..builder import UNLOCKED, SheetBuilder
from .directional_survey import interp_tvd

N_STRING = 8   # component rows in the drill string table
N_ANN = 6      # section rows in the annulus table

# key cell refs published for the Kill Form print sheet (populated by build())
REFS = {}

# component names match the Tubular Library catalog so OD/ID auto-fill
STRING_DEFAULTS = [
    ("DP 5 19.50#", 9700),
    ("HWDP 5 49.3#", 500),
    ("DC 6-1/2 92#", 300),
]
ANN_DEFAULTS = [
    ("DC x open hole", 8.5, 6.5, 300),
    ("DP x open hole", 8.5, 5.0, 4300),
    ("DP x casing", 8.681, 5.0, 5900),
]


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
        wb, "Kill Sheet", "drilling",
        "Well Control Kill Sheet - Surface BOP (Vertical / Deviated / Horizontal)",
        "Component-level volumes, kill mud weight, ICP/FCP, survey-driven pressure "
        "schedule and auto-generated kill plot",
        description="Full kill sheet: string & annulus component tables, KMW, ICP, FCP, "
                    "survey-driven step-down schedule for deviated/horizontal wells, kill plot",
    )
    ws = sb.ws

    sb.section("1. Pre-Recorded Data (light blue = linked to Well Data sheet)")
    c = sb.calc("Well & Pump Data",
                note="Linked to the Well Data sheet - update there, or overwrite locally. "
                     "The schedule below also reads the Directional Survey sheet directly.")
    omw = c.link("Current mud weight (OMW)", "WD_OMW", "ppg")
    md = c.link("Bit / hole measured depth (MD)", "WD_MD", "ft", fmt="#,##0")
    tvd = c.link("Bit / hole true vertical depth (TVD)", "WD_TVD", "ft", fmt="#,##0")
    shoe_md = c.link("Casing shoe MD", "WD_ShoeMD", "ft", fmt="#,##0")
    shoe_tvd = c.link("Casing shoe TVD", "WD_ShoeTVD", "ft", fmt="#,##0")
    lot = c.link("LOT / FIT equivalent mud weight", "WD_LOT", "ppg")
    scr = c.link("Slow circulating rate pressure (SCR)", "WD_SCR", "psi", fmt="#,##0")
    spr = c.link("Pump output", "WD_SPR", "bbl/stk", fmt="0.0000")
    krate = c.link("Kill rate", "WD_KillRate", None, fmt="#,##0",
                   note="strokes per minute (spm); linked to Well Data.")

    c = sb.calc("Maximum Allowable Annular Surface Pressure (MAASP)",
                eq="MAASP = (LOT_EMW - MW) x 0.052 x Shoe TVD",
                note="Valid only while the annulus above the shoe contains mud of density MW. "
                     "Rounding rule: maximized values round UP to whole psi (1000.1 -> 1001).")
    maasp = c.out("MAASP (initial, with current mud)",
                  f"ROUNDUP(ROUND(({lot}-{omw})*0.052*{shoe_tvd},6),0)", "psi", fmt="#,##0")

    # ------------------------------------------------------- drill string table
    sb.section("2. Drill String Volume (component by component, top down)")
    ws.cell(row=sb.row, column=1,
            value="Pick components from the dropdown (Tubular Library) - OD/ID auto-fill. "
                  "For non-catalog pipe, type any name and overwrite OD/ID. Unused rows stay "
                  "blank.").font = S.F_NOTE
    sb.row += 1
    hdr = sb.row
    _table_header(ws, hdr, ["Component", "OD (in)", "ID (in)", "Length (ft)",
                            "Capacity (bbl/ft)", "Volume (bbl)", "Top MD (ft)",
                            "Cum vol at top (bbl)"])
    first = hdr + 1
    for i in range(N_STRING):
        r = first + i
        name, ln = STRING_DEFAULTS[i] if i < len(STRING_DEFAULTS) else ("", None)
        nc = ws.cell(row=r, column=1, value=name)
        nc.fill = S.FILL_INPUT
        nc.border = S.BORDER_BOX
        nc.font = S.F_INPUT
        nc.protection = UNLOCKED
        _cell(ws, r, 2, f'=IF($A{r}="","",IFERROR(VLOOKUP($A{r},TL_Table,2,FALSE),""))',
              "0.000", is_input=True)
        _cell(ws, r, 3, f'=IF($A{r}="","",IFERROR(VLOOKUP($A{r},TL_Table,3,FALSE),""))',
              "0.000", is_input=True)
        _cell(ws, r, 4, ln, "#,##0", is_input=True)
        _cell(ws, r, 5, f'=IF($C{r}="",0,$C{r}^2/1029.4)', "0.00000")
        _cell(ws, r, 6, f'=$E{r}*IF($D{r}="",0,$D{r})', "0.00")
        _cell(ws, r, 7, "=0" if i == 0 else f'=$G{r - 1}+IF($D{r - 1}="",0,$D{r - 1})', "#,##0")
        _cell(ws, r, 8, "=0" if i == 0 else f"=$H{r - 1}+$F{r - 1}", "0.00")
    last = first + N_STRING - 1
    dv = DataValidation(type="list", formula1="=TL_Names", allow_blank=True,
                        showErrorMessage=False)
    ws.add_data_validation(dv)
    dv.add(f"A{first}:A{last}")
    str_cap_rng = f"$E${first}:$E${last}"
    str_top_rng = f"$G${first}:$G${last}"
    str_cum_rng = f"$H${first}:$H${last}"
    sb.row = last + 1

    c = sb.calc("Drill String Totals",
                eq="Capacity = ID^2/1029.4 [bbl/ft];  Strokes = Volume / Pump output")
    str_len = c.out("Total string length", f"SUM($D${first}:$D${last})", "ft", fmt="#,##0")
    c.out("Length check vs bit MD",
          f'IF({str_len}={md},"OK - matches bit MD","CHECK: components <> bit MD")', None, fmt="@")
    str_vol = c.out("Drill string volume", f"SUM($F${first}:$F${last})", "bbl", fmt="0.0")
    stb = c.out("Strokes surface to bit", f"ROUNDUP(ROUND({str_vol}/{spr},6),0)", None, fmt="#,##0")
    c.out("Time surface to bit", f"{stb}/{krate}", None, fmt="0.0", note="minutes at kill rate")

    # ------------------------------------------------------------ annulus table
    sb.section("3. Annulus Volume (bottom up)")
    sb.row += 0
    hdr = sb.row
    _table_header(ws, hdr, ["Section", "Hole/Csg ID (in)", "Pipe OD (in)", "Length (ft)",
                            "Capacity (bbl/ft)", "Volume (bbl)"])
    afirst = hdr + 1
    for i in range(N_ANN):
        r = afirst + i
        name, hid, pod, ln = ANN_DEFAULTS[i] if i < len(ANN_DEFAULTS) else ("", None, None, None)
        nc = ws.cell(row=r, column=1, value=name)
        nc.fill = S.FILL_INPUT
        nc.border = S.BORDER_BOX
        nc.font = S.F_INPUT
        nc.protection = UNLOCKED
        _cell(ws, r, 2, hid, "0.000", is_input=True)
        _cell(ws, r, 3, pod, "0.000", is_input=True)
        _cell(ws, r, 4, ln, "#,##0", is_input=True)
        _cell(ws, r, 5, f'=IF(OR($B{r}="",$C{r}=""),0,($B{r}^2-$C{r}^2)/1029.4)', "0.00000")
        _cell(ws, r, 6, f'=$E{r}*IF($D{r}="",0,$D{r})', "0.00")
    alast = afirst + N_ANN - 1
    bha_ann_cap = f"$E${afirst}"  # capacity around the BHA (first row = deepest section)
    sb.row = alast + 1

    c = sb.calc("Annulus Totals",
                eq="Annular capacity = (Dh^2 - Dp^2)/1029.4 [bbl/ft]")
    ann_vol = c.out("Annulus volume", f"SUM($F${afirst}:$F${alast})", "bbl", fmt="0.0")
    bts = c.out("Strokes bit to surface", f"ROUNDUP(ROUND({ann_vol}/{spr},6),0)", None, fmt="#,##0")
    tot = c.out("Total circulation strokes", f"{stb}+{bts}", None, fmt="#,##0")
    c.out("Total circulation time", f"{tot}/{krate}", None, fmt="0.0", note="minutes at kill rate")

    sb.section("4. Kick Data (Shut-In)")
    c = sb.calc("Recorded on Shut-In",
                note="Allow pressures to stabilise; watch for gas migration on SIDPP. On "
                     "horizontal wells an influx lying in the lateral may show little or no "
                     "SICP-SIDPP difference until it enters the build.")
    sidpp = c.inp("Shut-in drill pipe pressure (SIDPP)", 500, "psi", fmt="#,##0")
    sicp = c.inp("Shut-in casing pressure (SICP)", 700, "psi", fmt="#,##0")
    gain = c.inp("Pit gain", 15, "bbl", fmt="0.0")

    sb.section("5. Kill Calculations")
    c = sb.calc("Kill Mud Weight (KMW)",
                eq="KMW = OMW + SIDPP / (0.052 x TVD)",
                note="TVD, never MD. Round UP to the nearest 0.1 ppg for practical mixing.")
    kmw_x = c.out("Kill mud weight (exact)", f"{omw}+{sidpp}/(0.052*{tvd})", "ppg", fmt="0.000")
    kmw = c.out("Kill mud weight (rounded up)", f"ROUNDUP(ROUND({kmw_x}*10,6),0)/10", "ppg", fmt="0.0")

    c = sb.calc("Initial & Final Circulating Pressure",
                eq="ICP = SCR + SIDPP;   FCP = SCR x KMW / OMW")
    icp = c.out("Initial circulating pressure (ICP)", f"{scr}+{sidpp}", "psi", fmt="#,##0")
    fcp = c.out("Final circulating pressure (FCP)", f"{scr}*{kmw}/{omw}", "psi", fmt="#,##0")
    drop = c.out("Pressure drop per 100 strokes (vertical well)",
                 f"ROUNDDOWN(ROUND(({icp}-{fcp})/{stb}*100,6),0)", "psi", fmt="#,##0",
          note="Rounding rule: psi/step always rounds DOWN (161.9 -> 161). Linear ICP->FCP "
               "ramp is only valid for near-vertical wells - use the survey-driven schedule "
               "below for deviated/horizontal wells.")

    c = sb.calc("Bottomhole Pressure (constant during kill)",
                eq="BHP = SIDPP + 0.052 x OMW x TVD")
    fp = c.out("Formation pressure", f"{sidpp}+0.052*{omw}*{tvd}", "psi", fmt="#,##0")
    c.out("Formation pressure EMW", f"({sidpp}+0.052*{omw}*{tvd})/(0.052*{tvd})", "ppg", fmt="0.00")

    c = sb.calc("Influx Characterisation",
                eq="h_influx = Pit gain / Ann. capacity (at BHA);   "
                   "Grad_influx = 0.052 x OMW - (SICP - SIDPP) / h_influx",
                note="Gas ~0.05-0.25 psi/ft, oil ~0.3-0.4, salt water ~0.4-0.5. Assumes influx "
                     "around the BHA and a VERTICAL influx column - unreliable in a lateral, "
                     "where the influx adds little vertical height.")
    h = c.out("Influx height (along hole)", f"{gain}/{bha_ann_cap}", "ft", fmt="#,##0")
    gi = c.out("Influx gradient", f"0.052*{omw}-({sicp}-{sidpp})/{h}", "psi/ft", fmt="0.000")
    c.out("Likely influx type",
          f'IF({gi}<0.25,"GAS",IF({gi}<0.4,"OIL / GAS-CUT","WATER"))', None, fmt="@")

    c = sb.calc("MAASP After Kill",
                eq="MAASP_kill = (LOT_EMW - KMW) x 0.052 x Shoe TVD",
                note="Rounding rule: maximized values round UP to whole psi.")
    maasp_k = c.out("MAASP with kill mud", f"ROUNDUP(ROUND(({lot}-{kmw})*0.052*{shoe_tvd},6),0)",
                    "psi", fmt="#,##0")

    # ------------------------------------------------- survey-driven schedule
    sb.section("6. Kill Schedule - Survey-Driven (valid for any trajectory)")
    ws.cell(row=sb.row, column=1,
            value="Front MD: pumped volume located in the string tables above. Front TVD: "
                  "interpolated from the Directional Survey sheet. P = SIDPP - 0.052 x "
                  "(KMW-OMW) x TVD(front) + SCR + (FCP-SCR) x s. With KMW rounded up, the "
                  "final pressure ends slightly below FCP (slight overbalance - normal). "
                  "The 'vertical well' column steps down by the ROUNDDOWN psi/100stk figure "
                  "(never below FCP), the way the schedule is written on a manual kill sheet.").font = S.F_NOTE
    ws.merge_cells(start_row=sb.row, start_column=1, end_row=sb.row, end_column=6)
    ws.cell(row=sb.row, column=1).alignment = S.AL_WRAP
    ws.row_dimensions[sb.row].height = 40
    sb.row += 1
    hdr = sb.row
    _table_header(ws, hdr, ["% strokes to bit", "Strokes", "Front MD (ft)", "Front TVD (ft)",
                            "DP pressure (psi)", "Vertical-well ramp (psi)"])
    sfirst = hdr + 1
    for i in range(21):
        r = sfirst + i
        s_f = i / 20
        _cell(ws, r, 1, s_f, "0%")
        _cell(ws, r, 2, f"=ROUND({stb}*{s_f},0)", "#,##0")
        vt = f"({s_f}*{str_vol})"
        m = f"MATCH({vt},{str_cum_rng},1)"
        _cell(ws, r, 3,
              f"=INDEX({str_top_rng},{m})+IF(INDEX({str_cap_rng},{m})=0,0,"
              f"({vt}-INDEX({str_cum_rng},{m}))/INDEX({str_cap_rng},{m}))", "#,##0")
        _cell(ws, r, 4, "=" + interp_tvd(f"$C{r}"), "#,##0")
        _cell(ws, r, 5,
              f"=ROUND({sidpp}-0.052*({kmw}-{omw})*$D{r}+{scr}+({fcp}-{scr})*{s_f},0)",
              "#,##0", is_output=True)
        # driller's ramp: step down by the ROUNDDOWN psi/100stk figure, never below FCP
        _cell(ws, r, 6, f"=MAX({fcp},{icp}-{drop}*$B{r}/100)", "#,##0")
    slast = sfirst + 20
    sb.row = slast + 1

    # ------------------------------------------------------------- kill plot
    chart = ScatterChart()
    chart.title = "Kill Plot - DP Pressure vs Strokes"
    chart.x_axis.title = "Strokes pumped"
    chart.y_axis.title = "Drill pipe pressure (psi)"
    for ax in (chart.x_axis, chart.y_axis):
        ax.delete = False
        ax.tickLblPos = "nextTo"
    chart.height = 11
    chart.width = 20
    xref = Reference(ws, min_col=2, min_row=sfirst, max_row=slast)
    for col, name in ((5, "Survey-driven schedule"), (6, "Vertical-well linear ramp")):
        yref = Reference(ws, min_col=col, min_row=sfirst, max_row=slast)
        series = Series(yref, xref, title=name)
        series.marker.symbol = "circle"
        series.marker.size = 4
        chart.series.append(series)
    ws.add_chart(chart, f"H{hdr}")

    REFS.clear()
    REFS.update({
        "omw": omw, "md": md, "tvd": tvd, "shoe_md": shoe_md, "shoe_tvd": shoe_tvd,
        "lot": lot, "scr": scr, "spr": spr, "krate": krate, "maasp": maasp,
        "str_vol": str_vol, "stb": stb, "ann_vol": ann_vol, "bts": bts, "tot": tot,
        "sidpp": sidpp, "sicp": sicp, "gain": gain, "kmw_x": kmw_x, "kmw": kmw,
        "icp": icp, "fcp": fcp, "drop": drop, "fp": fp, "maasp_k": maasp_k,
        "sched_first": sfirst, "sched_last": slast,
    })
