"""Drilling: annular/pipe velocity, cuttings transport, rheology, annular losses, ECD, surge & swab."""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "Hydraulics", "drilling",
        "Drilling Hydraulics",
        "Annular velocity, cuttings transport, Bingham and power-law rheology, annular losses, ECD, surge and swab",
        description="Velocities, slip velocity, PV/YP, n and K, annular pressure loss, ECD, surge/swab",
    )

    sb.section("Velocities & Cuttings Transport")

    c = sb.calc("Annular Velocity",
                eq="AV [ft/min] = 24.5 x Q / (Dh^2 - Dp^2)",
                note="Q in gpm, diameters in inches. Rule of thumb: keep AV above ~100-120 ft/min in vertical wells.")
    q = c.inp("Flow rate (Q)", 600, "gpm", fmt="#,##0")
    dh = c.inp("Hole diameter (Dh)", 8.5, "in", fmt="0.000")
    dp = c.inp("Pipe outside diameter (Dp)", 5.0, "in", fmt="0.000")
    c.out("Annular velocity", f"24.5*{q}/({dh}^2-{dp}^2)", "ft/min", fmt="#,##0.0")

    c = sb.calc("Pipe (Internal) Velocity",
                eq="V_pipe [ft/min] = 24.5 x Q / ID^2")
    q = c.inp("Flow rate (Q)", 600, "gpm", fmt="#,##0")
    idp = c.inp("Pipe inside diameter (ID)", 4.276, "in", fmt="0.000")
    c.out("Pipe velocity", f"24.5*{q}/{idp}^2", "ft/min", fmt="#,##0.0")

    c = sb.calc("Cuttings Slip Velocity & Transport Ratio",
                eq="V_slip [ft/min] = 92.6 x SQRT( Dc x (MW_c - MW) / MW );   TR = (AV - V_slip) / AV x 100",
                note="Turbulent (Newtonian) slip form, drag coefficient ~1.5; cuttings SG 2.6 = 21.7 ppg. "
                     "Ignores mud rheology support, so it is conservative in viscous muds. TR > 50% is generally "
                     "adequate hole cleaning in near-vertical hole.")
    dc = c.inp("Cutting diameter (Dc)", 0.25, "in", fmt="0.000")
    mwc = c.inp("Cuttings density", 21.7, "ppg", note="SG 2.6 shale/sand.")
    mw = c.inp("Mud weight (MW)", 12.5, "ppg")
    q = c.inp("Flow rate (Q)", 600, "gpm", fmt="#,##0")
    dh = c.inp("Hole diameter (Dh)", 8.5, "in", fmt="0.000")
    dp = c.inp("Pipe outside diameter (Dp)", 5.0, "in", fmt="0.000")
    av = c.out("Annular velocity", f"24.5*{q}/({dh}^2-{dp}^2)", "ft/min", fmt="#,##0.0")
    vs = c.out("Cuttings slip velocity", f"92.6*SQRT({dc}*({mwc}-{mw})/{mw})", "ft/min", fmt="#,##0.0")
    c.out("Net cuttings rise velocity", f"{av}-{vs}", "ft/min", fmt="#,##0.0")
    c.out("Transport ratio", f"({av}-{vs})/{av}*100", "%", fmt="0.0")

    sb.section("Rheology from Viscometer Readings")

    c = sb.calc("Bingham Plastic: PV & YP",
                eq="PV [cP] = theta600 - theta300;   YP [lb/100ft2] = theta300 - PV",
                note="Standard 600/300 rpm Fann dial readings.")
    t600 = c.inp("Dial reading at 600 rpm (theta600)", 65, None, fmt="0.0", note="Fann dial degrees.")
    t300 = c.inp("Dial reading at 300 rpm (theta300)", 40, None, fmt="0.0", note="Fann dial degrees.")
    pv = c.out("Plastic viscosity (PV)", f"{t600}-{t300}", None, fmt="0.0", note="cP.")
    c.out("Yield point (YP)", f"{t300}-{pv}", None, fmt="0.0", note="lb/100 ft2.")

    c = sb.calc("Power Law: n & K",
                eq="n = 3.32 x LOG(theta600 / theta300);   K = 510 x theta300 / 511^n",
                note="K in eq. centipoise (dyne-s^n/100 cm2). LOG is base 10.")
    t600 = c.inp("Dial reading at 600 rpm (theta600)", 65, None, fmt="0.0")
    t300 = c.inp("Dial reading at 300 rpm (theta300)", 40, None, fmt="0.0")
    n = c.out("Flow behavior index (n)", f"3.32*LOG({t600}/{t300})", None, fmt="0.000")
    c.out("Consistency index (K)", f"510*{t300}/511^{n}", None, fmt="0.0", note="eq. cP.")

    sb.section("Annular Pressure Loss & ECD")

    c = sb.calc("Annular Pressure Loss & ECD (Bingham, Laminar)",
                eq="APL [psi] = L x PV x AV / (60000 x (Dh - Dp)^2) + L x YP / (200 x (Dh - Dp));   "
                   "ECD = MW + APL / (0.052 x TVD)",
                note="Simple field form, laminar annular flow, uniform geometry. Sum section by section for tapered "
                     "strings; underestimates in turbulent flow.")
    l = c.inp("Annulus length (L)", 10000, "ft", fmt="#,##0")
    pv = c.inp("Plastic viscosity (PV)", 25, None, fmt="0.0", note="cP.")
    yp = c.inp("Yield point (YP)", 15, None, fmt="0.0", note="lb/100 ft2.")
    q = c.inp("Flow rate (Q)", 600, "gpm", fmt="#,##0")
    dh = c.inp("Hole diameter (Dh)", 8.5, "in", fmt="0.000")
    dp = c.inp("Pipe outside diameter (Dp)", 5.0, "in", fmt="0.000")
    mw = c.inp("Mud weight (MW)", 12.5, "ppg")
    tvd = c.inp("True vertical depth (TVD)", 10000, "ft", fmt="#,##0")
    av = c.out("Annular velocity", f"24.5*{q}/({dh}^2-{dp}^2)", "ft/min", fmt="#,##0.0")
    apl = c.out("Annular pressure loss (APL)",
                f"{l}*{pv}*{av}/(60000*({dh}-{dp})^2)+{l}*{yp}/(200*({dh}-{dp}))", "psi", fmt="#,##0")
    c.out("Equivalent circulating density (ECD)", f"{mw}+{apl}/(0.052*{tvd})", "ppg")

    sb.section("Surge & Swab")

    c = sb.calc("Surge & Swab Pressure (Burkhardt-Style, Simplified)",
                eq="Ve = Vp x (0.45 + Dp^2/(Dh^2 - Dp^2));   "
                   "Ps [psi] = L x PV x Ve / (60000 x (Dh - Dp)^2) + L x YP / (200 x (Dh - Dp));   "
                   "EMW = MW +/- Ps / (0.052 x TVD)",
                note="Clinging constant 0.45; closed-end (or float-equipped) pipe, laminar flow. Vp is the average "
                     "pipe running speed - peak speed can be 1.5-2x average, so apply to the fastest stand. "
                     "Surge adds to BHP (running in), swab subtracts (pulling out).")
    vp = c.inp("Pipe running speed (Vp)", 90, "ft/min", fmt="#,##0.0",
               note="Stand length / seconds per stand x 60.")
    dh = c.inp("Hole diameter (Dh)", 8.5, "in", fmt="0.000")
    dp = c.inp("Pipe outside diameter (Dp)", 5.0, "in", fmt="0.000")
    l = c.inp("String length in hole (L)", 10000, "ft", fmt="#,##0")
    pv = c.inp("Plastic viscosity (PV)", 25, None, fmt="0.0", note="cP.")
    yp = c.inp("Yield point (YP)", 15, None, fmt="0.0", note="lb/100 ft2.")
    mw = c.inp("Mud weight (MW)", 12.5, "ppg")
    tvd = c.inp("True vertical depth (TVD)", 10000, "ft", fmt="#,##0")
    ve = c.out("Effective annular velocity (Ve)", f"{vp}*(0.45+{dp}^2/({dh}^2-{dp}^2))", "ft/min", fmt="#,##0.0")
    ps = c.out("Surge / swab pressure (Ps)",
               f"{l}*{pv}*{ve}/(60000*({dh}-{dp})^2)+{l}*{yp}/(200*({dh}-{dp}))", "psi", fmt="#,##0")
    c.out("Equivalent MW while surging", f"{mw}+{ps}/(0.052*{tvd})", "ppg",
          note="Keep below fracture gradient EMW at the shoe.")
    c.out("Equivalent MW while swabbing", f"{mw}-{ps}/(0.052*{tvd})", "ppg",
          note="Keep above pore pressure EMW - otherwise slow the trip.")
