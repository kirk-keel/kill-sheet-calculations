"""Completions: tubing/packer geometry, Lubinski force-length effects, stretch, buckling."""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "Tubing & Packer Forces", "completions",
        "Tubing & Packer Forces",
        "Cross-sections, capacities, tubing stretch, and Lubinski piston/buckling/ballooning/temperature effects",
        description="Tubing areas and volumes, stretch, packer setting force, Lubinski force-length effects, buckling",
    )

    sb.section("Geometry, Materials & Volumes")

    c = sb.calc("Cross-Section Areas & Section Properties",
                eq="A = pi/4 x D^2;   I = pi/64 x (OD^4 - ID^4);   r = (ID_csg - OD_tbg)/2",
                note="These areas, properties and material constants are referenced by the force calculations below. Steel defaults: E = 30e6 psi, nu = 0.30.")
    od = c.inp("Tubing OD", 2.875, "in", fmt="0.000")
    idt = c.inp("Tubing ID", 2.441, "in", fmt="0.000")
    pb = c.inp("Packer seal bore diameter", 3.250, "in", fmt="0.000")
    idc = c.inp("Casing ID", 6.276, "in", fmt="0.000")
    e_mod = c.inp("Young's modulus (E)", 30000000, "psi", si=("GPa", 6.894757e-06), fmt="#,##0")
    nu = c.inp("Poisson's ratio (nu)", 0.30, None, fmt="0.00", note="Dimensionless; 0.30 for steel.")
    ao = c.out("Tubing OD area (Ao)", f"PI()/4*{od}^2", "in2", fmt="0.000")
    ai = c.out("Tubing ID area (Ai)", f"PI()/4*{idt}^2", "in2", fmt="0.000")
    as_ = c.out("Steel cross-section (As = Ao - Ai)", f"{ao}-{ai}", "in2", fmt="0.000")
    ap = c.out("Packer bore area (Ap)", f"PI()/4*{pb}^2", "in2", fmt="0.000")
    i_mom = c.out("Moment of inertia (I)", f"PI()/64*({od}^4-{idt}^4)", None, fmt="0.000",
                  note="in4")
    rcl = c.out("Radial clearance tubing-to-casing (r)", f"({idc}-{od})/2", "in", fmt="0.000")

    c = sb.calc("Tubing Capacity & Displacement",
                eq="Cap [bbl/ft] = ID^2 / 1029.4;   Disp_metal = (OD^2 - ID^2) / 1029.4;   Disp_closed = OD^2 / 1029.4",
                note="Uses tubing OD/ID from the geometry block above.")
    ltb = c.inp("Tubing length", 8800, "ft", fmt="#,##0")
    cap = c.out("Capacity", f"{idt}^2/1029.4", "bbl/ft", fmt="0.00000")
    dm = c.out("Metal displacement (open-ended)", f"({od}^2-{idt}^2)/1029.4", "bbl/ft", fmt="0.00000")
    dc = c.out("Closed-end displacement", f"{od}^2/1029.4", "bbl/ft", fmt="0.00000")
    c.out("String internal volume", f"{cap}*{ltb}", "bbl", fmt="#,##0.0")
    c.out("String metal displacement", f"{dm}*{ltb}", "bbl", fmt="#,##0.0")
    c.out("String closed-end displacement", f"{dc}*{ltb}", "bbl", fmt="#,##0.0")

    c = sb.calc("Annular Volume Between Tubing and Casing",
                eq="V_ann [bbl/ft] = (ID_csg^2 - OD_tbg^2) / 1029.4",
                note="Uses casing ID and tubing OD from the geometry block above.")
    lann = c.inp("Annulus length", 8800, "ft", fmt="#,##0")
    va = c.out("Annular capacity", f"({idc}^2-{od}^2)/1029.4", "bbl/ft", fmt="0.00000")
    c.out("Annular volume", f"{va}*{lann}", "bbl", fmt="#,##0.0")

    sb.section("Stretch & Setting Forces")

    c = sb.calc("Free Tubing Stretch Under Pull",
                eq="e [in] = P [lbf] x L [ft] x 12 / (As [in2] x E [psi])",
                note="Hooke's law for free (unanchored) tubing. Uses As and E from the geometry block above.")
    p = c.inp("Pull force (P)", 20000, "lbf", fmt="#,##0")
    lst = c.inp("Free length (L)", 8800, "ft", fmt="#,##0")
    c.out("Stretch (e)", f"{p}*{lst}*12/({as_}*{e_mod})", "in", fmt="0.00")

    c = sb.calc("Packer Setting Force from Surface Slack-Off",
                eq="F_pkr = W_slackoff x (1 - friction/100)",
                note="Simplified: a percentage of surface slack-off weight is lost to drag before reaching the packer. In deviated wells use a torque-and-drag model - losses can be far higher than a flat percentage.")
    wso = c.inp("Surface slack-off weight", 20000, "lbf", fmt="#,##0")
    fr = c.inp("Friction / drag loss", 10, None, fmt="0.0", note="Percent of slack-off lost to drag.")
    c.out("Force delivered to packer", f"{wso}*(1-{fr}/100)", "lbf", fmt="#,##0")

    sb.section("Packer Force-Length Effects (Lubinski)")

    c = sb.calc("Load Case: Pressure & Temperature Changes",
                eq="BF = 1 - rho_ann/65.4;   w_b [lb/in] = w [lb/ft] x BF / 12",
                note="Changes (final minus initial) from the landed condition, for a tubing string free to move in the packer bore. dP at packer drives piston and buckling; average dP over the string drives ballooning. Negative dT = cooling (e.g. injection/stimulation).")
    lp = c.inp("Tubing length to packer (L)", 8800, "ft", fmt="#,##0")
    w = c.inp("Tubing weight in air (w)", 6.5, "lb/ft", fmt="0.00")
    rhoa = c.inp("Fluid density for buoyancy", 9.2, "ppg")
    dpi = c.inp("Tubing pressure change at packer (dPi)", 2000, "psi", fmt="#,##0")
    dpo = c.inp("Annulus pressure change at packer (dPo)", 0, "psi", fmt="#,##0")
    dpia = c.inp("Average tubing pressure change (dPi_avg)", 1000, "psi", fmt="#,##0")
    dpoa = c.inp("Average annulus pressure change (dPo_avg)", 0, "psi", fmt="#,##0")
    dt = c.inp("Average temperature change (dT)", -40, "degF (delta)",
               si=("degC (delta)", 0.5555556), fmt="#,##0")
    bf = c.out("Buoyancy factor (BF)", f"1-{rhoa}/65.4", None, fmt="0.000")
    wb = c.out("Buoyed weight (w_b)", f"{w}*{bf}/12", None, fmt="0.0000",
               note="lb/in, used in buckling terms.")

    c = sb.calc("1. Piston Effect",
                eq="F1 = (Ap - Ai) x dPi - (Ap - Ao) x dPo;   dL1 [in] = -F1 x 12 x L / (E x As)",
                note="Force on the tubing end at the packer bore. Positive F1 shortens the tubing (negative dL1). Uses areas from the geometry block.")
    f1 = c.out("Piston force (F1)", f"({ap}-{ai})*{dpi}-({ap}-{ao})*{dpo}", "lbf", fmt="#,##0")
    dl1 = c.out("Piston length change (dL1)", f"-{f1}*12*{lp}/({e_mod}*{as_})", "in", fmt="0.00",
                note="Negative = shortening.")

    c = sb.calc("2. Helical Buckling Effect",
                eq="dL2 [in] = -r^2 x Ap^2 x (dPi - dPo)^2 / (8 x E x I x w_b)",
                note="Lubinski helical buckling shortening; applies only when dPi > dPo and the neutral point is within the string. w_b is buoyed weight in lb/in - fluid-gradient corrections to the effective weight are neglected (approximate).")
    dl2 = c.out("Buckling length change (dL2)",
                f"IF({dpi}>{dpo},-{rcl}^2*{ap}^2*({dpi}-{dpo})^2/(8*{e_mod}*{i_mom}*{wb}),0)",
                "in", fmt="0.00", note="Negative = shortening; 0 if dPi <= dPo.")

    c = sb.calc("3. Ballooning Effect",
                eq="dL3 [in] = -(2 x nu x 12 x L / E) x (dPi_avg x Ai - dPo_avg x Ao) / (Ao - Ai)",
                note="Classic Lubinski ballooning/reverse-ballooning form with average pressure changes. Internal pressure increase swells the tubing and shortens it.")
    dl3 = c.out("Ballooning length change (dL3)",
                f"-(2*{nu}*12*{lp}/{e_mod})*({dpia}*{ai}-{dpoa}*{ao})/({ao}-{ai})",
                "in", fmt="0.00", note="Negative = shortening.")

    c = sb.calc("4. Temperature Effect",
                eq="dL4 [in] = 12 x L [ft] x beta x dT [degF]",
                note="beta = coefficient of thermal expansion for steel, 6.9e-6 per degF.")
    beta = c.inp("Thermal expansion coeff (beta)", 0.0000069, None, fmt="0.0000000",
                 note="per degF (6.9e-6 for steel)")
    dl4 = c.out("Temperature length change (dL4)", f"12*{lp}*{beta}*{dt}", "in", fmt="0.00",
                note="Negative = shortening (cooling).")

    c = sb.calc("Force-Length Summary & Compensating Force",
                eq="dL_total = dL1 + dL2 + dL3 + dL4;   F_comp = -dL_total x E x As / (12 x L)",
                note="Net motion at the seal assembly if free to move. F_comp is the slack-off (dL_total negative) or pick-up (positive) force to land so the seals stay in place - linear Hooke approximation, ignores buckling nonlinearity.")
    c.out("Piston (dL1)", f"{dl1}", "in", fmt="0.00")
    c.out("Buckling (dL2)", f"{dl2}", "in", fmt="0.00")
    c.out("Ballooning (dL3)", f"{dl3}", "in", fmt="0.00")
    c.out("Temperature (dL4)", f"{dl4}", "in", fmt="0.00")
    dlt = c.out("Total length change (dL_total)", f"{dl1}+{dl2}+{dl3}+{dl4}", "in", fmt="0.00",
                note="Negative = net shortening, seals move up.")
    c.out("Compensating force (F_comp)", f"-{dlt}*{e_mod}*{as_}/(12*{lp})", "lbf", fmt="#,##0",
          note="Positive = slack-off weight needed; negative = pick-up.")

    sb.section("Buckling Stability")

    c = sb.calc("Neutral Point & Helical Buckling Onset",
                eq="n [ft] = F / (w x BF);   F_hel = 5.55 x (E x I x w_b^2)^(1/3)",
                note="n = distance from the bottom to the neutral point for compressive force F. Buckled below the neutral point. F_hel is the vertical-well helical buckling onset load (Lubinski/Wu form) - approximate; deviation and clearance change it.")
    fc = c.inp("Compression at bottom of string (F)", 15000, "lbf", fmt="#,##0")
    n = c.out("Neutral point above bottom (n)", f"{fc}/({w}*{bf})", "ft", fmt="#,##0")
    c.out("Helical buckling onset force (F_hel)", f"5.55*({e_mod}*{i_mom}*{wb}^2)^(1/3)",
          "lbf", fmt="#,##0")
    c.out("Buckling status",
          f'IF({fc}<=0,"NO COMPRESSION - STRAIGHT",IF({fc}<5.55*({e_mod}*{i_mom}*{wb}^2)^(1/3),"SINUSOIDAL / ONSET REGION","HELICALLY BUCKLED"))',
          None, fmt="@", note="Text result, vertical-well approximation.")

    sb.section("Swab & Surge - Running Tubing / Packer")

    c = sb.calc("Surge & Swab Pressure (Burkhardt simplified, Bingham)",
                eq="closed: Ve = Vp x (0.45 + Dp^2/(Dc^2-Dp^2));  "
                   "open: Ve = Vp x (0.45 + (Dp^2-Di^2)/(Dc^2-Dp^2+Di^2));  "
                   "dP = L x PV x Ve/(60000x(Dc-Dp)^2) + L x YP/(200x(Dc-Dp))",
                note="Closed-ended applies with a plug, packer, or float in the string (worst case). 0.45 is "
                     "the Burkhardt clinging constant; laminar Bingham-plastic approximation.")
    dcs = c.inp("Casing ID (Dc)", 8.681, "in", fmt="0.000")
    dps = c.inp("Tubing OD (Dp)", 4.5, "in", fmt="0.000")
    dis = c.inp("Tubing ID (Di)", 3.958, "in", fmt="0.000")
    vps = c.inp("Running speed (Vp)", 90, "ft/min", fmt="#,##0",
                note="~ one 40-ft joint in 30 s.")
    pvs = c.inp("Fluid plastic viscosity (PV)", 15, "cP", si=("mPa-s", 1.0), fmt="#,##0")
    yps = c.inp("Fluid yield point (YP)", 12, None, fmt="#,##0",
                note="lb/100ft2 (no SI mirror; 1 lb/100ft2 = 0.4788 Pa)")
    lsw = c.inp("Open hole / casing length below string shoe (L)", 9000, "ft", fmt="#,##0")
    mwsw = c.inp("Fluid density (MW)", 9.0, "ppg")
    tvdsw = c.inp("TVD", 9000, "ft", fmt="#,##0")
    vec = c.out("Effective velocity, closed-ended (Ve)",
                f"{vps}*(0.45+{dps}^2/({dcs}^2-{dps}^2))", "ft/min", fmt="#,##0")
    veo = c.out("Effective velocity, open-ended (Ve)",
                f"{vps}*(0.45+({dps}^2-{dis}^2)/({dcs}^2-{dps}^2+{dis}^2))", "ft/min", fmt="#,##0")
    dpcl = c.out("Surge pressure, closed-ended",
                 f"{lsw}*{pvs}*{vec}/(60000*({dcs}-{dps})^2)+{lsw}*{yps}/(200*({dcs}-{dps}))",
                 "psi", fmt="#,##0")
    c.out("Surge pressure, open-ended",
          f"{lsw}*{pvs}*{veo}/(60000*({dcs}-{dps})^2)+{lsw}*{yps}/(200*({dcs}-{dps}))",
          "psi", fmt="#,##0")
    c.out("Surge EMW, closed-ended", f"{mwsw}+{dpcl}/(0.052*{tvdsw})", "ppg", fmt="0.00",
          note="Running in; keep below frac / loss-limit EMW.")
    c.out("Swab EMW, closed-ended", f"{mwsw}-{dpcl}/(0.052*{tvdsw})", "ppg", fmt="0.00",
          note="Pulling out; keep above pore / kick-margin EMW.")

    c = sb.calc("Max Running Speed vs Frac / Loss Margin",
                eq="dP_allow = (EMW_limit - MW) x 0.052 x TVD;  "
                   "Vmax = (dP_allow - L x YP/(200x(Dc-Dp))) x 60000 x (Dc-Dp)^2 / "
                   "(L x PV x (0.45 + Dp^2/(Dc^2-Dp^2)))",
                note="Closed-ended (worst case). 0 means the YP term alone exceeds the allowance - slow "
                     "further, open-end the string, or raise the loss limit.")
    emwl = c.inp("Frac or loss-limit EMW", 10.2, "ppg")
    mwm = c.inp("Fluid density (MW)", 9.0, "ppg")
    tvdm = c.inp("TVD", 9000, "ft", fmt="#,##0")
    dcm = c.inp("Casing ID (Dc)", 8.681, "in", fmt="0.000")
    dpm = c.inp("Tubing OD (Dp)", 4.5, "in", fmt="0.000")
    pvm = c.inp("Fluid plastic viscosity (PV)", 15, "cP", si=("mPa-s", 1.0), fmt="#,##0")
    ypm = c.inp("Fluid yield point (YP)", 12, None, fmt="#,##0",
                note="lb/100ft2")
    lmr = c.inp("Length below string shoe (L)", 9000, "ft", fmt="#,##0")
    dpalw = c.out("Allowable surge pressure", f"({emwl}-{mwm})*0.052*{tvdm}", "psi", fmt="#,##0")
    c.out("Max running speed, closed-ended",
          f"MAX(0,({dpalw}-{lmr}*{ypm}/(200*({dcm}-{dpm})))*60000*({dcm}-{dpm})^2/"
          f"({lmr}*{pvm}*(0.45+{dpm}^2/({dcm}^2-{dpm}^2))))",
          "ft/min", fmt="#,##0")
