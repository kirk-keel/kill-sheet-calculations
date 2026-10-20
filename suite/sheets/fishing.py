"""Interventions: fishing and stuck pipe - free point, overpull, spotting, sticking force."""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "Fishing & Stuck Pipe", "interventions",
        "Fishing & Stuck Pipe",
        "Free point from stretch, overpull margin, spotting fluid placement, differential sticking",
        description="Free point, overpull margin, spot/chase volumes, sticking force, soak pills, milling time",
    )

    sb.section("Free Point")

    c = sb.calc("Free Point from Stretch",
                eq="L_free [ft] = 735294 x e [in] x w_dp [lb/ft] / P_diff [lbf]",
                note="Classic field formula. Origin: L = e x E x A / P with E = 30e6 psi and steel area "
                     "A ~ w/3.4 in2 per lb/ft, so L [ft] = e x 30e6 x w / (3.4 x 12 x P) = 735294 x e x w / P. "
                     "Approximate (~5-10%): uses nominal weight incl. tool joints and average E for steel.")
    e = c.inp("Differential stretch measured (e)", 20.0, "in", fmt="0.0")
    wdp = c.inp("Pipe weight (w_dp)", 19.5, "lb/ft", fmt="0.00",
                note="Nominal weight of the section above the stuck point; recompute per section for "
                     "tapered strings.")
    pdiff = c.inp("Differential pull (P_diff)", 40000, "lbf", fmt="#,##0")
    c.out("Free point depth (below rig floor)", f"735294*{e}*{wdp}/{pdiff}", "ft", fmt="#,##0")
    c.txt("Differential pull procedure",
          "Pull to P1 (above hanging weight, below limits) and mark the pipe; pull to P2 and mark again. "
          "Use e = stretch difference between marks and P_diff = P2 - P1. This cancels drag and initial "
          "slack. Confirm with a free-point indicator tool before backing off.")

    sb.section("Pulling")

    c = sb.calc("Overpull Margin",
                eq="Max pull = MIN(0.9 x F_yield, weak link);  margin = max pull - hanging weight",
                note="90% of pipe tensile yield is a common working limit - also check top drive / hook, "
                     "elevators, and the weakest connection in the string.")
    fy = c.inp("Pipe tensile yield strength", 395, "klbf", fmt="#,##0")
    fweak = c.inp("Weakest connection / weak link rating", 350, "klbf", fmt="#,##0")
    whang = c.inp("Buoyed hanging weight before stuck", 180, "klbf", fmt="#,##0")
    maxp = c.out("Maximum pull at surface", f"MIN(0.9*{fy},{fweak})", "klbf", fmt="#,##0")
    marg = c.out("Available overpull margin", f"{maxp}-{whang}", "klbf", fmt="#,##0")
    c.out("Margin check", f'IF({marg}>0,"OK - overpull available","NO MARGIN - do not pull, work string")',
          None, fmt="@")

    sb.section("Spotting Fluid")

    c = sb.calc("Spot Fluid Volume & Chase (Displacement) Volume",
                eq="V_ann = (Dh^2 - OD^2)/1029.4 x L_stuck;  V_pill = V_ann x (1 + excess);  "
                   "V_chase = string volume - pill left inside string",
                note="Pill left inside the string = V_pill - annulus interval volume, so after displacement "
                     "the pill covers the stuck interval with the excess still inside the pipe for periodic "
                     "top-ups while soaking.")
    dh = c.inp("Hole / casing ID (Dh)", 8.500, "in", fmt="0.000")
    pod = c.inp("Pipe OD", 4.500, "in", fmt="0.000")
    pid = c.inp("Pipe ID", 3.826, "in", fmt="0.000")
    bitd = c.inp("Bit / end of string depth (MD)", 9800, "ft", fmt="#,##0")
    lstk = c.inp("Stuck interval length (above bit)", 300, "ft", fmt="#,##0")
    xsp = c.inp("Excess", 25, None, fmt="#,##0", note="% extra pill volume; 25-50% typical")
    acap = c.out("Annular capacity", f"({dh}^2-{pod}^2)/1029.4", "bbl/ft", fmt="0.00000")
    vint = c.out("Annulus volume over stuck interval", f"{acap}*{lstk}", "bbl", fmt="0.0")
    vpill = c.out("Total pill volume to mix", f"{vint}*(1+{xsp}/100)", "bbl", fmt="0.0")
    scap = c.out("String internal capacity", f"{pid}^2/1029.4", "bbl/ft", fmt="0.00000")
    vstr = c.out("String internal volume", f"{scap}*{bitd}", "bbl", fmt="0.0")
    c.out("Chase volume to spot pill on depth", f"{vstr}-({vpill}-{vint})", "bbl", fmt="0.0",
          note="Pump pill, then this chase; under-displace slightly and top up ~1 bbl every 30-60 min.")

    sb.section("Stuck Pipe Mechanics")

    c = sb.calc("Differential Sticking Force",
                eq="F = dP x contact area x f;  area [in2] = L_contact x 12 x w_contact",
                note="Order-of-magnitude estimate - contact width and friction factor are highly uncertain. "
                     "Shows why even modest overbalance over a long permeable interval can exceed any "
                     "available overpull.")
    dp = c.inp("Overbalance across cake (dP)", 500, "psi", fmt="#,##0")
    lc = c.inp("Contact (stuck) length", 300, "ft", fmt="#,##0")
    wc = c.inp("Effective contact width", 2.0, "in", fmt="0.00",
               note="Rule of thumb 1-4 in, depending on cake thickness and pipe OD.")
    fric = c.inp("Friction coefficient (f)", 0.20, None, fmt="0.00",
                 note="0.1-0.3 typical; increases with time as the cake dehydrates - act fast.")
    area = c.out("Contact area", f"{lc}*12*{wc}", "in2", fmt="#,##0")
    c.out("Sticking force (approximate)", f"{dp}*{area}*{fric}", "lbf", fmt="#,##0")

    c = sb.calc("Acid / Solvent Soak Pill Volume",
                eq="V = annular capacity x interval x (1 + excess)",
                note="For scale, cement, or fill around the fish; uses the annular capacity above. Verify "
                     "metallurgy and H2S risk before acid soaks.")
    lsoak = c.inp("Interval to soak", 60, "ft", fmt="#,##0")
    xsk = c.inp("Excess", 50, None, fmt="#,##0", note="%")
    c.out("Soak pill volume", f"{acap}*{lsoak}*(1+{xsk}/100)", "bbl", fmt="0.0")

    sb.section("Milling & Notes")

    c = sb.calc("Milling Time",
                eq="t [hr] = length to mill / milling rate")
    lmill = c.inp("Length to mill", 6.0, "ft", fmt="0.0")
    rmill = c.inp("Milling rate", 1.5, "ft/hr", fmt="0.00",
                  note="Typical 0.5-5 ft/hr depending on mill type, fish material, and WOB.")
    c.out("Milling time", f"{lmill}/{rmill}", None, fmt="0.0", note="hours, excluding trips and mill changes")

    c = sb.calc("Field Notes")
    c.txt("Jar placement & intensifier",
          "Place drilling jars in the transition from tension to compression, never inside the expected "
          "stuck zone; run an intensifier (accelerator) above the jars plus 3-5 heavy-weight joints between "
          "them so the hammer mass is effective at shallow depths and in deviated wells.")
    c.txt("Back-off / safety joint torque",
          "Back off with left-hand torque worked down to the free point with string weight at neutral at the "
          "backoff depth; applied torque typically must stay below ~80% of connection make-up torque. "
          "Safety joints release with a fraction of make-up torque per the manufacturer data sheet.")
    c.txt("Pipe recovery ton-miles",
          "Jarring and repeated overpull cycles accumulate drill-line ton-miles quickly - recalculate "
          "slip-and-cut schedule during long fishing jobs.")
