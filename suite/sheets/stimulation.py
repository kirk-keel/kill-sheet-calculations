"""Completions: frac gradients, treating pressures, HHP, perf friction, proppant and acid totals."""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "Stimulation & Fracturing", "completions",
        "Stimulation & Fracturing",
        "Frac gradient, treating pressures, hydraulic horsepower, perforation friction, proppant and acid volumes",
        description="Frac/closure gradients, BHTP and STP, HHP, perf friction, proppant schedule totals, acid volumes",
    )

    sb.section("Fracture Pressures & Gradients")

    c = sb.calc("Fracture Gradient from LOT / Minifrac",
                eq="FG [psi/ft] = (P_surf + 0.052 x rho x TVD) / TVD",
                note="P_surf = surface pressure at leak-off (LOT) or at breakdown/ISIP from a minifrac, with fluid density rho in the string. Gives the gradient at the test depth.")
    plot = c.inp("Surface pressure at leak-off / ISIP", 1800, "psi", fmt="#,##0")
    rho = c.inp("Fluid density in string", 9.2, "ppg")
    tvdt = c.inp("TVD of test point", 9000, "ft", fmt="#,##0")
    c.out("Fracture gradient (FG)", f"({plot}+0.052*{rho}*{tvdt})/{tvdt}", "psi/ft", fmt="0.000")

    c = sb.calc("Closure Pressure & Gradient",
                eq="G_c [psi/ft] = P_closure / TVD",
                note="Closure pressure picked from minifrac decline (G-function / sqrt-time). Approximates minimum horizontal stress.")
    pc = c.inp("Closure pressure (P_closure)", 6300, "psi", fmt="#,##0")
    tvd = c.inp("TVD at mid-perf", 9000, "ft", fmt="#,##0")
    c.out("Closure gradient (G_c)", f"{pc}/{tvd}", "psi/ft", fmt="0.000")

    c = sb.calc("Bottomhole Treating Pressure (BHTP)",
                eq="BHTP = FG x TVD",
                note="Pressure needed at the perfs to extend the fracture.")
    fg = c.inp("Fracture gradient (FG)", 0.75, "psi/ft", fmt="0.000")
    tvd = c.inp("TVD at mid-perf", 9000, "ft", fmt="#,##0")
    bhtp = c.out("Bottomhole treating pressure", f"{fg}*{tvd}", "psi", fmt="#,##0")

    sb.section("Treating Pressure & Horsepower")

    c = sb.calc("Perforation Friction",
                eq="dP_pf = 0.2369 x Q^2 x rho / (N^2 x d^4 x Cd^2)",
                note="Q = total rate in bpm, rho in ppg, d = perf diameter in inches, N = open perfs, Cd = discharge coefficient (0.85 new holes, up to 0.95 after erosion by proppant).")
    q = c.inp("Total pump rate (Q)", 30, "bbl/min", fmt="#,##0.0")
    rhos = c.inp("Slurry density (rho)", 8.6, "ppg")
    n = c.inp("Number of open perforations (N)", 24, None, fmt="#,##0")
    d = c.inp("Perforation diameter (d)", 0.42, "in", fmt="0.000")
    cd = c.inp("Discharge coefficient (Cd)", 0.90, None, fmt="0.00")
    dppf = c.out("Perforation friction (dP_pf)", f"0.2369*{q}^2*{rhos}/({n}^2*{d}^4*{cd}^2)",
                 "psi", fmt="#,##0")

    c = sb.calc("Surface Treating Pressure (STP)",
                eq="STP = BHTP - P_hyd + dP_pipe + dP_pf",
                note="P_hyd = 0.052 x rho x TVD. Pipe friction entered as psi per 1000 ft of measured depth - from service company friction tables for the fluid and pipe size. Uses BHTP and dP_pf computed above.")
    rho = c.inp("Treating fluid density", 8.6, "ppg")
    tvd = c.inp("TVD at mid-perf", 9000, "ft", fmt="#,##0")
    fr = c.inp("Pipe friction", 60, None, si=("kPa/100m", 2.262059), fmt="#,##0.0",
               note="psi per 1000 ft")
    md = c.inp("Measured depth of flow path", 9200, "ft", fmt="#,##0")
    ph = c.out("Hydrostatic (P_hyd)", f"0.052*{rho}*{tvd}", "psi", fmt="#,##0")
    dpp = c.out("Total pipe friction (dP_pipe)", f"{fr}*{md}/1000", "psi", fmt="#,##0")
    stp = c.out("Surface treating pressure (STP)", f"{bhtp}-{ph}+{dpp}+{dppf}", "psi", fmt="#,##0")

    c = sb.calc("Hydraulic Horsepower",
                eq="HHP = STP x Q / 40.8   (Q in bpm)",
                note="Order pump HHP with headroom - typically 1.2-1.5 x calculated. Uses STP and Q from above.")
    hhp = c.out("Hydraulic horsepower (HHP)", f"{stp}*{q}/40.8", "hp", fmt="#,##0")
    sf = c.inp("Horsepower safety factor", 1.3, None, fmt="0.00")
    c.out("Ordered horsepower", f"{hhp}*{sf}", "hp", fmt="#,##0")

    c = sb.calc("Net Pressure & Injectivity",
                eq="P_net = BHTP - P_closure;   II = Q / (BHTP - P_res)",
                note="Net pressure drives fracture width/height growth. Injectivity index from the treating condition. Uses BHTP, closure and Q from above.")
    presv = c.inp("Reservoir pressure (P_res)", 4500, "psi", fmt="#,##0")
    c.out("Net pressure (P_net)", f"{bhtp}-{pc}", "psi", fmt="#,##0")
    c.out("Injectivity index (II)", f"{q}/({bhtp}-{presv})", None, fmt="0.0000",
          note="bpm per psi")

    c = sb.calc("Max Surface Pressure vs Tubular Limit",
                eq="Margin = P_limit - STP",
                note="P_limit = lowest derated burst / wellhead / treating iron working pressure in the load path. Uses STP from above.")
    plim = c.inp("Weakest limit in load path (P_limit)", 5000, "psi", fmt="#,##0")
    mg = c.out("Margin to limit", f"{plim}-{stp}", "psi", fmt="#,##0")
    c.out("Status", f'IF({mg}<0,"EXCEEDS LIMIT - REDESIGN",IF({mg}<500,"OK - LOW MARGIN","OK"))',
          None, fmt="@", note="Text result; set trip/pop-off below the limit.")

    sb.section("Fluid & Proppant Totals")

    c = sb.calc("Clean / Dirty Volume & Proppant Mass",
                eq="M_prop = V_clean x ppa;   V_dirty = V_clean x (1 + ppa x AV);   pad fraction = V_pad / V_clean",
                note="ppa = average proppant added per clean gallon (lb/gal). AV = proppant absolute volume, gal/lb (0.0453 for sand SG 2.65). Stage totals at the average concentration - use the pump schedule for stage-by-stage numbers.")
    vcl = c.inp("Clean fluid volume (V_clean)", 50000, "gal", fmt="#,##0")
    ppa = c.inp("Average proppant concentration (ppa)", 2.0, None, fmt="0.00",
                note="lb proppant per clean gal")
    av = c.inp("Proppant absolute volume (AV)", 0.0453, None, fmt="0.0000",
               note="gal per lb (sand 0.0453)")
    vpad = c.inp("Pad volume (V_pad)", 15000, "gal", fmt="#,##0")
    mp = c.out("Proppant mass", f"{vcl}*{ppa}", "lbm", fmt="#,##0")
    c.out("Proppant mass", f"{mp}/2000", None, fmt="#,##0.0", note="short tons")
    c.out("Dirty (slurry) volume", f"{vcl}*(1+{ppa}*{av})", "gal", fmt="#,##0")
    c.out("Dirty (slurry) volume", f"{vcl}*(1+{ppa}*{av})/42", "bbl", fmt="#,##0")
    c.out("Pad fraction", f"{vpad}/{vcl}*100", None, fmt="0.0", note="percent of clean volume")

    sb.section("Matrix Acidizing")

    c = sb.calc("Acid Volume & Dissolving Power",
                eq="V_acid = (gal/ft) x interval;   M_rock = DP x V_acid;   V_rock = M_rock / rho_rock",
                note="Coverage rule-of-thumb 50-100 gal/ft for carbonate matrix wormholing. DP = dissolving power: 15 pct HCl dissolves approx 1.84 lb CaCO3 per gallon (equivalently approx 10.8 ft3 of rock per 1000 gal). Limestone approx 169 lb/ft3. Spend/contact time and wormhole efficiency depend on temperature and rate - approximate planning numbers only.")
    gpf = c.inp("Acid coverage", 75, None, fmt="#,##0", note="gal per ft of interval")
    itv = c.inp("Treated interval", 40, "ft", fmt="#,##0")
    dp15 = c.inp("Dissolving power (DP)", 1.84, None, fmt="0.00",
                 note="lb CaCO3 per gal acid (1.84 for 15 pct HCl)")
    rrock = c.inp("Rock density", 169, None, fmt="#,##0", note="lb/ft3 (limestone approx 169)")
    va = c.out("Total acid volume", f"{gpf}*{itv}", "gal", fmt="#,##0")
    mr = c.out("Rock dissolved (mass)", f"{dp15}*{va}", "lbm", fmt="#,##0")
    c.out("Rock dissolved (volume)", f"{mr}/{rrock}", "ft3", fmt="0.0")

    c = sb.calc("Ball Sealer Count",
                eq="Balls = ROUNDUP(N_perfs x excess, 0)",
                note="Typical excess factor 1.5 - 2.0 x the open perforation count to get effective diversion.")
    np_ = c.inp("Open perforations (N_perfs)", 96, None, fmt="#,##0")
    exf = c.inp("Excess factor", 1.5, None, fmt="0.0")
    c.out("Ball sealers to pump", f"ROUNDUP(ROUND({np_}*{exf},6),0)", None, fmt="#,##0")
