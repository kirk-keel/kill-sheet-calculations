"""Completions: completion equipment - TRSV/control line, hydraulic packer
setting, space-out and seal stroke, packer envelope, nipple profile ladder.

After Bellarby, "Well Completion Design" (completion equipment chapter).
Vendor data governs all ratings - these are planning checks.
"""
from ..builder import SheetBuilder
from ..convert import TEMP_F


def build(wb):
    sb = SheetBuilder(
        wb, "Completion Equipment", "completions",
        "Completion Equipment Checks",
        "TRSV setting depth and control line pressure, hydraulic packer "
        "setting, space-out / seal stroke, packer envelope, nipple ladder",
        description="TRSV/control line, hydraulic packer setting, seal stroke "
                    "space-out, packer envelope and nipple profile checks",
    )

    # ------------------------------------------------------- TRSV
    sb.section("TRSV / Safety Valve & Control Line")

    c = sb.calc("Control Line Pressure & Setting Depth",
                eq="P_hyd_CL = 0.433 x SG x TVD;  P_surf = P_open + P_tbg - P_hyd_CL",
                note="Deep-set valves need hydrostatic-balanced or "
                     "nitrogen-charged designs; verify slam-closure rating "
                     "with the vendor.")
    dep = c.inp("Valve setting depth (TVD)", 1500, "ft", fmt="#,##0")
    sg = c.inp("Control line fluid SG", 1.02, None, fmt="0.000")
    pop = c.inp("Valve full-open operating pressure", 2500, "psi", fmt="#,##0",
                note="Bench value at zero ambient (at-depth differential to "
                     "open and hold the flapper/flow tube).")
    ptbg = c.inp("Tubing pressure at valve during operation", 1500, "psi",
                 fmt="#,##0")
    dmax = c.inp("Vendor max fail-safe setting depth", 2000, "ft", fmt="#,##0")
    phyd = c.out("Control line hydrostatic at valve",
                 f"0.433*{sg}*{dep}", "psi", fmt="#,##0",
                 note="P_hyd_CL [psi] = 0.433 x SG x TVD [ft]")
    c.out("Required surface control pressure",
          f"MAX(0,{pop}+{ptbg}-{phyd})", "psi", fmt="#,##0",
          note="Surface pressure to hold the valve fully open against tubing "
               "pressure, net of control line hydrostatic.")
    c.out("Setting depth status",
          f'IF({dep}<={dmax},"OK - within fail-safe depth rating",'
          f'"CHECK: EXCEEDS fail-safe setting depth - deeper spring/mag coupling valve required")',
          None, fmt="@",
          note="Fail-safe closure relies on the spring beating control line "
               "hydrostatic - depth-limited per vendor.")

    # ------------------------------------------------------- packer setting
    sb.section("Hydraulic Packer Setting")

    c = sb.calc("Setting Pressure from Shear Pins",
                eq="F_shear = n x F_pin;  P_set = F_shear / A_piston;  "
                   "P_applied = P_set + margin",
                note="Requires a plug or ball on seat below the packer to "
                     "pressure up against - verify plug/ball seat depth and "
                     "retrieval plan before running.")
    n = c.inp("Number of shear pins", 5, None, fmt="#,##0")
    fp = c.inp("Rating per pin", 2000, "lbf", fmt="#,##0")
    ap = c.inp("Setting piston area", 6.0, "in2", fmt="0.00")
    mgn = c.inp("Applied pressure margin", 500, "psi", fmt="#,##0")
    brst = c.inp("Tubing burst (derated)", 7700, "psi", fmt="#,##0",
                 note="Derated tubing burst at the weak point of the string.")
    fs = c.out("Total shear value", f"{n}*{fp}", "lbf", fmt="#,##0")
    ps = c.out("Setting pressure required", f"{fs}/{ap}", "psi", fmt="#,##0")
    pa = c.out("Recommended applied surface pressure", f"{ps}+{mgn}", "psi",
               fmt="#,##0",
               note="Plus/minus hydrostatic differences if the plug is deep "
                    "and fluid weights differ inside/outside the tubing.")
    c.out("Applied pressure vs tubing burst",
          f'IF({pa}<=0.8*{brst},"OK - comfortable vs tubing burst",'
          f'IF({pa}<={brst},"MARGINAL - close to tubing rating",'
          f'"CHECK: EXCEEDS tubing rating - reduce pins or bigger piston"))',
          None, fmt="@")

    # ------------------------------------------------------- space-out
    sb.section("Space-Out & Seal Stroke")

    c = sb.calc("Seal Stroke vs Predicted Tubing Movement",
                eq="Stroke_req = movement x SF;  compare to stroke available",
                note="For latched (anchored) tubing, movement converts to "
                     "force - run the Tubing Stress Analysis sheet instead.")
    mov = c.inp("Total predicted tubing movement", 36, "in", fmt="0.0",
                note="From the Tubing & Packer Forces sheet - enter the total "
                     "length change (sum of piston, ballooning, buckling and "
                     "temperature terms).")
    stk = c.inp("Seal assembly stroke available", 120, "in", fmt="0.0")
    sf = c.inp("Movement safety factor", 1.5, None, fmt="0.00")
    req = c.out("Required stroke", f"{mov}*{sf}", "in", fmt="0.0")
    c.out("Seal stroke status",
          f'IF({stk}>={req},"OK - seal stroke sufficient",'
          f'IF({stk}>={mov},"MARGINAL - stroke less than factored movement",'
          f'"CHECK: INSUFFICIENT seal stroke - longer seal assembly or anchor latch"))',
          None, fmt="@")

    # ------------------------------------------------------- packer envelope
    sb.section("Packer Envelope Checks")

    c = sb.calc("Differential & Temperature vs Packer Ratings",
                eq="Utilization [%] = expected / rating x 100;  "
                   "flags at 80% and 100%",
                note="Check the full packer performance envelope "
                     "(pressure/tension/compression combined) against vendor "
                     "curves - these single-axis checks are screening only.")
    prat = c.inp("Packer differential rating", 7500, "psi", fmt="#,##0")
    pexp = c.inp("Max expected differential (above-below)", 5200, "psi",
                 fmt="#,##0")
    trat = c.inp("Packer temperature rating", 300, "degF", si=TEMP_F,
                 fmt="#,##0")
    texp = c.inp("Max expected temperature", 250, "degF", si=TEMP_F,
                 fmt="#,##0")
    du = c.out("Differential utilization", f"{pexp}/{prat}*100", "%", fmt="0.0")
    c.out("Differential status",
          f'IF({du}<=80,"OK - within differential rating",'
          f'IF({du}<=100,"MARGINAL - above 80% of differential rating",'
          f'"CHECK: EXCEEDS packer differential rating"))',
          None, fmt="@")
    tu = c.out("Temperature utilization", f"{texp}/{trat}*100", "%", fmt="0.0")
    c.out("Temperature status",
          f'IF({tu}<=80,"OK - within temperature rating",'
          f'IF({tu}<=100,"MARGINAL - above 80% of temperature rating",'
          f'"CHECK: EXCEEDS packer temperature rating"))',
          None, fmt="@",
          note="Elastomer and slip ratings both derate with temperature - "
               "confirm element system for the expected life-of-well range.")

    # ------------------------------------------------------- nipple ladder
    sb.section("Nipple Profile Ladder")

    c = sb.calc("Nipple ID Step-Down Check",
                eq="Each nipple ID must be smaller than the one above",
                note="No-go profiles land on the ID step; selective profiles "
                     "allow same-size stacking but need selective running "
                     "tools. Keep the largest possible IDs for future "
                     "intervention access.")
    n1 = c.inp("Nipple ID - top", 2.813, "in", fmt="0.000")
    n2 = c.inp("Nipple ID - upper-middle", 2.750, "in", fmt="0.000")
    n3 = c.inp("Nipple ID - lower-middle", 2.688, "in", fmt="0.000")
    n4 = c.inp("Nipple ID - bottom", 2.562, "in", fmt="0.000")
    c.out("Ladder status",
          f'IF(AND({n1}>{n2},{n2}>{n3},{n3}>{n4}),'
          f'"OK - IDs step down toward bottom (through-tubing access preserved)",'
          f'"CHECK: nipple IDs do not step down - tools cannot pass")',
          None, fmt="@")

    # ------------------------------------------------------- running notes
    sb.section("Completion Running Notes")

    c = sb.calc("Running Checklist",
                note="Free-text reminders - no calculations.")
    c.txt("Running speed",
          "Reference the Trip Speed Schedule sheet for surge-safe running "
          "speeds - swab/surge limits apply to the completion too.")
    c.txt("Drift & crossovers",
          "Drift all tubulars on the pipe deck; count and log every crossover "
          "in the running tally.")
    c.txt("TRSV function test",
          "Function-test the TRSV at surface and again after spacing out, "
          "before displacing to the packer fluid.")
    c.txt("Well file",
          "Record the final space-out and landed weight for the well file - "
          "future workovers depend on them.")
