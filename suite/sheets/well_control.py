"""Drilling: kick tolerance, MAASP, margins, gas behavior, kill and volumetric calculations."""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "Well Control", "drilling",
        "Well Control",
        "Kick tolerance, MAASP, trip/swab/riser margins, gas behavior, kill weight and volumetric method",
        description="Kick tolerance, MAASP, margins, gas migration/expansion, kill mud, volumetric control",
    )

    sb.section("Kick Tolerance & MAASP")

    c = sb.calc("MAASP (Maximum Allowable Annular Surface Pressure)",
                eq="MAASP [psi] = 0.052 x (FG - MW) x TVD_shoe",
                note="FG = fracture gradient at shoe from leak-off test, expressed as EMW. "
                     "Recalculate whenever mud weight changes.")
    fg = c.inp("Fracture gradient at shoe (FG)", 14.5, "ppg", note="From LOT/FIT, as equivalent mud weight.")
    mw = c.inp("Current mud weight (MW)", 12.5, "ppg")
    ds = c.inp("Shoe TVD", 5000, "ft", fmt="#,##0")
    c.out("MAASP", f"ROUNDUP(ROUND(0.052*({fg}-{mw})*{ds},6),0)", "psi", fmt="#,##0",
          note="Rounding rule: maximized values round UP to whole psi (1000.1 -> 1001).")

    c = sb.calc("Kick Tolerance (Volume Basis, Gas at Shoe)",
                eq="H_max = [P_frac - P_form + 0.052 x MW x (TVD - TVD_shoe)] / (0.052 x MW - G_gas);  "
                   "V_shoe = H_max x C_ann;  KT [bbl] = V_shoe x P_frac / P_form",
                note="Single gas bubble, no gas cut above it, Boyle expansion from bottom to shoe (isothermal, Z ignored). "
                     "KT is the largest influx at bottomhole conditions that can be circulated out without breaking down the shoe.")
    fg = c.inp("Fracture gradient at shoe (FG)", 14.5, "ppg")
    mw = c.inp("Mud weight (MW)", 12.5, "ppg")
    ds = c.inp("Shoe TVD", 5000, "ft", fmt="#,##0")
    d = c.inp("Well TVD", 10000, "ft", fmt="#,##0")
    sidpp = c.inp("Design SIDPP (kick overpressure)", 350, "psi", fmt="#,##0",
                  note="Anticipated shut-in drill pipe pressure for the design kick.")
    gg = c.inp("Gas gradient", 0.10, "psi/ft", fmt="0.000", note="0.10-0.15 psi/ft typical for gas.")
    cann = c.inp("Annular capacity at shoe/BHA", 0.0459, "bbl/ft", fmt="0.00000")
    pfrac = c.out("Fracture pressure at shoe", f"0.052*{fg}*{ds}", "psi", fmt="#,##0")
    pform = c.out("Formation (kick) pressure", f"0.052*{mw}*{d}+{sidpp}", "psi", fmt="#,##0")
    hmax = c.out("Max influx height at shoe",
                 f"MAX(0,({pfrac}-{pform}+0.052*{mw}*({d}-{ds}))/(0.052*{mw}-{gg}))",
                 "ft", fmt="#,##0")
    vshoe = c.out("Max influx volume at shoe", f"{hmax}*{cann}", "bbl", fmt="0.0")
    c.out("Kick tolerance (at bottomhole)", f"{vshoe}*{pfrac}/{pform}", "bbl", fmt="0.0",
          note="Compare with realistic kick detection volume; if smaller, set casing or raise MW policy.")

    sb.section("Margins")

    c = sb.calc("Trip Margin / Swab Margin",
                eq="TM [ppg] = YP / (11.7 x (Dh - Dp))",
                note="Overbalance added to cover swab pressures when pulling out (trip margin) or, equally, "
                     "the swab reduction expected running in. Field approximation from yield point.")
    yp = c.inp("Mud yield point (YP)", 12, None, fmt="0.0", note="lb/100 ft2 from viscometer.")
    dh = c.inp("Hole diameter (Dh)", 8.5, "in", fmt="0.000")
    dp = c.inp("Pipe outside diameter (Dp)", 5.0, "in", fmt="0.000")
    tvd = c.inp("Well TVD", 10000, "ft", fmt="#,##0")
    tm = c.out("Trip / swab margin", f"{yp}/(11.7*({dh}-{dp}))", "ppg", fmt="0.00")
    c.out("Equivalent overbalance", f"0.052*{tm}*{tvd}", "psi", fmt="#,##0")

    c = sb.calc("Riser Margin (Floating Rigs)",
                eq="MW_req = (MW x TVD - MW_sw x WD) / (TVD - WD - AG);   RM = MW_req - MW",
                note="Mud weight increment so that, after riser disconnect, seawater above the mudline still balances "
                     "bottomhole pressure. AG = air gap (RKB to sea level). Often impractical in deep water.")
    mw = c.inp("Current mud weight (MW)", 12.5, "ppg")
    tvd = c.inp("Well TVD (from RKB)", 10000, "ft", fmt="#,##0")
    wd = c.inp("Water depth (WD)", 3000, "ft", fmt="#,##0")
    ag = c.inp("Air gap (AG)", 75, "ft", fmt="#,##0")
    sw = c.inp("Seawater density", 8.55, "ppg")
    rq = c.out("Required mud weight after disconnect",
               f"({mw}*{tvd}-{sw}*{wd})/({tvd}-{wd}-{ag})", "ppg", fmt="0.00")
    c.out("Riser margin", f"{rq}-{mw}", "ppg", fmt="0.00")

    sb.section("Gas Behavior")

    c = sb.calc("Gas Migration Rate from Casing Pressure Rise",
                eq="V_mig [ft/hr] = (dP/dt) / (0.052 x MW)",
                note="Shut-in well: migrating gas carries its pressure up; casing pressure rise rate converts to "
                     "migration speed through the mud gradient.")
    dpdt = c.inp("Casing pressure rise rate", 150, "psi/hr", fmt="#,##0", si=("kPa/hr", 6.894757))
    mw = c.inp("Mud weight (MW)", 12.5, "ppg")
    c.out("Gas migration rate", f"{dpdt}/(0.052*{mw})", "ft/hr", fmt="#,##0")

    c = sb.calc("Gas Expansion (Boyle's Law)",
                eq="P1 x V1 = P2 x V2   ->   V2 = P1 x V1 / P2",
                note="Isothermal ideal gas (Z and temperature ignored). Use absolute pressures for accuracy; "
                     "at wellbore pressures the gauge/absolute difference is usually negligible.")
    p1 = c.inp("Initial pressure (P1)", 5200, "psi", fmt="#,##0")
    v1 = c.inp("Initial gas volume (V1)", 10, "bbl", fmt="0.0")
    p2 = c.inp("Final pressure (P2)", 500, "psi", fmt="#,##0")
    c.out("Expanded gas volume (V2)", f"{p1}*{v1}/{p2}", "bbl", fmt="0.0")

    c = sb.calc("Gas-Cut Mud: Bottomhole Pressure Reduction",
                eq="dBHP [psi] ~ 0.052 x TVD x (MW - MW_cut) / 2",
                note="Annular-average approximation: gas expands mostly near surface, so the density cut measured at the "
                     "flowline acts over roughly half the column on average. Actual reduction is usually even smaller - "
                     "treat as an upper-bound screening number, not a reason to raise mud weight by itself.")
    mw = c.inp("Uncut mud weight (MW)", 12.5, "ppg")
    mwc = c.inp("Gas-cut mud weight at flowline", 10.0, "ppg")
    tvd = c.inp("Well TVD", 10000, "ft", fmt="#,##0")
    full = c.out("Reduction if cut acted over full column", f"0.052*{tvd}*({mw}-{mwc})", "psi", fmt="#,##0",
                 note="Unrealistic worst case shown for comparison.")
    c.out("Approx. BHP reduction (annular average)", f"{full}/2", "psi", fmt="#,##0")

    sb.section("Kill Calculations")

    c = sb.calc("Kill Mud Weight, ICP, FCP & Barite",
                eq="KMW = MW + SIDPP/(0.052 x TVD);  ICP = SCRP + SIDPP;  FCP = SCRP x KMW/MW;  "
                   "Sacks = 1470 x (KMW - MW)/(35 - KMW) x V/100",
                note="Driller's/Wait-and-Weight standard kill-sheet values. Barite: SG 4.20 (35 ppg), 100-lb sacks.")
    mw = c.inp("Current mud weight (MW)", 12.5, "ppg")
    sidpp = c.inp("Shut-in drill pipe pressure (SIDPP)", 350, "psi", fmt="#,##0")
    tvd = c.inp("Well TVD", 10000, "ft", fmt="#,##0")
    scrp = c.inp("Slow circulating rate pressure (SCRP)", 800, "psi", fmt="#,##0")
    vsys = c.inp("Active mud system volume", 1000, "bbl", fmt="#,##0")
    kmw_x = c.out("Kill mud weight (exact)", f"{mw}+{sidpp}/(0.052*{tvd})", "ppg", fmt="0.000")
    kmw = c.out("Kill mud weight (KMW, rounded up)", f"ROUNDUP(ROUND({kmw_x}*10,6),0)/10", "ppg", fmt="0.0",
                note="Rounding rule: kill weight fluid density rounds UP to the nearest 0.1 ppg.")
    c.out("Initial circulating pressure (ICP)", f"{scrp}+{sidpp}", "psi", fmt="#,##0")
    c.out("Final circulating pressure (FCP)", f"{scrp}*{kmw}/{mw}", "psi", fmt="#,##0")
    c.out("Barite required", f"1470*({kmw}-{mw})/(35-{kmw})*{vsys}/100", None, fmt="#,##0",
          note="100-lb sacks to weight the whole active system to KMW.")

    sb.section("Volumetric Method")

    c = sb.calc("Volumetric Method: Bleed Increments",
                eq="P per bbl [psi/bbl] = 0.052 x MW / C_ann;   bbl per step = P_working / (psi/bbl)",
                note="Gas migrating with pipe off bottom or no circulation possible: hold BHP constant by bleeding mud "
                     "in measured steps as casing pressure rises by the chosen working pressure.")
    mw = c.inp("Mud weight (MW)", 12.5, "ppg")
    cann = c.inp("Annular capacity at gas", 0.0459, "bbl/ft", fmt="0.00000")
    pw = c.inp("Working pressure per step", 100, "psi", fmt="#,##0",
               note="Also allow a safety margin (typically 50-100 psi) before the first bleed.")
    ppb = c.out("Hydrostatic pressure per barrel", f"0.052*{mw}/{cann}", "psi/bbl", fmt="0.0")
    c.out("Mud to bleed per step", f"{pw}/{ppb}", "bbl", fmt="0.00",
          note="Bleed mud only (never gas) at constant casing pressure, then wait; repeat as gas migrates.")

    c = sb.calc("Lubricate & Bleed",
                eq="P gained per bbl lubricated = 0.052 x MW_lube / C_csg;   P to bleed per cycle = bbl x psi/bbl",
                note="Gas at surface under the BOP: pump (lubricate) mud in, allow it to fall through the gas, "
                     "then bleed gas pressure equal to the hydrostatic added. Capacity here is usually casing "
                     "(no pipe) below the BOP.")
    mwl = c.inp("Lubricating mud weight", 13.2, "ppg")
    ccap = c.inp("Casing capacity at gas", 0.0732, "bbl/ft", fmt="0.00000")
    vl = c.inp("Mud lubricated per cycle", 5, "bbl", fmt="0.0")
    ppb = c.out("Hydrostatic gained per barrel", f"0.052*{mwl}/{ccap}", "psi/bbl", fmt="0.0")
    c.out("Pressure to bleed per cycle", f"{vl}*{ppb}", "psi", fmt="0.0",
          note="Bleed dry gas only; stop if mud reaches the choke.")
