"""Completions: tubing stress analysis (Bellarby ch. 9 style, single-string).

Load-case screening for a tubing string latched to a packer:
  - axial load build-up (weight, piston at the packer bore, ballooning, thermal)
  - API uniaxial checks (Barlow burst, catalog collapse, axial yield) with
    design factors
  - triaxial von Mises equivalent stress at the tubing ID (Lame thick-wall)
    at surface and at the packer, for a hot production case and a cold
    high-pressure injection/stimulation case
  - buckling screen (Paslay-Dawson) and trapped-annulus APB estimate

Sign convention: tension positive, compression negative. This is a screening
tool - full TSA software (WellCat etc.) for HPHT, multi-string or annulus
interaction design.
"""
from ..builder import SheetBuilder

DF_NOTE = "Typical design factors (Bellarby): burst 1.1, collapse 1.0-1.1, axial 1.3, triaxial 1.25."


def build(wb):
    sb = SheetBuilder(
        wb, "Tubing Stress Analysis", "completions",
        "Tubing Stress Analysis - Load Cases & Triaxial Check",
        "Axial load build-up, API uniaxial ratings, von Mises triaxial check at surface "
        "and packer, buckling screen, APB estimate",
        description="Bellarby-style TSA screening: piston/ballooning/thermal axial loads, "
                    "Barlow burst, triaxial von Mises with design factors, buckling, APB",
    )

    sb.section("Tubular & String Data")
    c = sb.calc("Tubing Geometry",
                eq="Ai = pi/4 x ID^2;  Ao = pi/4 x OD^2;  As = Ao - Ai",
                note=DF_NOTE)
    od = c.link("Tubing OD", "WD_TbgOD", "in", fmt="0.000")
    idd = c.link("Tubing ID", "WD_TbgID", "in", fmt="0.000")
    wt = c.inp("Tubing weight", 9.3, "lb/ft", fmt="0.00")
    yp = c.inp("Pipe body yield strength (Yp)", 80000, "psi", fmt="#,##0",
               note="L-80 default. Derate for temperature above ~250 degF.")
    coll = c.inp("Catalog collapse rating", 10530, "psi", fmt="#,##0",
                 note="API 5C3 value for the size/weight/grade (3-1/2 9.3# L-80 shown).")
    ai = c.out("Bore area (Ai)", f"PI()/4*{idd}^2", "in2", fmt="0.0000")
    ao = c.out("Outer area (Ao)", f"PI()/4*{od}^2", "in2", fmt="0.0000")
    as_ = c.out("Steel cross-section (As)", f"{ao}-{ai}", "in2", fmt="0.0000")
    tw = c.out("Wall thickness", f"({od}-{idd})/2", "in", fmt="0.000")

    c = sb.calc("Packer & Depth Data")
    pkr = c.link("Packer depth (TVD)", "WD_PerfTVD", "ft", fmt="#,##0",
                 note="Packer assumed just above perfs; overwrite locally.")
    apb_d = c.inp("Seal bore diameter (packer)", 3.25, "in", fmt="0.000")
    ap = c.out("Seal bore area (Ap)", f"PI()/4*{apb_d}^2", "in2", fmt="0.0000")
    wair = c.out("String weight in air", f"{wt}*{pkr}", "lbf", fmt="#,##0")

    sb.section("Load Cases (pressures at surface; gradients build the profiles)")
    c = sb.calc("Initial / As-Landed Condition",
                note="Baseline the string was landed in - changes are measured from here.")
    pi0 = c.inp("Tubing surface pressure (initial)", 0, "psi", fmt="#,##0")
    gi0 = c.inp("Tubing fluid gradient (initial)", 0.45, "psi/ft", fmt="0.000",
                note="Packer/completion fluid at landing.")
    po0 = c.inp("Annulus surface pressure (initial)", 0, "psi", fmt="#,##0")
    go0 = c.inp("Annulus fluid gradient", 0.45, "psi/ft", fmt="0.000")

    c = sb.calc("Case A - Hot Production (shut-in tubing head, flowing temps)")
    piA = c.inp("Tubing surface pressure (A)", 3000, "psi", fmt="#,##0",
                note="SITP for gas well shut-in is often the worst burst-at-surface case.")
    giA = c.inp("Tubing fluid gradient (A)", 0.10, "psi/ft", fmt="0.000",
                note="Gas gradient when shut in on gas.")
    dtA = c.inp("Average string temp change (A)", 80, None, fmt="0",
                note="degF, heating positive (production warms the string).")

    c = sb.calc("Case B - Cold Injection / Stimulation")
    piB = c.inp("Tubing surface pressure (B)", 6500, "psi", fmt="#,##0")
    giB = c.inp("Tubing fluid gradient (B)", 0.465, "psi/ft", fmt="0.000")
    dtB = c.inp("Average string temp change (B)", -60, None, fmt="0",
                note="degF, cooling negative (injection cools the string).")

    c = sb.calc("Pressures at the Packer",
                eq="P(packer) = P(surface) + gradient x TVD")
    pi0p = c.out("Initial tubing P at packer", f"{pi0}+{gi0}*{pkr}", "psi", fmt="#,##0")
    po_p = c.out("Annulus P at packer", f"{po0}+{go0}*{pkr}", "psi", fmt="#,##0")
    piAp = c.out("Case A tubing P at packer", f"{piA}+{giA}*{pkr}", "psi", fmt="#,##0")
    piBp = c.out("Case B tubing P at packer", f"{piB}+{giB}*{pkr}", "psi", fmt="#,##0")

    sb.section("Axial Load Build-Up (latched to packer; tension positive)")
    c = sb.calc("Load Changes from Initial - Case A",
                eq="dF_piston = -dPi(pkr) x (Ap - Ai) + dPo(pkr) x (Ap - Ao);  "
                   "dF_balloon = 0.6 x (dPi_avg x Ai - dPo_avg x Ao);  "
                   "dF_thermal = -207 x As x dT",
                note="Latched string: length changes are prevented, so each effect appears "
                     "as force. 207 = E x alpha for steel (30e6 x 6.9e-6). Piston uses "
                     "pressure changes at the packer; ballooning uses average-over-length "
                     "changes (surface+packer)/2.")
    fpA = c.out("Piston force change (A)",
                f"-({piAp}-{pi0p})*({ap}-{ai})+0*({ap}-{ao})", "lbf", fmt="#,##0",
                note="Annulus pressure unchanged from initial in this case.")
    fbA = c.out("Ballooning force change (A)",
                f"0.6*((({piA}+{piAp})/2-({pi0}+{pi0p})/2)*{ai}-0*{ao})", "lbf", fmt="#,##0")
    ftA = c.out("Thermal force change (A)", f"-207*{as_}*{dtA}", "lbf", fmt="#,##0")
    c = sb.calc("Axial Profile - Case A",
                eq="F(surface) = W_air - Pi0(pkr) x (Ap - Ai) + Po(pkr) x (Ap - Ao) + sum(dF);  "
                   "F(packer) = F(surface) - W_air",
                note="Initial surface tension = hanging weight with the initial packer-bore "
                     "piston terms; case loads add the deltas.")
    f0s = c.out("Initial surface tension",
                f"{wair}-{pi0p}*({ap}-{ai})+{po_p}*({ap}-{ao})", "lbf", fmt="#,##0")
    fAs = c.out("Case A surface tension", f"{f0s}+{fpA}+{fbA}+{ftA}", "lbf", fmt="#,##0")
    fAp = c.out("Case A tension at packer", f"{fAs}-{wair}", "lbf", fmt="#,##0",
                note="Negative = compression into the packer.")

    c = sb.calc("Load Changes from Initial - Case B (same construction)")
    fpB = c.out("Piston force change (B)", f"-({piBp}-{pi0p})*({ap}-{ai})", "lbf", fmt="#,##0")
    fbB = c.out("Ballooning force change (B)",
                f"0.6*((({piB}+{piBp})/2-({pi0}+{pi0p})/2)*{ai})", "lbf", fmt="#,##0")
    ftB = c.out("Thermal force change (B)", f"-207*{as_}*{dtB}", "lbf", fmt="#,##0")
    fBs = c.out("Case B surface tension", f"{f0s}+{fpB}+{fbB}+{ftB}", "lbf", fmt="#,##0")
    fBp = c.out("Case B tension at packer", f"{fBs}-{wair}", "lbf", fmt="#,##0")

    sb.section("API Uniaxial Checks")
    c = sb.calc("Ratings & Utilisation",
                eq="Burst (Barlow, 87.5% wall) = 0.875 x 2 x Yp x t/OD;  Axial = Yp x As",
                note=DF_NOTE)
    brst = c.out("Burst rating (API wall tolerance)", f"0.875*2*{yp}*{tw}/{od}", "psi",
                 fmt="#,##0")
    dfb = c.inp("Burst design factor", 1.1, None, fmt="0.00")
    dfc = c.inp("Collapse design factor", 1.0, None, fmt="0.00")
    dfa = c.inp("Axial design factor", 1.3, None, fmt="0.00")
    c.out("Allowable burst differential", f"{brst}/{dfb}", "psi", fmt="#,##0")
    bmax = c.out("Max burst differential (worst case, surface B)",
                 f"MAX({piA}-{po0},{piB}-{po0})", "psi", fmt="#,##0")
    c.out("Burst status",
          f'IF({bmax}<={brst}/{dfb},"OK - burst within design factor",'
          f'IF({bmax}<={brst},"MARGINAL - inside rating but below design factor",'
          f'"CHECK: EXCEEDS burst rating"))', None, fmt="@")
    cmax = c.out("Max collapse differential (evacuated tubing)",
                 f"{po_p}-0", "psi", fmt="#,##0",
                 note="Full evacuation against packer-fluid annulus - classic gas-lift/"
                      "blowdown collapse case.")
    c.out("Collapse status",
          f'IF({cmax}<={coll}/{dfc},"OK - collapse within design factor",'
          f'"CHECK: EXCEEDS collapse allowable - heavier wall or higher grade")',
          None, fmt="@")
    tmax = c.out("Max axial tension (all cases, surface)", f"MAX({f0s},{fAs},{fBs})",
                 "lbf", fmt="#,##0")
    c.out("Axial status",
          f'IF({tmax}<={yp}*{as_}/{dfa},"OK - axial within design factor",'
          f'"CHECK: EXCEEDS axial allowable - higher grade or heavier string")',
          None, fmt="@")

    sb.section("Triaxial von Mises (Lame, at tubing ID)")
    c = sb.calc("Case A at Packer",
                eq="sig_h = (Pi x (ro^2+ri^2) - 2 x Po x ro^2)/(ro^2-ri^2);  sig_r = -Pi;  "
                   "sig_a = F/As;  VME = sqrt(((sa-sh)^2+(sh-sr)^2+(sr-sa)^2)/2)",
                note="ID face is normally the governing location. Bending from dogleg "
                     "excluded - add sig_b = 218 x DLS x OD for curved hole screening.")
    ri2 = f"({idd}/2)^2"
    ro2 = f"({od}/2)^2"
    shA = c.out("Hoop stress (A, packer)",
                f"({piAp}*({ro2}+{ri2})-2*{po_p}*{ro2})/({ro2}-{ri2})", "psi", fmt="#,##0")
    srA = c.out("Radial stress (A, packer)", f"-{piAp}", "psi", fmt="#,##0")
    saA = c.out("Axial stress (A, packer)", f"{fAp}/{as_}", "psi", fmt="#,##0")
    vmA = c.out("von Mises equivalent (A, packer)",
                f"SQRT((({saA}-{shA})^2+({shA}-{srA})^2+({srA}-{saA})^2)/2)",
                "psi", fmt="#,##0")
    dft = c.inp("Triaxial design factor", 1.25, None, fmt="0.00")
    c.out("Triaxial status (A)",
          f'IF({vmA}<={yp}/{dft},"OK - triaxial SF met",'
          f'IF({vmA}<={yp},"MARGINAL - below yield but under design factor",'
          f'"CHECK: EXCEEDS yield - redesign"))', None, fmt="@")

    c = sb.calc("Case B at Surface (cold, high internal pressure)")
    shB = c.out("Hoop stress (B, surface)",
                f"({piB}*({ro2}+{ri2})-2*{po0}*{ro2})/({ro2}-{ri2})", "psi", fmt="#,##0")
    srB = c.out("Radial stress (B, surface)", f"-{piB}", "psi", fmt="#,##0")
    saB = c.out("Axial stress (B, surface)", f"{fBs}/{as_}", "psi", fmt="#,##0")
    vmB = c.out("von Mises equivalent (B, surface)",
                f"SQRT((({saB}-{shB})^2+({shB}-{srB})^2+({srB}-{saB})^2)/2)",
                "psi", fmt="#,##0")
    c.out("Triaxial status (B)",
          f'IF({vmB}<={yp}/{dft},"OK - triaxial SF met",'
          f'IF({vmB}<={yp},"MARGINAL - below yield but under design factor",'
          f'"CHECK: EXCEEDS yield - redesign"))', None, fmt="@")

    sb.section("Buckling Screen & Annulus Pressure Build-Up")
    c = sb.calc("Paslay-Dawson Buckling at the Packer",
                eq="F_sin = 2 x sqrt(E x I x w_b x sin(inc)/r);  F_hel = 2.83 x sqrt(...)",
                note="Compression at the packer (negative tension above) is screened "
                     "against the sinusoidal/helical onsets. 3-deg inclination floor "
                     "avoids the vertical singularity.")
    inc = c.inp("Inclination at packer", 90, None, fmt="0", note="deg")
    cid = c.link("Casing ID", "WD_CsgID", "in", fmt="0.000")
    mwf = c.inp("Annulus fluid density", 8.6, "ppg")
    ii = c.out("Tubing moment of inertia (I)", f"PI()/64*({od}^4-{idd}^4)", None,
               fmt="0.000", note="in^4")
    wb_ = c.out("Buoyed weight per inch", f"{wt}*(1-{mwf}/65.5)/12", None, fmt="0.000",
                note="lb/in")
    rcl = c.out("Radial clearance", f"({cid}-{od})/2", "in", fmt="0.000")
    fsin = c.out("Sinusoidal onset force",
                 f"2*SQRT(30000000*{ii}*{wb_}*SIN(RADIANS(MAX({inc},3)))/{rcl})",
                 "lbf", fmt="#,##0")
    c.out("Buckling status (worst packer compression)",
          f'IF(MIN({fAp},{fBp})>-{fsin},"OK - no buckling at packer",'
          f'IF(MIN({fAp},{fBp})>-1.41*{fsin},"MARGINAL - sinusoidal buckling",'
          f'"CHECK: helical BUCKLING at packer - seal wear/lockup risk"))', None, fmt="@")

    c = sb.calc("Trapped Annulus Pressure Build-Up (APB)",
                eq="dP = (alpha_v / c_f) x dT   (rigid, fully-trapped annulus)",
                note="Screening upper bound: no casing/tubing compliance, no gas cap, "
                     "no leak-off. Real APB is lower; mitigate with gas cushion, "
                     "crushable foam or burst disks.")
    av = c.inp("Fluid thermal expansion (alpha_v)", 0.00025, None, fmt="0.00000",
               note="1/degF, water ~2.1e-4 to 2.8e-4 rising with temperature.")
    cf = c.inp("Fluid compressibility (c_f)", 0.000003, None, fmt="0.0000000",
               note="1/psi, water ~3e-6.")
    dta = c.inp("Trapped annulus temp rise", 40, None, fmt="0", note="degF")
    c.out("APB estimate (rigid annulus)", f"{av}/{cf}*{dta}", "psi", fmt="#,##0")
    c.txt("", "Compare APB against casing burst and collapse ratings on the Casing & "
              "Tubular Design sheet.")
