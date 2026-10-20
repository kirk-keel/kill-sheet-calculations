"""Drilling: buoyancy, string weight, overpull, collar length, stretch, slip crush, critical RPM, ton-miles."""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "Drill String & Tension", "drilling",
        "Drill String Weight, Tension & Vibration",
        "Buoyancy, hook load, margin of overpull, collar length for WOB, stretch, slip crush, critical RPM, ton-miles",
        description="Buoyancy factor, hook load, MOP, DC length, pipe stretch, slip crush, critical RPM, ton-miles",
    )

    sb.section("Buoyancy & String Weight")

    c = sb.calc("Buoyancy Factor",
                eq="BF = (65.5 - MW) / 65.5",
                note="65.5 ppg = density of steel. Multiply air weights by BF to get buoyed weight in mud.")
    mw = c.inp("Mud weight (MW)", 12.5, "ppg")
    c.out("Buoyancy factor (BF)", f"(65.5-{mw})/65.5", None, fmt="0.0000")

    c = sb.calc("Buoyed String Weight (Hook Load)",
                eq="W_buoyed = (L_dp x W_dp + L_dc x W_dc) x BF",
                note="Air weights per foot include tool joints (use 'approximate weight' from pipe tables). "
                     "Add HWDP as a third term if run.")
    ldp = c.inp("Drill pipe length", 9400, "ft", fmt="#,##0")
    wdp = c.inp("Drill pipe weight (incl. tool joints)", 20.89, "lb/ft")
    ldc = c.inp("Drill collar length", 600, "ft", fmt="#,##0")
    wdc = c.inp("Drill collar weight", 92.0, "lb/ft", note="6-1/2 in x 2-13/16 in collars.")
    mw = c.inp("Mud weight (MW)", 12.5, "ppg")
    bf = c.out("Buoyancy factor (BF)", f"(65.5-{mw})/65.5", None, fmt="0.0000")
    hkld = c.out("Buoyed string weight", f"({ldp}*{wdp}+{ldc}*{wdc})*{bf}", "lbf", fmt="#,##0")

    sb.section("Tension, Overpull & Slips")

    c = sb.calc("Maximum Allowable Pull & Margin of Overpull",
                eq="Max pull = T_yield x DF;   MOP = Max pull - buoyed hook load;   SF = T_yield / hook load",
                note="T_yield = pipe body tensile yield for the weakest (usually top) joint and wear class. "
                     "DF of 0.90 on new pipe is common; use premium-class ratings for worn pipe. "
                     "Hook load defaults to the buoyed string weight computed above.")
    ty = c.inp("Pipe body tensile yield", 553830, "lbf", fmt="#,##0",
               note="5 in 19.5 lb/ft G-105, new.")
    df = c.inp("Tension design factor (DF)", 0.90, None, fmt="0.00")
    hl = c.inp("Hook load (buoyed)", 203400, "lbf", fmt="#,##0")
    mp = c.out("Maximum allowable pull", f"{ty}*{df}", "lbf", fmt="#,##0")
    c.out("Margin of overpull (MOP)", f"{mp}-{hl}", "lbf", fmt="#,##0",
          note="Keep at least 50,000-100,000 lbf for stuck-pipe contingency.")
    c.out("Safety factor in tension", f"{ty}/{hl}", None, fmt="0.00")

    c = sb.calc("Drill Collar Length for Desired WOB",
                eq="L_dc [ft] = WOB x SF / (W_dc x BF x COS(angle))",
                note="Keeps the neutral point inside the collars (drill pipe never in compression). "
                     "SF 1.10-1.20 places the neutral point 10-20% below the top of the collars.")
    wob = c.inp("Desired weight on bit (WOB)", 45000, "lbf", fmt="#,##0")
    sf = c.inp("Safety factor (SF)", 1.15, None, fmt="0.00")
    wdc = c.inp("Drill collar weight", 92.0, "lb/ft")
    mw = c.inp("Mud weight (MW)", 12.5, "ppg")
    ang = c.inp("Hole inclination", 10.0, "deg", fmt="0.0")
    c.out("Drill collar length required",
          f"{wob}*{sf}/({wdc}*(65.5-{mw})/65.5*COS(RADIANS({ang})))", "ft", fmt="#,##0")

    c = sb.calc("Slip Crush Ratio",
                eq="SH/SA = SQRT( 1 + D x K/(2 x Ls) + (D x K/(2 x Ls))^2 );   Max static load = T_yield / (SH/SA)",
                note="Reinhold-Spiri (API RP 7G) hoop-to-axial stress ratio. K = lateral load factor "
                     "(~4.0 for 9 deg 27.5 min taper, friction 0.08); Ls = slip contact length. "
                     "Hook loads above the max static load risk crushing the pipe in the slips.")
    d = c.inp("Pipe outside diameter (D)", 5.0, "in", fmt="0.000")
    k = c.inp("Lateral load factor (K)", 4.0, None, fmt="0.00")
    ls = c.inp("Slip contact length (Ls)", 16.0, "in", fmt="0.0")
    ty = c.inp("Pipe body tensile yield", 553830, "lbf", fmt="#,##0")
    ratio = c.out("Slip crush ratio (SH/SA)",
                  f"SQRT(1+{d}*{k}/(2*{ls})+({d}*{k}/(2*{ls}))^2)", None, fmt="0.000")
    c.out("Max static hook load in slips", f"{ty}/{ratio}", "lbf", fmt="#,##0")

    sb.section("Stretch")

    c = sb.calc("Drill Pipe Stretch Under Pull",
                eq="e [in] = P x L x 12 / (A x E),   A = PI()/4 x (OD^2 - ID^2),   E = 29.6e6 psi",
                note="Elastic stretch of the free (unstuck) length under an applied pull P. Also used inverted "
                     "to find stuck point: L_free = e x A x E / (12 x P).")
    p = c.inp("Applied pull (P)", 50000, "lbf", fmt="#,##0",
              note="Differential pull above the string's own hanging weight.")
    l = c.inp("Free pipe length (L)", 10000, "ft", fmt="#,##0")
    od = c.inp("Pipe outside diameter (OD)", 5.0, "in", fmt="0.000")
    idp = c.inp("Pipe inside diameter (ID)", 4.276, "in", fmt="0.000")
    a = c.out("Pipe wall cross-section area (A)", f"PI()/4*({od}^2-{idp}^2)", "in2", fmt="0.000")
    c.out("Stretch", f"{p}*{l}*12/({a}*29600000)", "in", fmt="0.0")

    c = sb.calc("Stretch Due to Own Weight (Free-Hanging)",
                eq="e [in] = 12 x w x L^2 x BF / (2 x A x E)",
                note="Average tension over the string is half the hanging weight, hence the factor 2. "
                     "w = air weight per foot; buoyancy applied through BF.")
    w = c.inp("Pipe weight in air", 19.5, "lb/ft")
    l = c.inp("String length (L)", 10000, "ft", fmt="#,##0")
    mw = c.inp("Mud weight (MW)", 12.5, "ppg")
    a = c.inp("Pipe wall cross-section area (A)", 5.275, "in2", fmt="0.000")
    c.out("Stretch due to own weight",
          f"12*{w}*{l}^2*(65.5-{mw})/65.5/(2*{a}*29600000)", "in", fmt="0.0")

    sb.section("Vibration & Ton-Miles")

    c = sb.calc("Critical Rotary Speed (Transverse, One Joint)",
                eq="RPM_crit = 33055 x SQRT(OD^2 + ID^2) / L^2   (L = joint length in ft)",
                note="Lubinski-style field formula for the first transverse (lateral) mode of one joint between "
                     "tool joints; equivalent to 4.76e6 x SQRT(OD^2+ID^2)/L^2 with L in inches. Avoid running "
                     "within about +/-15% of the critical speed; axial and higher modes also exist, so treat as "
                     "a screening value only.")
    od = c.inp("Pipe outside diameter (OD)", 5.0, "in", fmt="0.000")
    idp = c.inp("Pipe inside diameter (ID)", 4.276, "in", fmt="0.000")
    lj = c.inp("Joint length (L)", 31.0, "ft", fmt="0.0", note="Range 2 joint ~31 ft.")
    c.out("Critical rotary speed", f"33055*SQRT({od}^2+{idp}^2)/{lj}^2", "RPM", fmt="#,##0")

    c = sb.calc("Ton-Miles for a Round Trip",
                eq="T_rt = W_p x D x (L_s + D) / 10560000 + D x (M + C/2) / 2640000",
                note="Standard drilling-line service formula. W_p = buoyed drill pipe weight per foot, D = depth, "
                     "L_s = stand length, M = traveling block+hook weight, C = buoyed excess collar (and HWDP) "
                     "weight over the same length of drill pipe. Drilling/coring/short trips are counted as "
                     "multiples of round-trip ton-miles per the standard schedule.")
    wdp = c.inp("Drill pipe weight (incl. tool joints)", 20.89, "lb/ft")
    mw = c.inp("Mud weight (MW)", 12.5, "ppg")
    d = c.inp("Trip depth (D)", 10000, "ft", fmt="#,##0")
    lstand = c.inp("Stand length (Ls)", 93, "ft", fmt="0.0")
    m = c.inp("Traveling block + hook weight (M)", 100000, "lbf", fmt="#,##0")
    ldc = c.inp("Drill collar length", 600, "ft", fmt="#,##0")
    wdc = c.inp("Drill collar weight", 92.0, "lb/ft")
    bf = c.out("Buoyancy factor (BF)", f"(65.5-{mw})/65.5", None, fmt="0.0000")
    wp = c.out("Buoyed drill pipe weight", f"{wdp}*{bf}", "lb/ft", fmt="0.00")
    cx = c.out("Buoyed excess collar weight (C)", f"({wdc}-{wdp})*{ldc}*{bf}", "lbf", fmt="#,##0")
    c.out("Round-trip ton-miles",
          f"{wp}*{d}*({lstand}+{d})/10560000+{d}*({m}+{cx}/2)/2640000",
          None, fmt="#,##0", si=("tonne-km", 1.459972), note="US ton-miles (2000 lb x 5280 ft).")
