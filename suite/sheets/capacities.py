"""Drilling: pipe/annulus capacities, displacements, pump output, strokes, tripping, slug."""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "Capacities & Displacement", "drilling",
        "Capacities, Displacement & Pump Output",
        "Pipe and annular capacities, hole volume, pump output, circulation strokes, tripping and slug",
        description="Capacities, displacements, pump output, stroke/lag times, tripping and slug volumes",
    )

    sb.section("Pipe, Annulus & Hole Capacities")

    c = sb.calc("Pipe (Internal) Capacity",
                eq="C_pipe [bbl/ft] = ID^2 / 1029.4")
    idp = c.inp("Pipe inside diameter (ID)", 4.276, "in", fmt="0.000")
    c.out("Pipe capacity", f"{idp}^2/1029.4", "bbl/ft", fmt="0.00000",
          note="5 in 19.5 lb/ft drill pipe shown.")

    c = sb.calc("Annular Capacity",
                eq="C_ann [bbl/ft] = (Dh^2 - Dp^2) / 1029.4")
    dh = c.inp("Hole (or casing ID) diameter (Dh)", 8.5, "in", fmt="0.000")
    dp = c.inp("Pipe outside diameter (Dp)", 5.0, "in", fmt="0.000")
    c.out("Annular capacity", f"({dh}^2-{dp}^2)/1029.4", "bbl/ft", fmt="0.00000")

    c = sb.calc("Pipe Displacement",
                eq="Closed-end [bbl/ft] = OD^2 / 1029.4;   Open-end (steel) [bbl/ft] = (OD^2 - ID^2) / 1029.4",
                note="Open-end = steel displacement (tripping with open pipe). Closed-end = capacity + steel (plugged bit / float).")
    od = c.inp("Pipe outside diameter (OD)", 5.0, "in", fmt="0.000")
    idp = c.inp("Pipe inside diameter (ID)", 4.276, "in", fmt="0.000")
    c.out("Closed-end displacement", f"{od}^2/1029.4", "bbl/ft", fmt="0.00000")
    c.out("Open-end (steel) displacement", f"({od}^2-{idp}^2)/1029.4", "bbl/ft", fmt="0.00000")

    c = sb.calc("Hole Volume",
                eq="V [bbl] = Dh^2 / 1029.4 x L x (1 + washout)",
                note="Washout entered as a fraction (0.10 = 10% over-gauge).")
    dh = c.inp("Hole diameter (Dh)", 8.5, "in", fmt="0.000")
    lh = c.inp("Hole length", 10000, "ft", fmt="#,##0")
    wo = c.inp("Washout factor", 0.10, None, fmt="0.00", note="Fraction of excess over gauge hole.")
    c.out("Hole volume", f"{dh}^2/1029.4*{lh}*(1+{wo})", "bbl", fmt="#,##0")

    sb.section("Pump Output & Flow Rate")

    c = sb.calc("Triplex Pump Output",
                eq="Q [bbl/stk] = 0.000243 x D_liner^2 x L_stroke x eff",
                note="Single-acting, three cylinders. D and stroke in inches; eff as a fraction (0.95-0.98 typical).")
    dl = c.inp("Liner diameter (D)", 6.0, "in", fmt="0.000")
    st = c.inp("Stroke length (L)", 12.0, "in", fmt="0.0")
    ef = c.inp("Volumetric efficiency", 0.95, None, fmt="0.00")
    tpo = c.out("Pump output", f"0.000243*{dl}^2*{st}*{ef}", "bbl/stk", fmt="0.00000")

    c = sb.calc("Duplex Pump Output",
                eq="Q [bbl/stk] = 0.000162 x L_stroke x (2 x D_liner^2 - d_rod^2) x eff",
                note="Double-acting, two cylinders; d = piston rod diameter. Eff 0.85-0.90 typical.")
    dl = c.inp("Liner diameter (D)", 6.5, "in", fmt="0.000")
    dr = c.inp("Rod diameter (d)", 2.5, "in", fmt="0.000")
    st = c.inp("Stroke length (L)", 14.0, "in", fmt="0.0")
    ef = c.inp("Volumetric efficiency", 0.90, None, fmt="0.00")
    c.out("Pump output", f"0.000162*{st}*(2*{dl}^2-{dr}^2)*{ef}", "bbl/stk", fmt="0.00000")

    c = sb.calc("Pump Flow Rate from Stroke Rate",
                eq="Q [bbl/min] = output [bbl/stk] x SPM;   Q [gpm] = bbl/min x 42")
    po = c.inp("Pump output", 0.0997, "bbl/stk", fmt="0.00000")
    spm = c.inp("Pump speed", 60, "spm", fmt="#,##0", note="Strokes per minute.")
    qb = c.out("Flow rate", f"{po}*{spm}", "bbl/min", fmt="0.00")
    c.out("Flow rate", f"{qb}*42", "gpm", fmt="#,##0")

    sb.section("Circulation Strokes & Lag Time")

    c = sb.calc("Surface-to-Bit Strokes & Time",
                eq="Strokes = string volume / pump output;   Time [min] = strokes / SPM",
                note="String volume = drill string internal capacity x measured length (add BHA capacity if significant).")
    cap = c.inp("Drill string capacity", 0.01776, "bbl/ft", fmt="0.00000")
    ls = c.inp("Drill string measured length", 10000, "ft", fmt="#,##0")
    po = c.inp("Pump output", 0.0997, "bbl/stk", fmt="0.00000")
    spm = c.inp("Pump speed", 60, "spm", fmt="#,##0")
    v1 = c.out("String volume", f"{cap}*{ls}", "bbl", fmt="#,##0.0")
    s1 = c.out("Surface-to-bit strokes", f"ROUNDUP(ROUND({v1}/{po},6),0)", "stk", fmt="#,##0")
    t1 = c.out("Surface-to-bit time", f"{s1}/{spm}", "min", fmt="0.0")

    c = sb.calc("Bottoms-Up Strokes & Lag Time",
                eq="Strokes = annular volume / pump output;   Lag time [min] = strokes / SPM",
                note="Annular volume = annular capacity x length; sum open-hole and cased-hole sections for accuracy.")
    cap = c.inp("Annular capacity", 0.0459, "bbl/ft", fmt="0.00000")
    la = c.inp("Annulus length", 10000, "ft", fmt="#,##0")
    po = c.inp("Pump output", 0.0997, "bbl/stk", fmt="0.00000")
    spm = c.inp("Pump speed", 60, "spm", fmt="#,##0")
    v2 = c.out("Annular volume", f"{cap}*{la}", "bbl", fmt="#,##0.0")
    s2 = c.out("Bottoms-up strokes", f"ROUNDUP(ROUND({v2}/{po},6),0)", "stk", fmt="#,##0")
    t2 = c.out("Bottoms-up (lag) time", f"{s2}/{spm}", "min", fmt="0.0")

    c = sb.calc("Total Circulation (Surface-to-Surface)",
                eq="Total = surface-to-bit + bottoms-up",
                note="Uses the two calculators above. Total cycle time is one complete circulation of the well.")
    c.out("Total circulating volume", f"{v1}+{v2}", "bbl", fmt="#,##0.0")
    c.out("Total circulation strokes", f"{s1}+{s2}", "stk", fmt="#,##0")
    c.out("Total circulation time", f"{t1}+{t2}", "min", fmt="0.0")

    sb.section("Tripping & Slug")

    c = sb.calc("Drill String Displacement While Tripping",
                eq="Dry [bbl/ft] = (OD^2 - ID^2)/1029.4;   Wet [bbl/ft] = OD^2/1029.4 (steel + contents)",
                note="Dry pipe: hole fill (pulling) or pit gain (running) equals steel volume only. "
                     "Wet pipe (no float / plugged bit not draining): add the pipe contents.")
    od = c.inp("Pipe outside diameter (OD)", 5.0, "in", fmt="0.000")
    idp = c.inp("Pipe inside diameter (ID)", 4.276, "in", fmt="0.000")
    lst = c.inp("Average stand length", 93, "ft", fmt="0.0")
    ns = c.inp("Number of stands pulled", 10, None, fmt="#,##0", note="Stands between flow checks / trip tank readings.")
    dd = c.out("Dry displacement", f"({od}^2-{idp}^2)/1029.4", "bbl/ft", fmt="0.00000")
    wd = c.out("Wet displacement", f"{od}^2/1029.4", "bbl/ft", fmt="0.00000")
    c.out("Expected pit change - dry pipe", f"{dd}*{lst}*{ns}", "bbl", fmt="0.00",
          note="Hole should take this much mud when pulling dry; deviation indicates swabbing or losses.")
    c.out("Expected pit change - wet pipe", f"{wd}*{lst}*{ns}", "bbl", fmt="0.00")

    c = sb.calc("Slug Volume for Desired Dry Pipe",
                eq="V_slug [bbl] = L_dry x MW / (SW - MW) x C_pipe",
                note="Heavy slug pumped before tripping drops the fluid level inside the pipe so stands pull dry.")
    ld = c.inp("Desired dry pipe length", 200, "ft", fmt="#,##0")
    mw = c.inp("Mud weight (MW)", 12.5, "ppg")
    sw = c.inp("Slug weight (SW)", 14.0, "ppg")
    cap = c.inp("Pipe capacity", 0.01776, "bbl/ft", fmt="0.00000")
    c.out("Slug volume required", f"{ld}*{mw}/({sw}-{mw})*{cap}", "bbl", fmt="0.0")

    c = sb.calc("Dry Pipe Length from Slug Pumped",
                eq="L_dry [ft] = V_slug / C_pipe x (SW - MW) / MW")
    vs = c.inp("Slug volume pumped", 30, "bbl", fmt="0.0")
    sw = c.inp("Slug weight (SW)", 14.0, "ppg")
    mw = c.inp("Mud weight (MW)", 12.5, "ppg")
    cap = c.inp("Pipe capacity", 0.01776, "bbl/ft", fmt="0.00000")
    c.out("Expected dry pipe length", f"{vs}/{cap}*({sw}-{mw})/{mw}", "ft", fmt="#,##0")
