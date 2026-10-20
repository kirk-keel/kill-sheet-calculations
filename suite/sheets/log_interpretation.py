"""Drilling: open-hole log interpretation - quick-look petrophysics.

Single-point calculator blocks (Vsh from GR, density/neutron/sonic porosity,
effective porosity, Archie Sw, Rw from SP, Timur permeability, net pay
cutoffs) plus a 25-row log data table that applies the same chain of
calculations depth by depth, flags net pay against the cutoffs, and sums
net pay, pay-average PHIE/Sw and hydrocarbon pore-feet.

Table geometry (bespoke, nodal.py style):
  A=Depth  B=GR  C=RHOB  D=NPHI  E=RT          (yellow inputs)
  F=IGR  G=Vsh(Larionov T)  H=PHID  I=PHIND  J=PHIE  K=Sw  L=pay flag
  M..P = NA()-guarded chart helpers (depth, Sw, Vsh, PHIE) so chart source
  ranges stay purely numeric even if the user blanks input rows.
"""
from openpyxl.chart import Reference, ScatterChart, Series

from .. import style as S
from ..builder import UNLOCKED, SheetBuilder
from ..convert import TEMP_F

N_ROWS = 25

# Depth (ft), GR (API), RHOB (g/cc), NPHI (v/v), RT (ohm-m)
# Shale cap, clean hydrocarbon sand 5412-5430, wet sand, shale base.
TABLE_DATA = [
    (5400, 108, 2.55, 0.33, 4.0),
    (5402, 112, 2.56, 0.34, 3.5),
    (5404, 118, 2.58, 0.35, 3.0),
    (5406, 110, 2.55, 0.33, 4.0),
    (5408,  95, 2.50, 0.30, 5.0),
    (5410,  62, 2.42, 0.24, 5.0),
    (5412,  34, 2.28, 0.19, 22.0),
    (5414,  30, 2.24, 0.17, 35.0),
    (5416,  27, 2.21, 0.15, 48.0),
    (5418,  25, 2.20, 0.14, 55.0),
    (5420,  26, 2.21, 0.15, 60.0),
    (5422,  28, 2.23, 0.16, 45.0),
    (5424,  29, 2.25, 0.18, 38.0),
    (5426,  31, 2.27, 0.19, 30.0),
    (5428,  33, 2.29, 0.20, 24.0),
    (5430,  35, 2.31, 0.21, 20.0),
    (5432,  55, 2.38, 0.24, 4.0),
    (5434,  32, 2.40, 0.24, 3.5),
    (5436,  30, 2.41, 0.25, 3.0),
    (5438,  33, 2.42, 0.25, 3.0),
    (5440,  88, 2.52, 0.31, 4.5),
    (5442, 104, 2.55, 0.33, 4.0),
    (5444, 115, 2.57, 0.34, 3.0),
    (5446, 109, 2.56, 0.33, 3.5),
    (5448, 106, 2.55, 0.33, 4.0),
]


def _cell(ws, row, col, value, fmt="0.000", is_input=False, is_output=False):
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
        wb, "Log Interpretation", "drilling",
        "Open-Hole Log Interpretation - Quick-Look Petrophysics",
        "Vsh from GR, density/neutron/sonic porosity, Archie Sw, Rw from SP, "
        "Timur permeability, net pay cutoffs and a 25-point log data table",
        description="Quick-look petrophysics: Vsh, porosity models, Archie Sw, "
                    "permeability estimate, net pay table with Sw/Vsh and porosity "
                    "depth plots",
    )
    ws = sb.ws

    sb.section("Single-Point Petrophysics")

    # ------------------------------------------------------------ 1. Vsh from GR
    c = sb.calc("Shale Volume from Gamma Ray",
                eq="IGR = (GR - GR_clean)/(GR_shale - GR_clean);   "
                   "Vsh(Larionov Tertiary) = 0.083 x (2^(3.7 x IGR) - 1);   "
                   "Vsh(Larionov older) = 0.33 x (2^(2 x IGR) - 1)",
                note="Pick GR_clean in the cleanest sand and GR_shale in a thick "
                     "shale on the same log run.")
    gr = c.inp("Gamma ray reading (GR)", 45, "API", fmt="0.0")
    grcl = c.inp("Clean sand baseline (GR_clean)", 20, "API", fmt="0.0")
    grsh = c.inp("Shale baseline (GR_shale)", 120, "API", fmt="0.0")
    igr = c.out("Gamma ray index (IGR)", f"({gr}-{grcl})/({grsh}-{grcl})",
                None, fmt="0.000")
    c.out("Vsh - linear (Vsh = IGR)", f"{igr}", None, fmt="0.000",
          note="Linear index overstates Vsh in most rocks - use as an upper bound.")
    vsh_lt = c.out("Vsh - Larionov Tertiary", f"0.083*(2^(3.7*{igr})-1)",
                   None, fmt="0.000",
                   note="Larionov (1969) Tertiary (unconsolidated) rocks - use for "
                        "young clastics (Gulf Coast type).")
    c.out("Vsh - Larionov older rocks", f"0.33*(2^(2*{igr})-1)",
          None, fmt="0.000",
          note="Larionov older (consolidated, pre-Tertiary) rocks. Both curves "
               "reduce the linear IGR; pick the one matching rock age/compaction.")

    # ------------------------------------------------------------ 2. density porosity
    c = sb.calc("Density Porosity",
                eq="PHID = (rho_ma - rho_b) / (rho_ma - rho_f)",
                note="Matrix density 2.65 g/cc sandstone, 2.71 limestone, "
                     "2.87 dolomite. Fluid density 1.0 fresh filtrate, ~1.1 "
                     "salt filtrate.")
    rhob = c.inp("Bulk density log (RHOB)", 2.35, None, fmt="0.000",
                 note="g/cc.")
    rhoma = c.inp("Matrix density (rho_ma)", 2.65, None, fmt="0.000",
                  note="g/cc - 2.65 sandstone (default), 2.71 limestone.")
    rhof = c.inp("Fluid density (rho_f)", 1.0, None, fmt="0.000",
                 note="g/cc - mud filtrate in the flushed zone.")
    phid = c.out("Density porosity (PHID)", f"({rhoma}-{rhob})/({rhoma}-{rhof})",
                 "v/v", fmt="0.0000")

    # ------------------------------------------------------------ 3. neutron-density
    c = sb.calc("Neutron-Density & Gas Flag",
                eq="PHIND = (PHID + NPHI)/2;   gas flag when PHID - NPHI > 0.04",
                note="On sandstone-scaled logs in a gas zone the density curve reads "
                     "high porosity and the neutron reads low (crossover, "
                     "PHID >> NPHI). Convention here: positive PHID - NPHI beyond "
                     "0.04 v/v flags likely gas effect.")
    nphi = c.inp("Neutron porosity (NPHI)", 0.12, "v/v", fmt="0.000",
                 note="Sandstone matrix scale, environmentally corrected.")
    phind = c.out("Neutron-density porosity (PHIND)", f"({phid}+{nphi})/2",
                  "v/v", fmt="0.0000",
                  note="Simple average; use SQRT((PHID^2+NPHI^2)/2) in gas zones.")
    c.out("Gas crossover status",
          f'IF({phid}-{nphi}>0.04,'
          f'"CHECK: N-D crossover - gas effect likely (PHID >> NPHI)",'
          f'"OK - no significant gas crossover")',
          None, fmt="@")

    # ------------------------------------------------------------ 4. sonic porosity
    c = sb.calc("Sonic Porosity (Wyllie)",
                eq="PHIS = (DT - DT_ma) / (DT_f - DT_ma);   corrected = PHIS / Cp",
                note="Wyllie time-average (1956) - compacted, water-filled clean "
                     "rock. DT_ma: 55.5 us/ft sandstone, 47.5 limestone, 43.5 "
                     "dolomite; DT_f 189 us/ft fresh mud.")
    dt = c.inp("Sonic transit time (DT)", 75, None, fmt="0.0", note="us/ft.")
    dtma = c.inp("Matrix transit time (DT_ma)", 55.5, None, fmt="0.0",
                 note="us/ft - 55.5 sandstone (default).")
    dtf = c.inp("Fluid transit time (DT_f)", 189, None, fmt="0.0", note="us/ft.")
    phis = c.out("Sonic porosity (PHIS)", f"({dt}-{dtma})/({dtf}-{dtma})",
                 "v/v", fmt="0.0000")
    cp = c.inp("Compaction correction factor (Cp)", 1.0, None, fmt="0.00",
               note="Divide PHIS by Cp > 1 in uncompacted sands (Cp ~ DT_shale x "
                    "C / 100, typically 1.0-1.3 where shale DT > 100 us/ft).")
    c.out("Sonic porosity, compaction corrected", f"{phis}/{cp}", "v/v",
          fmt="0.0000")

    # ------------------------------------------------------------ 5. effective porosity
    c = sb.calc("Effective Porosity",
                eq="PHIE = PHIND x (1 - Vsh)",
                note="Shale-corrected total porosity; uses the Larionov Tertiary "
                     "Vsh and neutron-density porosity from the blocks above.")
    phie = c.out("Effective porosity (PHIE)", f"{phind}*(1-{vsh_lt})",
                 "v/v", fmt="0.0000")

    # ------------------------------------------------------------ 6. Archie Sw
    c = sb.calc("Water Saturation (Archie)",
                eq="Sw = ( (a x Rw) / (PHI^m x Rt) )^(1/n)",
                note="Archie (1942) - clean (shale-free) formations. Defaults "
                     "a = 1, m = 2, n = 2 (carbonate/consolidated sand); "
                     "a = 0.62, m = 2.15 (Humble) for unconsolidated sands. "
                     "For shaly sands use Simandoux or dual-water instead - "
                     "Archie overstates Sw when clay conductivity is significant.")
    rw = c.inp("Formation water resistivity (Rw)", 0.05, "ohm-m", fmt="0.000")
    rt = c.inp("True formation resistivity (Rt)", 20, "ohm-m", fmt="0.00")
    a_f = c.inp("Tortuosity factor (a)", 1.0, None, fmt="0.00")
    m_f = c.inp("Cementation exponent (m)", 2.0, None, fmt="0.00")
    n_f = c.inp("Saturation exponent (n)", 2.0, None, fmt="0.00")
    phi_sw = c.inp("Porosity for Sw (PHI)", 0.22, "v/v", fmt="0.000",
                   note="Use PHIE (effective porosity) here.")
    sw = c.out("Water saturation (Archie)",
               f"(({a_f}*{rw})/({phi_sw}^{m_f}*{rt}))^(1/{n_f})",
               "v/v", fmt="0.0000")
    c.out("Water saturation", f"{sw}*100", None, fmt="0.0", note="percent.")
    c.out("Bulk volume water (BVW)", f"{phi_sw}*{sw}", "v/v", fmt="0.0000",
          note="Near-constant BVW over an interval indicates the zone is at "
               "irreducible water saturation (will produce water-free).")

    # ------------------------------------------------------------ 7. Rw from SP
    c = sb.calc("Rw from SP",
                eq="K = 61 + 0.133 x T [degF];   Rw ~ Rmf / 10^(-SSP/K)",
                note="Quick-look only: clean, thick, water-bearing zone, "
                     "NaCl-equivalent filtrate and formation water. Strictly the "
                     "SP gives Rwe/Rmfe (equivalent resistivities) - correct via "
                     "SP charts for precise work.")
    ssp = c.inp("Static SP deflection (SSP)", -80, None, fmt="0.0",
                note="mV, negative in a wet sand with Rmf > Rw.")
    t_f = c.inp("Formation temperature", 150, "degF", fmt="0.0", si=TEMP_F)
    rmf = c.inp("Mud filtrate resistivity at formation temp (Rmf)", 0.35,
                "ohm-m", fmt="0.000")
    k_sp = c.out("SP coefficient (K)", f"61+0.133*{t_f}", None, fmt="0.00")
    c.out("Formation water resistivity (Rw, approx)", f"{rmf}/10^(-{ssp}/{k_sp})",
          "ohm-m", fmt="0.0000")

    # ------------------------------------------------------------ 8. permeability
    c = sb.calc("Permeability Estimates",
                eq="Timur (1968): k [mD] = 0.136 x (PHI x 100)^4.4 / (Swi x 100)^2",
                note="Timur correlation from sandstone core data - order-of-"
                     "magnitude estimate only; requires porosity as a fraction and "
                     "IRREDUCIBLE water saturation. Coates free-fluid / NMR forms "
                     "(e.g. k = ((100 x PHI)^2 x (1-Swi)/Swi)^2 variants) need "
                     "local core calibration before use - not computed here.")
    kphi = c.inp("Porosity (PHI)", 0.22, "v/v", fmt="0.000")
    kswi = c.inp("Irreducible water saturation (Swi)", 0.25, "v/v", fmt="0.000",
                 note="From capillary pressure data or BVW in a zone at "
                      "irreducible conditions.")
    kperm = c.out("Timur permeability (k)",
                  f"0.136*({kphi}*100)^4.4/({kswi}*100)^2",
                  "mD", fmt="#,##0.0")
    c.out("Rough permeability class",
          f'IF({kperm}<1,"tight (< 1 mD)",IF({kperm}<10,"poor (1-10 mD)",'
          f'IF({kperm}<100,"moderate (10-100 mD)",'
          f'IF({kperm}<1000,"good (100-1,000 mD)","excellent (> 1,000 mD)"))))',
          None, fmt="@")

    # ------------------------------------------------------------ 9. cutoffs
    c = sb.calc("Net Pay Cutoffs",
                eq="pay when Vsh <= Vsh_max AND PHIE >= PHIE_min AND Sw <= Sw_max",
                note="Typical clastic quick-look cutoffs; tighten PHIE_min for "
                     "gas (lower viscosity) and loosen for heavy oil per field "
                     "practice. These cells drive the pay flag in the table below.")
    vsh_max = c.inp("Maximum shale volume (Vsh_max)", 0.40, "v/v", fmt="0.00")
    phie_min = c.inp("Minimum effective porosity (PHIE_min)", 0.08, "v/v",
                     fmt="0.00")
    sw_max = c.inp("Maximum water saturation (Sw_max)", 0.60, "v/v", fmt="0.00")
    c.out("Cutoff set",
          f'"Pay = Vsh <= "&TEXT({vsh_max},"0.00")&", PHIE >= "'
          f'&TEXT({phie_min},"0.00")&", Sw <= "&TEXT({sw_max},"0.00")',
          None, fmt="@")

    # ============================================================ log data table
    sb.section("Log Data Table & Quick-Look")

    sb.row += 1
    band_row = sb.row
    ws.merge_cells(start_row=band_row, start_column=1, end_row=band_row,
                   end_column=6)
    band = ws.cell(row=band_row, column=1,
                   value="25-point log listing - enter Depth/GR/RHOB/NPHI/RT "
                         "(yellow); IGR through pay flag computed with the "
                         "single-point parameters above")
    band.font = S.F_SECTION
    band.fill = S.FILL_SECTION
    for col in range(1, 7):
        ws.cell(row=band_row, column=col).fill = S.FILL_SECTION
    sb.row += 1

    hdr_row = sb.row
    headers = ["Depth (ft)", "GR (API)", "RHOB (g/cc)", "NPHI (v/v)",
               "RT (ohm-m)", "IGR", "Vsh", "PHID", "PHIND", "PHIE", "Sw",
               "pay", "D*", "Sw*", "Vsh*", "PHIE*"]
    for i, h in enumerate(headers, start=1):
        hc = ws.cell(row=hdr_row, column=i, value=h)
        hc.font = S.F_HEADER
        hc.border = S.BORDER_BOX
        hc.alignment = S.AL_RIGHT if i > 1 else S.AL_LEFT
    for col in range(7, 17):
        ws.column_dimensions[ws.cell(row=hdr_row, column=col).column_letter].width = 9
    sb.row += 1

    first = sb.row
    last = first + N_ROWS - 1
    for i, (dep, gr_v, rhob_v, nphi_v, rt_v) in enumerate(TABLE_DATA):
        r = first + i
        _cell(ws, r, 1, dep, fmt="#,##0", is_input=True)
        _cell(ws, r, 2, gr_v, fmt="0.0", is_input=True)
        _cell(ws, r, 3, rhob_v, fmt="0.00", is_input=True)
        _cell(ws, r, 4, nphi_v, fmt="0.000", is_input=True)
        _cell(ws, r, 5, rt_v, fmt="0.0", is_input=True)
        # IGR, clipped 0-1
        _cell(ws, r, 6,
              f"=IF(ISNUMBER($B{r}),"
              f"MAX(0,MIN(1,($B{r}-{grcl})/({grsh}-{grcl}))),\"\")",
              is_output=True)
        # Vsh Larionov Tertiary
        _cell(ws, r, 7,
              f"=IF(ISNUMBER($F{r}),0.083*(2^(3.7*$F{r})-1),\"\")",
              is_output=True)
        # PHID, clipped 0-1
        _cell(ws, r, 8,
              f"=IF(ISNUMBER($C{r}),"
              f"MAX(0,MIN(1,({rhoma}-$C{r})/({rhoma}-{rhof}))),\"\")",
              is_output=True)
        # PHIND
        _cell(ws, r, 9,
              f"=IF(AND(ISNUMBER($H{r}),ISNUMBER($D{r})),($H{r}+$D{r})/2,\"\")",
              is_output=True)
        # PHIE
        _cell(ws, r, 10,
              f"=IF(AND(ISNUMBER($I{r}),ISNUMBER($G{r})),"
              f"$I{r}*(1-$G{r}),\"\")",
              is_output=True)
        # Sw (Archie on PHIE), capped at 1
        _cell(ws, r, 11,
              f"=IF(OR(NOT(ISNUMBER($J{r})),NOT(ISNUMBER($E{r}))),\"\","
              f"IF($J{r}<=0,\"\","
              f"MIN(1,(({a_f}*{rw})/($J{r}^{m_f}*$E{r}))^(1/{n_f}))))",
              is_output=True)
        # pay flag
        _cell(ws, r, 12,
              f"=IF(AND(ISNUMBER($G{r}),ISNUMBER($J{r}),ISNUMBER($K{r})),"
              f"IF(AND($G{r}<={vsh_max},$J{r}>={phie_min},$K{r}<={sw_max}),1,0),"
              f"0)",
              fmt="0", is_output=True)
        # NA()-guarded chart helpers
        hd = _cell(ws, r, 13, f"=IF(ISNUMBER($A{r}),$A{r},NA())", fmt="#,##0")
        hs = _cell(ws, r, 14,
                   f"=IF(AND(ISNUMBER($A{r}),ISNUMBER($K{r})),$K{r},NA())")
        hv = _cell(ws, r, 15,
                   f"=IF(AND(ISNUMBER($A{r}),ISNUMBER($G{r})),$G{r},NA())")
        hp = _cell(ws, r, 16,
                   f"=IF(AND(ISNUMBER($A{r}),ISNUMBER($J{r})),$J{r},NA())")
        for hc in (hd, hs, hv, hp):
            hc.font = S.F_NOTE
    sb.row = last + 1
    note = ws.cell(row=sb.row, column=1,
                   value="* columns M-P are NA()-guarded chart helpers (depth, "
                         "Sw, Vsh, PHIE) - leave them in place. Blank input rows "
                         "drop out of the charts as #N/A by design.")
    note.font = S.F_NOTE
    sb.row += 1

    flag_rng = f"$L${first}:$L${last}"
    phie_rng = f"$J${first}:$J${last}"
    sw_rng = f"$K${first}:$K${last}"

    sb.section("Net Pay Summary")

    c = sb.calc("Net Pay & Pay-Average Properties",
                eq="Net pay = SUM(pay flags) x sample interval;   averages via "
                   "SUMPRODUCT over flagged rows",
                note="Sample-count method: each flagged sample contributes one "
                     "interval of pay. Averages and hydrocarbon pore-feet are "
                     "arithmetic over the flagged samples only.")
    step = c.inp("Sample interval", 2, "ft", fmt="0.0",
                 note="Depth step of the table rows (2 ft default).")
    npay = c.out("Net pay", f"SUM({flag_rng})*{step}", "ft", fmt="0.0")
    c.out("Average PHIE over pay",
          f"IF(SUM({flag_rng})=0,NA(),"
          f"SUMPRODUCT({flag_rng},{phie_rng})/SUM({flag_rng}))",
          "v/v", fmt="0.0000",
          note="#N/A when no samples pass the cutoffs.")
    c.out("Average Sw over pay",
          f"IF(SUM({flag_rng})=0,NA(),"
          f"SUMPRODUCT({flag_rng},{sw_rng})/SUM({flag_rng}))",
          "v/v", fmt="0.0000")
    c.out("Hydrocarbon pore-feet",
          f"(SUMPRODUCT({flag_rng},{phie_rng})"
          f"-SUMPRODUCT({flag_rng},{phie_rng},{sw_rng}))*{step}",
          "ft", fmt="0.00",
          note="SUM over pay of PHIE x (1 - Sw) x interval. Multiply by "
               "drainage area x 7,758 bbl/ac-ft for STOIIP (oil, before Bo).")
    c.out("Status",
          f'IF(SUM({flag_rng})=0,'
          f'"CHECK: no samples pass the pay cutoffs - review cutoff set",'
          f'IF({npay}<10,"MARGINAL: thin pay ("&TEXT({npay},"0.0")&" ft)",'
          f'"OK - "&TEXT({npay},"0.0")&" ft net pay flagged"))',
          None, fmt="@")

    # ------------------------------------------------------------ charts
    dep_ref = Reference(ws, min_col=13, min_row=first, max_row=last)

    ch1 = ScatterChart()
    ch1.varyColors = False
    ch1.title = "Sw & Vsh vs Depth"
    ch1.x_axis.title = "Fraction (v/v)"
    ch1.y_axis.title = "Depth (ft)"
    for ax in (ch1.x_axis, ch1.y_axis):
        ax.delete = False
        ax.tickLblPos = "nextTo"
    ch1.x_axis.scaling.min = 0
    ch1.x_axis.scaling.max = 1
    ch1.y_axis.scaling.orientation = "maxMin"
    ch1.height = 12
    ch1.width = 12
    for col, name in ((14, "Sw"), (15, "Vsh")):
        xref = Reference(ws, min_col=col, min_row=first, max_row=last)
        s = Series(dep_ref, xref, title=name)
        s.marker.symbol = "circle"
        s.marker.size = 4
        ch1.series.append(s)
    ws.add_chart(ch1, f"R{hdr_row}")

    ch2 = ScatterChart()
    ch2.varyColors = False
    ch2.title = "Porosity vs Depth"
    ch2.x_axis.title = "PHIE (v/v)"
    ch2.y_axis.title = "Depth (ft)"
    for ax in (ch2.x_axis, ch2.y_axis):
        ax.delete = False
        ax.tickLblPos = "nextTo"
    ch2.y_axis.scaling.orientation = "maxMin"
    ch2.height = 12
    ch2.width = 12
    xref = Reference(ws, min_col=16, min_row=first, max_row=last)
    s = Series(dep_ref, xref, title="PHIE")
    s.marker.symbol = "circle"
    s.marker.size = 4
    ch2.series.append(s)
    ws.add_chart(ch2, f"R{hdr_row + 25}")
