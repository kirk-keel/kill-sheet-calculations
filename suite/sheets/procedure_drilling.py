"""Drilling: template drilling procedure builder.

Step descriptions are yellow formula cells that embed live Well Data values
(WD_* defined names) so the wording tracks the current well; every step is
unlocked so the engineer edits it against the approved program before use.
"""
from ._procedure import ProcedureSheet


def build(wb):
    p = ProcedureSheet(
        wb, "Procedure - Drilling", "drilling",
        "Drilling Procedure - Template Builder",
        "Step text pulls live values from Well Data (WD_* names) - edit every "
        "step against the approved program before use",
        description="Editable template drilling procedure whose step text embeds "
                    "live Well Data values",
    )

    p.phase("A. Rig Up & Spud")
    p.step("Hold pre-spud meeting; confirm drilling permit, MOC register, rig "
           "acceptance and third-party equipment certification are current.", 2)
    p.step("Nipple up BOP stack and choke manifold; pressure test to 250 psi "
           "low / 5,000 psi high; record on test charts and log in the BOP "
           "test register.", 6)
    p.step("Function test accumulator per API Std 53; verify bottle precharge "
           "and closing times against acceptance criteria.", 2)
    p.step("Spud well; drill conductor / surface hole with spud mud at "
           "controlled ROP through the unconsolidated section.", 12)
    p.step("Line up flow paddle, pit volume totalizer, trip tank and gas "
           "detection; verify alarms with the driller before drilling ahead.", 1)

    p.phase("B. Surface Hole & Casing")
    p.step("Drill surface hole to section TD; pump hi-vis sweeps every stand "
           "and monitor cuttings returns at the shakers.", 18)
    p.step("Perform wiper trip and condition mud; confirm the hole is clean "
           "before pulling out to run casing.", 6)
    p.step("Run surface casing with centralizers per program; fill every "
           "joint and monitor displacement against the trip sheet.", 8)
    p.step("Cement surface casing; confirm cement returns to surface; record "
           "densities, rates and lift pressure.", 6)
    p.step("Wait on cement per program; nipple up and test wellhead / BOP "
           "connections; pressure test casing per program.", 8)
    p.step('="Drill out shoe track plus ~10 ft of new formation; perform '
           'FIT/LOT to "&TEXT(WD_LOT,"0.0")&" ppg EMW; record result and '
           'update Well Data (WD_LOT)."', 3)

    p.phase("C. Intermediate / Build Section")
    p.step('="Displace to drilling mud of "&TEXT(WD_OMW,"0.0")&" ppg per '
           'program; verify mud properties (PV/YP) against the mud program '
           'before drilling ahead."', 3)
    p.step("Kick off at the planned KOP and build angle per the Directional "
           "Survey sheet well plan; survey every stand and compare to plan.", 24)
    p.step('="Monitor ECD against the LOT of "&TEXT(WD_LOT,"0.0")&" ppg EMW '
           'while drilling the build section; keep ECD below LOT with margin '
           'per program."', None, 30)
    p.step("Record torque and drag roadmap each trip and compare against the "
           "Torque & Drag sheet; ream tight spots only as required.", None)
    p.step('="Run and cement intermediate casing; shoe planned at "'
           '&TEXT(WD_ShoeMD,"#,##0")&" ft MD / "&TEXT(WD_ShoeTVD,"#,##0")'
           '&" ft TVD; test shoe after drill-out."', 24)

    p.phase("D. Production Hole to TD")
    p.step('="Drill out shoe track; drill "&TEXT(WD_HoleDiam,"0.00")&" in '
           'production hole; establish drilling parameters per the Hydraulics '
           'and Bit Hydraulics sheets."', 6)
    p.step('="Drill ahead to TD at "&TEXT(WD_MD,"#,##0")&" ft MD / "'
           '&TEXT(WD_TVD,"#,##0")&" ft TVD; survey per program and geosteer '
           'to the target."', 48)
    p.step("Manage hole cleaning per the Hole Cleaning sheet - maintain "
           "minimum flow rate and pipe rotation; pump sweeps in the lateral "
           "as required.", None)
    p.step("Circulate hole clean at TD - minimum two bottoms-up; confirm "
           "shakers clean before the flow check.", 4)
    p.step("Flow check; pull out per the Trip Schedule sheet speed limits "
           "with the trip sheet monitored against calculated displacement.", 8)
    p.step("Rig up and run evaluation logs per program; interpret against "
           "the Log Interpretation program note before casing point call.", 12)

    p.phase("E. Contingency - Well Control")
    p.step("On any positive flow check or unexplained pit gain: space out, "
           "shut the well in per the station bill (hard shut-in); note the "
           "time and alert the toolpusher and company representative.", None)
    p.step("Record stabilized SIDPP, SICP and pit gain on the Kill Sheet; "
           "verify gauge readings on two independent gauges.", None)
    p.step('="Kill the well per the Kill Sheet: circulate at the kill rate '
           'of "&TEXT(WD_KillRate,"#,##0")&" spm using the "'
           '&TEXT(WD_SCR,"#,##0")&" psi SCR reference; follow the drillpipe '
           'pressure schedule."', None, 30)
    p.step('="Do not exceed MAASP - shoe integrity is "&TEXT(WD_LOT,"0.0")'
           '&" ppg EMW at the "&TEXT(WD_ShoeTVD,"#,##0")&" ft TVD shoe; '
           'monitor casing pressure throughout the kill."', None, 30)
    p.step("Flow check after the kill; confirm the well is dead, weight up "
           "per program and resume operations only after MOC review.", None)

    p.finish()
