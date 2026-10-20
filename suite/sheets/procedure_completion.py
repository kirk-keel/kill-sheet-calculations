"""Completions: template completion procedure builder.

Step descriptions are yellow formula cells that embed live Well Data values
(WD_* defined names) so the wording tracks the current well; every step is
unlocked so the engineer edits it against the approved program before use.
"""
from ._procedure import ProcedureSheet


def build(wb):
    p = ProcedureSheet(
        wb, "Procedure - Completion", "completions",
        "Completion Procedure - Template Builder",
        "Step text pulls live values from Well Data (WD_* names) - edit every "
        "step against the approved program before use",
        description="Editable template completion procedure whose step text embeds "
                    "live Well Data values",
    )

    p.phase("A. Wellbore Preparation")
    p.step("Hold pre-job meeting; confirm completion program, permits, MOC "
           "register and barrier plan with all crews.", 2)
    p.step("Displace wellbore to filtered completion brine per the Completion "
           "Fluids sheet; density and inhibition package per program.", 8)
    p.step('="Run casing scraper and junk basket to "&TEXT(WD_MD,"#,##0")'
           '&" ft MD; work through liner top and nipple depths; recover and '
           'inspect junk basket contents."', 10)
    p.step("Circulate a minimum of two wellbore volumes; filter returns "
           "until turbidity meets program specification (typically < 20 "
           "NTU) before running the completion.", 6)
    p.step("Pressure test casing / liner lap per program; record charts in "
           "the completion file.", 3)

    p.phase("B. Lower Completion")
    p.step("Make up and RIH lower completion (screens / liner) per the "
           "Completion Design sheet gravel and screen selection; do not "
           "rotate through the build section unless the program allows.", 12)
    p.step("Set liner hanger / sump packer at program depth; verify "
           "set-down weight and pressure test the setting.", 4)
    p.step("Perform gravel pack per the Completion Design sheet pumping "
           "schedule; record rates, pressures and returns throughout.", 8)
    p.step("Reverse out excess carrier fluid; confirm full screen coverage "
           "from pump-in / returns behavior.", 4)
    p.step("Inflow test the lower completion barrier; monitor for a "
           "stabilized response per program acceptance criteria.", 4)

    p.phase("C. Upper Completion")
    p.step('="RIH "&TEXT(WD_TbgOD,"0.000")&" in OD x "&TEXT(WD_TbgID,"0.000")'
           '&" in ID production tubing; drift every joint and torque '
           'connections per the connection data sheet."', 18)
    p.step("Install control line(s) with protectors at every coupling; "
           "pressure test the control line at intervals per the Completion "
           "Equipment sheet.", None)
    p.step("Space out per the Completion Equipment sheet seal stroke "
           "calculation; confirm sting-in depth and available stroke.", 3)
    p.step('="Set production packer above the perforations (top perf at "'
           '&TEXT(WD_PerfTVD,"#,##0")&" ft TVD) per the running procedure; '
           'verify set with tubing pick-up / slack-off."', 4)
    p.step("Land and lock down tubing hanger; verify hanger neck seal test.", 3)
    p.step("Pressure test the A-annulus against the packer per program; "
           "record charts.", 3)

    p.phase("D. TRSV & Surface")
    p.step("Install / function test TRSV (open-close cycles) at the "
           "control-line operating pressure per the Completion Equipment "
           "sheet; record opening and closing signatures.", 3)
    p.step("Confirm nipple and plug profiles are clear with a drift or "
           "slickline gauge run to below the deepest profile.", 4)
    p.step("Nipple down BOP; install production tree; torque connections "
           "per manufacturer specification.", 8)
    p.step("Pressure test tree voids, connections and valves per program; "
           "function all tree valves and record.", 4)

    p.phase("E. Unload & Handover")
    p.step("Displace tubing to underbalance fluid or nitrogen cushion per "
           "the Perforating sheet cushion calculations.", 6)
    p.step('="Perforate on depth per program or open sleeves - interval at "'
           '&TEXT(WD_PerfTVD,"#,##0")&" ft TVD; correlate to the reference '
           'log before firing."', 6)
    p.step('="Flow the well for clean-up per the program choke schedule; '
           'anticipated reservoir pressure "&TEXT(WD_ResP,"#,##0")&" psi; '
           'sample until sand-free and BS&W stabilized."', 12)
    p.step("Shut in and record buildup as required; secure the well and "
           "verify barriers before rig-down.", 6)
    p.step("Compile and hand over the completion data pack: tallies, test "
           "charts, TRSV signatures and the as-built schematic.", 4)

    p.finish()
