"""Completions: sand control method selection, gravel/screen sizing, proppant
selection, tubing erosional velocity (API RP 14E) and Turner liquid loading.

Sieve-based method selection follows Tiffin-style rules of thumb - screening
guidance only, not a substitute for laboratory sand retention testing.
"""
from ..builder import SheetBuilder
from ..convert import TEMP_F


def build(wb):
    sb = SheetBuilder(
        wb, "Completion Design", "completions",
        "Completion Design - Sand Control & Sizing",
        "Sieve analysis, gravel & screen sizing (Saucier), gravel pack volumes, "
        "proppant selection, erosional velocity, Turner liquid loading",
        description="Sand control method selection, gravel/screen/proppant sizing, "
                    "API RP 14E erosional velocity, Turner critical rate",
    )

    # ------------------------------------------------------------------
    sb.section("Formation Sieve Analysis & Method Selection")

    c = sb.calc("Sieve Analysis (from LPSA / dry sieve)",
                eq="UC = d40 / d90 (uniformity coefficient)",
                note="Enter grain sizes from laser particle size analysis (LPSA) or dry "
                     "sieve of formation samples. dXX = sieve size that XX wt% of the "
                     "sample is coarser than.")
    d10 = c.inp("d10 grain size", 350, "micron", fmt="#,##0")
    d40 = c.inp("d40 grain size", 180, "micron", fmt="#,##0")
    d50 = c.inp("d50 grain size (median)", 150, "micron", fmt="#,##0")
    d90 = c.inp("d90 grain size", 44, "micron", fmt="#,##0")
    fines = c.inp("Fines content (< 44 micron)", 4, "%", fmt="0.0",
                  note="Sub-325-mesh fraction; high fines plug gravel packs and screens.")
    uc = c.out("Uniformity coefficient (UC)", f"{d40}/{d90}", None, fmt="0.00")
    c.out("Sorting classification",
          f'IF({uc}<3,"Uniform sand",IF({uc}<5,"Non-uniform","Highly non-uniform"))',
          None, fmt="@")

    c = sb.calc("Sand Control Method Selection (Tiffin-style rules of thumb)",
                note="Screening guidance only - NOT a substitute for laboratory sand "
                     "retention / slurry testing on actual formation samples.")
    c.out("Recommended method",
          f'IF(AND({uc}<3,{fines}<2),"Standalone screen (SAS) candidate",'
          f'IF(AND({uc}<5,{fines}<5),"Gravel pack or high-rate water pack",'
          f'IF({uc}<10,"Gravel pack with enlarged borehole / frac pack",'
          f'"Frac pack or oriented perf + screenless - lab testing required")))',
          None, fmt="@")

    # ------------------------------------------------------------------
    sb.section("Gravel Sizing (Saucier)")

    c = sb.calc("Saucier Gravel Sizing",
                eq="Dg50 = 5 to 6 x d50 (Saucier); gravel range = Dg50 / 2 to "
                   "Dg50 x 1.5 checked vs commercial mesh",
                note="Commercial US mesh ranges [micron]: 40/60: 250-425; 30/50: 300-600; "
                     "20/40: 425-850; 16/30: 600-1180; 12/20: 850-1700; 8/12: 1700-2360. "
                     "Pick the smallest commercial size whose range contains Dg50.")
    smult = c.inp("Saucier multiplier", 6, None, fmt="0.0",
                  note="5-6 x d50 typical; 6 for retention with reasonable permeability.")
    gmed = c.out("Gravel median size (Saucier)", f"{smult}*{d50}", "micron", fmt="#,##0")
    c.out("Gravel median size", f"{gmed}/25400", "in", fmt="0.0000")
    c.out("Commercial gravel selection",
          f'IF({gmed}<=425,"40/60",IF({gmed}<=600,"30/50",IF({gmed}<=850,"20/40",'
          f'IF({gmed}<=1180,"16/30",IF({gmed}<=1700,"12/20","8/12")))))',
          None, fmt="@",
          note="Smallest commercial size whose range contains the Saucier median.")
    grain = c.inp("Selected gravel smallest grain", 0.0236, "in", fmt="0.0000",
                  note="Smallest grain of the selected commercial gravel; 16/30 = 600 "
                       "micron = 0.0236 in. Update if a different mesh is selected.")

    # ------------------------------------------------------------------
    sb.section("Screen & Slot Selection")

    c = sb.calc("Gravel-Pack Screen Gauge",
                eq="Screen gauge (slot) <= smallest gravel grain / 2",
                note="Standard wire-wrap gauges (thousandths of an inch): 6, 8, 12, 16, 20. "
                     "Pick the largest standard gauge not exceeding the computed slot.")
    gauge = c.out("Maximum screen gauge (slot width)", f"{grain}/2", "in", fmt="0.0000")
    c.out("Commercial gauge selection",
          f'IF({gauge}*1000>=20,"20 gauge",IF({gauge}*1000>=16,"16 gauge",'
          f'IF({gauge}*1000>=12,"12 gauge",IF({gauge}*1000>=8,"8 gauge","6 gauge"))))',
          None, fmt="@")

    c = sb.calc("Standalone Screen (SAS) Slot / Mesh Rating",
                eq="SAS slot ~ rule multiplier x d10",
                note="Wire-wrap: ~2 x d10. Premium (woven mesh) micron rating ~ d10. "
                     "Confirm with sand retention testing.")
    srule = c.inp("SAS sizing rule multiplier", 2.0, None, fmt="0.0",
                  note="2 x d10 for wire-wrap; use 1.0 for premium mesh rating ~ d10.")
    sas = c.out("SAS slot / rating", f"{srule}*{d10}", "micron", fmt="#,##0")
    c.out("SAS slot / rating", f"{sas}/25400", "in", fmt="0.0000")

    c = sb.calc("Radial Clearance Check",
                eq="Clearance = (Casing ID - Screen OD) / 2",
                note="Adequate annulus needed for a good gravel pack around the screen.")
    csgid = c.link("Casing ID", "WD_CsgID", "in", fmt="0.000")
    scrod = c.inp("Screen OD (over wire wrap)", 5.5, "in", fmt="0.000")
    clr = c.out("Radial clearance", f"({csgid}-{scrod})/2", "in", fmt="0.000")
    c.out("Clearance status",
          f'IF({clr}>=0.75,"OK - adequate gravel annulus",'
          f'IF({clr}>=0.5,"MARGINAL - tight annulus",'
          f'"CHECK: INSUFFICIENT clearance - smaller screen or bigger casing"))',
          None, fmt="@")

    # ------------------------------------------------------------------
    sb.section("Gravel Pack Volumes")

    c = sb.calc("Screen-Casing Annulus Gravel Volume",
                eq="Cap [bbl/ft] = (CsgID^2 - ScrOD^2) / 1029.4;  "
                   "Gravel [lbm] = V [bbl] x 5.615 x bulk density [lb/ft3]",
                note="Uses BULK packed density (~58 lb/ft3 for sand gravel). The 9.7 lb/gal "
                     "figure sometimes quoted is the slurry absolute-volume convention - "
                     "NOT used here.")
    slen = c.inp("Screen + blank length", 120, "ft", fmt="#,##0")
    exc = c.inp("Washdown / rathole excess", 25, "%", fmt="0")
    bulk = c.inp("Gravel bulk (packed) density", 58, "lb/ft3", si=("kg/m3", 16.01846),
                 fmt="0.0",
                 note="Packed bulk density of gravel in the annulus (~58 lb/ft3).")
    cap = c.out("Annulus capacity", f"({csgid}^2-{scrod}^2)/1029.4", "bbl/ft",
                fmt="0.00000",
                note="Casing ID and screen OD from the Radial Clearance Check above.")
    gvol = c.out("Gross pack volume (with excess)", f"{cap}*{slen}*(1+{exc}/100)",
                 "bbl", fmt="0.00")
    glb = c.out("Gravel required", f"{gvol}*5.615*{bulk}", "lbm", fmt="#,##0")
    c.out("Gravel required", f"{glb}/100", None, fmt="#,##0.0", note="100-lb sacks")
    c.txt("Reserve", "Carry surface reserve gravel (typically +25-50%) for losses, "
                     "rathole fill and pressure-out contingency.")

    # ------------------------------------------------------------------
    sb.section("Proppant Selection (Frac / Frac Pack)")

    c = sb.calc("Closure Stress & Proppant Strength",
                eq="Closure ~ frac gradient x perf TVD;  "
                   "Max stress on proppant = closure - flowing BHP",
                note="Closure ~ frac pressure is a simplification - better closure comes "
                     "from a DFIT. Maximum effective stress occurs at lowest flowing BHP "
                     "(end of life).")
    fg = c.link("Fracture gradient", "WD_FracGrad", "psi/ft", fmt="0.000")
    resp = c.link("Reservoir pressure", "WD_ResP", "psi", fmt="#,##0",
                  note="Linked to Well Data - for reference / depletion adjustment.")
    ptvd = c.link("Perforation TVD", "WD_PerfTVD", "ft", fmt="#,##0")
    fbhp = c.inp("Flowing BHP at end of life", 1800, "psi", fmt="#,##0")
    clo = c.out("Closure pressure", f"{fg}*{ptvd}", "psi", fmt="#,##0")
    stress = c.out("Max effective closure stress on proppant", f"{clo}-{fbhp}", "psi",
                   fmt="#,##0")
    c.out("Proppant selection",
          f'IF({stress}<6000,"White sand (e.g. 20/40 Ottawa)",'
          f'IF({stress}<8000,"Resin-coated sand",'
          f'IF({stress}<10000,"Intermediate-strength ceramic",'
          f'"High-strength ceramic / bauxite")))',
          None, fmt="@")
    c.txt("Conductivity", "Check conductivity vs stress from vendor data; scale up mesh "
                          "size for higher conductivity where stress allows.")

    # ------------------------------------------------------------------
    sb.section("Tubing Sizing - Erosional Velocity (API RP 14E)")

    c = sb.calc("Erosional Velocity & Maximum Rate",
                eq="Ve = C/sqrt(rho_mix);  Q_max = Ve x A")
    cfac = c.inp("C factor", 100, None, fmt="#,##0",
                 note="100 for continuous non-corrosive service; up to 150-200 with "
                      "corrosion inhibition (API RP 14E).")
    rho = c.inp("Mixture density", 60, "lb/ft3", si=("kg/m3", 16.01846), fmt="0.0")
    tbgid = c.link("Tubing ID", "WD_TbgID", "in", fmt="0.000")
    ve = c.out("Erosional velocity", f"{cfac}/SQRT({rho})", "ft/s", fmt="0.00")
    area = c.out("Tubing flow area", f"PI()/4*{tbgid}^2/144", "ft2",
                 si=("m2", 0.09290304), fmt="0.0000")
    qmax = c.out("Max liquid rate at Ve", f"{ve}*{area}*86400/5.615", None, fmt="#,##0",
                 note="bbl/d")
    qexp = c.inp("Expected liquid rate", 1500, None, fmt="#,##0", note="bbl/d")
    c.out("Erosional status",
          f'IF({qexp}<={qmax},"OK - below erosional limit",'
          f'"CHECK: EXCEEDS erosional velocity - larger tubing or lower rate")',
          None, fmt="@")

    # ------------------------------------------------------------------
    sb.section("Gas Well Liquid Loading (Turner)")

    c = sb.calc("Turner Critical Velocity & Rate",
                eq="Vt = 20.4 x sigma^0.25 x (rho_l - rho_g)^0.25 / rho_g^0.5   "
                   "[ft/s, water; 1.2 x Coleman note]",
                note="Turner droplet model evaluated at wellhead conditions. Qc form: "
                     "Qc [MMscf/d] = 3.06 x P [psia] x Vt [ft/s] x A [ft2] / (T [degR] "
                     "x Z). Turner ~ 1.2 x Coleman (Coleman for low wellhead pressure "
                     "< ~500 psi).")
    sig = c.inp("Surface tension (sigma)", 60, "dyne/cm", fmt="0.0",
                note="~60 water, ~20 condensate.")
    rhol = c.inp("Liquid density", 67, "lb/ft3", si=("kg/m3", 16.01846), fmt="0.0")
    rhog = c.inp("Gas density at wellhead", 2.5, "lb/ft3", si=("kg/m3", 16.01846),
                 fmt="0.00",
                 note="Alternative: rho_g = 2.7 x SG x P / (T_R x Z).")
    whp = c.inp("Wellhead pressure", 300, "psi", fmt="#,##0")
    wht = c.inp("Wellhead temperature", 100, "degF", si=TEMP_F, fmt="0.0")
    c.inp("Gas specific gravity", 0.65, None, fmt="0.00",
          note="For the alternative gas density estimate rho_g = 2.7 x SG x P/(T_R x Z).")
    zf = c.inp("Gas Z factor at wellhead", 0.9, None, fmt="0.00")
    tid2 = c.link("Tubing ID", "WD_TbgID", "in", fmt="0.000")
    vt = c.out("Turner terminal velocity (Vt)",
               f"20.4*{sig}^0.25*({rhol}-{rhog})^0.25/{rhog}^0.5", "ft/s", fmt="0.00")
    a2 = c.out("Tubing flow area", f"PI()/4*{tid2}^2/144", "ft2",
               si=("m2", 0.09290304), fmt="0.0000")
    qc = c.out("Critical gas rate (Qc)",
               f"3.06*{whp}*{vt}*{a2}/(({wht}+460)*{zf})", None, fmt="0.00",
               note="MMscf/d; standard field form with P psia, T degR, A ft2.")
    qg = c.inp("Current gas rate", 1.2, None, fmt="0.00", note="MMscf/d")
    c.out("Liquid loading status",
          f'IF({qg}>={qc},"OK - above critical unloading rate",'
          f'"CHECK: below Turner critical - liquid loading likely; consider '
          f'plunger/velocity string")',
          None, fmt="@")

    # ------------------------------------------------------------------
    sb.section("Completion Design Notes")

    c = sb.calc("Rules of Thumb")
    c.txt("Screen flux", "Gravel pack screen flux guideline: < ~30-50 bpd per ft of "
                         "screen.")
    c.txt("Blank pipe", "Run 1.5-2x screen length of blank pipe as gravel reserve above "
                        "the top of the screen.")
    c.txt("Perforating", "Big-hole charges at 12 spf typical for cased-hole gravel pack "
                         "perforating.")
    c.txt("Placement", "Centralize screens; washpipe OD ~ 0.8 x screen base pipe ID for "
                       "good alpha-beta wave placement.")
