"""Drilling: nozzle TFA, bit pressure drop, hydraulic horsepower, HSI, jet impact force."""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "Bit Hydraulics", "drilling",
        "Bit Hydraulics",
        "Total flow area, nozzle velocity, bit pressure drop, hydraulic horsepower, HSI and jet impact force",
        description="TFA, nozzle velocity, bit pressure drop, HHP, HSI, impact force, optimization targets",
    )

    sb.section("Nozzles & Flow Area")

    c = sb.calc("Total Flow Area (TFA)",
                eq="TFA [in2] = PI()/4 x sum( (d/32)^2 )   for each nozzle, d in 1/32 in",
                note="Three-nozzle bit shown; enter 0 for blanked nozzles and extend the sum for more nozzles.")
    n1 = c.inp("Nozzle 1 size", 13, None, fmt="#,##0", note="1/32 in.")
    n2 = c.inp("Nozzle 2 size", 13, None, fmt="#,##0", note="1/32 in.")
    n3 = c.inp("Nozzle 3 size", 14, None, fmt="#,##0", note="1/32 in.")
    tfa = c.out("Total flow area (TFA)", f"PI()/4*(({n1}/32)^2+({n2}/32)^2+({n3}/32)^2)", "in2", fmt="0.0000")

    c = sb.calc("Nozzle (Jet) Velocity",
                eq="Vn [ft/s] = 0.32086 x Q / TFA",
                note="Uses TFA computed above. Typical target 350-450 ft/s for adequate bottomhole cleaning.")
    q = c.inp("Flow rate (Q)", 450, "gpm", fmt="#,##0")
    c.out("Nozzle velocity (Vn)", f"0.32086*{q}/{tfa}", "ft/s", fmt="#,##0")

    sb.section("Bit Pressure Drop & Horsepower")

    c = sb.calc("Pressure Drop Across Bit",
                eq="dPb [psi] = Q^2 x MW / (12042 x TFA^2)",
                note="Nozzle discharge coefficient 0.95 built into the constant. Uses Q and TFA from above.")
    mw = c.inp("Mud weight (MW)", 12.5, "ppg")
    psurf = c.inp("Surface (standpipe) pressure", 3200, "psi", fmt="#,##0")
    dpb = c.out("Bit pressure drop (dPb)", f"{q}^2*{mw}/(12042*{tfa}^2)", "psi", fmt="#,##0")
    pct = c.out("Percent of surface pressure at bit", f"{dpb}/{psurf}*100", "%", fmt="0.0")

    c = sb.calc("Hydraulic Horsepower & HSI",
                eq="HHP = P x Q / 1714;   HSI = HHP_bit / (PI()/4 x D_bit^2)",
                note="HSI 2.5-5+ hp/in2 is a common target for effective PDC/roller-cone cleaning.")
    dbit = c.inp("Bit diameter", 8.5, "in", fmt="0.000")
    c.out("System hydraulic horsepower", f"{psurf}*{q}/1714", "hp", fmt="#,##0")
    hhpb = c.out("Bit hydraulic horsepower", f"{dpb}*{q}/1714", "hp", fmt="#,##0")
    c.out("Hydraulic horsepower per in2 (HSI)", f"{hhpb}/(PI()/4*{dbit}^2)", "hp/in2", fmt="0.00")

    sb.section("Jet Impact Force")

    c = sb.calc("Hydraulic Impact Force",
                eq="IF [lbf] = 0.01823 x Cd x Q x SQRT( MW x dPb )",
                note="Uses Q, MW and dPb from above. Impact per unit bit area is a useful comparison between bit runs.")
    cd = c.inp("Nozzle discharge coefficient (Cd)", 0.95, None, fmt="0.00")
    imp = c.out("Jet impact force (IF)", f"0.01823*{cd}*{q}*SQRT({mw}*{dpb})", "lbf", fmt="#,##0")
    c.out("Impact force per in2 of bit area", f"{imp}/(PI()/4*{dbit}^2)", None, fmt="0.00",
          note="lbf/in2 of bit face.")

    sb.section("Optimization Guidance")

    c = sb.calc("Rules of Thumb for Bit Hydraulics Optimization",
                note="Compare the 'percent of surface pressure at bit' output above against these targets.")
    c.txt("Maximum bit hydraulic horsepower:",
          "achieved when dPb is about 65% of surface pressure (friction exponent u ~ 1.86).")
    c.txt("Maximum jet impact force:",
          "achieved when dPb is about 48% of surface pressure.")
    c.txt("Practical window:",
          "most operators size nozzles for 50-65% of surface pressure at the bit, subject to minimum "
          "annular velocity for hole cleaning and maximum pump pressure/liner rating.")
    c.txt("Nozzle selection:",
          "adjust nozzle sizes (TFA) rather than flow rate first; flow rate is usually set by hole "
          "cleaning and motor/MWD requirements.")
