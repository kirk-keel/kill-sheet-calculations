"""Spot-check hand-verified engineering values in the built workbook.

Usage:  python spot_check.py [workbook.xlsx]

Finds each (sheet, row label) in column A via openpyxl, then compares the
recalculated column-B value (via `formulas`) with the hand-computed answer.
"""
import sys

import openpyxl

# (sheet name, column-A label, expected value, rel tolerance)
CHECKS = [
    ("Mud & Hydrostatics", "Hydrostatic pressure (P_hyd)", 6500.0, 1e-6),
    ("Mud & Hydrostatics", "Blended density", 10.875, 1e-6),
    ("Mud & Hydrostatics", "Barite required", 546.98, 1e-2),
    ("Mud & Hydrostatics", "Equivalent circulating density", 12.8846, 1e-4),
    # horizontal-well example: TVD 5573, MD 10500, SIDPP 500, SCR 750
    ("Kill Sheet", "Kill mud weight (exact)", 14.22535, 1e-5),
    ("Kill Sheet", "Kill mud weight (rounded up)", 14.3, 1e-9),
    ("Kill Sheet", "Initial circulating pressure (ICP)", 1250.0, 1e-9),
    ("Kill Sheet", "Final circulating pressure (FCP)", 858.0, 1e-9),
    # rounding rule 2: maximized values round UP to whole psi (782.449 -> 783)
    ("Kill Sheet", "MAASP (initial, with current mud)", 783.0, 1e-9),
    # rounding rule 3: psi/step rounds DOWN ((1250-858)/1755*100 = 22.34 -> 22)
    ("Kill Sheet", "Pressure drop per 100 strokes (vertical well)", 22.0, 1e-9),
    # rounding rule 1: kill weight density rounds UP to nearest 0.1 (13.198 -> 13.2)
    ("Well Control", "Kill mud weight (KMW, rounded up)", 13.2, 1e-9),
    ("Kill Sheet", "Formation pressure", 4122.45, 1e-4),
    # string table: 9700 ft 4.276" ID + 500 ft 3" ID + 300 ft 2.8125" ID
    ("Kill Sheet", "Drill string volume", 178.968, 1e-3),
    ("Kill Sheet", "Strokes surface to bit", 1755.0, 1e-9),
    # minimum-curvature TVD in the lateral (MD 8000) of the example survey
    ("Directional Survey", "TVD at that MD", 5572.955, 1e-4),
    # T&D vs independent Johancsik implementation (12.5 ppg, mu .25/.30, WOB 15k)
    ("Torque & Drag", "Buoyancy factor", 0.80916, 1e-4),
    ("Torque & Drag", "Pick-up hookload", 231.19, 1e-3),
    ("Torque & Drag", "Slack-off hookload", 113.94, 1e-3),
    ("Torque & Drag", "Surface torque (rotating)", 13480.6, 1e-3),
    # CCI = K x AV x MW / 400000 with PV 15, YP 12, 600 gpm in 8.5 x 5
    ("Hole Cleaning", "Carrying capacity index (CCI)", 2.524, 5e-3),
    # Vogel IPR x simplified VLP intersection (hand interpolation)
    ("Nodal Analysis", "Operating rate (Qop)", 1379.3, 1e-2),
    # subsea: ROUNDUP(783 - 250 CLF) - rounding rule 2 applies
    ("Kill Sheet - Subsea", "Dynamic MAASP (circulating up choke line)", 533.0, 1e-9),
    # ESP: TDH = 900x2.31/1.02 lift terms + 20 ft/kft friction + THP head
    ("ESP Design", "Total dynamic head (TDH)", 3809.47, 1e-3),
    ("ESP Design", "Stages required", 153.0, 1e-9),
    # rod pump: 0.1166 x 86 x 8 x 1.5^2
    ("Rod Pump Design", "Pump displacement (100% eff)", 180.50, 1e-3),
    # completion design: Saucier 6 x 150 micron; API RP 14E 100/sqrt(60)
    ("Completion Design", "Uniformity coefficient (UC)", 4.0909, 1e-3),
    ("Completion Design", "Gravel median size (Saucier)", 900.0, 1e-6),
    ("Completion Design", "Erosional velocity", 12.910, 1e-3),
    # tubing stress: hand-computed with 3.5 x 2.992 L-80 at 5573 ft packer
    ("Tubing Stress Analysis", "Steel cross-section (As)", 2.59019, 1e-4),
    ("Tubing Stress Analysis", "Burst rating (API wall tolerance)", 10160.0, 1e-4),
    ("Tubing Stress Analysis", "von Mises equivalent (A, packer)", 17943.0, 2e-3),
    # log interpretation: Archie with Rw .05, Rt 20, phi .22, a=1, m=n=2
    ("Log Interpretation", "Water saturation (Archie)", 0.22727, 1e-3),
    # rig-up example: 84 ft of 1502 iron, valves are the 1.69-in restriction
    ("Surface Rig-Up", "Total iron footage", 84.0, 1e-6),
    ("Surface Rig-Up", "Minimum ID (restriction)", 1.69, 1e-6),
]


def main(path):
    import formulas

    wb = openpyxl.load_workbook(path)
    targets = []
    for sheet, label, expected, tol in CHECKS:
        ws = wb[sheet]
        found = None
        for row in ws.iter_rows(min_col=1, max_col=1):
            if row[0].value == label:
                found = row[0].row
                break
        if found is None:
            print(f"MISSING LABEL  {sheet}!{label}")
            continue
        targets.append((sheet, label, f"B{found}", expected, tol))

    xl = formulas.ExcelModel().loads(path).finish()
    sol = xl.calculate()
    book = path.replace("\\", "/").split("/")[-1]
    fails = 0
    for sheet, label, addr, expected, tol in targets:
        key = f"'[{book}]{sheet.upper()}'!{addr}"
        try:
            got = sol[key].value[0, 0]
        except KeyError:
            print(f"NO CELL  {key}")
            fails += 1
            continue
        ok = abs(got - expected) <= tol * max(1.0, abs(expected))
        print(f"{'PASS' if ok else 'FAIL'}  {sheet}!{addr}  {label}: got {got:.5g}, expected {expected:.5g}")
        fails += 0 if ok else 1
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "petroleum_engineering_suite.xlsx")
