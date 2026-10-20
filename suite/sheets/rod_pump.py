"""Completions: sucker rod (beam) pump design - displacement, loads, torque,
Goodman stress check and effective plunger stroke.

Mills-type approximations throughout (acceleration factor alpha = S x N^2 /
70500): quick-look polished rod loads, counterbalance and peak torque. API RP
11L gives more accurate answers for final design. Rod weight per foot is
approximated as w = 2.904 x d^2 (steel rods with couplings; matches published
2.224 lb/ft at 7/8 in and 1.634 lb/ft at 3/4 in).
"""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "Rod Pump Design", "completions",
        "Sucker Rod Pump Design",
        "Pump displacement, Mills polished-rod loads, counterbalance and "
        "torque, Goodman stress check, effective plunger stroke",
        description="Beam pump: displacement, PPRL/MPRL, counterbalance, peak "
                    "torque, motor HP, Goodman check and plunger stroke",
    )

    sb.section("Pump Displacement")

    c = sb.calc("Pump Displacement",
                eq="PD [bpd] = 0.1166 x S [in] x N [spm] x D^2 [in];   "
                   "K = 0.1166 x D^2",
                note="Theoretical displacement at 100% volumetric efficiency; "
                     "actual rate applies the efficiency (slippage, fillage, "
                     "gas interference).")
    dpl = c.inp("Plunger diameter (D)", 1.5, "in", fmt="0.000")
    stk = c.inp("Stroke length (S)", 86, "in", fmt="0.0")
    spm = c.inp("Pumping speed (N)", 8, None, fmt="0.0",
                note="Strokes per minute.")
    ev = c.inp("Volumetric efficiency", 80, None, fmt="0.0", note="Percent.")
    c.out("Pump constant (K)", f"0.1166*{dpl}^2", None, fmt="0.0000",
          note="bpd per (in of stroke x spm).")
    pd100 = c.out("Pump displacement (100% eff)",
                  f"0.1166*{stk}*{spm}*{dpl}^2", None, fmt="#,##0.00",
                  note="bpd.")
    qact = c.out("Actual rate", f"{pd100}*{ev}/100", None, fmt="#,##0.0",
                 note="bpd.")

    sb.section("Rod String & Loads")

    c = sb.calc("Two-Taper Rod String Weight",
                eq="w [lb/ft] = 2.904 x d^2;   Wr = sum(w x L);   "
                   "Wrf = Wr x (1 - 0.128 x SG)",
                note="w = 2.904 x d^2 approximates steel rods with couplings "
                     "(2.224 lb/ft at 7/8 in, 1.634 lb/ft at 3/4 in). Buoyancy "
                     "factor 1 - 0.128 x SG.")
    dep = c.inp("Pump depth (L)", 5400, "ft", fmt="#,##0")
    sg = c.inp("Fluid specific gravity", 1.02, None, fmt="0.000")
    d1 = c.inp("Taper 1 rod diameter (top)", 0.875, "in", fmt="0.000")
    l1 = c.inp("Taper 1 length", 1900, "ft", fmt="#,##0")
    d2 = c.inp("Taper 2 rod diameter", 0.75, "in", fmt="0.000")
    l2 = c.inp("Taper 2 length", 3500, "ft", fmt="#,##0",
               note="Taper lengths should total the pump depth.")
    wr = c.out("Rod weight in air (Wr)",
               f"2.904*{d1}^2*{l1}+2.904*{d2}^2*{l2}", "lbf", fmt="#,##0")
    wrf = c.out("Buoyed rod weight (Wrf)", f"{wr}*(1-0.128*{sg})",
                "lbf", fmt="#,##0")

    c = sb.calc("Fluid Load & Mills Polished Rod Loads",
                eq="Fo = 0.340 x SG x D^2 x H;   alpha = S x N^2 / 70500;   "
                   "PPRL = Fo + Wrf x (1 + alpha);   MPRL = Wrf x (1 - alpha)",
                note="Mills-type approximations - API RP 11L gives more "
                     "accurate loads for final design. H is the net lift "
                     "(fluid level depth), not the pump depth.")
    hnet = c.inp("Net lift (H, fluid level depth)", 3400, "ft", fmt="#,##0",
                 note="Working fluid level TVD - the head the pump actually "
                      "lifts against.")
    fo = c.out("Fluid load on plunger (Fo)", f"0.340*{sg}*{dpl}^2*{hnet}",
               "lbf", fmt="#,##0")
    alpha = c.out("Mills acceleration factor (alpha)",
                  f"{stk}*{spm}^2/70500", None, fmt="0.0000")
    pprl = c.out("Peak polished rod load (PPRL)",
                 f"{fo}+{wrf}*(1+{alpha})", "lbf", fmt="#,##0")
    mprl = c.out("Minimum polished rod load (MPRL)",
                 f"{wrf}*(1-{alpha})", "lbf", fmt="#,##0")

    sb.section("Counterbalance, Torque & Power")

    c = sb.calc("Counterbalance & Peak Torque",
                eq="CBE = Wrf + Fo/2;   PT = (PPRL - CBE) x S/2",
                note="Ideal counterbalance carries the buoyed rods plus half "
                     "the fluid load. Peak torque is a simplified crank-torque "
                     "approximation (no torque factors / unit geometry) - use "
                     "the API torque analysis for gearbox rating.")
    cbe = c.out("Ideal counterbalance effect (CBE)", f"{wrf}+{fo}/2",
                "lbf", fmt="#,##0")
    c.out("Peak torque (approx)", f"({pprl}-{cbe})*{stk}/2", None,
          fmt="#,##0", note="in-lb, simplified.")

    c = sb.calc("Power & Motor Sizing",
                eq="HHP = 7.36e-6 x Q x SG x H;   FHP = 6.31e-7 x Wr x S x N;  "
                   " PRHP = HHP + FHP;   motor HP = ROUNDUP(PRHP x CLF x SF)",
                note="Q is the actual rate. Cyclic load factor covers the "
                     "fluctuating beam-pump load on the motor (NEMA D).")
    clf = c.inp("Cyclic load factor", 1.35, None, fmt="0.00")
    msf = c.inp("Motor safety factor", 1.15, None, fmt="0.00")
    hhp = c.out("Hydraulic horsepower", f"0.00000736*{qact}*{sg}*{hnet}",
                "hp", fmt="0.00")
    fhp = c.out("Friction horsepower", f"0.000000631*{wr}*{stk}*{spm}",
                "hp", fmt="0.00")
    prhp = c.out("Polished rod horsepower", f"{hhp}+{fhp}", "hp", fmt="0.00")
    c.out("Motor HP required", f"ROUNDUP(ROUND({prhp}*{clf}*{msf},6),0)", "hp",
          fmt="#,##0")

    sb.section("Rod Stress & Goodman Check")

    c = sb.calc("Modified Goodman Diagram Check",
                eq="Smax = PPRL/A;   Smin = MPRL/A;   "
                   "Sallow = (T/4 + 0.5625 x Smin) x SF",
                note="Top rod carries the highest load - stresses on the top "
                     "taper area. Service factor 1.0 non-corrosive; lower for "
                     "corrosive service (e.g. 0.9 salt water, 0.65 H2S).")
    ts = c.inp("Rod tensile strength (T)", 115000, "psi", fmt="#,##0",
               note="Grade D minimum tensile.")
    svf = c.inp("Service factor", 0.9, None, fmt="0.00")
    ar1 = c.out("Top rod area (A)", f"PI()/4*{d1}^2", "in2", fmt="0.000")
    smax = c.out("Maximum rod stress", f"{pprl}/{ar1}", "psi", fmt="#,##0")
    smin = c.out("Minimum rod stress", f"{mprl}/{ar1}", "psi", fmt="#,##0")
    sall = c.out("Modified Goodman allowable stress",
                 f"({ts}/4+0.5625*{smin})*{svf}", "psi", fmt="#,##0")
    c.out("Goodman status",
          f'IF({smax}<={sall},"OK - within Goodman diagram",'
          f'IF({smax}<={sall}*1.05,"MARGINAL - at Goodman limit",'
          f'"CHECK: EXCEEDS Goodman allowable - heavier taper or slower '
          f'speed"))',
          None, fmt="@")

    sb.section("Plunger Stroke & Stretch")

    c = sb.calc("Rod / Tubing Stretch & Effective Plunger Stroke",
                eq="er = 12 x Fo x (L1/A1 + L2/A2) / E;   "
                   "et = IF(anchored, 0, 12 x Fo x L / (At x E));   "
                   "eo = S x alpha;   Sp = S - er - et + eo",
                note="E = 30.5e6 psi (steel). Rod stretch is summed per taper; "
                     "tubing stretch is zero when the tubing is anchored. "
                     "Plunger overtravel eo = S x alpha is the documented "
                     "simple approximation.")
    anch = c.inp("Tubing anchored? (1 = yes, 0 = no)", 1, None, fmt="0",
                 note="Anchored (tension-set) tubing does not breathe with "
                      "the fluid load - tubing stretch term becomes zero.")
    tod = c.link("Tubing OD", "WD_TbgOD", "in", fmt="0.000")
    tid = c.link("Tubing ID", "WD_TbgID", "in", fmt="0.000")
    at = c.out("Tubing wall area (At)", f"PI()/4*({tod}^2-{tid}^2)",
               "in2", fmt="0.000")
    ar2 = c.out("Taper 2 rod area (A2)", f"PI()/4*{d2}^2", "in2", fmt="0.000")
    er = c.out("Rod stretch (er)",
               f"12*{fo}*({l1}/{ar1}+{l2}/{ar2})/30500000", "in", fmt="0.00")
    et = c.out("Tubing stretch (et)",
               f"IF({anch}=1,0,12*{fo}*{dep}/({at}*30500000))", "in",
               fmt="0.00")
    eo = c.out("Plunger overtravel (eo)", f"{stk}*{alpha}", "in", fmt="0.00",
               note="eo = S x alpha (simple dynamic overtravel approximation).")
    sp = c.out("Effective plunger stroke (Sp)", f"{stk}-{er}-{et}+{eo}",
               "in", fmt="0.00")
    c.out("Displacement with effective stroke",
          f"0.1166*{sp}*{spm}*{dpl}^2*{ev}/100", None, fmt="#,##0.0",
          note="bpd - compare with the actual rate above (stretch-corrected).")
