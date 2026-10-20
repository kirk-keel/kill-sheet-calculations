"""Interventions: template intervention procedure builder.

Step descriptions are yellow formula cells that embed live Well Data values
(WD_* defined names) so the wording tracks the current well; every step is
unlocked so the engineer edits it against the approved program before use.
"""
from ._procedure import ProcedureSheet


def build(wb):
    p = ProcedureSheet(
        wb, "Procedure - Intervention", "interventions",
        "Intervention Procedure - Template Builder",
        "Step text pulls live values from Well Data (WD_* names) - edit every "
        "step against the approved program before use",
        description="Editable template intervention procedure whose step text "
                    "embeds live Well Data values",
    )

    p.phase("A. Planning & Barriers")
    p.step("Hold pre-job meeting; confirm intervention program, permits, MOC "
           "register, SIMOPS plan and emergency response arrangements.", 2)
    p.step("Confirm the two-barrier policy is satisfied for every planned "
           "operational step; document barriers on the barrier diagram and "
           "have it endorsed before rig-up.", 2)
    p.step("Function test SCSSV / TRSV; record closing time and leak rate "
           "against acceptance criteria before starting work.", 2)
    p.step('="Record wellhead pressures (tubing and all annuli) and compare '
           'to expected - reservoir pressure "&TEXT(WD_ResP,"#,##0")&" psi '
           'at "&TEXT(WD_PerfTVD,"#,##0")&" ft TVD."', 1)
    p.step("Rig up pressure control equipment; pressure test the PCE stack "
           "per the Surface Rig-Up sheet line test - low pressure then high "
           "pressure holds against the program test values.", 4)

    p.phase("B. Kill / Pressure Control (if required)")
    p.step('="If a kill is required: bullhead kill fluid per the Well Kill - '
           'Interventions sheet - density to balance "&TEXT(WD_ResP,"#,##0")'
           '&" psi at "&TEXT(WD_PerfTVD,"#,##0")&" ft TVD plus overbalance '
           'per program."', 6)
    p.step('="Do not exceed the formation fracture limit while bullheading - '
           'fracture gradient "&TEXT(WD_FracGrad,"0.000")&" psi/ft at the '
           'perforations; stage rates accordingly."', None, 30)
    p.step("Alternatively lubricate and bleed in stages; record injected "
           "volumes and bled pressures each cycle.", None)
    p.step("Confirm the well is dead / stable; observe for the minimum "
           "period per program before breaking containment.", 2)

    p.phase("C. Intervention Execution")
    p.step("Verify stem weight is sufficient against wellhead pressure per "
           "the Wireline sheet stem / fall-back check before opening the "
           "well to run in.", 1)
    p.step("RIH with the toolstring observing speed limits per the Wireline "
           "and Trip Speed sheets; slow through restrictions, known "
           "profiles and across fluid interfaces.", 4)
    p.step('="Tag and correlate depth - reference the tally to "'
           '&TEXT(WD_MD,"#,##0")&" ft MD; adjust for stretch per the '
           'Wireline sheet before any setting or firing operation."', 2)
    p.step("Perform the programmed task (set / pull plug, shift sleeve, "
           "bail, perforate, log); record all weights, depths and times.", 6)
    p.step("Confirm tool function / result before pulling out (pressure "
           "response, mechanical indicator or gauge run as applicable).", 2)

    p.phase("D. Return to Production")
    p.step("Pull out of hole staging at the speed limits; slow through the "
           "lubricator entry and all restrictions.", 4)
    p.step("Close and test barriers in reverse order; verify each barrier "
           "before removing the next containment element.", 3)
    p.step("Function test the TRSV; confirm closure and inflow test against "
           "acceptance criteria.", 2)
    p.step("Rig down PCE; restore the tree and pressure test every "
           "connection that was broken.", 4)
    p.step("Unload / bring the well back on line per the program choke "
           "schedule; monitor for sand and solids during clean-up.", 6)
    p.step("Monitor well and annulus pressures for 24 hours; hand over with "
           "the job report, tallies and barrier verification records.", None)

    p.finish()
