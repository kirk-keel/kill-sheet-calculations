"""Completions: advanced topics - ICDs, ICVs, multilateral junctions (TAML),
injection thermal fatigue, APB mitigation, deep-set safety valves (Bellarby)."""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "Advanced Completions", "completions",
        "Advanced Completion Design",
        "Inflow control devices, interval control valves, multilateral junctions, "
        "injection thermal fatigue, APB mitigation, deep-set safety valves",
        description="ICD/ICV sizing, TAML multilateral classification, thermal cycling "
                    "fatigue screen, APB compliance & gas cushion, deep-set SCSSV design",
    )

    # ------------------------------------------------------------------
    sb.section("Inflow Control Devices (ICD)")

    c = sb.calc("Nozzle ICD Pressure Drop per Joint",
                eq="dP_nozzle = 0.2369 x Q^2 x rho / (N^2 x d^4 x Cd^2)   [psi; Q bpm through the joint]",
                note="Purpose is balancing heel-toe flux in horizontal wells: adding restriction at "
                     "the heel evens out drawdown along the lateral and delays water/gas cresting. "
                     "Verify the joint-by-joint nozzle distribution with reservoir simulation.")
    q = c.inp("Rate per ICD joint", 0.5, "bbl/min", fmt="0.000",
              note="Approx = total target rate / number of ICD joints.")
    rho = c.inp("Fluid density", 7.2, "ppg")
    n = c.inp("Nozzles per joint", 4, None, fmt="#,##0")
    d = c.inp("Nozzle diameter", 0.25, "in", fmt="0.000")
    cd = c.inp("Discharge coefficient (Cd)", 0.85, None, fmt="0.00",
               note="0.80-0.90 typical for rounded ICD nozzles.")
    dp = c.out("dP per joint at design rate",
               f"0.2369*{q}^2*{rho}/({n}^2*{d}^4*{cd}^2)", "psi", fmt="#,##0.0")
    c.out("ICD strength selection",
          f'IF({dp}<1,"Low restriction - consider smaller nozzles for balancing",'
          f'IF({dp}<15,"OK - typical ICD design range 2-15 psi",'
          f'"CHECK: EXCEEDS typical ICD range - erosion/plugging risk"))',
          fmt="@")

    # ------------------------------------------------------------------
    sb.section("Interval Control Valves (ICV)")

    c = sb.calc("ICV Trim Capacity - Liquid",
                eq="Q = Cv x sqrt(dP / SG)   [gpm, liquid]",
                note="Cv from the vendor trim curve at the chosen choke position (multi-position or "
                     "infinitely variable). Gas requires compressible-flow sizing (vendor software) - "
                     "the liquid Cv equation is NOT valid for gas. Keep trim velocity below the vendor "
                     "erosion limit, especially with any sand production - erosion of the trim destroys "
                     "the choking characteristic.")
    cv = c.inp("Valve Cv at chosen position", 25, None, fmt="0.0",
               note="Vendor curve; full-open Cv is much higher.")
    dpv = c.inp("dP across trim", 150, "psi", fmt="#,##0")
    sg = c.inp("Fluid SG", 0.85, None, fmt="0.000")
    qgpm = c.out("Liquid rate through valve", f"{cv}*SQRT({dpv}/{sg})", "gpm", fmt="#,##0.0")
    c.out("Liquid rate through valve", f"{qgpm}*34.29", "bpd",
          si=("m3/d", 0.1589873), fmt="#,##0", note="1 gpm = 34.29 bpd.")

    # ------------------------------------------------------------------
    sb.section("Multilateral Junction - TAML Classification")

    c = sb.calc("TAML Level Screen",
                note="Enter 1/0 flags describing the junction as designed/built. "
                     "TAML level rises with junction integrity (support, cement, hydraulic seal, "
                     "pressure competence).")
    fsup = c.inp("Junction mechanically supported (1/0)", 1, None, fmt="0")
    fseal = c.inp("Hydraulic seal at junction (1/0)", 0, None, fmt="0")
    fcem = c.inp("Cemented junction (1/0)", 1, None, fmt="0")
    fpc = c.inp("Pressure-competent at junction (1/0)", 0, None, fmt="0")
    c.out("TAML level",
          f'IF({fpc}=1,"TAML 5/6 - pressure-competent junction",'
          f'IF({fseal}=1,"TAML 4+ - cemented and sealed",'
          f'IF({fcem}=1,"TAML 3/4 - cemented junction, no pressure seal",'
          f'IF({fsup}=1,"TAML 2 - open hole with mechanical support",'
          f'"TAML 1 - open/unsupported junction"))))',
          fmt="@")
    c.txt("Level trade-offs",
          "Cost and complexity rise steeply with TAML level. Low levels (1-2) are cheap but rely on "
          "competent rock at the junction and give no sand or pressure isolation; high levels (5-6) "
          "give full pressure integrity at the junction but need premium junction hardware, more trips "
          "and tight depth/orientation control. Choose the lowest level that meets junction-integrity "
          "and sand-exclusion needs over well life.")
    c.txt("Re-entry access",
          "Plan lateral re-entry before choosing the junction: selective re-entry needs a deflector or "
          "orientation feature (latch coupling, whipstock ramp) and limits through-bore ID. Confirm "
          "intervention tools (CT/wireline trackers, kick-over) can reach each lateral, and record "
          "junction depth/orientation in the well file.")

    # ------------------------------------------------------------------
    sb.section("Injection Thermal Cycling Fatigue Screen")

    c = sb.calc("Constrained Thermal Stress & Cycle Count",
                eq="sigma_thermal = 207 x dT   [psi, fully-constrained steel]",
                note="207 psi/degF = E x alpha for steel (~30e6 psi x 6.9e-6 /degF), fully "
                     "constrained - a conservative upper bound for anchored tubing. Screening only; "
                     "a stress range above the limit calls for a proper S-N (fatigue) assessment.")
    dt = c.inp("Injection/shut-in temperature swing (dT)", 120, "degF", fmt="#,##0",
               note="Cold injection vs shut-in (geothermal) temperature at the critical depth.")
    cyr = c.inp("Cycles per year", 52, None, fmt="#,##0")
    life = c.inp("Design life", 20, "yr", fmt="#,##0")
    endur = c.inp("Endurance limit", 30000, "psi", fmt="#,##0",
                  note="Smooth-specimen carbon steel in air ~0.5 x UTS. Sour/corrosive service "
                       "lowers this sharply - corrosion fatigue has no true endurance limit.")
    sig = c.out("Constrained thermal stress range", f"207*{dt}", "psi", fmt="#,##0")
    c.out("Total cycles over design life", f"{cyr}*{life}", None, fmt="#,##0")
    c.out("Fatigue screen",
          f'IF({sig}<{endur},"OK - below endurance limit (infinite life screening)",'
          f'IF({sig}<1.5*{endur},"MARGINAL - finite life - run S-N assessment",'
          f'"CHECK: EXCEEDS fatigue screening limit - expansion device or premium design"))',
          fmt="@")

    # ------------------------------------------------------------------
    sb.section("APB with Compliance & Gas Cushion (improves the rigid estimate)")

    c = sb.calc("Compliant APB & Gas Cushion Mitigation",
                eq="APB_compliant = APB_rigid x C;   dP_cushion = P1 x ( 1/(1 - alpha_v x dT / fg) - 1 )   [isothermal ideal gas]",
                note="The rigid estimate assumes a perfectly stiff sealed annulus; real casing "
                     "balloons and adjacent fluid systems share the expansion (compliance factor C). "
                     "A nitrogen gas cushion at the top of the annulus absorbs the heated-fluid "
                     "expansion. Burst disks or crushable foam wrap are alternatives where a cushion "
                     "cannot be placed or maintained (e.g. cemented-to-surface annuli).")
    rigid = c.inp("Rigid APB estimate", 3333, "psi", fmt="#,##0",
                  note="From Tubing Stress Analysis sheet.")
    cf = c.inp("Annulus compliance factor", 0.4, None, fmt="0.00",
               note="0.25-0.6 typical - casing balloon + fluid systems share the expansion.")
    p1 = c.inp("Initial annulus pressure", 500, "psia", si=("kPa", 6.894757), fmt="#,##0")
    av = c.inp("Fluid thermal expansion coeff (alpha_v)", 0.00025, "1/degF", fmt="0.00000")
    dta = c.inp("Annulus temperature rise (dT)", 40, "degF", fmt="#,##0")
    fg = c.inp("Gas cushion fraction (fg)", 0.05, None, fmt="0.000",
               note="Gas volume / annulus volume, placed at the top of the annulus (5% = 0.05).")
    comp = c.out("Compliant APB", f"{rigid}*{cf}", "psi", fmt="#,##0",
                 note="Rigid estimate x compliance factor.")
    cush = c.out("APB with gas cushion",
                 f"IF({fg}<={av}*{dta},NA(),{p1}*(1/(1-{av}*{dta}/{fg})-1))",
                 "psi", fmt="#,##0",
                 note="Isothermal ideal-gas compression of the cushion by the expanding liquid.")
    c.out("Gas cushion status",
          f'IF({fg}<={av}*{dta},"CHECK: cushion too small - gas fully compressed",'
          f'"OK - cushion absorbs the fluid expansion")',
          fmt="@")
    c.out("Best mitigated APB (min of options)",
          f"IF({fg}<={av}*{dta},{comp},MIN({comp},{cush}))",
          "psi", fmt="#,##0",
          note="Lower of the compliance-corrected and gas-cushion estimates. Confirm the governing "
               "mechanism with a full multi-string APB model before relying on it.")

    # ------------------------------------------------------------------
    sb.section("Deep-Set Safety Valve Design")

    c = sb.calc("Control Line Hydrostatic & Valve Type",
                eq="P_cl = 0.433 x SG x depth   [psi]",
                note="Conventional spring-only SCSSVs are typically limited to roughly 1,000-2,000 ft "
                     "setting depth: control-line hydrostatic acting on the piston can overcome the "
                     "closure spring and hold the valve open. Deep-set valves need a balance line or "
                     "a nitrogen dome charge to compensate. Also check slam-closure loads at maximum "
                     "flow rate, and always equalize across the flapper before reopening "
                     "(self-equalizing flapper or apply pressure from above).")
    dep = c.inp("Setting depth", 4500, "ft", fmt="#,##0")
    sgc = c.inp("Control fluid SG", 1.02, None, fmt="0.000")
    marg = c.inp("Spring closure pressure margin", 350, "psi", fmt="#,##0",
                 note="Spring force (expressed as pressure on the piston) available to close "
                      "against control-line hydrostatic.")
    dome = c.inp("Nitrogen dome charged (1/0)", 1, None, fmt="0")
    c.out("Control line hydrostatic at valve", f"0.433*{sgc}*{dep}", "psi", fmt="#,##0")
    c.out("Spring-only max setting depth (guide)", f"{marg}/(0.433*{sgc})", "ft", fmt="#,##0",
          note="Depth at which control-line hydrostatic consumes the spring margin - beyond this "
               "a spring-only valve may fail to close.")
    c.out("Hydrostatic compensation check",
          f'IF({dome}=1,"Nitrogen-charged or balance-line valve - hydrostatic compensated; '
          f'verify charge at depth temperature",'
          f'"CHECK: spring-only valve at depth - hydrostatic may hold valve open; '
          f'balance line or dome charge required")',
          fmt="@")
