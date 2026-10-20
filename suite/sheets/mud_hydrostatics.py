"""Drilling: mud density, gradients, hydrostatic pressure, ECD, weight-up."""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "Mud & Hydrostatics", "drilling",
        "Mud Density & Hydrostatic Pressure",
        "Gradients, hydrostatic pressure, equivalent mud weight, ECD, weight-up and dilution",
        description="Pressure gradients, hydrostatic pressure, EMW, ECD, barite weight-up, dilution",
    )

    sb.section("Gradients & Hydrostatic Pressure")

    c = sb.calc("Pressure Gradient from Mud Weight",
                eq="Grad [psi/ft] = 0.052 x MW [ppg]")
    mw = c.inp("Mud weight (MW)", 12.5, "ppg")
    c.out("Pressure gradient", f"0.052*{mw}", "psi/ft", fmt="0.0000")

    c = sb.calc("Hydrostatic Pressure",
                eq="P_hyd [psi] = 0.052 x MW [ppg] x TVD [ft]",
                note="Always use true vertical depth, never measured depth.")
    mw = c.inp("Mud weight (MW)", 12.5, "ppg")
    tvd = c.inp("True vertical depth (TVD)", 10000, "ft", fmt="#,##0")
    c.out("Hydrostatic pressure (P_hyd)", f"0.052*{mw}*{tvd}", "psi", fmt="#,##0")

    c = sb.calc("Mud Weight from Pressure Gradient",
                eq="MW [ppg] = Grad [psi/ft] / 0.052")
    g = c.inp("Pressure gradient", 0.65, "psi/ft", fmt="0.0000")
    c.out("Equivalent mud weight", f"{g}/0.052", "ppg")

    c = sb.calc("Equivalent Mud Weight (EMW) at Depth",
                eq="EMW [ppg] = P [psi] / (0.052 x TVD [ft])")
    p = c.inp("Pressure at depth (P)", 6500, "psi", fmt="#,##0")
    tvd = c.inp("True vertical depth (TVD)", 10000, "ft", fmt="#,##0")
    c.out("Equivalent mud weight (EMW)", f"{p}/(0.052*{tvd})", "ppg")

    c = sb.calc("Hydrostatic Pressure of a Column of Multiple Fluids",
                eq="P_hyd = 0.052 x [ MW1 x L1_tvd + MW2 x L2_tvd ]",
                note="Extend by summing 0.052 x MW x TVD-length for each fluid in the column.")
    m1 = c.inp("Fluid 1 density", 8.6, "ppg")
    l1 = c.inp("Fluid 1 vertical length", 4000, "ft", fmt="#,##0")
    m2 = c.inp("Fluid 2 density", 12.5, "ppg")
    l2 = c.inp("Fluid 2 vertical length", 6000, "ft", fmt="#,##0")
    c.out("Total hydrostatic pressure", f"0.052*({m1}*{l1}+{m2}*{l2})", "psi", fmt="#,##0")

    sb.section("Density Conversions")

    c = sb.calc("Specific Gravity <-> Mud Weight",
                eq="MW [ppg] = SG x 8.345;   SG = MW / 8.345")
    sg = c.inp("Specific gravity (SG)", 1.20, None, fmt="0.000")
    c.out("Mud weight", f"{sg}*8.345", "ppg")
    mw = c.inp("Mud weight (MW)", 12.5, "ppg")
    c.out("Specific gravity", f"{mw}/8.345", None, fmt="0.000")

    c = sb.calc("Mud Weight <-> lb/ft3",
                eq="MW [lb/ft3] = MW [ppg] x 7.48")
    mw = c.inp("Mud weight", 12.5, "ppg")
    c.out("Density", f"{mw}*7.48", "lb/ft3", si=("kg/m3", 16.01846))

    sb.section("ECD & Annular Friction")

    c = sb.calc("Equivalent Circulating Density (ECD)",
                eq="ECD [ppg] = MW + APL / (0.052 x TVD)",
                note="APL = annular pressure loss while circulating.")
    mw = c.inp("Mud weight (MW)", 12.5, "ppg")
    apl = c.inp("Annular pressure loss (APL)", 200, "psi", fmt="#,##0")
    tvd = c.inp("True vertical depth (TVD)", 10000, "ft", fmt="#,##0")
    c.out("Equivalent circulating density", f"{mw}+{apl}/(0.052*{tvd})", "ppg")

    c = sb.calc("Bottomhole Pressure While Circulating",
                eq="BHP = P_hyd + APL = 0.052 x ECD x TVD")
    mw = c.inp("Mud weight (MW)", 12.5, "ppg")
    apl = c.inp("Annular pressure loss (APL)", 200, "psi", fmt="#,##0")
    tvd = c.inp("True vertical depth (TVD)", 10000, "ft", fmt="#,##0")
    c.out("Circulating bottomhole pressure", f"0.052*{mw}*{tvd}+{apl}", "psi", fmt="#,##0")

    sb.section("Weight-Up & Dilution")

    c = sb.calc("Barite Required to Weight Up",
                eq="Sacks/100 bbl = 1470 x (MW2 - MW1) / (35 - MW2)",
                note="Barite SG 4.20 (35 ppg); 100 lb sacks. Final volume increases.")
    v = c.inp("Initial mud volume", 800, "bbl", fmt="#,##0")
    m1 = c.inp("Initial mud weight (MW1)", 12.5, "ppg")
    m2 = c.inp("Desired mud weight (MW2)", 13.5, "ppg")
    sx = c.out("Barite required", f"1470*({m2}-{m1})/(35-{m2})*{v}/100", None, fmt="#,##0",
               note="100-lb sacks")
    c.out("Volume increase", f"{sx}*100/(35*42)", "bbl", fmt="0.0",
          note="V_inc [bbl] = sacks x 100 lb / (35 ppg x 42 gal/bbl)")

    c = sb.calc("Calcium Carbonate Required to Weight Up",
                eq="Sacks/100 bbl = 945 x (MW2 - MW1) / (22.5 - MW2)",
                note="CaCO3 SG 2.70 (22.5 ppg); 100 lb sacks. Acid-soluble, for reservoir drill-in fluids.")
    v = c.inp("Initial mud volume", 400, "bbl", fmt="#,##0")
    m1 = c.inp("Initial mud weight (MW1)", 9.0, "ppg")
    m2 = c.inp("Desired mud weight (MW2)", 10.0, "ppg")
    c.out("CaCO3 required", f"945*({m2}-{m1})/(22.5-{m2})*{v}/100", None, fmt="#,##0",
          note="100-lb sacks")

    c = sb.calc("Dilution to Reduce Mud Weight",
                eq="V_dil [bbl] = V1 x (MW1 - MW2) / (MW2 - MW_dil)",
                note="Volume of dilution fluid (water/base oil) to add to V1 to cut density from MW1 to MW2.")
    v1 = c.inp("Initial mud volume (V1)", 800, "bbl", fmt="#,##0")
    m1 = c.inp("Initial mud weight (MW1)", 13.0, "ppg")
    m2 = c.inp("Desired mud weight (MW2)", 12.2, "ppg")
    md = c.inp("Dilution fluid density (MW_dil)", 8.34, "ppg")
    c.out("Dilution volume required", f"{v1}*({m1}-{m2})/({m2}-{md})", "bbl", fmt="#,##0.0")

    c = sb.calc("Blending Two Fluids (Final Density)",
                eq="MW_f = (V1 x MW1 + V2 x MW2) / (V1 + V2)")
    v1 = c.inp("Volume of fluid 1 (V1)", 500, "bbl", fmt="#,##0")
    m1 = c.inp("Density of fluid 1 (MW1)", 12.0, "ppg")
    v2 = c.inp("Volume of fluid 2 (V2)", 300, "bbl", fmt="#,##0")
    m2 = c.inp("Density of fluid 2 (MW2)", 9.0, "ppg")
    c.out("Blended density", f"({v1}*{m1}+{v2}*{m2})/({v1}+{v2})", "ppg")
    c.out("Total volume", f"{v1}+{v2}", "bbl", fmt="#,##0")
