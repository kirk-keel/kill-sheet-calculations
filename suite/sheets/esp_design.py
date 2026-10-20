"""Completions: ESP design - intake conditions, free gas, TDH, stages and power.

Rate & Intake works forward from the linked reservoir pressure and PI to pump
intake pressure at the desired rate. Gas at Intake screens free-gas fraction on
a simplified per-STB basis. Total Dynamic Head uses a rounded design PIP
(yellow override - the computed PIP above stays live for comparison), then
Stages & Power sizes the pump and motor from catalog per-stage figures.
"""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "ESP Design", "completions",
        "Electric Submersible Pump Design",
        "Intake pressure and free gas at the desired rate; total dynamic head, "
        "stage count, motor sizing and surface electrical loads",
        description="ESP sizing: PIP and free gas at intake, TDH, stages, motor "
                    "HP/kW, surface voltage, current and kVA",
    )

    sb.section("Rate & Intake")

    c = sb.calc("Flowing BHP & Pump Intake Pressure",
                eq="Pwf = Pres - Q/J;   grad = 0.433 x SG_comp;   "
                   "PIP = Pwf - grad x (perf TVD - pump TVD)",
                note="Straight-line PI inflow. Composite SG mixes water and oil "
                     "by water cut; the fluid between the perfs and the pump "
                     "intake is assumed at the composite gradient.")
    pres = c.link("Reservoir pressure (Pres)", "WD_ResP", "psi", fmt="#,##0")
    perf = c.link("Perforation TVD", "WD_PerfTVD", "ft", fmt="#,##0")
    q = c.inp("Desired rate (Q)", 1500, None, fmt="#,##0", note="bpd (gross liquid).")
    j = c.inp("Productivity index (J)", 1.2, None, fmt="0.00", note="bpd/psi.")
    dset = c.inp("Pump setting depth (TVD)", 5400, "ft", fmt="#,##0")
    wc = c.inp("Water cut", 60, None, fmt="0.0",
               note="Percent - formulas divide by 100.")
    api = c.inp("Oil gravity", 32, None, fmt="0.0", note="degrees API.")
    sgw = c.inp("Water specific gravity (SGw)", 1.05, None, fmt="0.000")
    pwf = c.out("Flowing BHP at desired rate (Pwf)", f"{pres}-{q}/{j}",
                "psi", fmt="#,##0")
    sgo = c.out("Oil specific gravity (SGo)", f"141.5/(131.5+{api})",
                None, fmt="0.000", note="SGo = 141.5 / (131.5 + API)")
    sgc = c.out("Composite fluid SG",
                f"{wc}/100*{sgw}+(1-{wc}/100)*{sgo}",
                None, fmt="0.000",
                note="SG_comp = WC x SGw + (1 - WC) x SGo, WC as a fraction "
                     "(input is percent, /100 in the formula).")
    grad = c.out("Fluid gradient", f"0.433*{sgc}", "psi/ft", fmt="0.0000")
    pip = c.out("Pump intake pressure (PIP)",
                f"{pwf}-{grad}*({perf}-{dset})", "psi", fmt="#,##0")
    c.out("Intake status",
          f'IF({pip}>=250,"OK - adequate submergence",'
          f'IF({pip}>=100,"MARGINAL - low intake pressure",'
          f'"CHECK: pump-off risk - lower pump or cut rate"))',
          None, fmt="@")

    sb.section("Gas at Intake")

    c = sb.calc("Free Gas Fraction at Intake",
                eq="free GOR = GOR - Rs;   Vgas = freeGOR x (1-WC) x Bg;   "
                   "free gas % = 100 x Vgas / (Vgas + 1.0)",
                note="Simplified per-STB basis: free gas volume at intake per "
                     "stock-tank barrel of liquid, liquid shrinkage ignored "
                     "(Vliq taken as 1.0 bbl/STB). Rs and Bg at PIP from PVT "
                     "data or Standing correlation. Rule of thumb: standard "
                     "pumps to ~10% free gas, rotary separator to ~20%.")
    gor = c.inp("Producing GOR", 300, "scf/bbl", fmt="#,##0",
                note="scf/STB total producing gas-oil ratio.")
    rs = c.inp("Solution GOR at PIP (Rs)", 120, "scf/bbl", fmt="#,##0",
               note="scf/STB still in solution at PIP - from PVT report or "
                    "Standing correlation.")
    bg = c.inp("Gas formation volume factor at PIP (Bg)", 0.008, None,
               fmt="0.0000", note="bbl/scf at pump intake pressure and temperature.")
    eff = c.inp("Gas separator efficiency", 0.7, None, fmt="0.00",
                note="Fraction of free gas diverted to the annulus (0 = none).")
    fgor = c.out("Free GOR at intake", f"{gor}-{rs}", "scf/bbl", fmt="#,##0",
                 note="scf/STB of free (undissolved) gas at PIP.")
    vgas = c.out("Free gas volume at intake (Vgas)",
                 f"{fgor}*(1-{wc}/100)*{bg}", None, fmt="0.000",
                 note="bbl per STB of liquid (gas evolves from the oil "
                      "fraction only).")
    fg = c.out("Free gas fraction at intake",
               f"100*{vgas}/({vgas}+1)", None, fmt="0.0",
               note="Percent by volume entering the intake before separation.")
    fga = c.out("Free gas into pump after separator",
                f"{fg}*(1-{eff})", None, fmt="0.0", note="Percent.")
    c.out("Gas status",
          f'IF({fga}<10,"OK - gas manageable",'
          f'IF({fga}<20,"MARGINAL - rotary separator recommended",'
          f'"CHECK: EXCEEDS 20% free gas - gas handler/AGH required"))',
          None, fmt="@")

    sb.section("Total Dynamic Head")

    c = sb.calc("Total Dynamic Head (TDH)",
                eq="TDH = (pump depth - PIP x 2.31/SG) + f x depth/1000 + "
                   "THP x 2.31/SG",
                note="Design block uses a rounded design PIP (yellow override) "
                     "so the head calc is stable while inflow inputs are "
                     "tuned - the computed PIP above is the live value. "
                     "2.31 ft of fresh-water head per psi, divided by SG.")
    dpip = c.inp("PIP for design (override)", 900, "psi", fmt="#,##0",
                 note="Rounded design intake pressure - compare with the "
                      "computed PIP above.")
    dsg = c.inp("Composite SG for design", 1.02, None, fmt="0.000")
    thp = c.inp("Tubing head pressure (THP)", 150, "psi", fmt="#,##0")
    fric = c.inp("Tubing friction head", 20, None, fmt="0.0",
                 note="ft per 1000 ft of tubing - from friction charts for "
                      "the tubing size and rate.")
    fop = c.out("Fluid over pump", f"{dpip}*2.31/{dsg}", "ft", fmt="#,##0.0",
                note="Head equivalent of the design PIP.")
    lift = c.out("Net vertical lift", f"{dset}-{fop}", "ft", fmt="#,##0.0",
                 note="Pump depth minus fluid over pump (dynamic fluid level).")
    thph = c.out("THP head", f"{thp}*2.31/{dsg}", "ft", fmt="#,##0.0")
    tfr = c.out("Tubing friction", f"{fric}*{dset}/1000", "ft", fmt="#,##0.0")
    tdh = c.out("Total dynamic head (TDH)", f"{lift}+{tfr}+{thph}",
                "ft", fmt="#,##0.0")

    sb.section("Stages & Power")

    c = sb.calc("Stage Count & Motor Sizing",
                eq="stages = ROUNDUP(TDH / head-per-stage);   "
                   "BHP = stages x BHP/stage x SG;   HP = ROUNDUP(BHP x SF)",
                note="Head and BHP per stage from the catalog curve at the "
                     "best-efficiency point for the design rate. Catalog BHP "
                     "is on water - multiply by SG for the pumped fluid.")
    hps = c.inp("Head per stage (catalog, at BEP)", 25, "ft", fmt="0.0")
    bhps = c.inp("BHP per stage (catalog, water)", 0.35, "hp", fmt="0.000")
    sf = c.inp("Motor safety factor", 1.15, None, fmt="0.00")
    vmot = c.inp("Motor voltage", 2300, None, fmt="#,##0", note="Volts, nameplate.")
    pf = c.inp("Motor power factor", 0.85, None, fmt="0.00")
    vdrop = c.inp("Cable voltage drop", 12, None, fmt="0.0",
                  note="Volts per 1000 ft of cable at motor amps.")
    stg = c.out("Stages required", f"ROUNDUP(ROUND({tdh}/{hps},6),0)", None, fmt="#,##0")
    bhp = c.out("Pump brake horsepower", f"{stg}*{bhps}*{dsg}", "hp", fmt="0.0")
    mhp = c.out("Motor HP required", f"ROUNDUP(ROUND({bhp}*{sf},6),0)", "hp", fmt="#,##0")
    c.out("Motor power", f"{mhp}*0.7457", None, fmt="0.0", note="kW.")
    vs = c.out("Surface voltage required",
               f"{vmot}+{vdrop}*{dset}/1000", None, fmt="#,##0",
               note="Volts: motor nameplate plus cable drop over the setting depth.")
    amp = c.out("Motor current estimate",
                f"{mhp}*746/(1.732*{vmot}*{pf}*0.9)", None, fmt="0.0",
                note="Amps. I = HP x 746 / (1.732 x V x PF x 0.9) - the 0.9 "
                     "is an assumed motor efficiency constant.")
    c.out("Surface kVA", f"1.732*{vs}*{amp}/1000", None, fmt="0.0")
    c.txt("Check the design rate against the catalog operating range",
          "Desired rate must sit inside the recommended range of the pump "
          "curve - running left of range causes downthrust wear, right of "
          "range causes upthrust wear.")
    c.txt("Thrust limits",
          "Verify downthrust/upthrust limits for the stage count and head at "
          "the operating point against the manufacturer thrust charts.")
    c.txt("Start-up current",
          "Direct-start ESP motors draw roughly 3-5x running amps at start-up "
          "- confirm generator/transformer and cable are rated for it (soft "
          "start or VSD reduces this).")
