"""Drilling: casing burst/collapse/tension ratings and load cases, biaxial correction, stretch."""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "Casing & Tubular Design", "drilling",
        "Casing & Tubular Design",
        "Barlow burst, collapse and tension load cases with safety factors, biaxial correction, MASP, landing stretch",
        description="Burst/collapse/tension ratings and SFs, biaxial collapse derating, gas-to-surface MASP, stretch",
    )

    sb.section("Pipe Body Properties")

    c = sb.calc("Cross-Section Area & Pipe Body Yield",
                eq="t = (OD - ID)/2;   A [in2] = PI()/4 x (OD^2 - ID^2);   Fy [lbf] = Yp x A",
                note="9-5/8 in 47 lb/ft N-80 shown (ID 8.681 in, Yp 80,000 psi).")
    od = c.inp("Casing outside diameter (OD)", 9.625, "in", fmt="0.000")
    idc = c.inp("Casing inside diameter (ID)", 8.681, "in", fmt="0.000")
    yp = c.inp("Minimum yield strength (Yp)", 80000, "psi", fmt="#,##0")
    c.out("Nominal wall thickness (t)", f"({od}-{idc})/2", "in", fmt="0.000")
    a = c.out("Pipe body cross-section area (A)", f"PI()/4*({od}^2-{idc}^2)", "in2", fmt="0.000")
    fy = c.out("Pipe body yield strength (Fy)", f"{yp}*{a}", "lbf", fmt="#,##0")

    sb.section("Burst")

    c = sb.calc("Internal Yield (Barlow) with Wall Tolerance & Design Factor",
                eq="P_burst = 0.875 x 2 x Yp x t / OD;   Working limit = P_burst / DF",
                note="API internal yield: Barlow thin-wall formula with 87.5% minimum wall (12.5% API "
                     "manufacturing tolerance). Typical burst design factor 1.1.")
    od = c.inp("Casing outside diameter (OD)", 9.625, "in", fmt="0.000")
    idc = c.inp("Casing inside diameter (ID)", 8.681, "in", fmt="0.000")
    yp = c.inp("Minimum yield strength (Yp)", 80000, "psi", fmt="#,##0")
    dfb = c.inp("Burst design factor (DF)", 1.10, None, fmt="0.00")
    pb = c.out("Internal yield (burst) rating", f"0.875*2*{yp}*(({od}-{idc})/2)/{od}", "psi", fmt="#,##0",
               note="Matches the API catalog rating (6,870 psi for 9-5/8 47# N-80).")
    c.out("Maximum working burst pressure", f"{pb}/{dfb}", "psi", fmt="#,##0")

    c = sb.calc("Burst Load Case: Gas to Surface & MASP",
                eq="MASP = P_form - G_gas x TVD_form;   Burst load = P_internal - P_external (backup)",
                note="Worst-case design load: well full of gas from the next-section TD. External backup is the "
                     "mud/completion fluid gradient behind the casing (cement often ignored conservatively).")
    pfg = c.inp("Formation pore pressure gradient", 13.0, "ppg", note="At next-section TD, as EMW.")
    tvdf = c.inp("Formation (next TD) TVD", 10000, "ft", fmt="#,##0")
    gg = c.inp("Gas gradient", 0.10, "psi/ft", fmt="0.000")
    tvds = c.inp("Casing shoe TVD", 6000, "ft", fmt="#,##0")
    bkg = c.inp("External backup fluid density", 8.6, "ppg")
    br = c.inp("Burst rating (derated if worn)", 6870, "psi", fmt="#,##0")
    pform = c.out("Formation pressure", f"0.052*{pfg}*{tvdf}", "psi", fmt="#,##0")
    masp = c.out("MASP (gas to surface)", f"{pform}-{gg}*{tvdf}", "psi", fmt="#,##0")
    bls = c.out("Burst load at surface", f"{masp}-0", "psi", fmt="#,##0", note="No backup at surface.")
    blsh = c.out("Burst load at shoe", f"{masp}+{gg}*{tvds}-0.052*{bkg}*{tvds}", "psi", fmt="#,##0")
    c.out("Burst SF at surface", f"{br}/{bls}", None, fmt="0.00")
    c.out("Burst SF at shoe", f"{br}/{blsh}", None, fmt="0.00",
          note="SF >= 1.1 typical burst acceptance.")

    sb.section("Collapse")

    c = sb.calc("Collapse Load & Safety Factor",
                eq="P_collapse = 0.052 x MW_ext x TVD - 0.052 x MW_int x (TVD - L_drop);   SF = rating / load",
                note="External: mud the casing was cemented in. Internal: partial or full evacuation "
                     "(lost circulation, gas lift die-out). Set L_drop = TVD and MW_int = 0 for full evacuation. "
                     "Collapse rating from the API catalog (mode depends on D/t).")
    mwo = c.inp("External fluid density", 12.5, "ppg")
    tvds = c.inp("Casing shoe TVD", 6000, "ft", fmt="#,##0")
    mwi = c.inp("Internal fluid density", 8.6, "ppg")
    ldrop = c.inp("Internal fluid level drop", 2000, "ft", fmt="#,##0",
                  note="Depth from surface to internal fluid level.")
    cr = c.inp("Catalog collapse rating", 4750, "psi", fmt="#,##0",
               note="9-5/8 47# N-80 = 4,750 psi.")
    pc = c.out("Net collapse load at shoe",
               f"0.052*{mwo}*{tvds}-0.052*{mwi}*({tvds}-{ldrop})", "psi", fmt="#,##0")
    c.out("Collapse safety factor", f"{cr}/{pc}", None, fmt="0.00",
          note="SF >= 1.0-1.125 typical collapse acceptance.")

    c = sb.calc("Biaxial Correction: Collapse Under Tension",
                eq="f = SQRT(1 - 0.75 x (Sa/Yp)^2) - 0.5 x Sa/Yp;   Reduced rating = rating x f",
                note="Ellipse of plasticity: axial tension derates collapse resistance (and boosts burst). "
                     "Sa = axial stress = tension / pipe body area.")
    ten = c.inp("Axial tension at point of interest", 300000, "lbf", fmt="#,##0")
    ax = c.inp("Pipe body cross-section area (A)", 13.572, "in2", fmt="0.000")
    yp = c.inp("Minimum yield strength (Yp)", 80000, "psi", fmt="#,##0")
    cr = c.inp("Catalog collapse rating", 4750, "psi", fmt="#,##0")
    pc2 = c.inp("Net collapse load", 2111, "psi", fmt="#,##0")
    sa = c.out("Axial stress (Sa)", f"{ten}/{ax}", "psi", fmt="#,##0")
    fred = c.out("Collapse reduction factor (f)",
                 f"SQRT(1-0.75*({sa}/{yp})^2)-0.5*{sa}/{yp}", None, fmt="0.000")
    rcr = c.out("Tension-reduced collapse rating", f"{cr}*{fred}", "psi", fmt="#,##0")
    c.out("Collapse SF under tension", f"{rcr}/{pc2}", None, fmt="0.00")

    sb.section("Tension")

    c = sb.calc("Axial Tension & Safety Factor",
                eq="T = w x L x BF (buoyed weight);   SF = Fy / T",
                note="Static buoyed hanging weight at the top joint; add overpull, bending and shock loads for the "
                     "full design case. SF >= 1.6-1.8 typical tension acceptance (or 100,000 lbf MOP).")
    w = c.inp("Casing weight in air", 47.0, "lb/ft")
    lc = c.inp("Casing length", 6000, "ft", fmt="#,##0")
    mw = c.inp("Mud weight (MW)", 12.5, "ppg")
    op = c.inp("Design overpull", 100000, "lbf", fmt="#,##0")
    t = c.out("Buoyed hanging weight", f"{w}*{lc}*(65.5-{mw})/65.5", "lbf", fmt="#,##0")
    tt = c.out("Total design tension (with overpull)", f"{t}+{op}", "lbf", fmt="#,##0")
    c.out("Tension SF (vs pipe body yield)", f"{fy}/{tt}", None, fmt="0.00",
          note="Uses pipe body yield Fy from the first calculator; check connection rating separately.")

    c = sb.calc("Casing Stretch When Landed",
                eq="e [in] = P x L x 12 / (A x E),   E = 29.6e6 psi",
                note="Elastic stretch from the landing (pickup) tension applied at surface before hanging off - "
                     "e.g. landing 'as cemented' plus a chosen pickup load.")
    p = c.inp("Landing pickup tension (P)", 50000, "lbf", fmt="#,##0")
    lc = c.inp("Free casing length (L)", 6000, "ft", fmt="#,##0")
    ax = c.inp("Pipe body cross-section area (A)", 13.572, "in2", fmt="0.000")
    c.out("Casing stretch", f"{p}*{lc}*12/({ax}*29600000)", "in", fmt="0.0")
