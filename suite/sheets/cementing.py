"""Drilling: slurry yield and density, sacks and mix water, displacement, balanced plug, pressures."""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "Cementing", "drilling",
        "Cementing",
        "Slurry yield and density, sacks and mix water, displacement to bump, balanced plugs, hydrostatics and loads",
        description="Slurry yield/density, sack and water volumes, plug bump displacement, balanced plug, ECD, contact time",
    )

    sb.section("Slurry Properties")

    c = sb.calc("Slurry Yield & Water Requirement",
                eq="Yield [ft3/sk] = ( W_cmt/(SG_cmt x 8.34) + V_water + V_add ) / 7.48",
                note="Absolute volumes per sack: cement solids from weight and specific gravity, plus mix water "
                     "and liquid additives in gal/sk. 94-lb sack of neat Class G/H with 5.2 gal/sk shown.")
    wc = c.inp("Cement weight per sack", 94.0, None, fmt="0.0", note="lb/sk (94 lb standard sack).")
    sgc = c.inp("Cement specific gravity", 3.14, None, fmt="0.00")
    vw = c.inp("Mix water requirement", 5.2, "gal/sk", fmt="0.00")
    va = c.inp("Liquid additives", 0.0, "gal/sk", fmt="0.00")
    absc = c.out("Cement absolute volume", f"{wc}/({sgc}*8.34)", None, fmt="0.000", note="gal/sk.")
    c.out("Slurry yield", f"({absc}+{vw}+{va})/7.48", "ft3/sk", fmt="0.000")

    c = sb.calc("Slurry Density Check (Mass Balance)",
                eq="MW_slurry [ppg] = ( W_cmt + V_water x 8.34 + W_add ) / ( V_abs_cmt + V_water + V_add )",
                note="Total mass per sack divided by total absolute volume per sack. Neat 15.8 ppg Class G/H shown; "
                     "compare against the lab-designed density.")
    wc = c.inp("Cement weight per sack", 94.0, None, fmt="0.0", note="lb/sk.")
    sgc = c.inp("Cement specific gravity", 3.14, None, fmt="0.00")
    vw = c.inp("Mix water", 5.2, "gal/sk", fmt="0.00")
    va = c.inp("Liquid additives volume", 0.0, "gal/sk", fmt="0.00")
    wa = c.inp("Additives weight per sack", 0.0, None, fmt="0.00", note="lb/sk.")
    c.out("Slurry density",
          f"({wc}+{vw}*8.34+{wa})/({wc}/({sgc}*8.34)+{vw}+{va})", "ppg", fmt="0.00")

    sb.section("Primary Cementing Volumes")

    c = sb.calc("Sacks Required (Annulus + Shoe Track + Rathole)",
                eq="V [ft3] = [ (Dh^2 - OD^2) x L_ann x (1+xs) + Dh^2 x L_rat x (1+xs) + ID^2 x L_track ] "
                   "/ 1029.4 x 5.615;   Sacks = ROUNDUP( V / yield )",
                note="Open-hole excess applied to annulus and rathole only (caliper or 25-100% rule of thumb); "
                     "shoe track is inside casing, no excess.")
    dh = c.inp("Open hole diameter (Dh)", 12.25, "in", fmt="0.000")
    od = c.inp("Casing outside diameter (OD)", 9.625, "in", fmt="0.000")
    idc = c.inp("Casing inside diameter (ID)", 8.681, "in", fmt="0.000")
    lann = c.inp("Annulus length to cement", 2000, "ft", fmt="#,##0")
    lrat = c.inp("Rathole length below shoe", 30, "ft", fmt="#,##0")
    ltrk = c.inp("Shoe track length", 80, "ft", fmt="#,##0", note="Float shoe to float collar (typically 2 joints).")
    xs = c.inp("Open-hole excess", 0.25, None, fmt="0.00", note="Fraction (0.25 = 25%).")
    yld = c.inp("Slurry yield", 1.18, "ft3/sk", fmt="0.000")
    vtot = c.out("Total slurry volume",
                 f"(({dh}^2-{od}^2)*{lann}*(1+{xs})+{dh}^2*{lrat}*(1+{xs})+{idc}^2*{ltrk})/1029.4*5.615",
                 "ft3", fmt="#,##0")
    sk = c.out("Sacks required", f"ROUNDUP(ROUND({vtot}/{yld},6),0)", None, fmt="#,##0", note="Sacks (94 lb).")
    c.txt("", "Order extra sacks for surface losses and density adjustments (typically +10%).")

    c = sb.calc("Total Mix Water",
                eq="V_water [bbl] = sacks x water per sack [gal/sk] / 42")
    sk2 = c.inp("Sacks to mix", 750, None, fmt="#,##0", note="Sacks.")
    vw = c.inp("Water requirement", 5.2, "gal/sk", fmt="0.00")
    c.out("Mix water required", f"{sk2}*{vw}/42", "bbl", fmt="#,##0.0",
          note="Add contingency water for washup and rate changes.")

    c = sb.calc("Displacement Volume to Bump the Plug",
                eq="V_disp [bbl] = ID^2/1029.4 x (L_casing - L_track);   Strokes = ROUNDUP( V / pump output )",
                note="Displace until the top plug lands on the float collar; the shoe track stays full of cement.")
    idc = c.inp("Casing inside diameter (ID)", 8.681, "in", fmt="0.000")
    lcsg = c.inp("Casing setting depth (MD)", 6000, "ft", fmt="#,##0")
    ltrk = c.inp("Shoe track length", 80, "ft", fmt="#,##0")
    po = c.inp("Pump output", 0.0997, "bbl/stk", fmt="0.00000")
    vd = c.out("Displacement volume", f"{idc}^2/1029.4*({lcsg}-{ltrk})", "bbl", fmt="#,##0.0")
    c.out("Displacement strokes", f"ROUNDUP(ROUND({vd}/{po},6),0)", "stk", fmt="#,##0")

    c = sb.calc("Cement Contact Time",
                eq="CT [min] = V_slurry / pump rate",
                note="Time slurry flows past a point in the annulus (e.g. a zone to isolate); 10 min minimum "
                     "turbulent contact time is a common design target.")
    vsl = c.inp("Slurry volume pumped", 100, "bbl", fmt="#,##0.0")
    rate = c.inp("Pump rate", 5.0, "bbl/min", fmt="0.00")
    c.out("Contact time", f"{vsl}/{rate}", "min", fmt="0.0")

    sb.section("Balanced Cement Plug")

    c = sb.calc("Balanced Plug: Sacks, Heights, Spacer & Displacement",
                eq="V_slurry = L_plug x C_hole x 5.615 / yield [sacks];   H = V_slurry / (C_ann + C_pipe);   "
                   "V_behind = V_ahead x C_pipe / C_ann;   V_disp = C_pipe x (D_set - H) - V_behind",
                note="Stinger (drill pipe/tubing) run to plug base. Slurry stands at equal height H inside and "
                     "outside the stinger; spacer behind balances the spacer ahead so no U-tube on pull-out. "
                     "Pull slowly to just above the plug top and reverse circulate clean.")
    lplug = c.inp("Desired plug length (pipe out)", 500, "ft", fmt="#,##0")
    dh = c.inp("Hole (or casing ID) diameter", 8.5, "in", fmt="0.000")
    dp = c.inp("Stinger outside diameter", 5.0, "in", fmt="0.000")
    cp = c.inp("Stinger capacity", 0.01776, "bbl/ft", fmt="0.00000")
    dset = c.inp("Plug base setting depth (MD)", 8000, "ft", fmt="#,##0")
    yld = c.inp("Slurry yield", 1.18, "ft3/sk", fmt="0.000")
    vah = c.inp("Spacer ahead", 10.0, "bbl", fmt="0.0")
    chole = c.out("Hole capacity", f"{dh}^2/1029.4", "bbl/ft", fmt="0.00000")
    cann = c.out("Annular capacity (hole - stinger)", f"({dh}^2-{dp}^2)/1029.4", "bbl/ft", fmt="0.00000")
    vslu = c.out("Slurry volume", f"{lplug}*{chole}", "bbl", fmt="0.0")
    c.out("Sacks required", f"ROUNDUP(ROUND({vslu}*5.615/{yld},6),0)", None, fmt="#,##0", note="Sacks.")
    hh = c.out("Plug height with stinger in hole", f"{vslu}/({cann}+{cp})", "ft", fmt="#,##0")
    vbh = c.out("Spacer behind (balance)", f"{vah}*{cp}/{cann}", "bbl", fmt="0.00")
    c.out("Displacement mud volume", f"{cp}*({dset}-{hh})-{vbh}", "bbl", fmt="#,##0.0")
    c.out("Pull stinger to (depth)", f"{dset}-{hh}", "ft", fmt="#,##0",
          note="Top of slurry with pipe in hole; pull above this before circulating.")

    sb.section("Hydrostatics & Loads")

    c = sb.calc("Hydrostatic Pressure & ECD at Shoe (Multiple Columns)",
                eq="P = 0.052 x sum( MW_i x L_tvd_i );   EMW = P / (0.052 x TVD_shoe);   ECD = EMW + APL/(0.052 x TVD)",
                note="TVD lengths of mud, spacer, lead and tail in the annulus must sum to shoe TVD. "
                     "Check ECD against the fracture gradient at the shoe and weak zones.")
    m1 = c.inp("Mud density", 12.0, "ppg")
    l1 = c.inp("Mud column TVD length", 4000, "ft", fmt="#,##0")
    m2 = c.inp("Spacer density", 12.5, "ppg")
    l2 = c.inp("Spacer column TVD length", 1000, "ft", fmt="#,##0")
    m3 = c.inp("Lead slurry density", 13.5, "ppg")
    l3 = c.inp("Lead column TVD length", 4000, "ft", fmt="#,##0")
    m4 = c.inp("Tail slurry density", 15.8, "ppg")
    l4 = c.inp("Tail column TVD length", 1000, "ft", fmt="#,##0")
    apl = c.inp("Annular friction loss while pumping", 150, "psi", fmt="#,##0")
    ph = c.out("Hydrostatic pressure at shoe",
               f"0.052*({m1}*{l1}+{m2}*{l2}+{m3}*{l3}+{m4}*{l4})", "psi", fmt="#,##0")
    tvds = c.out("Shoe TVD (sum of columns)", f"{l1}+{l2}+{l3}+{l4}", "ft", fmt="#,##0")
    emw = c.out("Static equivalent mud weight at shoe", f"{ph}/(0.052*{tvds})", "ppg")
    c.out("ECD at shoe while pumping", f"{emw}+{apl}/(0.052*{tvds})", "ppg")

    c = sb.calc("Plug Bump: Differential, Force & Pressure Margin",
                eq="dP_float = P_bump + P_hyd_inside - P_hyd_annulus;   F = dP x PI()/4 x ID^2;   "
                   "Margin = burst rating x DF - P_bump",
                note="At bump the inside is full of displacement fluid, the annulus full of cement/spacer/mud - "
                     "the float carries the differential. Do not exceed the casing internal yield x design factor "
                     "at surface when bumping.")
    pb = c.inp("Surface bump pressure", 1200, "psi", fmt="#,##0",
               note="Final displacement pressure + 500 psi is a common bump target.")
    phi = c.inp("Hydrostatic inside casing", 6240, "psi", fmt="#,##0")
    pho = c.inp("Hydrostatic in annulus", 6776, "psi", fmt="#,##0")
    idc = c.inp("Casing inside diameter (ID)", 8.681, "in", fmt="0.000")
    br = c.inp("Casing internal yield (burst) rating", 6870, "psi", fmt="#,##0")
    df = c.inp("Burst design factor on bump", 0.80, None, fmt="0.00")
    dpf = c.out("Differential across float at bump", f"{pb}+{phi}-{pho}", "psi", fmt="#,##0")
    c.out("Axial force on casing/plug", f"{dpf}*PI()/4*{idc}^2", "lbf", fmt="#,##0")
    c.out("Surface pressure margin to rating", f"{br}*{df}-{pb}", "psi", fmt="#,##0")
