"""Interventions: well kill methods for completed wells - bullhead, lube & bleed,
circulation, volumetric."""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "Well Kill - Interventions", "interventions",
        "Well Kill for Interventions",
        "Kill fluid density, bullheading, lubricate & bleed, circulation kills, volumetric control",
        description="Kill weight fluid, bullhead pressures/volumes, lube & bleed cycles, forward/reverse circulation, volumetric",
    )

    sb.section("Kill Fluid")

    c = sb.calc("Kill Fluid Density for Target Overbalance",
                eq="KWM [ppg] = (P_res + OB) / (0.052 x TVD_perfs)")
    pres = c.inp("Reservoir pressure at perfs (P_res)", 3600, "psi", fmt="#,##0")
    tvd = c.inp("TVD of perforations", 9000, "ft", fmt="#,##0")
    ob = c.inp("Target overbalance (OB)", 200, "psi", fmt="#,##0")
    kwm_x = c.out("Kill fluid density (exact)", f"({pres}+{ob})/(0.052*{tvd})", "ppg", fmt="0.000")
    kwm = c.out("Kill fluid density (KWM, rounded up)", f"ROUNDUP(ROUND({kwm_x}*10,6),0)/10", "ppg", fmt="0.0",
                note="Rounding rule: kill weight fluid density rounds UP to the nearest 0.1 ppg.")

    sb.section("Bullheading")

    c = sb.calc("Bullhead Surface Pressure - Start & End",
                eq="P_surf = P_res - P_hyd(column) + P_fric;  start: gas column;  end: kill-fluid column",
                note="Start of job: tubing full of gas (worst case, highest surface pressure). End of job: "
                     "tubing full of kill fluid. Friction from planned pump rate.")
    ggrad = c.inp("Gas column gradient", 0.10, "psi/ft", fmt="0.000",
                  note="Dry gas ~0.05-0.12 psi/ft depending on pressure and SG; condensate/oil higher.")
    pfric = c.inp("Tubing friction at pump rate", 300, "psi", fmt="#,##0")
    pstart = c.out("Surface pressure at start (gas-filled)",
                   f"MAX(0,{pres}-{ggrad}*{tvd}+{pfric})", "psi", fmt="#,##0")
    pend = c.out("Surface pressure at end (kill-filled)",
                 f"MAX(0,{pres}-0.052*{kwm}*{tvd}+{pfric})", "psi", fmt="#,##0")
    tburst = c.inp("Tubing burst rating (derated)", 7700, "psi", fmt="#,##0",
                   note="Derate for wear/corrosion and apply design factor before entering here.")
    whrate = c.inp("Wellhead / tree working pressure", 10000, "psi", fmt="#,##0")
    pallow = c.out("Maximum allowable surface pressure", f"ROUNDUP(ROUND(MIN({tburst},{whrate}),6),0)",
                   "psi", fmt="#,##0",
                   note="Rounding rule: maximized values round UP to whole psi.")
    c.out("Surface pressure check",
          f'IF(MAX({pstart},{pend})<={pallow},"OK","EXCEEDS TUBING/WELLHEAD LIMIT - do not bullhead")',
          None, fmt="@")

    c = sb.calc("Bullhead Volume & Time",
                eq="V = tubing capacity x MD x excess factor;  capacity [bbl/ft] = ID^2 / 1029.4")
    tid = c.inp("Tubing ID", 2.992, "in", fmt="0.000")
    md = c.inp("Tubing length to perfs (MD)", 9200, "ft", fmt="#,##0")
    tcap = c.out("Tubing capacity", f"{tid}^2/1029.4", "bbl/ft", fmt="0.00000")
    vtub = c.out("Tubing volume", f"{tcap}*{md}", "bbl", fmt="0.0")
    xs = c.inp("Excess factor", 1.5, None, fmt="0.00",
               note="1.2-2.0 typical: pushes the gas/kill interface and any influx back into the formation.")
    vbh = c.out("Bullhead volume to pump", f"{vtub}*{xs}", "bbl", fmt="0.0")
    qbh = c.inp("Bullhead pump rate", 2.0, "bbl/min", fmt="0.00")
    c.out("Pumping time", f"{vbh}/{qbh}", None, fmt="#,##0.0", note="minutes")

    c = sb.calc("Injection Pressure vs Frac Gradient Check",
                eq="P_frac = frac grad x TVD;  max P_surf vs frac = P_frac - 0.052 x KWM x TVD + P_fric",
                note="Keep BHP below frac pressure at the perfs unless deliberately bullheading above frac "
                     "(a last-resort decision). BHP = P_surf + hydrostatic - friction.")
    fgrad = c.inp("Fracture gradient at perfs", 0.75, "psi/ft", fmt="0.000")
    pfrac = c.out("Fracture pressure at perfs", f"{fgrad}*{tvd}", "psi", fmt="#,##0")
    psmax = c.out("Max surface pressure to stay below frac",
                  f"ROUNDUP(ROUND({pfrac}-0.052*{kwm}*{tvd}+{pfric},6),0)", "psi", fmt="#,##0",
                  note="Rounding rule: maximized values round UP to whole psi.")
    c.out("Frac check at start-of-job pressure",
          f'IF({pstart}<={psmax},"OK - below frac","ABOVE FRAC - reduce rate or accept fracturing")',
          None, fmt="@")

    sb.section("Lubricate & Bleed")

    c = sb.calc("Lube & Bleed Cycles",
                eq="V_lube = capacity x lube length;  dP/cycle = 0.052 x KWM x lube length;  "
                   "cycles = ROUNDUP(target / dP_cycle)",
                note="Each cycle: pump the lube volume, wait for the fluid to fall through the gas, then bleed "
                     "gas at constant pressure until fluid reaches the choke. Gas bled per cycle at surface "
                     "equals the lube volume at wellhead conditions.")
    llen = c.inp("Lube column length per cycle", 500, "ft", fmt="#,##0",
                 note="Limited by available tubing volume above the gas and by allowable pressure rise.")
    vlube = c.out("Lube volume per cycle", f"{tcap}*{llen}", "bbl", fmt="0.00")
    dpcyc = c.out("Hydrostatic gain per cycle", f"0.052*{kwm}*{llen}", "psi", fmt="#,##0")
    ptarget = c.inp("Surface pressure to remove (target)", 1500, "psi", fmt="#,##0")
    c.out("Cycles required", f"ROUNDUP(ROUND({ptarget}/{dpcyc},6),0)", None, fmt="#,##0",
          note="Plus waiting time for fluid fall-through each cycle - plan several hours per cycle.")

    sb.section("Circulation Kills")

    c = sb.calc("Forward vs Reverse Circulation Volumes & Times",
                eq="forward: down tubing, up annulus;  reverse: down annulus, up tubing;  time = V / rate",
                note="Forward puts kill fluid at bottom after one tubing volume but takes the full annulus to "
                     "surface the gas at low friction. Reverse brings tubing contents up fast at higher "
                     "surface pressure on the annulus - check packer/casing limits before reversing.")
    cid = c.inp("Casing / liner ID", 6.184, "in", fmt="0.000")
    tod = c.inp("Tubing OD", 3.500, "in", fmt="0.000")
    acap = c.out("Annular capacity", f"({cid}^2-{tod}^2)/1029.4", "bbl/ft", fmt="0.00000")
    vann = c.out("Annulus volume", f"{acap}*{md}", "bbl", fmt="0.0")
    qc = c.inp("Circulating rate", 2.0, "bbl/min", fmt="0.00")
    c.out("Forward: kill fluid at bottom after", f"{vtub}/{qc}", None, fmt="#,##0.0",
          note="minutes (one tubing volume)")
    c.out("Forward: full circulation", f"({vtub}+{vann})/{qc}", None, fmt="#,##0.0",
          note="minutes (tubing + annulus)")
    c.out("Reverse: kill fluid at bottom after", f"{vann}/{qc}", None, fmt="#,##0.0",
          note="minutes (one annulus volume)")
    c.out("Reverse: tubing contents bottoms-up", f"{vtub}/{qc}", None, fmt="#,##0.0",
          note="minutes (one tubing volume)")

    sb.section("Volumetric Control")

    c = sb.calc("Volumetric Method During Gas Migration",
                eq="dP per bbl bled = 0.052 x MW / ann capacity;  bleed V = working range / (dP per bbl)",
                note="Static well with migrating gas and no pipe to bottom of the gas: let pressure build by "
                     "the safety margin + working range, then bleed the computed volume of FLUID (never gas) "
                     "holding casing pressure constant. Repeat; hydrostatic lost per bleed equals pressure "
                     "gained by migration. Same principle as drilling volumetric, tubing/annulus geometry.")
    mwa = c.inp("Fluid density in annulus/tubing", 8.6, "ppg")
    dpbbl = c.out("Pressure per bbl bled", f"0.052*{mwa}/{acap}", "psi/bbl", fmt="0.0")
    pmarg = c.inp("Safety margin", 100, "psi", fmt="#,##0")
    prange = c.inp("Working pressure range", 50, "psi", fmt="#,##0")
    c.out("Allow pressure to rise by (first step)", f"{pmarg}+{prange}", "psi", fmt="#,##0")
    c.out("Fluid to bleed per cycle", f"{prange}/{dpbbl}", "bbl", fmt="0.00",
          note="Bleed at constant surface pressure; then wait for the next pressure build of one working range.")
