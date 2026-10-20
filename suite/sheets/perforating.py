"""Completions: underbalance design, cushion design, perf geometry, TCP gun totals."""
from ..builder import SheetBuilder
from ..convert import TEMP_F


def build(wb):
    sb = SheetBuilder(
        wb, "Perforating", "completions",
        "Perforating",
        "Underbalance design, cushion and nitrogen columns, shot density, flow area, TCP gun totals",
        description="Optimal underbalance, wellbore pressure at perfs, cushion design, perf flow area, gun string totals",
    )

    sb.section("Underbalance Design")

    c = sb.calc("Optimal Static Underbalance (King-Style Correlation)",
                eq="dP_opt [psi] = C / k^0.37   (k in mD)",
                note="Rule-of-thumb correlation in the style of King (1985) / Behrmann guidance for perforation cleanup in sandstone. C approx 2500 for oil zones, approx 2900-3500 for gas zones (gas needs more underbalance at the same permeability). Approximate only - cap at what the completion and sand strength can tolerate.")
    k = c.inp("Formation permeability (k)", 100, "mD", fmt="#,##0.0")
    co = c.inp("Coefficient - oil zone (C_oil)", 2500, None, fmt="#,##0", note="King-style, sandstone oil zones.")
    cg = c.inp("Coefficient - gas zone (C_gas)", 2900, None, fmt="#,##0", note="Gas correction: higher C for gas zones.")
    c.out("Optimal underbalance - oil", f"{co}/{k}^0.37", "psi", fmt="#,##0")
    c.out("Optimal underbalance - gas", f"{cg}/{k}^0.37", "psi", fmt="#,##0")

    c = sb.calc("Underbalance from Wellbore Fluid Column",
                eq="P_wb = 0.052 x rho x (TVD_perf - D_level);   dP_ub = P_res - P_wb",
                note="Fluid level below surface (D_level = 0 for a full column). Positive dP_ub = underbalanced.")
    pres = c.inp("Reservoir pressure (P_res)", 4500, "psi", fmt="#,##0")
    rho = c.inp("Wellbore fluid density", 9.0, "ppg")
    tvd = c.inp("TVD at perforations", 9000, "ft", fmt="#,##0")
    lvl = c.inp("Fluid level below surface (D_level)", 500, "ft", fmt="#,##0")
    pwb = c.out("Wellbore pressure at perfs (P_wb)", f"0.052*{rho}*({tvd}-{lvl})", "psi", fmt="#,##0")
    ub = c.out("Static underbalance (dP_ub)", f"{pres}-{pwb}", "psi", fmt="#,##0")
    c.out("Status", f'IF({ub}>0,"UNDERBALANCED",IF({ub}=0,"BALANCED","OVERBALANCED"))',
          None, fmt="@", note="Text result.")

    c = sb.calc("Cushion Design for a Target Underbalance",
                eq="rho_req = (P_res - dP_ub) / (0.052 x TVD);   h_col = (P_res - dP_ub) / (0.052 x rho);   D_level = TVD - h_col",
                note="Two options: full column of lighter fluid (rho_req), or a partial column (swabbed / N2-displaced) of the given brine with the fluid level at D_level.")
    pres = c.inp("Reservoir pressure (P_res)", 4500, "psi", fmt="#,##0")
    dub = c.inp("Target underbalance (dP_ub)", 500, "psi", fmt="#,##0")
    tvd = c.inp("TVD at perforations", 9000, "ft", fmt="#,##0")
    rho = c.inp("Available cushion fluid density", 9.0, "ppg")
    c.out("Required density, full column", f"({pres}-{dub})/(0.052*{tvd})", "ppg", fmt="0.00")
    hc = c.out("Required fluid column height (h_col)", f"({pres}-{dub})/(0.052*{rho})", "ft", fmt="#,##0")
    c.out("Fluid level below surface (D_level)", f"{tvd}-{hc}", "ft", fmt="#,##0",
          note="Negative means the fluid alone is too light to reach the target - see full-column density above.")

    c = sb.calc("Nitrogen Cushion over Brine",
                eq="P_int = P_surf x EXP(0.01875 x SG x D_int / (T_avg_R x Z));   P_perf = P_int + 0.052 x rho x (TVD - D_int)",
                note="Static gas column approximation with average temperature (T in Rankine = degF + 460) and average Z. N2 gas gravity approx 0.97. dP_ub = P_res - P_perf.")
    psf = c.inp("N2 surface pressure (P_surf)", 1500, "psi", fmt="#,##0", note="Use absolute pressure (psia).")
    sg = c.inp("Gas specific gravity (SG)", 0.97, None, fmt="0.000", note="Air = 1.0; N2 approx 0.97.")
    tav = c.inp("Average gas column temperature", 140, "degF", si=TEMP_F, fmt="#,##0")
    z = c.inp("Average Z factor", 1.00, None, fmt="0.000", note="Approx 1.0 for N2 at moderate pressure.")
    dint = c.inp("Gas/brine interface depth (D_int)", 6000, "ft", fmt="#,##0")
    rho = c.inp("Brine density below interface", 8.4, "ppg")
    tvd = c.inp("TVD at perforations", 9000, "ft", fmt="#,##0")
    pres = c.inp("Reservoir pressure (P_res)", 4500, "psi", fmt="#,##0")
    pint = c.out("Pressure at interface (P_int)",
                 f"{psf}*EXP(0.01875*{sg}*{dint}/(({tav}+460)*{z}))", "psi", fmt="#,##0")
    ppf = c.out("Pressure at perfs (P_perf)", f"{pint}+0.052*{rho}*({tvd}-{dint})", "psi", fmt="#,##0")
    c.out("Underbalance with N2 cushion", f"{pres}-{ppf}", "psi", fmt="#,##0",
          note="Positive = underbalanced.")

    sb.section("Perforation Geometry & Flow Area")

    c = sb.calc("Shot Density, Phasing & Flow Area",
                eq="A_flow [in2/ft] = SPF x pi/4 x d_perf^2",
                note="Total open flow area per foot from entrance-hole diameter. Shots per phasing plane = 360 / phasing angle. Flow area is the simple first-order screen for perforation flow efficiency - low SPF and small holes drive perforation skin; use a McLeod / Karakas-Tariq model for a rigorous skin value.")
    spf = c.inp("Shot density (SPF)", 6, None, fmt="#,##0", note="Shots per foot.")
    ph = c.inp("Phasing", 60, None, fmt="#,##0", note="Degrees between adjacent shots.")
    dp = c.inp("Entrance hole diameter (d_perf)", 0.43, "in", fmt="0.000")
    itv = c.inp("Perforated interval", 40, "ft", fmt="#,##0")
    c.out("Shots per full helix turn", f"360/{ph}", None, fmt="#,##0")
    ts = c.out("Total shots", f"{spf}*{itv}", None, fmt="#,##0", note="Assumes 100 pct shot efficiency.")
    af = c.out("Flow area per foot", f"{spf}*PI()/4*{dp}^2", None, fmt="0.000",
               si=("cm2/m", 21.16535), note="in2/ft")
    c.out("Total flow area", f"{af}*{itv}", "in2", fmt="#,##0.0")

    c = sb.calc("Perforation Tunnel Volume",
                eq="V_perf [in3] = pi/4 x d_perf^2 x Pen;   total = V_perf x shots",
                note="Cylindrical tunnel approximation using entrance-hole diameter and penetration depth. Small volume - matters for spotting acid or ball sealer coverage.")
    pen = c.inp("Penetration depth (Pen)", 12, "in", fmt="0.0")
    vp = c.out("Volume per perforation", f"PI()/4*{dp}^2*{pen}", None,
               si=("cm3", 16.38706), fmt="0.000", note="in3")
    c.out("Total perforation volume", f"{vp}*{ts}/231", "gal", fmt="0.00",
          note="231 in3 per gallon.")

    sb.section("TCP Gun String")

    c = sb.calc("Tubing-Conveyed Gun Weight & Length",
                eq="L_string = N x L_gun + L_subs;   W_string = N x L_gun x w_gun + W_subs",
                note="Firing head, subs and spacers entered as lump length and weight. Check totals against crane/derrick limits and lubricator length for wireline contingency.")
    ngun = c.inp("Number of gun sections (N)", 2, None, fmt="#,##0")
    lgun = c.inp("Length per gun section (L_gun)", 20, "ft", fmt="#,##0.0")
    wgun = c.inp("Gun weight per foot (w_gun)", 25, "lb/ft", fmt="0.0")
    lsub = c.inp("Subs / firing head length (L_subs)", 15, "ft", fmt="#,##0.0")
    wsub = c.inp("Subs / firing head weight (W_subs)", 500, "lbm", fmt="#,##0")
    c.out("Total string length", f"{ngun}*{lgun}+{lsub}", "ft", fmt="#,##0.0")
    c.out("Total string weight", f"{ngun}*{lgun}*{wgun}+{wsub}", "lbm", fmt="#,##0")
