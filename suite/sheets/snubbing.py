"""Interventions: snubbing / hydraulic workover forces, buckling, pressure limits."""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "Snubbing & Hydraulic Workover", "interventions",
        "Snubbing & Hydraulic Workover",
        "Ejection force, pipe-light/pipe-heavy, snub force, buckling between guides, ram checks",
        description="Ejection force, balance point, snubbing force, jack SF, Euler buckling, shear ram check",
    )

    sb.section("Forces & Balance Point")

    c = sb.calc("Wellhead Ejection Force",
                eq="F_ej [lbf] = WHP x pi/4 x OD^2",
                note="Pressure acts on the full pipe OD area sealed at the stripper rams (closed-end pipe or "
                     "plugged/BPV string).")
    whp = c.inp("Wellhead pressure (WHP)", 3000, "psi", fmt="#,##0")
    od = c.inp("Pipe outside diameter (OD)", 2.875, "in", fmt="0.000")
    fej = c.out("Ejection force", f"{whp}*PI()/4*{od}^2", "lbf", fmt="#,##0")

    c = sb.calc("Pipe-Light / Pipe-Heavy & Balance Point",
                eq="W_buoyed = w x (1 - MW/65.5) x depth;  balance depth = (F_ej + F_fric) / (w x BF)",
                note="Below the balance depth the string weight exceeds the well's push and conventional "
                     "(pipe-heavy) handling applies.")
    wpf = c.inp("Pipe weight in air", 6.5, "lb/ft", fmt="0.00")
    mw = c.inp("Wellbore fluid density (MW)", 9.0, "ppg")
    depth = c.inp("Pipe depth in well", 1500, "ft", fmt="#,##0")
    bf = c.out("Buoyancy factor (BF)", f"1-{mw}/65.5", None, fmt="0.000")
    wbuoy = c.out("Buoyed string weight", f"{wpf}*{bf}*{depth}", "lbf", fmt="#,##0")
    ffr = c.inp("Stripper / ram friction", 2000, "lbf", fmt="#,##0",
                note="From ram/stripper energization; re-check whenever sealing pressure is changed.")
    c.out("Balance point depth (incl. friction)", f"({fej}+{ffr})/({wpf}*{bf})", "ft", fmt="#,##0")
    c.out("String state", f'IF({wbuoy}>{fej}+{ffr},"PIPE HEAVY","PIPE LIGHT - snub required")', None, fmt="@")

    c = sb.calc("Snubbing Force Required",
                eq="F_snub = MAX(0, F_ej + F_fric - W_buoyed)")
    fsnub = c.out("Snubbing force required", f"MAX(0,{fej}+{ffr}-{wbuoy})", "lbf", fmt="#,##0")

    c = sb.calc("Jack Capacity Check",
                eq="SF = jack snub capacity / F_snub",
                note="Check both snub and lift ratings of the unit; travelling slips must also be rated for "
                     "the pipe size at this load.")
    jack = c.inp("Jack snub capacity", 170, "klbf", fmt="#,##0")
    sfreq = c.inp("Required safety factor", 1.50, None, fmt="0.00")
    sfact = c.out("Actual safety factor", f"{jack}*1000/MAX({fsnub},1)", None, fmt="0.00",
                  note="MAX(...,1) guards divide-by-zero when the string is pipe heavy.")
    c.out("Capacity check",
          f'IF({fsnub}=0,"PIPE HEAVY - no snub force needed",'
          f'IF({sfact}>={sfreq},"OK","JACK CAPACITY INSUFFICIENT"))',
          None, fmt="@")

    sb.section("Equalizing & BOP Volumes")

    c = sb.calc("Volume Between BOP Rams (Equalizing)",
                eq="V [bbl] = ID^2 / 1029.4 x L;  gal = bbl x 42",
                note="Volume to pressurize/bleed when equalizing across rams while staging pipe in or out.")
    sid = c.inp("Spool / BOP bore ID", 7.063, "in", fmt="0.000")
    sl = c.inp("Length between rams", 8.0, "ft", fmt="0.00")
    vbop = c.out("Volume between rams", f"{sid}^2/1029.4*{sl}", "bbl", fmt="0.000")
    c.out("Volume between rams", f"{vbop}*42", "gal", fmt="0.0")

    sb.section("Buckling Between Guides")

    c = sb.calc("Euler Critical Buckling Load (Guided Pipe)",
                eq="F_cr = pi^2 x E x I / (L_g x 12)^2;  I = pi/64 x (OD^4 - ID^4);  E = 30e6 psi",
                note="Pinned-pinned Euler column between guides / window openings - the classic snubbing "
                     "check for the unsupported interval between stationary slips and stripper. Shorten guide "
                     "spacing if the check fails; unguided pipe above the BOP buckles at far lower load.")
    pid = c.inp("Pipe inside diameter (ID)", 2.441, "in", fmt="0.000")
    lg = c.inp("Guide spacing (unsupported length, L_g)", 4.0, "ft", fmt="0.00")
    imom = c.out("Moment of inertia (I)", f"PI()/64*({od}^4-{pid}^4)", "in4",
                 si=("cm4", 41.62314), fmt="0.000")
    fcr = c.out("Critical buckling load (F_cr)", f"PI()^2*30000000*{imom}/({lg}*12)^2", "lbf", fmt="#,##0")
    sfb = c.inp("Required buckling safety factor", 2.00, None, fmt="0.00")
    c.out("Buckling check",
          f'IF({fsnub}*{sfb}<={fcr},"OK","BUCKLING RISK - shorten guide spacing or reduce snub force")',
          None, fmt="@")

    sb.section("Pressure & Ram Limits")

    c = sb.calc("Maximum WHP for Chosen Pipe",
                eq="WHP_max = MIN(burst rating, collapse rating) / SF",
                note="Simplified screen: worst case assumes full WHP as differential either way (empty or "
                     "plugged pipe). Use the tubular design sheet for combined-load checks.")
    brate = c.inp("Pipe burst rating", 10570, "psi", fmt="#,##0")
    crate = c.inp("Pipe collapse rating", 11160, "psi", fmt="#,##0")
    sfp = c.inp("Design safety factor", 1.25, None, fmt="0.00")
    whpmax = c.out("Maximum allowable WHP", f"MIN({brate},{crate})/{sfp}", "psi", fmt="#,##0")
    c.out("Current WHP check", f'IF({whp}<={whpmax},"OK","WHP EXCEEDS PIPE RATING / SF")', None, fmt="@")

    c = sb.calc("Shear Ram Capability Check",
                eq="F_shear ~ 0.577 x Yp x A_steel  (von Mises shear, approximate)",
                note="Rough screen only - actual shear force depends on ram blade design and WHP assist. "
                     "Always confirm against the manufacturer shear tables for this pipe at actual WHP.")
    yp = c.inp("Pipe yield strength (Yp)", 80000, "psi", fmt="#,##0")
    ash = c.out("Steel cross-section area", f"PI()/4*({od}^2-{pid}^2)", "in2", fmt="0.000")
    fsh = c.out("Estimated force to shear pipe", f"0.577*{yp}*{ash}", "lbf", fmt="#,##0")
    ram = c.inp("Shear ram shearing capacity", 250000, "lbf", fmt="#,##0")
    c.out("Shear check",
          f'IF({ram}>={fsh},"OK - rams should shear this pipe","VERIFY - rams may not shear, check tables")',
          None, fmt="@")
