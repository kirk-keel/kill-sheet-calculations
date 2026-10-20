"""Completions: brine density design, blending, temperature correction, packer fluids."""
from ..builder import SheetBuilder
from ..convert import TEMP_F


def build(wb):
    sb = SheetBuilder(
        wb, "Completion Fluids & Brines", "completions",
        "Completion Fluids & Brines",
        "Brine density design, hydrostatics at the perfs, blending, temperature correction, salt weight-up",
        description="Brine density for overbalance, blending, temperature correction, CaCl2 weight-up, packer fluids",
    )

    sb.section("Brine Density Design")

    c = sb.calc("Required Brine Density for Target Overbalance",
                eq="rho [ppg] = (P_res + OB) / (0.052 x TVD_perf [ft])",
                note="Density of a full column of clean brine giving the desired overbalance at the perforations.")
    pres = c.inp("Reservoir pressure (P_res)", 4500, "psi", fmt="#,##0")
    ob = c.inp("Target overbalance (OB)", 200, "psi", fmt="#,##0")
    tvd = c.inp("TVD at perforations", 9000, "ft", fmt="#,##0")
    rbx = c.out("Required brine density (exact)", f"({pres}+{ob})/(0.052*{tvd})", "ppg", fmt="0.000")
    c.out("Required brine density (rounded up)", f"ROUNDUP(ROUND({rbx}*10,6),0)/10", "ppg", fmt="0.0",
          note="Rounding rule: kill weight fluid density rounds UP to the nearest 0.1 ppg.")

    c = sb.calc("Hydrostatic & Overbalance at the Perforations",
                eq="P_hyd = 0.052 x rho x TVD;   OB = P_hyd - P_res",
                note="Positive result = overbalanced, negative = underbalanced.")
    rho = c.inp("Brine density in hole", 10.0, "ppg")
    tvd = c.inp("TVD at perforations", 9000, "ft", fmt="#,##0")
    pres = c.inp("Reservoir pressure (P_res)", 4500, "psi", fmt="#,##0")
    ph = c.out("Hydrostatic at perfs (P_hyd)", f"0.052*{rho}*{tvd}", "psi", fmt="#,##0")
    c.out("Overbalance (OB)", f"{ph}-{pres}", "psi", fmt="#,##0",
          note="Positive = overbalance on the formation.")

    c = sb.calc("Overbalance / Underbalance Margin Check",
                eq="Status = IF chain on (P_hyd - P_res) vs required margin",
                note="Typical completion practice: 150-300 psi overbalance for well control unless an underbalanced operation is planned.")
    rho = c.inp("Fluid density in hole", 10.0, "ppg")
    tvd = c.inp("TVD at perforations", 9000, "ft", fmt="#,##0")
    pres = c.inp("Reservoir pressure (P_res)", 4500, "psi", fmt="#,##0")
    mgn = c.inp("Minimum overbalance margin", 150, "psi", fmt="#,##0")
    ob = c.out("Actual overbalance", f"0.052*{rho}*{tvd}-{pres}", "psi", fmt="#,##0")
    c.out("Status",
          f'IF({ob}>={mgn},"OVERBALANCED - MARGIN OK",IF({ob}>=0,"OVERBALANCED - BELOW MARGIN","UNDERBALANCED"))',
          None, fmt="@", note="Text result.")

    c = sb.calc("Kill Weight Fluid for Completion",
                eq="KWF [ppg] = (P_res + safety) / (0.052 x TVD)",
                note="Same form as drilling kill mud weight: fluid density that balances reservoir pressure plus a safety margin with a full column.")
    pres = c.inp("Reservoir pressure (P_res)", 4500, "psi", fmt="#,##0")
    saf = c.inp("Safety margin", 100, "psi", fmt="#,##0")
    tvd = c.inp("TVD at perforations", 9000, "ft", fmt="#,##0")
    kwx = c.out("Kill weight fluid density (exact)", f"({pres}+{saf})/(0.052*{tvd})", "ppg", fmt="0.000")
    c.out("Kill weight fluid density (rounded up)", f"ROUNDUP(ROUND({kwx}*10,6),0)/10", "ppg", fmt="0.0",
          note="Rounding rule: kill weight fluid density rounds UP to the nearest 0.1 ppg.")

    sb.section("Blending & Temperature Correction")

    c = sb.calc("Blending Two Brines to a Target Density",
                eq="V1 = Vt x (rho_t - rho2) / (rho1 - rho2);   V2 = Vt - V1",
                note="Volume-weighted blend, mixing volumes assumed additive (small error for very heavy brines). rho1 must be the heavier brine; target must lie between the two stock densities.")
    vt = c.inp("Total blended volume required (Vt)", 500, "bbl", fmt="#,##0")
    rt = c.inp("Target density (rho_t)", 10.5, "ppg")
    r1 = c.inp("Heavy brine density (rho1)", 11.6, "ppg")
    r2 = c.inp("Light brine density (rho2)", 8.4, "ppg")
    v1 = c.out("Heavy brine volume (V1)", f"{vt}*({rt}-{r2})/({r1}-{r2})", "bbl", fmt="#,##0.0")
    c.out("Light brine volume (V2)", f"{vt}-{v1}", "bbl", fmt="#,##0.0")

    c = sb.calc("Brine Density Correction for Temperature",
                eq="rho@T = rho@70F - EF x (T - 70)",
                note="Linear expansion approximation. Expansion factor EF is brine-specific; typical 0.00023 - 0.00033 ppg/degF from supplier tables. Density falls as temperature rises.")
    r70 = c.inp("Density at 70 degF (rho@70F)", 10.0, "ppg")
    ef = c.inp("Expansion factor (EF)", 0.00028, None, fmt="0.00000",
               note="ppg per degF, from brine supplier tables")
    t = c.inp("Average fluid temperature (T)", 180, "degF", si=TEMP_F, fmt="#,##0")
    c.out("Density at temperature", f"{r70}-{ef}*({t}-70)", "ppg", fmt="0.000")

    sb.section("Salt Weight-Up")

    c = sb.calc("Weight-Up with Dry CaCl2 (Sacks per 100 bbl)",
                eq="lb per bbl = 42 x (rho2 - rho1) / (1 - rho2 x AV)",
                note="Documented simplified mass balance: dry salt dissolves and adds its absolute volume. AV = absolute volume of the salt in gal/lb (approx 0.056 gal/lb for CaCl2, from supplier tables). Ignores purity (94-97 pct flake) and crystallization limits - check supplier tables before mixing near saturation (11.6 ppg for CaCl2).")
    r1 = c.inp("Starting brine density (rho1)", 10.0, "ppg")
    r2 = c.inp("Target brine density (rho2)", 11.0, "ppg")
    av = c.inp("Salt absolute volume factor (AV)", 0.056, None, fmt="0.0000",
               note="gal per lb of dry salt")
    sk = c.inp("Sack weight", 80, None, fmt="#,##0", note="lb per sack (CaCl2 commonly 80-lb sacks)")
    lb = c.out("Dry CaCl2 per bbl of starting brine", f"42*({r2}-{r1})/(1-{r2}*{av})", None,
               fmt="#,##0.0", note="lb/bbl")
    c.out("Sacks per 100 bbl", f"{lb}*100/{sk}", None, fmt="#,##0.0", note="sacks")
    c.out("Final volume per 100 bbl start", f"100+{lb}*100*{av}/42", "bbl", fmt="#,##0.0",
          note="Volume increase from dissolved salt absolute volume.")

    sb.section("Packer Fluids")

    c = sb.calc("Packer Fluid Hydrostatic & Annulus Surface Pressure",
                eq="P_hyd = 0.052 x rho_pf x TVD_pkr;   P_ann_surf = P_target - P_hyd",
                note="Surface annulus pressure needed so the annulus pressure at the packer equals the target (e.g. to balance tubing pressure across the packer). Negative result means the packer fluid alone over-balances the target.")
    rpf = c.inp("Packer fluid density (rho_pf)", 9.2, "ppg")
    tvdp = c.inp("TVD at packer", 8800, "ft", fmt="#,##0")
    pt = c.inp("Target pressure at packer (P_target)", 4400, "psi", fmt="#,##0")
    ph = c.out("Packer fluid hydrostatic at packer", f"0.052*{rpf}*{tvdp}", "psi", fmt="#,##0")
    c.out("Required annulus surface pressure", f"{pt}-{ph}", "psi", fmt="#,##0")
