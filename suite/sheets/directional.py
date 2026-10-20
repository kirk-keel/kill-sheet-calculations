"""Drilling: dogleg severity, minimum curvature, closure, build geometry, slide/rotate planning."""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "Directional Drilling", "drilling",
        "Directional Drilling",
        "Dogleg severity, minimum curvature surveys, closure, radius of curvature, build geometry, slide vs rotate",
        description="DLS, minimum curvature, closure and vertical section, build planning, slide/rotate split",
    )

    sb.section("Surveys & Dogleg")

    c = sb.calc("Dogleg Severity Between Two Surveys",
                eq="DL [deg] = ACOS( COS(I1) x COS(I2) + SIN(I1) x SIN(I2) x COS(A2 - A1) );   "
                   "DLS = DL x 100 / CL",
                note="I = inclination, A = azimuth, CL = course length (MD between surveys). "
                     "Typical limits: 3-5 deg/100 ft for drill pipe fatigue, less for casing running.")
    i1 = c.inp("Inclination at survey 1 (I1)", 20.0, "deg", fmt="0.00")
    a1 = c.inp("Azimuth at survey 1 (A1)", 45.0, "deg", fmt="0.00")
    i2 = c.inp("Inclination at survey 2 (I2)", 22.0, "deg", fmt="0.00")
    a2 = c.inp("Azimuth at survey 2 (A2)", 48.0, "deg", fmt="0.00")
    cl = c.inp("Course length (CL)", 100.0, "ft", fmt="0.0")
    dl = c.out("Dogleg angle (DL)",
               f"DEGREES(ACOS(COS(RADIANS({i1}))*COS(RADIANS({i2}))"
               f"+SIN(RADIANS({i1}))*SIN(RADIANS({i2}))*COS(RADIANS({a2}-{a1}))))",
               "deg", fmt="0.00")
    c.out("Dogleg severity (DLS)", f"{dl}*100/{cl}", "deg/100ft", fmt="0.00")

    c = sb.calc("Minimum Curvature Between Two Surveys",
                eq="RF = 2/DL x TAN(DL/2)  (DL in radians);   dTVD = CL/2 x (COS I1 + COS I2) x RF;   "
                   "dN = CL/2 x (SIN I1 x COS A1 + SIN I2 x COS A2) x RF;   "
                   "dE = CL/2 x (SIN I1 x SIN A1 + SIN I2 x SIN A2) x RF",
                note="Industry-standard survey calculation. RF = 1 when the dogleg is zero (straight course).")
    i1 = c.inp("Inclination at survey 1 (I1)", 20.0, "deg", fmt="0.00")
    a1 = c.inp("Azimuth at survey 1 (A1)", 45.0, "deg", fmt="0.00")
    i2 = c.inp("Inclination at survey 2 (I2)", 22.0, "deg", fmt="0.00")
    a2 = c.inp("Azimuth at survey 2 (A2)", 48.0, "deg", fmt="0.00")
    cl = c.inp("Course length (CL)", 100.0, "ft", fmt="0.0")
    dl = c.out("Dogleg angle (DL)",
               f"DEGREES(ACOS(COS(RADIANS({i1}))*COS(RADIANS({i2}))"
               f"+SIN(RADIANS({i1}))*SIN(RADIANS({i2}))*COS(RADIANS({a2}-{a1}))))",
               "deg", fmt="0.00")
    rf = c.out("Ratio factor (RF)",
               f"IF({dl}=0,1,2/RADIANS({dl})*TAN(RADIANS({dl})/2))", None, fmt="0.00000")
    c.out("Delta TVD", f"{cl}/2*(COS(RADIANS({i1}))+COS(RADIANS({i2})))*{rf}", "ft", fmt="0.00")
    c.out("Delta North", f"{cl}/2*(SIN(RADIANS({i1}))*COS(RADIANS({a1}))"
                         f"+SIN(RADIANS({i2}))*COS(RADIANS({a2})))*{rf}", "ft", fmt="0.00")
    c.out("Delta East", f"{cl}/2*(SIN(RADIANS({i1}))*SIN(RADIANS({a1}))"
                        f"+SIN(RADIANS({i2}))*SIN(RADIANS({a2})))*{rf}", "ft", fmt="0.00")

    c = sb.calc("Closure & Vertical Section",
                eq="Closure = SQRT(N^2 + E^2);   Closure azimuth = ATAN2(N, E);   "
                   "VS = closure x COS(VS azimuth - closure azimuth)",
                note="N and E are cumulative coordinates from the wellhead. Vertical section is the closure "
                     "projected onto the plan (target) direction.")
    nn = c.inp("Cumulative North (+N/-S)", 1450.0, "ft", fmt="#,##0.0")
    ee = c.inp("Cumulative East (+E/-W)", 1620.0, "ft", fmt="#,##0.0")
    vsaz = c.inp("Vertical section plane azimuth", 45.0, "deg", fmt="0.00")
    clo = c.out("Closure distance", f"SQRT({nn}^2+{ee}^2)", "ft", fmt="#,##0.0")
    caz = c.out("Closure azimuth", f"MOD(DEGREES(ATAN2({nn},{ee})),360)", "deg", fmt="0.00")
    c.out("Vertical section (VS)", f"{clo}*COS(RADIANS({vsaz}-{caz}))", "ft", fmt="#,##0.0")

    sb.section("Build Planning")

    c = sb.calc("Radius of Curvature & Build Section Length",
                eq="R [ft] = 18000 / (PI() x BUR);   MD_build = (I_end - I_start) x 100 / BUR",
                note="BUR in deg/100 ft. R is the radius of the build arc in the vertical plane.")
    bur = c.inp("Build-up rate (BUR)", 3.0, "deg/100ft", fmt="0.00")
    ist = c.inp("Starting inclination", 0.0, "deg", fmt="0.00")
    ien = c.inp("Ending inclination", 35.0, "deg", fmt="0.00")
    c.out("Radius of curvature (R)", f"18000/(PI()*{bur})", "ft", fmt="#,##0")
    c.out("Measured depth of build section", f"({ien}-{ist})*100/{bur}", "ft", fmt="#,##0")

    c = sb.calc("TVD & Displacement Through a Build from KOP",
                eq="TVD_eob = TVD_kop + R x SIN(I);   HD_eob = R x (1 - COS(I))",
                note="Vertical hole above the kick-off point, constant build to inclination I.")
    kop = c.inp("Kick-off point TVD", 2000, "ft", fmt="#,##0")
    bur = c.inp("Build-up rate (BUR)", 3.0, "deg/100ft", fmt="0.00")
    inc = c.inp("End-of-build inclination (I)", 35.0, "deg", fmt="0.00")
    r = c.out("Radius of curvature (R)", f"18000/(PI()*{bur})", "ft", fmt="#,##0")
    c.out("TVD at end of build", f"{kop}+{r}*SIN(RADIANS({inc}))", "ft", fmt="#,##0")
    c.out("Horizontal displacement at end of build", f"{r}*(1-COS(RADIANS({inc})))", "ft", fmt="#,##0")

    c = sb.calc("Build & Hold: TVD and Displacement at TD",
                eq="MD_tan = TD_md - KOP_md - MD_build;   TVD_td = KOP + R x SIN(I) + MD_tan x COS(I);   "
                   "HD_td = R x (1 - COS(I)) + MD_tan x SIN(I)",
                note="Vertical to KOP, constant build to hold angle I, straight tangent to TD.")
    kop = c.inp("Kick-off point MD (= TVD, vertical above)", 2000, "ft", fmt="#,##0")
    bur = c.inp("Build-up rate (BUR)", 3.0, "deg/100ft", fmt="0.00")
    inc = c.inp("Hold inclination (I)", 35.0, "deg", fmt="0.00")
    td = c.inp("Total depth (TD) measured depth", 10000, "ft", fmt="#,##0")
    r = c.out("Radius of curvature (R)", f"18000/(PI()*{bur})", "ft", fmt="#,##0")
    mtan = c.out("Tangent section length", f"{td}-{kop}-{inc}*100/{bur}", "ft", fmt="#,##0")
    c.out("TVD at TD", f"{kop}+{r}*SIN(RADIANS({inc}))+{mtan}*COS(RADIANS({inc}))", "ft", fmt="#,##0")
    c.out("Horizontal displacement at TD",
          f"{r}*(1-COS(RADIANS({inc})))+{mtan}*SIN(RADIANS({inc}))", "ft", fmt="#,##0")

    c = sb.calc("Slide vs Rotate Footage for Required Build",
                eq="Slide fraction = (BUR_req - BUR_rot) / (DLS_motor - BUR_rot);   "
                   "Slide ft per stand = fraction x L_stand",
                note="DLS_motor = motor yield while sliding (from bend setting and formation); BUR_rot = build/drop "
                     "tendency while rotating (negative if dropping). Plan the slide at the start of each stand "
                     "and confirm with surveys.")
    breq = c.inp("Required build rate", 3.0, "deg/100ft", fmt="0.00")
    brot = c.inp("Rotating build tendency", 0.3, "deg/100ft", fmt="0.00")
    my = c.inp("Motor yield while sliding", 8.0, "deg/100ft", fmt="0.00")
    lstand = c.inp("Stand length", 93.0, "ft", fmt="0.0")
    frac = c.out("Slide fraction", f"({breq}-{brot})/({my}-{brot})", None, fmt="0.000")
    sl = c.out("Slide footage per stand", f"{frac}*{lstand}", "ft", fmt="0.0")
    c.out("Rotate footage per stand", f"{lstand}-{sl}", "ft", fmt="0.0")
