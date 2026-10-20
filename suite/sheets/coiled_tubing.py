"""Interventions: coiled tubing capacities, weights, forces, pressure limits, N2."""
from ..builder import SheetBuilder
from ..convert import TEMP_F


def build(wb):
    sb = SheetBuilder(
        wb, "Coiled Tubing", "interventions",
        "Coiled Tubing Operations",
        "CT capacities, buoyed weight, ejection force, pull limits, cleanout hydraulics, nitrogen",
        description="CT volumes, pipe-light check, pull to yield, burst/collapse, annular velocity, N2 displacement",
    )

    sb.section("CT Geometry & Capacities")

    c = sb.calc("CT Capacity & Displacement",
                eq="ID = OD - 2 x t;  Cap [bbl/ft] = ID^2 / 1029.4;  Disp closed-end [bbl/ft] = OD^2 / 1029.4")
    od = c.inp("CT outside diameter (OD)", 2.000, "in", fmt="0.000")
    t = c.inp("CT wall thickness (t)", 0.156, "in", fmt="0.000",
              note="Single-wall value; tapered strings have several wall sections - use heaviest for limits.")
    ctid = c.out("CT inside diameter (ID)", f"{od}-2*{t}", "in", fmt="0.000")
    cap = c.out("Internal capacity", f"{ctid}^2/1029.4", "bbl/ft", fmt="0.00000")
    c.out("Closed-end displacement", f"{od}^2/1029.4", "bbl/ft", fmt="0.00000")
    c.out("Steel displacement (open-end)", f"({od}^2-{ctid}^2)/1029.4", "bbl/ft", fmt="0.00000")

    c = sb.calc("Reel & Wellbore Volumes",
                eq="V = capacity [bbl/ft] x length [ft]")
    lreel = c.inp("Total CT length on reel", 15000, "ft", fmt="#,##0")
    depth = c.inp("CT depth in well (MD)", 10000, "ft", fmt="#,##0")
    cid = c.inp("Completion / tubing ID", 4.892, "in", fmt="0.000")
    vct = c.out("CT internal volume (full reel)", f"{cap}*{lreel}", "bbl", fmt="0.0")
    vinhole = c.out("CT internal volume (surface to depth)", f"{cap}*{depth}", "bbl", fmt="0.0")
    vann = c.out("CT x completion annulus volume", f"({cid}^2-{od}^2)/1029.4*{depth}", "bbl", fmt="0.0")
    c.out("Completion volume (no CT in hole)", f"{cid}^2/1029.4*{depth}", "bbl", fmt="0.0")

    sb.section("Pumping & Circulation")

    c = sb.calc("Fill & Circulation Times at Pump Rate",
                eq="time [min] = volume [bbl] / rate [bbl/min]")
    q = c.inp("Pump rate", 1.0, "bbl/min")
    c.out("Fill full reel", f"{vct}/{q}", None, fmt="#,##0.0", note="minutes")
    c.out("Displace CT to end (surface to depth)", f"{vinhole}/{q}", None, fmt="#,##0.0", note="minutes")
    c.out("Annulus bottoms-up", f"{vann}/{q}", None, fmt="#,##0.0", note="minutes")
    c.out("Full circulation (down CT, up annulus)", f"({vinhole}+{vann})/{q}", None, fmt="#,##0.0",
          note="minutes; conventional circulation path")

    sb.section("Weights & Forces")

    c = sb.calc("CT Weight per Foot & Hanging Weight",
                eq="w [lb/ft] = 10.68 x (OD - t) x t;  BF = 1 - MW/65.5;  W_hang = w x BF x depth",
                note="Line-pipe plain-end weight formula (approx 3.4 lb/ft per in2 of steel). Approximate for "
                     "tapered CT strings - use the manufacturer string report for the real string.")
    mw = c.inp("Wellbore fluid density (MW)", 9.0, "ppg")
    wair = c.out("CT weight per ft in air", f"10.68*({od}-{t})*{t}", "lb/ft", fmt="0.000")
    bf = c.out("Buoyancy factor (BF)", f"1-{mw}/65.5", None, fmt="0.000",
               note="Steel in fluid, same fluid inside and outside the CT.")
    wbuoy = c.out("Buoyed weight per ft", f"{wair}*{bf}", "lb/ft", fmt="0.000")
    whang = c.out("Buoyed hanging weight at depth", f"{wbuoy}*{depth}", "lbf", fmt="#,##0")

    c = sb.calc("Wellhead Ejection Force & Pipe-Light Depth",
                eq="F_ej [lbf] = WHP x pi/4 x OD^2;  balance depth [ft] = (F_ej + F_strip) / (w x BF)",
                note="Above the balance depth the well pushes the CT out (pipe light) and the injector must snub.")
    whp = c.inp("Wellhead pressure (WHP)", 2500, "psi", fmt="#,##0")
    fstrip = c.inp("Stripper / pack-off friction", 500, "lbf", fmt="#,##0",
                   note="From stripper energization pressure; varies during the job.")
    fej = c.out("Ejection force on CT", f"{whp}*PI()/4*{od}^2", "lbf", fmt="#,##0")
    c.out("Pipe-light balance depth", f"({fej}+{fstrip})/{wbuoy}", "ft", fmt="#,##0")
    c.out("State at current depth",
          f'IF({whang}>{fej}+{fstrip},"PIPE HEAVY","PIPE LIGHT - snubbing force required")',
          None, fmt="@")

    c = sb.calc("Pull to Yield & Working Pull",
                eq="A_steel = pi/4 x (OD^2 - ID^2);  F_yield = Yp x A_steel;  F_work = 0.8 x F_yield")
    yp = c.inp("Tube yield strength (Yp)", 80000, "psi", fmt="#,##0",
               note="CT grades: 70, 80, 90, 100, 110 ksi.")
    asteel = c.out("Steel cross-section area", f"PI()/4*({od}^2-{ctid}^2)", "in2", fmt="0.000")
    fy = c.out("Pull to yield", f"{yp}*{asteel}", "lbf", fmt="#,##0")
    c.out("Working pull limit (80% of yield)", f"0.8*{fy}", "lbf", fmt="#,##0",
          note="New pipe. Derate further for fatigue-cycled CT, welds, and ovality per string report.")

    sb.section("Pressure Limits")

    c = sb.calc("Burst & Collapse Differential Check",
                eq="dP_burst = P_int - P_ext;  dP_collapse = P_ext - P_int;  require dP x SF <= rating",
                note="Ratings are manufacturer differential-pressure ratings for the current wall/fatigue state.")
    brate = c.inp("Burst rating (differential)", 10000, "psi", fmt="#,##0")
    crate = c.inp("Collapse rating (differential)", 9000, "psi", fmt="#,##0")
    pint = c.inp("Internal pressure at point of interest", 5000, "psi", fmt="#,##0")
    pext = c.inp("External pressure at same point", 3000, "psi", fmt="#,##0")
    sf = c.inp("Required safety factor", 1.25, None, fmt="0.00")
    dpb = c.out("Burst differential (P_int - P_ext)", f"{pint}-{pext}", "psi", fmt="#,##0")
    dpc = c.out("Collapse differential (P_ext - P_int)", f"{pext}-{pint}", "psi", fmt="#,##0")
    c.out("Burst check", f'IF(MAX(0,{dpb})*{sf}<={brate},"OK","EXCEEDS BURST RATING / SF")', None, fmt="@")
    c.out("Collapse check", f'IF(MAX(0,{dpc})*{sf}<={crate},"OK","EXCEEDS COLLAPSE RATING / SF")', None, fmt="@")

    sb.section("Cleanout Hydraulics")

    c = sb.calc("Annular Velocity in Completion",
                eq="AV [ft/min] = 24.5 x Q [gpm] / (D_id^2 - OD_ct^2)")
    qg = c.inp("Pump rate", 42, "gpm", fmt="#,##0", note="42 gpm = 1.0 bbl/min")
    av = c.out("Annular velocity", f"24.5*{qg}/({cid}^2-{od}^2)", "ft/min", fmt="#,##0")
    avmin = c.inp("Minimum AV for solids transport", 100, "ft/min", fmt="#,##0",
                  note="Rule of thumb: 100-150 ft/min vertical; substantially higher (or wiper trips / gel "
                       "sweeps) in deviated hole. Check with a solids-transport model for horizontal wells.")
    c.out("Solids transport check", f'IF({av}>={avmin},"OK","AV TOO LOW - raise rate or stage the cleanout")',
          None, fmt="@")

    sb.section("Nitrogen")

    c = sb.calc("N2 to Displace CT + Well to Gas",
                eq="V_N2 [scf] = V_liq [bbl] x 5.615 x (P_avg / 14.7) x (520 / (T_avg + 460)) / z",
                note="Real-gas estimate at average column pressure and temperature. For design, run a staged "
                     "N2 simulation; add 10-20% surface losses.")
    vdisp = c.out("Volume to displace (CT in hole + annulus)", f"{vinhole}+{vann}", "bbl", fmt="0.0")
    pavg = c.inp("Average column pressure (P_avg, absolute)", 1500, "psi", fmt="#,##0")
    tavg = c.inp("Average column temperature (T_avg)", 120, "degF", si=TEMP_F, fmt="#,##0")
    z = c.inp("Gas deviation factor (z)", 0.98, None, fmt="0.000",
              note="N2 z-factor near 1.0 at moderate pressure; from N2 tables at P_avg, T_avg.")
    c.out("N2 required", f"{vdisp}*5.615*({pavg}/14.7)*(520/({tavg}+460))/{z}", "scf", fmt="#,##0")

    c = sb.calc("Field Notes")
    c.txt("Maximum setdown / snubbing force",
          "Setdown and snub force are limited by helical buckling and lockup in the completion, not by the "
          "injector rating alone - run a tubing-forces model for the actual well path and clearances.")

    sb.section("Swab & Surge - CT Running")

    c = sb.calc("CT Surge/Swab in Completion (closed-ended, Bingham)",
                eq="Ve = V x (0.45 + Dp^2/(Dc^2-Dp^2));  "
                   "dP = L x PV x Ve/(60000 x (Dc-Dp)^2) + L x YP/(200 x (Dc-Dp));  "
                   "Dp = CT OD, Dc = completion ID",
                note="CT has check valves, so treat as closed-ended (Burkhardt clinging constant 0.45, "
                     "laminar Bingham approximation). While circulating, add annular friction from the "
                     "Hydraulics sheet.")
    dcsw = c.inp("Completion ID (Dc)", 4.892, "in", fmt="0.000")
    dpsw = c.inp("CT OD (Dp)", 2.0, "in", fmt="0.000")
    vsw = c.inp("Run speed", 100, "ft/min", fmt="#,##0")
    pvsw = c.inp("Fluid plastic viscosity (PV)", 10, "cP", si=("mPa-s", 1.0), fmt="#,##0")
    ypsw = c.inp("Fluid yield point (YP)", 8, None, fmt="#,##0",
                 note="lb/100ft2 (no SI mirror; 1 lb/100ft2 = 0.4788 Pa)")
    lsw = c.inp("Length below nozzle (L)", 10000, "ft", fmt="#,##0")
    mwsw = c.inp("Fluid density (MW)", 8.6, "ppg")
    tvdsw = c.inp("TVD", 9500, "ft", fmt="#,##0")
    vesw = c.out("Effective velocity (Ve)", f"{vsw}*(0.45+{dpsw}^2/({dcsw}^2-{dpsw}^2))",
                 "ft/min", fmt="#,##0")
    dpct = c.out("Surge/swab pressure (dP)",
                 f"{lsw}*{pvsw}*{vesw}/(60000*({dcsw}-{dpsw})^2)+{lsw}*{ypsw}/(200*({dcsw}-{dpsw}))",
                 "psi", fmt="#,##0")
    c.out("Surge EMW (running in)", f"{mwsw}+{dpct}/(0.052*{tvdsw})", "ppg", fmt="0.00",
          note="Keep below frac / loss-limit EMW.")
    c.out("Swab EMW (pulling out)", f"{mwsw}-{dpct}/(0.052*{tvdsw})", "ppg", fmt="0.00",
          note="Keep above pore / kick-margin EMW.")
