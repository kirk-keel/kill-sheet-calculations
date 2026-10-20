"""Interventions: wireline weights, pull limits, weak point, stretch, pressure forces."""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "Wireline", "interventions",
        "Wireline Operations",
        "Cable and tool weights, safe pull, weak point window, stretch, grease-head forces",
        description="Buoyed cable weight, head tension, safe pull, weak point, stretch and depth correction",
    )

    sb.section("Cable & String Weight")

    c = sb.calc("Buoyed Cable Weight",
                eq="w_buoyed [lb/kft] = w_air x (1 - MW / 65.5)",
                note="Steel-line buoyancy approximation (65.5 ppg steel). For exact values use the vendor "
                     "displaced-volume figure, especially for polymer-jacketed cable.")
    wair = c.inp("Cable weight in air", 340, "lb/kft", si=("kg/km", 1.488164), fmt="#,##0",
                 note="e.g. 0.108-in slickline ~ 31 lb/kft; 5/16-in braided ~ 330 lb/kft; 7/16 e-line ~ 460 lb/kft")
    mw = c.inp("Wellbore fluid density (MW)", 8.6, "ppg")
    bf = c.out("Buoyancy factor (BF)", f"1-{mw}/65.5", None, fmt="0.000")
    wbk = c.out("Buoyed cable weight", f"{wair}*{bf}", "lb/kft", si=("kg/km", 1.488164), fmt="#,##0")
    depth = c.inp("Tool depth", 12000, "ft", fmt="#,##0")
    wcab = c.out("Buoyed cable weight at depth", f"{wbk}*{depth}/1000", "lbf", fmt="#,##0")

    c = sb.calc("Tool String Weight & Surface Head Tension",
                eq="T_head = W_cable_buoyed + W_tools x BF + F_drag")
    wtool = c.inp("Tool string weight in air", 350, "lbf", fmt="#,##0")
    wtoolb = c.out("Buoyed tool string weight", f"{wtool}*{bf}", "lbf", fmt="#,##0")
    fdrag = c.inp("Friction + fluid drag at pickup", 100, "lbf", fmt="#,##0",
                  note="Depends on line speed, deviation, and stuffing-box / grease friction; from the weight "
                       "indicator on a pick-up/slack-off check.")
    c.out("Head tension at surface (pickup)", f"{wcab}+{wtoolb}+{fdrag}", "lbf", fmt="#,##0")

    sb.section("Pull Limits & Weak Point")

    c = sb.calc("Maximum Safe Pull",
                eq="F_safe = % x minimum breaking strength")
    fbreak = c.inp("Cable minimum breaking strength", 5600, "lbf", fmt="#,##0",
                   note="Use the current (aged/derated) break strength from cable records, not new-cable value.")
    pct = c.inp("Safe working percentage", 50, None, fmt="#,##0",
                note="% of minimum break; 50% typical for braided line, some operators allow 60% for a "
                     "controlled fishing pull.")
    fsafe = c.out("Maximum safe pull at surface", f"{fbreak}*{pct}/100", "lbf", fmt="#,##0")

    c = sb.calc("Weak Point Selection Window",
                eq="WP_max = F_safe - W_cable_buoyed;  WP_min = W_tools x BF + margin",
                note="Weak point must part (pull at the tool) before surface tension reaches cable safe pull, "
                     "but must carry the tool string with margin for jarring and drag.")
    margin = c.inp("Margin above buoyed tool weight", 300, "lbf", fmt="#,##0")
    wpmax = c.out("Weak point upper limit (WP_max)", f"{fsafe}-{wcab}", "lbf", fmt="#,##0")
    wpmin = c.out("Weak point lower limit (WP_min)", f"{wtoolb}+{margin}", "lbf", fmt="#,##0")
    wp = c.inp("Selected weak point rating", 2000, "lbf", fmt="#,##0")
    c.out("Weak point check",
          f'IF({wpmin}>{wpmax},"NO VALID WINDOW - reduce depth, lighter tools, or stronger cable",'
          f'IF(AND({wp}>={wpmin},{wp}<={wpmax}),"OK - inside window","OUTSIDE WINDOW"))',
          None, fmt="@")

    sb.section("Stretch & Depth Correction")

    c = sb.calc("Cable Stretch Under Pull",
                eq="e [ft] = P [klbf] x L [kft] x K [ft/kft/klbf]")
    k = c.inp("Cable stretch coefficient (K)", 0.90, None, fmt="0.00",
              note="ft per kft per klbf, from the cable data sheet. Typical 0.6-1.2 for braided line, "
                   "~1.6-2.0 for slickline sizes.")
    pull = c.inp("Pull applied over normal tension (P)", 1.50, "klbf", fmt="0.00")
    stretch = c.out("Cable stretch", f"{pull}*{depth}/1000*{k}", "ft", fmt="0.00")

    c = sb.calc("Thermal Expansion & Total Depth Correction",
                eq="e_th [ft] = L x alpha x dT_avg;  alpha = 8.3e-6 per degF (steel)",
                note="dT_avg = average cable temperature downhole minus calibration temperature. Standard "
                     "field constant for steel line; both corrections make true depth deeper than counter depth.")
    dt = c.inp("Average temperature rise (dT_avg)", 60, None, fmt="#,##0", note="degF")
    eth = c.out("Thermal elongation", f"{depth}*0.0000083*{dt}", "ft", fmt="0.00")
    c.out("Total depth correction (add to counter depth)", f"{stretch}+{eth}", "ft", fmt="0.00")

    sb.section("Pressure Forces at Surface")

    c = sb.calc("Grease Head Ejection Force & Tools-Light Check",
                eq="F_ej [lbf] = WHP x pi/4 x d_cable^2",
                note="Check at surface with tools just below the head: buoyed tool weight must exceed the "
                     "pressure force plus grease/pack-off friction or the string will not run in.")
    whp = c.inp("Wellhead pressure (WHP)", 5000, "psi", fmt="#,##0")
    dcab = c.inp("Cable diameter", 0.230, "in", fmt="0.000")
    ffr = c.inp("Grease head / pack-off friction", 50, "lbf", fmt="#,##0")
    fej = c.out("Pressure force pushing cable out", f"{whp}*PI()/4*{dcab}^2", "lbf", fmt="#,##0")
    c.out("Tools-light check",
          f'IF({wtoolb}>{fej}+{ffr},"OK - string will run in","TOOLS LIGHT - add weight bars / stem")',
          None, fmt="@")

    c = sb.calc("Field Notes")
    c.txt("Braided line vs slickline",
          "Slickline: single-strand, sealed by stuffing box, no conductor - depth/stretch constants per size. "
          "Braided/e-line: multi-strand, sealed by grease injection head, higher strength and drag; e-line "
          "carries conductors and uses an electrically-releasable or tension weak point.")
    c.txt("Fluid drag",
          "Drag rises with line speed, fluid viscosity, and tool OD vs completion ID; it adds to head tension "
          "running out and subtracts running in. Verify limits at planned line speed, not static weight.")
    c.txt("Running speed / swab & surge",
          "Large-OD tools in tight completions swab (running out) and surge (running in) the well. Slow down "
          "across restrictions and near the perforations; typical max 200-300 ft/min with close clearances.")

    sb.section("Stem Design & Fall-Back")

    c = sb.calc("Stem Required to Run Against Wellhead Pressure",
                eq="F_ej = WHP x pi/4 x d^2;  W_req_buoyed = SF x (F_ej + friction);  "
                   "stem length = stem weight in air / (lb/ft)",
                note="Buoyed string weight must beat the pressure ejection force plus stuffing-box friction "
                     "with a safety factor before the string will run in and fall reliably.")
    whps = c.inp("Wellhead pressure (WHP)", 3000, "psi", fmt="#,##0")
    dwire = c.inp("Wire diameter (d)", 0.125, "in", fmt="0.000")
    ffrs = c.inp("Stuffing box / grease friction", 75, "lbf", fmt="#,##0")
    wts = c.inp("Tool string weight in air", 150, "lbm", fmt="#,##0")
    mws = c.inp("Well fluid density (MW)", 8.6, "ppg", note="Use 0 for a gas well.")
    slbft = c.inp("Stem weight per foot", 9.5, "lb/ft", fmt="0.00",
                  note="9.5 lb/ft typical for 1-7/8 in stem.")
    sfs = c.inp("Safety factor (SF)", 1.5, None, fmt="0.00",
                note="Buoyed weight over ejection + friction; typically 1.5.")
    fejs = c.out("Ejection force (F_ej)", f"{whps}*PI()/4*{dwire}^2", "lbf", fmt="#,##0")
    bfs = c.out("Buoyancy factor (BF)", f"1-{mws}/65.5", None, fmt="0.000")
    wtb = c.out("Buoyed tool string weight", f"{wts}*{bfs}", "lbf", fmt="#,##0")
    wreq = c.out("Required buoyed weight", f"{sfs}*({fejs}+{ffrs})", "lbf", fmt="#,##0")
    addstem = c.out("Additional stem weight (in air)", f"MAX(0,({wreq}-{wtb})/{bfs})", "lbm", fmt="#,##0")
    c.out("Stem length required", f"{addstem}/{slbft}", "ft", fmt="0.0")

    c = sb.calc("Fall-Back Factor",
                eq="FBF = buoyed string weight / (F_ej + friction)",
                note="Fall-back factor = ratio of buoyed string weight to total upward force at the stuffing "
                     "box. Field rule of thumb: keep FBF >= 1.5 so tools reliably fall against wellhead "
                     "pressure and the X-mas tree check valves are not re-closed by a hung string. Not a "
                     "code requirement - a field rule of thumb only.")
    wfb = c.inp("Buoyed string weight incl. stem", 450, "lbf", fmt="#,##0")
    whpf = c.inp("Wellhead pressure (WHP)", 3000, "psi", fmt="#,##0")
    dwf = c.inp("Wire diameter", 0.125, "in", fmt="0.000")
    ffrf = c.inp("Stuffing box / grease friction", 75, "lbf", fmt="#,##0")
    fejf = c.out("Ejection force (F_ej)", f"{whpf}*PI()/4*{dwf}^2", "lbf", fmt="#,##0")
    fbf = c.out("Fall-back factor (FBF)", f"{wfb}/({fejf}+{ffrf})", None, fmt="0.00")
    c.out("Fall-back status",
          f'IF({fbf}>=1.5,"OK TO RUN",IF({fbf}>=1.2,"MARGINAL - CONSIDER MORE STEM","ADD STEM"))',
          None, fmt="@")

    sb.section("Swab & Surge - Running Tools")

    c = sb.calc("Tool Piston Swab/Surge in Tubing",
                eq="Ve = Vt x (0.45 + Dt^2/(Dtbg^2 - Dt^2));  "
                   "dP = L x PV x Ve/(60000 x (Dtbg-Dt)^2) + L x YP/(200 x (Dtbg-Dt))",
                note="Closed-body tool moving in tubing, Bingham-plastic laminar approximation with the "
                     "Burkhardt 0.45 clinging constant. Swab reduces BHP pulling out; surge raises it "
                     "running in.")
    dt_ = c.inp("Tool OD (Dt)", 2.5, "in", fmt="0.000")
    dtbg = c.inp("Tubing ID (Dtbg)", 2.992, "in", fmt="0.000")
    vt = c.inp("Running speed (Vt)", 200, "ft/min", fmt="#,##0")
    pv = c.inp("Fluid plastic viscosity (PV)", 12, "cP", si=("mPa-s", 1.0), fmt="#,##0")
    yp = c.inp("Fluid yield point (YP)", 10, None, fmt="#,##0",
               note="lb/100ft2 (no SI mirror; 1 lb/100ft2 = 0.4788 Pa)")
    lbelow = c.inp("Tubing length below tool (L)", 8000, "ft", fmt="#,##0")
    mwsw = c.inp("Fluid density (MW)", 8.6, "ppg")
    tvdsw = c.inp("TVD at tool", 8000, "ft", fmt="#,##0")
    ve = c.out("Effective velocity (Ve)", f"{vt}*(0.45+{dt_}^2/({dtbg}^2-{dt_}^2))", "ft/min", fmt="#,##0")
    dpss = c.out("Swab/surge pressure (dP)",
                 f"{lbelow}*{pv}*{ve}/(60000*({dtbg}-{dt_})^2)+{lbelow}*{yp}/(200*({dtbg}-{dt_}))",
                 "psi", fmt="#,##0")
    dppg = c.out("Equivalent density change", f"{dpss}/(0.052*{tvdsw})", "ppg", fmt="0.00")
    c.out("EMW while pulling (swab)", f"{mwsw}-{dppg}", "ppg", fmt="0.00",
          note="Keep above pore/kick margin - swabbing lowers effective BHP.")
    c.out("EMW while running (surge)", f"{mwsw}+{dppg}", "ppg", fmt="0.00",
          note="Keep below frac/loss margin - surging raises effective BHP.")

    c = sb.calc("Maximum Line Speed for Allowable Swab",
                eq="Vmax = (dP_allow - L x YP/(200 x (Dtbg-Dt))) x 60000 x (Dtbg-Dt)^2 / "
                   "(L x PV x (0.45 + Dt^2/(Dtbg^2-Dt^2)))",
                note="Inverts the Bingham swab equation for the line speed that just reaches the allowable "
                     "swab pressure.")
    dpal = c.inp("Allowable swab pressure", 150, "psi", fmt="#,##0")
    dtm = c.inp("Tool OD (Dt)", 2.5, "in", fmt="0.000")
    dtbgm = c.inp("Tubing ID (Dtbg)", 2.992, "in", fmt="0.000")
    pvm = c.inp("Fluid plastic viscosity (PV)", 12, "cP", si=("mPa-s", 1.0), fmt="#,##0")
    ypm = c.inp("Fluid yield point (YP)", 10, None, fmt="#,##0",
                note="lb/100ft2")
    lm = c.inp("Tubing length below tool (L)", 8000, "ft", fmt="#,##0")
    c.out("Maximum line speed",
          f"MAX(0,({dpal}-{lm}*{ypm}/(200*({dtbgm}-{dtm})))*60000*({dtbgm}-{dtm})^2/"
          f"({lm}*{pvm}*(0.45+{dtm}^2/({dtbgm}^2-{dtm}^2))))",
          "ft/min", fmt="#,##0",
          note="0 means the YP term alone exceeds the allowance - reduce tool OD or allowable.")
