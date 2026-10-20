"""Completions: productivity index, Darcy radial inflow, Vogel IPR, gas deliverability, skin."""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "Inflow & Productivity", "completions",
        "Inflow & Productivity",
        "Productivity index, Darcy radial inflow, Vogel IPR, gas backpressure deliverability, skin effects",
        description="PI, Darcy radial rate, Vogel IPR and Qmax, gas C-and-n deliverability, AOF, skin pressure drop",
    )

    sb.section("Productivity Index")

    c = sb.calc("Productivity Index from a Test Point",
                eq="J [STB/d/psi] = Q / (P_r - P_wf)",
                note="Straight-line PI; valid for single-phase liquid inflow (P_wf above bubble point). Use Vogel below the bubble point.")
    qt = c.inp("Test rate (Q)", 500, "STB/d", si=("m3/d", 0.1589873), fmt="#,##0")
    pr = c.inp("Average reservoir pressure (P_r)", 3000, "psi", fmt="#,##0")
    pwf = c.inp("Flowing bottomhole pressure (P_wf)", 2500, "psi", fmt="#,##0")
    j = c.out("Productivity index (J)", f"{qt}/({pr}-{pwf})", None, fmt="0.000",
              note="STB/d per psi")

    c = sb.calc("Rate at a Target Drawdown",
                eq="Q = J x dP_drawdown",
                note="Uses J from the test above.")
    dd = c.inp("Target drawdown (dP)", 800, "psi", fmt="#,##0")
    c.out("Expected rate", f"{j}*{dd}", "STB/d", si=("m3/d", 0.1589873), fmt="#,##0")

    sb.section("Darcy Radial Inflow (Oil)")

    c = sb.calc("Steady-State Radial Oil Rate",
                eq="Q = k x h x (P_r - P_wf) / (141.2 x B x mu x (LN(re/rw) + s))",
                note="Darcy radial steady-state, field units: k mD, h ft, P psi, B RB/STB, mu cP. Valid above the bubble point (single-phase oil).")
    k = c.inp("Permeability (k)", 100, "mD", fmt="#,##0.0")
    h = c.inp("Net pay thickness (h)", 50, "ft", fmt="#,##0")
    pr = c.inp("Reservoir pressure (P_r)", 3000, "psi", fmt="#,##0")
    pwf = c.inp("Flowing pressure (P_wf)", 2500, "psi", fmt="#,##0")
    b = c.inp("Formation volume factor (B)", 1.20, None, fmt="0.000", note="RB/STB")
    mu = c.inp("Oil viscosity (mu)", 1.5, None, si=("mPa-s", 1.0), fmt="0.00", note="cP")
    re = c.inp("Drainage radius (re)", 1500, "ft", fmt="#,##0")
    rw = c.inp("Wellbore radius (rw)", 0.354, "ft", fmt="0.000")
    s = c.inp("Skin factor (s)", 5.0, None, fmt="0.0", note="Dimensionless; positive = damage.")
    qd = c.out("Oil rate (Q)", f"{k}*{h}*({pr}-{pwf})/(141.2*{b}*{mu}*(LN({re}/{rw})+{s}))",
               "STB/d", si=("m3/d", 0.1589873), fmt="#,##0")

    c = sb.calc("Skin Pressure Drop & Flow Efficiency",
                eq="dP_skin = 141.2 x Q x B x mu x s / (k x h);   FE = (P_r - P_wf - dP_skin) / (P_r - P_wf)",
                note="Uses the Darcy inputs and rate above. FE = 1 for zero skin; FE < 1 means damage is consuming drawdown.")
    dps = c.out("Skin pressure drop (dP_skin)", f"141.2*{qd}*{b}*{mu}*{s}/({k}*{h})",
                "psi", fmt="#,##0")
    c.out("Flow efficiency (FE)", f"({pr}-{pwf}-{dps})/({pr}-{pwf})", None, fmt="0.000",
          note="Dimensionless.")

    sb.section("Vogel IPR (Solution-Gas Drive)")

    c = sb.calc("Vogel Qmax from a Test Point",
                eq="Qmax = Q_test / (1 - 0.2 x (P_wf/P_r) - 0.8 x (P_wf/P_r)^2)",
                note="Vogel two-phase IPR for solution-gas drive reservoirs below the bubble point. Above the bubble point use straight-line PI down to Pb, Vogel below (combined IPR).")
    prv = c.inp("Average reservoir pressure (P_r)", 3000, "psi", fmt="#,##0")
    qtv = c.inp("Test rate (Q_test)", 400, "STB/d", si=("m3/d", 0.1589873), fmt="#,##0")
    pwft = c.inp("Test flowing pressure (P_wf_test)", 2000, "psi", fmt="#,##0")
    qmax = c.out("Vogel Qmax (AOF)",
                 f"{qtv}/(1-0.2*({pwft}/{prv})-0.8*({pwft}/{prv})^2)",
                 "STB/d", si=("m3/d", 0.1589873), fmt="#,##0")

    c = sb.calc("Vogel Rate at a Given P_wf",
                eq="Q = Qmax x (1 - 0.2 x (P_wf/P_r) - 0.8 x (P_wf/P_r)^2)",
                note="Uses Qmax and P_r from above.")
    pwfd = c.inp("Design flowing pressure (P_wf)", 1000, "psi", fmt="#,##0")
    c.out("Expected rate (Q)",
          f"{qmax}*(1-0.2*({pwfd}/{prv})-0.8*({pwfd}/{prv})^2)",
          "STB/d", si=("m3/d", 0.1589873), fmt="#,##0")

    sb.section("Gas Well Deliverability")

    c = sb.calc("Backpressure (C and n) from a Test Point",
                eq="C = Q_test / (P_r^2 - P_wf^2)^n;   Q = C x (P_r^2 - P_wf^2)^n;   AOF at P_wf = 0",
                note="Simplified Rawlins-Schellhardt backpressure equation using pressure-squared - adequate below approx 2500 psi; use pseudo-pressure at higher pressure. n from a multirate test: 1.0 = laminar, 0.5 = fully turbulent.")
    prg = c.inp("Reservoir pressure (P_r)", 3000, "psi", fmt="#,##0", note="Use absolute pressure (psia).")
    qtg = c.inp("Test rate (Q_test)", 4000, "Mscf/d", si=("std m3/d", 28.31685), fmt="#,##0")
    pwfg = c.inp("Test flowing pressure (P_wf_test)", 2500, "psi", fmt="#,##0")
    ng = c.inp("Deliverability exponent (n)", 0.80, None, fmt="0.00", note="0.5 - 1.0")
    cg = c.out("Performance coefficient (C)", f"{qtg}/({prg}^2-{pwfg}^2)^{ng}", None,
               fmt="0.000000", note="Mscf/d per (psi2)^n")
    pwfd2 = c.inp("Design flowing pressure (P_wf)", 1500, "psi", fmt="#,##0")
    c.out("Rate at design P_wf", f"{cg}*({prg}^2-{pwfd2}^2)^{ng}", "Mscf/d",
          si=("std m3/d", 28.31685), fmt="#,##0")
    c.out("Absolute open flow (AOF)", f"{cg}*({prg}^2)^{ng}", "Mscf/d",
          si=("std m3/d", 28.31685), fmt="#,##0",
          note="Theoretical rate at atmospheric flowing pressure - ranking number only.")

    c = sb.calc("Water Coning Screening Note")
    c.txt("Critical coning rate is highly geometry- and anisotropy-dependent.",
          "Use a dedicated correlation (Meyer-Garder, Chaperon) or simulation before setting standoff and rate limits near an aquifer - not reduced to a single sheet formula here.")
