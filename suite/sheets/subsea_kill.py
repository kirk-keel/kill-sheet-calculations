"""Drilling: IWCF-style subsea supplement to the surface Kill Sheet.

Adds the subsea-specific corrections: choke line friction (CLF) acting on
the annulus side of a subsea stack, choke line volume/strokes, riser margin,
and the shut-in picture with the riser disconnected. Use together with the
main Kill Sheet - string/annulus volumes and the pumping schedule live there.
"""
from ..builder import SheetBuilder


def build(wb):
    sb = SheetBuilder(
        wb, "Kill Sheet - Subsea", "drilling",
        "Well Control Kill Sheet - Subsea BOP Supplement",
        "Choke line friction corrections, choke line displacement, riser margin "
        "and riser-disconnect hydrostatics (use with the main Kill Sheet)",
        description="Subsea supplement: CLF-corrected MAASP and choke pressure, choke "
                    "line volume, kill mud weight, riser margin, disconnected-riser BHP",
    )

    # ------------------------------------------------------------ well data
    sb.section("Subsea Well Data")

    c = sb.calc("Rig, Water Depth & Choke Line",
                note="Yellow inputs are subsea-specific for THIS calc (the Well Data "
                     "master defaults to a land / surface-BOP well). CLF should be "
                     "MEASURED, not calculated, where possible - record it during "
                     "slow-rate circulation up the choke line.")
    wd = c.inp("Water depth", 1500, "ft", fmt="#,##0")
    ag = c.inp("Air gap (RKB to sea level)", 75, "ft", fmt="#,##0")
    cl_len = c.inp("Choke line length", 1650, "ft", fmt="#,##0",
                   note="Approx. water depth + air gap + stack height.")
    cl_id = c.inp("Choke line ID", 3.0, "in", fmt="0.000")
    clf = c.inp("Choke line friction (CLF) at kill rate", 250, "psi", fmt="#,##0",
                note="Measured at the kill rate circulating up the choke line.")

    c = sb.calc("Linked Well Data",
                note="Light blue = linked to the Well Data sheet; overwrite locally "
                     "if this well differs.")
    omw = c.link("Current mud weight (OMW)", "WD_OMW", "ppg")
    tvd = c.link("Bit / TD true vertical depth (TVD)", "WD_TVD", "ft", fmt="#,##0")
    shoe_tvd = c.link("Casing shoe TVD", "WD_ShoeTVD", "ft", fmt="#,##0")
    lot = c.link("LOT / FIT equivalent mud weight", "WD_LOT", "ppg")
    scr = c.link("Slow circulating rate pressure (SCR)", "WD_SCR", "psi", fmt="#,##0")
    spr = c.link("Pump output", "WD_SPR", "bbl/stk", fmt="0.0000")

    # ------------------------------------------------------------ choke line
    sb.section("Choke Line")

    c = sb.calc("Choke Line Volume & Displacement",
                eq="Capacity = ID^2 / 1029.4 [bbl/ft];  Strokes = Volume / Pump output",
                note="Small ID over a long length: the choke line holds only a few "
                     "barrels but adds significant friction at kill rate.")
    cl_cap = c.out("Choke line capacity", f"{cl_id}^2/1029.4", "bbl/ft", fmt="0.00000")
    cl_vol = c.out("Choke line volume", f"{cl_cap}*{cl_len}", "bbl", fmt="0.00")
    c.out("Strokes to displace choke line", f"ROUNDUP(ROUND({cl_vol}/{spr},6),0)", None, fmt="#,##0")

    # ----------------------------------------------- CLF-corrected pressures
    sb.section("CLF-Corrected Pressures")

    c = sb.calc("Shut-In Pressures",
                note="Allow pressures to stabilise; watch for gas migration on SIDPP.")
    sidpp = c.inp("Shut-in drill pipe pressure (SIDPP)", 500, "psi", fmt="#,##0")
    sicp = c.inp("Shut-in casing pressure (SICP)", 700, "psi", fmt="#,##0")

    c = sb.calc("MAASP - Static & Dynamic",
                eq="MAASP_static = (LOT_EMW - MW) x 0.052 x Shoe TVD;   "
                   "MAASP_dynamic = MAASP_static - CLF",
                note="With a subsea stack the choke line friction acts on the ANNULUS "
                     "side: while circulating up the choke line the shoe feels surface "
                     "choke pressure + CLF, so the allowable surface reading drops by "
                     "CLF. Rounding rule: maximized values round UP to whole psi.")
    maasp_s = c.out("Static MAASP (well shut in)",
                    f"ROUNDUP(ROUND(({lot}-{omw})*0.052*{shoe_tvd},6),0)", "psi", fmt="#,##0")
    c.out("Dynamic MAASP (circulating up choke line)",
          f"ROUNDUP(ROUND({maasp_s}-{clf},6),0)", "psi", fmt="#,##0")

    c = sb.calc("Bringing the Pump to Kill Speed",
                eq="ICP = SCR + SIDPP (DP side unchanged);   "
                   "Choke pressure to hold = SICP - CLF",
                note="The DP-side target (ICP) is unchanged by the subsea stack. But as "
                     "the pump is brought up, CLF develops in the choke line on the "
                     "annulus side and adds to bottomhole pressure. To keep BHP "
                     "constant, open the choke so the surface CASING gauge falls to "
                     "SICP - CLF while bringing the pump to kill speed (rather than "
                     "holding SICP as on a surface stack).")
    c.out("Initial circulating pressure (ICP)", f"{scr}+{sidpp}", "psi", fmt="#,##0",
          note="SCR should itself be measured circulating up the choke line.")
    c.out("Choke pressure while bringing pump up",
          f"MAX(0,{sicp}-{clf})", "psi", fmt="#,##0")

    # -------------------------------------------------- kill mud & surface gas
    sb.section("Kill Mud & Gas at Surface")

    c = sb.calc("Kill Mud Weight (KMW)",
                eq="KMW = OMW + SIDPP / (0.052 x TVD)",
                note="TVD, never MD. Rounding rule: kill density always rounds UP to "
                     "the nearest 0.1 ppg.")
    kmw_x = c.out("Kill mud weight (exact)", f"{omw}+{sidpp}/(0.052*{tvd})",
                  "ppg", fmt="0.000")
    c.out("Kill mud weight (rounded up)", f"ROUNDUP(ROUND({kmw_x}*10,6),0)/10", "ppg", fmt="0.0")

    c.txt("Gas in the choke line",
          "Gas circulated up the narrow choke line expands very rapidly near "
          "surface - expect sudden unloading and fast choke response late in the "
          "circulation. Keep the choke line displaced to kill mud between "
          "circulations, or take returns up the kill line, and slow the pump if "
          "the choke cannot keep up.")

    # ------------------------------------------------------------ riser margin
    sb.section("Riser Margin")

    c = sb.calc("Riser Margin Mud Weight",
                eq="MW_rm = (0.052 x MW x TVD - SW x WD) / (0.052 x (TVD - WD - AG))",
                note="Mud weight that keeps BHP unchanged if the riser is disconnected "
                     "and seawater stands above the mudline. In deep water the "
                     "required increase often exceeds the fracture gradient - full "
                     "riser margin is frequently impractical.")
    sw = c.link("Seawater gradient (SW)", "WD_SWGrad", "psi/ft", fmt="0.000")
    mw_rm = c.out("Riser margin mud weight (MW_rm)",
                  f"(0.052*{omw}*{tvd}-{sw}*{wd})/(0.052*({tvd}-{wd}-{ag}))",
                  "ppg", fmt="0.00")
    c.out("Margin over current MW", f"{mw_rm}-{omw}", "ppg", fmt="0.00",
          note="Extra density needed for full riser margin.")

    # ------------------------------------------- shut-in, riser disconnected
    sb.section("Shut-In With Riser Disconnected")

    c = sb.calc("BHP After Disconnect",
                eq="BHP = SW x WD + 0.052 x MW x (TVD - WD - AG)",
                note="Seawater column to the mudline, current mud below the BOP. "
                     "Compares against formation pressure to show whether the well "
                     "stays overbalanced on the mud alone.")
    res_p = c.link("Reservoir / formation pressure", "WD_ResP", "psi", fmt="#,##0")
    bhp = c.out("BHP with seawater to mudline",
                f"{sw}*{wd}+0.052*{omw}*({tvd}-{wd}-{ag})", "psi", fmt="#,##0")
    c.out("Status vs formation pressure",
          f'IF({bhp}>={res_p},"OK - overbalanced after disconnect",'
          f'"CHECK: underbalanced after disconnect - well can flow at the mudline")',
          None, fmt="@")
