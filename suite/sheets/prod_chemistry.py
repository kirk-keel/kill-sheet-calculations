"""Completions: production chemistry - CO2/H2S corrosion screening, material
selection, hydrate formation and inhibition, scale screening.

After Bellarby, "Well Completion Design" (production chemistry / materials
selection chapter). All correlations are screening-level; lab and vendor
verification required before committing metallurgy or chemical programs.
"""
from ..builder import SheetBuilder
from ..convert import TEMP_F


def build(wb):
    sb = SheetBuilder(
        wb, "Production Chemistry", "completions",
        "Production Chemistry & Materials Screening",
        "CO2/H2S partial pressures, corrosion rate, material selection screen, "
        "hydrate formation and inhibitor dosing, scale screening",
        description="CO2/H2S corrosion screening, material selection, hydrate "
                    "formation and inhibition, scale screening (Bellarby-style)",
    )

    # ------------------------------------------------------------ CO2
    sb.section("CO2 Corrosion")

    c = sb.calc("CO2 Partial Pressure & Severity",
                eq="pCO2 [psi] = mol% CO2 / 100 x P_res",
                note="Partial pressure taken at reservoir pressure - worst case "
                     "for the completion. Use flowing pressure at the point of "
                     "interest for local checks.")
    pres = c.link("Reservoir pressure (P_res)", "WD_ResP", "psi", fmt="#,##0")
    co2 = c.inp("CO2 content", 2.0, "mol %", fmt="0.00")
    bht = c.inp("Bottomhole temperature", 180, "degF", si=TEMP_F, fmt="#,##0")
    pco2 = c.out("CO2 partial pressure (pCO2)", f"{co2}/100*{pres}", "psi", fmt="0.0")
    c.out("CO2 severity",
          f'IF({pco2}<7,"OK - carbon steel acceptable",'
          f'IF({pco2}<30,"MARGINAL - carbon steel + continuous inhibition",'
          f'"CHECK: corrosive - CRA (13Cr or better) indicated"))',
          None, fmt="@",
          note="7 / 30 psi pCO2 rules of thumb are screening only - actual "
               "corrosivity depends on temperature, water chemistry, wetting "
               "and flow regime.")

    c = sb.calc("de Waard-Milliams Corrosion Rate (1975 nomogram form)",
                eq="CR [mm/yr] = 10^(5.8 - 1710/T_K + 0.67 x LOG10(pCO2_bar))",
                note="de Waard & Milliams (1975), screening form. Uninhibited, "
                     "worst-case: no scaling, wetting, pH or velocity "
                     "corrections. Overpredicts above ~ 60 degC where protective "
                     "FeCO3 films form. Uses pCO2 and bottomhole temperature "
                     "from the block above.")
    pbar = c.out("CO2 partial pressure", f"{pco2}*0.0689476", "bar", fmt="0.000",
                 note="pCO2 [bar] = pCO2 [psi] x 0.0689476")
    c.out("Uninhibited corrosion rate (CR)",
          f"10^(5.8-1710/(({bht}-32)/1.8+273.15)+0.67*LOG10({pbar}))",
          "mm/yr", fmt="0.0",
          note="T_K = (T [degF] - 32)/1.8 + 273.15")

    # ------------------------------------------------------------ H2S
    sb.section("H2S & Sour Service (NACE MR0175 / ISO 15156)")

    c = sb.calc("H2S Partial Pressure & Sour-Service Threshold",
                eq="pH2S [psi] = mol% H2S / 100 x P_res",
                note="MR0175/ISO 15156 sour-service threshold: pH2S >= 0.05 psia "
                     "(0.0034 bar). Uses reservoir pressure linked above.")
    h2s = c.inp("H2S content", 0.002, "mol %", fmt="0.0000")
    ph2s = c.out("H2S partial pressure (pH2S)", f"{h2s}/100*{pres}", "psi",
                 fmt="0.0000")
    c.out("Sour-service status",
          f'IF({ph2s}>=0.05,'
          f'"CHECK: sour service - MR0175 materials required (max 22 HRC CS, sour-rated CRAs)",'
          f'"OK - non-sour per MR0175 threshold 0.05 psia")',
          None, fmt="@",
          note="Sour service restricts hardness (carbon steel max 22 HRC) and "
               "limits many CRAs by temperature/chloride/pH2S domain.")

    # ------------------------------------------------------------ materials
    sb.section("Material Selection Screen")

    c = sb.calc("Tubing Metallurgy First-Pass Screen",
                eq="Nested IF on pH2S (sour split), pCO2, temperature, chlorides",
                note="First-pass screen in the style of Bellarby's material "
                     "selection charts, using pCO2 and pH2S from the sections "
                     "above. Screening only - verify with NACE MR0175/ISO 15156 "
                     "domain limits, lab testing and vendor data before "
                     "selection.")
    cl = c.inp("Chloride content", 50000, "mg/L", fmt="#,##0")
    tmax = c.inp("Maximum temperature", 250, "degF", si=TEMP_F, fmt="#,##0")
    c.out("Indicated material class",
          f'IF({ph2s}>=0.05,'
          f'IF({pco2}<7,"Carbon steel (sour-rated, max 22 HRC)",'
          f'"S13Cr / duplex - verify sour limits vs chlorides"),'
          f'IF({pco2}<7,"Carbon steel",'
          f'IF(AND({tmax}<300,{cl}<50000),"13Cr","S13Cr or 22Cr duplex")))',
          None, fmt="@",
          note="Sweet 13Cr screen limited here to < 300 degF and < 50,000 mg/L "
               "chlorides; beyond that step up to super-13Cr or 22Cr duplex.")

    # ------------------------------------------------------------ hydrates
    sb.section("Hydrate Formation")

    c = sb.calc("Hydrate Formation Temperature (Towler & Mokhatab 2005)",
                eq="Thyd [degF] = 13.47 x LN(P) + 34.27 x LN(SG) "
                   "- 1.675 x LN(P) x LN(SG) - 20.35",
                note="Towler & Mokhatab (2005) correlation, P in psia, sweet "
                     "natural gas SG 0.55-1.0. Screening only - H2S/CO2 shift "
                     "the curve; use a thermodynamic model for design.")
    sg = c.inp("Gas specific gravity (air = 1)", 0.65, None, fmt="0.000")
    p = c.inp("Pressure at point of interest", 2000, "psi", fmt="#,##0",
              note="Absolute pressure (psia).")
    tamb = c.inp("Ambient / seabed temperature", 60, "degF", si=TEMP_F,
                 fmt="#,##0")
    thyd = c.out("Hydrate formation temperature (Thyd)",
                 f"13.47*LN({p})+34.27*LN({sg})-1.675*LN({p})*LN({sg})-20.35",
                 "degF", si=TEMP_F, fmt="0.0")
    mgn = c.out("Margin above hydrate curve", f"{tamb}-{thyd}", "degF",
                si=("degC", lambda ref: f"={ref}/1.8"), fmt="0.0",
                note="Margin = T_ambient - Thyd. Positive = operating above "
                     "(outside) the hydrate curve.")
    c.out("Hydrate status",
          f'IF({mgn}>=10,"OK - outside hydrate region",'
          f'IF({mgn}>=0,"MARGINAL - near hydrate curve",'
          f'"CHECK: inside hydrate region - inhibit or insulate"))',
          None, fmt="@")

    c = sb.calc("Hammerschmidt Inhibitor Dosing",
                eq="dT = K x W / (M x (100 - W))  ->  "
                   "W [wt%] = 100 x dT x M / (K + dT x M);  K = 2335",
                note="Hammerschmidt (1934) equation, K = 2335 (degF basis). "
                     "Valid to roughly 20-25 wt% inhibitor in the water phase - "
                     "beyond that use Nielsen-Bucklin or a thermodynamic model. "
                     "W is wt% in the aqueous phase, not of total liquids.")
    dt = c.out("Required hydrate depression (dT)",
               f"MAX(0,{thyd}-{tamb}+5)", "degF",
               si=("degC", lambda ref: f"={ref}/1.8"), fmt="0.0",
               note="dT = MAX(0, Thyd - T_ambient + 5 degF margin)")
    c.out("Methanol required (M = 32)",
          f"100*{dt}*32/(2335+{dt}*32)", "wt%", fmt="0.0",
          note="wt% methanol in the water phase.")
    c.out("MEG required (M = 62)",
          f"100*{dt}*62/(2335+{dt}*62)", "wt%", fmt="0.0",
          note="wt% mono-ethylene glycol in the water phase.")

    # ------------------------------------------------------------ scale
    sb.section("Scale & Deposition Screening")

    c = sb.calc("Deposition Screening Checklist",
                note="Qualitative screens - confirm with water analyses and lab "
                     "models before designing the chemical program.")
    c.txt("CaCO3 scale",
          "Risk rises with pressure drop (CO2 flashes off) and temperature "
          "increase - worst at chokes, SSSVs, pumps and perforations.")
    c.txt("BaSO4 / SrSO4 scale",
          "Driven by injection-water mixing (sulphate-rich seawater + "
          "barium/strontium formation water) - run a ScaleChem-type mixing "
          "model on the water analyses.")
    c.txt("Wax",
          "Wax appearance temperature (WAT) from lab measurement - keep "
          "flowing temperature above WAT + 10 degF or provide insulation / "
          "chemicals / pigging.")
    c.txt("Asphaltenes",
          "Onset screening via de Boer plot (in-situ density vs "
          "undersaturation P_res - P_bubble) - light, highly undersaturated "
          "oils are the usual offenders.")

    c = sb.calc("Langelier Saturation Index (water scaling quick screen)",
                eq="LSI = pH - pHs;  pHs = (9.3 + A + B) - (C + D);  "
                   "A = (LOG10(TDS)-1)/10;  B = -13.12 x LOG10(T_K) + 34.55;  "
                   "C = LOG10(Ca) - 0.4;  D = LOG10(alk)",
                note="Langelier (1936) index for CaCO3 in low-ionic-strength "
                     "water - use Stiff-Davis for oilfield brines. Positive LSI "
                     "= CaCO3 scaling tendency.")
    ph = c.inp("Water pH", 6.8, None, fmt="0.00")
    tds = c.inp("Total dissolved solids (TDS)", 35000, "mg/L", fmt="#,##0")
    ca = c.inp("Calcium hardness as CaCO3", 250, "mg/L", fmt="#,##0")
    alk = c.inp("Alkalinity as CaCO3", 300, "mg/L", fmt="#,##0")
    tw = c.inp("Water temperature", 150, "degF", si=TEMP_F, fmt="#,##0")
    phs = c.out("Saturation pH (pHs)",
                f"(9.3+(LOG10({tds})-1)/10+(-13.12*LOG10(({tw}-32)/1.8+273.15)+34.55))"
                f"-((LOG10({ca})-0.4)+LOG10({alk}))",
                None, fmt="0.00",
                note="T_K = (T [degF] - 32)/1.8 + 273.15")
    lsi = c.out("Langelier saturation index (LSI)", f"{ph}-{phs}", None,
                fmt="0.00")
    c.out("Scaling status",
          f'IF({lsi}>0.5,"CHECK: scaling likely - inhibition required",'
          f'IF({lsi}>0,"MARGINAL - scaling tendency",'
          f'"OK - non-scaling tendency"))',
          None, fmt="@")
