"""Drilling: high-angle hole cleaning - annular velocity, CCI, angle-band
flow guidance, slip velocity / transport ratio, cuttings concentration."""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "Hole Cleaning", "drilling",
        "Hole Cleaning - High-Angle Wells",
        "Annular velocity, carrying capacity index, angle-band minimum flow, "
        "slip velocity, transport ratio and cuttings concentration",
        description="Annular velocity, CCI, angle-band flow guidance, slip velocity, "
                    "transport ratio, cuttings concentration",
    )

    # ------------------------------------------------- annular velocity
    sb.section("Annular Velocity & Flow")

    c = sb.calc("Annular Velocity",
                eq="AV [ft/min] = 24.5 x Q [gpm] / (Dh^2 - Dp^2)",
                note="Typical minimums: 100-120 ft/min below 35 deg, 150-180 ft/min "
                     "at 35-65 deg, >= 180 ft/min above 65 deg (with pipe rotation).")
    dh = c.link("Hole diameter (Dh)", "WD_HoleDiam", "in", fmt="0.000")
    dp = c.inp("Pipe OD (Dp)", 5.0, "in", fmt="0.000")
    q = c.inp("Flow rate (Q)", 600, "gpm", fmt="#,##0")
    av = c.out("Annular velocity (AV)", f"24.5*{q}/({dh}^2-{dp}^2)", "ft/min", fmt="0.0")

    # ------------------------------------------------- carrying capacity
    sb.section("Carrying Capacity Index")

    c = sb.calc("Carrying Capacity Index (CCI)",
                eq="CCI = K x AV x MW / 400000;   K = 511^(1-n) x (PV + YP);   "
                   "n = 3.32 x LOG10((2 x PV + YP) / (PV + YP))",
                note="AV in ft/min, MW in ppg, K = power-law consistency (eq. cP). "
                     "CCI >= 1 indicates good hole cleaning.")
    mw = c.link("Mud weight (MW)", "WD_OMW", "ppg")
    pv = c.link("Plastic viscosity (PV)", "WD_PV", "cP", fmt="0.0")
    yp = c.link("Yield point (YP)", "WD_YP", None, fmt="0.0",
                note="lb/100ft2. Linked to Well Data - overwrite locally if needed.")
    n = c.out("Flow behavior index (n)",
              f"3.32*LOG10((2*{pv}+{yp})/({pv}+{yp}))", None, fmt="0.000")
    k = c.out("Power-law consistency (K)", f"511^(1-{n})*({pv}+{yp})", None,
              fmt="#,##0", note="Equivalent centipoise.")
    cci = c.out("Carrying capacity index (CCI)", f"{k}*{av}*{mw}/400000",
                None, fmt="0.00")
    c.out("Hole cleaning status",
          f'IF({cci}>=1,"OK - good cleaning",'
          f'IF({cci}>=0.5,"MARGINAL - increase flow/rheology",'
          f'"CHECK: poor hole cleaning likely"))', None, fmt="@")

    # ------------------------------------------------- angle-band guidance
    sb.section("Angle-Band Minimum Flow Guidance")

    c = sb.calc("Minimum Flow by Angle Band",
                eq="Qmin [gpm] = AVmin x (Dh^2 - Dp^2) / 24.5",
                note="Band minimum AV: < 35 deg -> 120 ft/min; 35 deg and above -> "
                     "180 ft/min (top of the 150-180 range in the hardest 35-65 deg "
                     "band, and the bed-prevention minimum above 65 deg).")
    ang = c.inp("Hole angle", 90, "deg", fmt="#,##0", note="Degrees from vertical.")
    c.out("Angle band guidance",
          f'IF({ang}<35,"OK to clean with AV 100-120 ft/min",'
          f'IF({ang}<=65,"CHECK: hardest band - avalanche/cuttings bed risk; '
          f'AV 150-180 ft/min + rotation",'
          f'"CHECK: bed forms unless AV >= 180 ft/min with pipe rotation"))',
          None, fmt="@")
    av_min = c.out("Minimum recommended AV for band",
                   f"IF({ang}<35,120,IF({ang}<=65,180,180))", "ft/min", fmt="#,##0")
    q_min = c.out("Minimum recommended flow rate (Qmin)",
                  f"{av_min}*({dh}^2-{dp}^2)/24.5", "gpm", fmt="#,##0")
    c.out("Current flow vs band minimum",
          f'IF({q}>={q_min},"OK - flow meets band minimum",'
          f'"INSUFFICIENT flow for this angle band - increase rate")', None, fmt="@")

    # ------------------------------------------------- slip velocity
    sb.section("Slip Velocity & Transport (vertical baseline)")

    c = sb.calc("Slip Velocity (Moore-style, turbulent)",
                eq="Vs [ft/min] = 92.6 x SQRT(Dc x (rho_c - MW) / MW)",
                note="Turbulent-regime approximation; Dc in inches, densities in ppg. "
                     "Vertical-well baseline - above ~65 deg cuttings beds, not slip, "
                     "control cleaning.")
    dc = c.inp("Cutting diameter (Dc)", 0.25, "in", fmt="0.000")
    rho_c = c.inp("Cutting density (rho_c)", 21.7, "ppg", fmt="0.0",
                  note="~2.6 SG for typical shale/sand cuttings.")
    vs = c.out("Slip velocity (Vs)", f"92.6*SQRT({dc}*({rho_c}-{mw})/{mw})",
               "ft/min", fmt="0.0")
    tr = c.out("Transport ratio (TR)", f"1-{vs}/{av}", None, fmt="0.00",
               note="TR = 1 - Vs/AV. Net upward cuttings velocity fraction.")
    c.out("Transport status",
          f'IF({tr}>0.5,"OK - good transport",'
          f'IF({tr}>0.3,"MARGINAL - watch cuttings returns",'
          f'"CHECK: increase flow"))', None, fmt="@")

    # ------------------------------------------------- cuttings concentration
    sb.section("Cuttings Concentration")

    c = sb.calc("Annular Cuttings Concentration",
                eq="Gen [bbl/hr] = ROP x Dh^2 / 1029.4;   "
                   "Conc [%] = 100 x Gen / (Gen + Q x 60/42)",
                note="Keep annular cuttings concentration below ~5% to avoid pack-off "
                     "and ECD spikes.")
    rop = c.inp("Rate of penetration (ROP)", 60, "ft/hr", fmt="#,##0")
    gen = c.out("Cuttings generation rate", f"{rop}*{dh}^2/1029.4", "bbl/hr", fmt="0.00")
    q_bbl = c.out("Circulation rate", f"{q}*60/42", "bbl/hr", fmt="#,##0.0")
    conc = c.out("Annular cuttings concentration", f"100*{gen}/({gen}+{q_bbl})",
                 None, fmt="0.00", note="Percent by volume, steady state.")
    c.out("Concentration status",
          f'IF({conc}<=4,"OK",IF({conc}<=6,"MARGINAL",'
          f'"CHECK: exceeds 5% guideline - reduce ROP or raise flow"))', None, fmt="@")

    # ------------------------------------------------- practices
    sb.section("Pipe Rotation & Practices")

    c = sb.calc("Good Practices - High-Angle Cleaning")
    c.txt("Pipe rotation",
          "Rotation >= 120 rpm agitates and disturbs cuttings beds in laterals - "
          "the single most effective mechanical aid to cleaning.")
    c.txt("Sweeps",
          "Pump sweeps (hi-vis or weighted) have limited value above 65 deg - "
          "flow rate and rotation do the work, not viscosity alone.")
    c.txt("Before tripping",
          "Circulate 2-3 bottoms-up at full rate with rotation before tripping "
          "in high-angle hole.")
    c.txt("Monitoring",
          "Monitor shaker returns against the expected cuttings volume "
          "(generation rate x circulating time) - a shortfall means a bed is "
          "building downhole.")
