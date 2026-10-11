"""Prints a kill sheet. Shared by the example wells in this folder.

Sections here are (name, capacity bbl/ft, length ft MD) - the name is only for
printing. The calculator itself works with (capacity bbl/ft, length ft).
Key points are (name, MD ft, TVD ft).

Driller's, Wait and Weight and volumetric sheets are worked out by
killsheet.kill_sheet (the web page uses the same module) and only printed here.
"""

from killsheet.bullhead import (
    bullhead_chart,
    equipment_limit,
    gas_migration_rate,
    minimum_spm_to_beat_gas_migration,
)
from killsheet.depths import tvd_at_md
from killsheet.formulas import kill_mud_weight, max_allowable_mud_weight
from killsheet.kill_sheet import DRILLERS, WAIT_AND_WEIGHT, kill_sheet, volumetric_sheet, without_names  # noqa: F401 (examples import DRILLERS, WAIT_AND_WEIGHT from here)
from killsheet.rounding import round_to_tenth, round_to_whole_number
from killsheet import reverse_circulation as reverse
from killsheet.schedule import STEP
from killsheet.strokes import surface_to_bit_strokes, total_length, total_volume
from killsheet.volumetric import mud_gradient


def print_kill_sheet(**well):
    """Print the Driller's or Wait and Weight kill sheet (see killsheet.kill_sheet.kill_sheet)."""
    sheet = kill_sheet(**well)
    print(sheet["title"])
    print("=" * 52)
    print(f"Kill mud weight              {sheet['kill_mud_weight_ppg']:>8.1f} ppg")
    print(f"Initial circulating pressure {sheet['icp_psi']:>8,} psi")
    print(f"Final circulating pressure   {sheet['fcp_psi']:>8,} psi")
    print(f"Max allowable mud weight     {sheet['max_allowable_mud_weight_ppg']:>8.1f} ppg")
    print(f"MAASP (original mud)         {sheet['maasp_original_psi']:>8,} psi")
    print(f"MAASP (after kill)           {sheet['maasp_after_kill_psi']:>8,} psi")
    print()
    print(f"Surface to bit               {sheet['surface_to_bit_strokes']:>8,} stks")
    print(f"Bit to shoe                  {sheet['bit_to_shoe_strokes']:>8,} stks")
    print(f"Bit to surface               {sheet['bit_to_surface_strokes']:>8,} stks")
    print()
    print("Drill string, top down (kill mud)            MD ft    TVD ft   Strokes")
    for row in sheet["string_depths"]:
        print(f"  {row['name']:<40}{row['md_ft']:>9,} {row['tvd_ft']:>9,} {row['strokes']:>9,}")
    print()
    print("Annulus, bit up                              MD ft    TVD ft   Strokes")
    for row in sheet["annulus_depths"]:
        print(f"  {row['name']:<40}{row['md_ft']:>9,} {row['tvd_ft']:>9,} {row['strokes']:>9,}")
    print()
    sf = sheet["safety_margin_psi"]
    print(f"Safety margin (SF)           {sf:>8,} psi")
    print()

    print(sheet["method"])
    check = sheet["icp_check"]
    if check is not None:
        print(f"  ICP check at kill rate: ICP + SF {check['icp_plus_sf_psi']:,} psi, "
              f"drill pipe reads {check['observed_psi']:,} psi")
        print(f"  {check['message']}")
    print_steps(sheet["steps"])
    if sheet["schedule"] is not None:
        print()
        print(f"  Drill pipe step-down schedule ({sheet['step_method']}) - pressure follows where the kill mud is")
        print("    Strokes    Kill mud MD ft   TVD ft      psi   psi + SF")
        for row in sheet["schedule"]:
            label = "" if row["label"] == STEP else f"   <- {row['label']}"
            print(f"    {row['strokes']:>7,}  {row['md_ft']:>15,}  {row['tvd_ft']:>7,}  {row['pressure_psi']:>7,}"
                  f"  {row['pressure_plus_sf_psi']:>8,}{label}")


def print_steps(steps):
    """Print kill steps grouped by circulation."""
    circulation = None
    for step in steps:
        if step["circulation"] != circulation:
            circulation = step["circulation"]
            print(f"  {circulation}")
        line = f"    {step['stage']:<11}{step['gauge']}"
        if step["hold_psi"] is not None:
            line += f" {step['hold_psi']:,} psi"
        if step["strokes"] is not None:
            line += f" for {step['strokes']:,} stks"
        print(line)
        print(f"{'':15}{step['note']}")


def print_volumetric_sheet(**well):
    """Print the volumetric method, then lubricate and bleed (see killsheet.kill_sheet.volumetric_sheet)."""
    sheet = volumetric_sheet(**well)
    pw = sheet["working_pressure_psi"]
    print(sheet["title"])
    print("=" * 52)
    print(f"Mud gradient                 {sheet['mud_gradient_psi_per_ft']:>8.4f} psi/ft  "
          f"({sheet['mud_weight_ppg']:.1f} ppg)")
    print(f"Kill mud gradient            {sheet['kill_mud_gradient_psi_per_ft']:>8.4f} psi/ft  "
          f"({sheet['kill_mud_weight_ppg']:.1f} ppg)")
    print(f"MAASP                        {sheet['maasp_psi']:>8,} psi")
    print(f"Safety margin / working      {sheet['safety_margin_psi']:>4,} / {pw:,} psi  (team's choice)")
    print()
    if sheet["vertical"]:
        print("Annulus, bottom up                      Capacity  Length ft")
        for row in sheet["sections"]:
            print(f"  {row['name']:<36}{row['capacity_bbl_per_ft']:>9.4f}  {row['length_ft']:>9,}")
    else:
        print("Annulus, bottom up              Capacity   MD ft  TVD ft  TVD/MD  Bleed bbl (angle corrected)")
        for row in sheet["sections"]:
            corrected = row["angle_corrected_bleed_bbl"]
            shown = "n/a - horizontal" if corrected is None else f"{corrected:.1f}"
            print(f"  {row['name']:<28}{row['capacity_bbl_per_ft']:>9.4f} {row['length_ft']:>7,} "
                  f"{row['tvd_ft']:>7,}  {row['tvd_over_md']:>6.3f}  {shown}")
        print("  Angle-corrected volumes are for information only - the volume bled is the")
        print("  vertical IADC #35 volume below, which bleeds the least mud.")
        if sheet["horizontal_note"]:
            print("  NOTE: gas in the horizontal section doesn't migrate the way it does vertically -")
            print("  it can sit in high spots. The volumetric method applies once the gas is in the")
            print("  build or vertical section.")
    print()
    print(f"Volume to bleed per {pw} psi = (working pressure / mud gradient) x annular capacity")
    for row in sheet["capacity_choices"]:
        marker = "  <- used" if row["used"] else ""
        print(f"  {row['choice']:<20}{row['capacity_bbl_per_ft']:>8.4f} bbl/ft  {row['bleed_bbl']:>5.1f} bbl{marker}")
    print()

    print("Volumetric method")
    print(f"  wait: let SICP rise from {sheet['sicp_psi']:,} to "
          f"{sheet['first_hold_psi']:,} psi (safety margin + working pressure)")
    print("  Cycle  Hold casing psi  Bleed bbl  Total bbl  15-min rise")
    for row in sheet["volumetric"]:
        note = "  GAS AT SURFACE" if row["gas_at_surface"] else ""
        warning = "  ! above MAASP - continue" if row["above_maasp"] else ""
        print(f"  {row['cycle']:>5}  {row['hold_psi']:>15,}  {row['bleed_bbl']:>9.1f}  {row['total_bled_bbl']:>9.1f}"
              f"  {row['sicp_rise_psi']:>8} psi{warning}{note}")
    print()

    surface_capacity = sheet["surface_capacity_bbl_per_ft"]
    print(f"Lubricate and bleed - kill mud, annulus at surface {surface_capacity:.4f} bbl/ft")
    print(f"  hydrostatic added = bbl pumped x {sheet['kill_mud_gradient_psi_per_ft']:.4f} / {surface_capacity:.4f}")
    print("  Cycle  Pump to psi  bbl pumped  Hydrostatic psi  Bleed to psi")
    for row in sheet["lubricate_and_bleed"]:
        done = "  hydrostatic control regained" if row["bleed_to_psi"] == 0 else ""
        warning = "  ! kill mud below KOP - less psi per bbl" if row["past_kop"] else ""
        print(f"  {row['cycle']:>5}  {row['pump_to_psi']:>11,}  {row['bbl_pumped']:>10.1f}  "
              f"{row['hydrostatic_added_psi']:>15,}  {row['bleed_to_psi']:>12,}{warning}{done}")
    if sheet["kop_md_ft"] is not None:
        print(f"  kill mud column {sheet['kill_mud_column_ft']:,} ft vs KOP {sheet['kop_md_ft']:,} ft"
              + (" - PASSED KOP" if sheet["passed_kop"] else " - stays above KOP"))


def print_bullhead_sheet(
    title,
    bit_tvd_ft,
    shoe_tvd_ft,
    original_mud_weight_ppg,
    lot_pressure_psi,
    test_mud_weight_ppg,
    sidpp_psi,
    sicp_increase_psi_per_hr,
    pump_output_bbl_per_stk,
    pump_rate_bbl_per_min,
    equipment_ratings,
    drill_string,
    annulus_bottom_up,
    overdisplacement_bbl=0,
    bit_md_ft=None,
    shoe_md_ft=None,
    key_points=(),
):
    """Bullhead sheet (drilling): annular shut, the same rate down the string and the backside.

    drill_string: (name, capacity, length) top down. annulus_bottom_up: (name,
    capacity, length) from the bottom up. equipment_ratings: (name, psi) - the
    lowest rating or tested value is the equipment limit.

    Vertical well: leave out bit_md_ft, shoe_md_ft and key_points (MD = TVD).
    Deviated or horizontal well: give the bit and shoe MD and the key points as
    (name, MD, TVD); the chart then shows MD and TVD for the kill fluid on each side.
    """
    string = without_names(drill_string)
    annulus = without_names(annulus_bottom_up)
    pump = pump_output_bbl_per_stk
    kill_fluid = kill_mud_weight(sidpp_psi, bit_tvd_ft, original_mud_weight_ppg)
    mamw = max_allowable_mud_weight(lot_pressure_psi, shoe_tvd_ft, test_mud_weight_ppg)
    limit_name, limit_psi = equipment_limit(equipment_ratings)

    string_strokes = surface_to_bit_strokes(string, pump)
    annulus_strokes = surface_to_bit_strokes(list(reversed(annulus)), pump)
    spm = round_to_whole_number(pump_rate_bbl_per_min / pump)
    migration = gas_migration_rate(sicp_increase_psi_per_hr, mud_gradient(original_mud_weight_ppg))
    largest_annulus = max(capacity for capacity, _length in annulus)
    minimum_spm = minimum_spm_to_beat_gas_migration(migration, largest_annulus, pump)

    print(title)
    print("=" * 52)
    print(f"Kill fluid density           {kill_fluid:>8.1f} ppg  (rounded UP to the next 0.1)")
    print(f"Max allowable mud weight     {mamw:>8.1f} ppg  (formation limit, from the LOT)")
    print(f"Equipment limit              {limit_psi:>8,} psi  ({limit_name} - lowest rating / test)")
    print()
    print(f"Drill string, surface to bit {total_volume(string):>8.1f} bbl  {string_strokes:>6,} stks")
    print(f"Annulus, surface to bottom   {total_volume(annulus):>8.1f} bbl  {annulus_strokes:>6,} stks  (kill point)")
    print(f"Overdisplacement             {overdisplacement_bbl:>8.1f} bbl  (team's choice)")
    past_bit_strokes = annulus_strokes - string_strokes
    print(f"String keeps pumping after kill fluid reaches the bit: {past_bit_strokes:,} stks "
          f"({round_to_tenth(past_bit_strokes * pump):.1f} bbl) out the bit by the kill point")
    print()
    print(f"Pump rate, SAME on both sides {pump_rate_bbl_per_min:.1f} bbl/min = {spm} spm each side")
    print(f"Time to the kill point       {round_to_whole_number(annulus_strokes / spm):>8,} min  ({annulus_strokes:,} stks / {spm} spm)")
    print(f"Gas migration                {migration:>8,} ft/hr  ({sicp_increase_psi_per_hr} psi/hr / "
          f"{mud_gradient(original_mud_weight_ppg):.4f} psi/ft)")
    print(f"Minimum rate to beat it      {minimum_spm:>8} spm  (largest annulus {largest_annulus:.4f} bbl/ft, rounded UP)")
    if spm < minimum_spm:
        print("  ! pump rate is BELOW the minimum to stay ahead of the gas")
    print()
    print("Annular shut: pump kill fluid down the string AND the backside at the same rate.")
    print("Pressure builds until injectivity is established, then falls as fluid is pushed")
    print("away. The goal is injectivity, NOT breaking down the formation - stay below the")
    print("max on both sides. Max = lower of the formation limit and the equipment limit.")
    print()
    bit_md = bit_tvd_ft if bit_md_ft is None else bit_md_ft
    shoe_md = shoe_tvd_ft if shoe_md_ft is None else shoe_md_ft
    vertical = bit_md == bit_tvd_ft and not key_points
    survey = [(md, tvd) for _name, md, tvd in key_points] + [(shoe_md, shoe_tvd_ft), (bit_md, bit_tvd_ft)]
    chart = bullhead_chart(original_mud_weight_ppg, kill_fluid, mamw, shoe_tvd_ft, string, annulus, pump,
                           limit_psi, overdisplacement_bbl, shoe_md_ft=shoe_md, bit_tvd_ft=bit_tvd_ft,
                           key_points=key_points)
    if vertical:
        print("  Strokes  Kill fluid MD ft    String max  Annulus max   Actual string  Actual annulus")
        print("    (each)   string  annulus         psi          psi             psi             psi")
    else:
        print("  Strokes  Kill fluid, string  Kill fluid, annulus  String  Annulus   Actual   Actual")
        print("    (each)     MD ft   TVD ft      MD ft   TVD ft  max psi  max psi   string  annulus")
    for row in chart:
        label = "" if row.label == "step" else f"  <- {row.label}"
        if vertical:
            print(f"  {row.strokes:>7,}  {row.string_kill_md_ft:>7,}  {row.annulus_kill_md_ft:>7,}"
                  f"  {row.string_max_psi:>10,}  {row.annulus_max_psi:>11,}   ____________    ____________{label}")
        else:
            print(f"  {row.strokes:>7,}  {row.string_kill_md_ft:>8,} {tvd_at_md(row.string_kill_md_ft, survey):>8,}"
                  f"   {row.annulus_kill_md_ft:>8,} {tvd_at_md(row.annulus_kill_md_ft, survey):>8,}"
                  f"  {row.string_max_psi:>7,}  {row.annulus_max_psi:>7,}   ______   ______{label}")


def print_reverse_circulation_sheet(
    title,
    formation_pressure_psi,
    sitp_psi,
    top_perf_tvd_ft,
    bottom_perf_tvd_ft,
    ssd_tvd_ft,
    packer_tvd_ft,
    packer_fluid_ppg,
    fracture_gradient_psi_per_ft,
    pump_output_bbl_per_stk,
    pump_rate_bbl_per_min,
    equipment_ratings,
    annulus_sections,
    tubing_sections,
    casing_capacity_bbl_per_ft,
    observed_icp_psi=None,
    margin_ppg=0,
    circulating_point="SSD",
    ssd_md_ft=None,
    packer_md_ft=None,
    top_perf_md_ft=None,
    key_points=(),
):
    """Reverse circulation kill sheet for a completion / workover / intervention (CWI) well.

    annulus_sections / tubing_sections: (name, capacity bbl/ft, length ft MD),
    surface down to the circulating point (an opened SSD or a tubing punch).
    observed_icp_psi: the annulus pressure read once at kill rate (None until then).

    Vertical well: leave out the MDs and key_points (MD = TVD).
    Deviated or horizontal well: give the SSD, packer and top-perf MD and the key
    points as (name, MD, TVD). Pressures use TVD; volumes and strokes use MD.
    """
    annulus = without_names(annulus_sections)
    tubing = without_names(tubing_sections)
    pump = pump_output_bbl_per_stk
    ssd_md = ssd_tvd_ft if ssd_md_ft is None else ssd_md_ft
    packer_md = packer_tvd_ft if packer_md_ft is None else packer_md_ft
    top_perf_md = top_perf_tvd_ft if top_perf_md_ft is None else top_perf_md_ft
    for name, sections in (("Annulus", annulus), ("Tubing", tubing)):
        if total_length(sections) != ssd_md:
            raise ValueError(f"{name} sections add up to {total_length(sections):,} ft MD "
                             f"but should reach the {circulating_point} at {ssd_md:,} ft")
    mid_perf = round_to_whole_number((top_perf_tvd_ft + bottom_perf_tvd_ft) / 2)
    gradient = reverse.tubing_fluid_gradient(formation_pressure_psi, sitp_psi, mid_perf)
    p_ssd = reverse.pressure_at_ssd(formation_pressure_psi, gradient, mid_perf, ssd_tvd_ft)
    kwf = reverse.kill_weight_fluid(p_ssd, ssd_tvd_ft, margin_ppg)
    sicp = reverse.sicp_after_ssd_opened(p_ssd, packer_fluid_ppg, ssd_tvd_ft)
    sitp = reverse.sitp_after_ssd_opened(p_ssd, gradient, ssd_tvd_ft)
    frac = reverse.fracture_pressure(fracture_gradient_psi_per_ft, top_perf_tvd_ft)
    limit_name, limit_psi = equipment_limit(equipment_ratings)
    max_packer = reverse.max_annulus_pressure(frac, kwf, packer_fluid_ppg, 0, ssd_tvd_ft, gradient, top_perf_tvd_ft)
    max_kill = reverse.max_annulus_pressure(frac, kwf, packer_fluid_ppg, ssd_tvd_ft, ssd_tvd_ft, gradient, top_perf_tvd_ft)
    annulus_strokes = surface_to_bit_strokes(annulus, pump)
    tubing_strokes = surface_to_bit_strokes(tubing, pump)
    point = circulating_point

    print(title)
    print("=" * 52)
    print(f"Tubing fluid gradient        {gradient:>8.4f} psi/ft  (({formation_pressure_psi:,} - {sitp_psi:,}) / "
          f"{mid_perf:,} mid-perf TVD)")
    print(f"Pressure at the {point:<13}{p_ssd:>8,} psi  (formation fluid left below it)")
    print(f"Kill weight fluid            {kwf:>8.1f} ppg  (balances at the {point}; rounded UP, margin {margin_ppg} ppg)")
    print()
    print(f"Before start-up: open the {point}, let pressures stabilise, record:")
    print(f"  SITP                       {sitp:>8,} psi")
    print(f"  SICP                       {sicp:>8,} psi  (= pressure at the {point} - annulus hydrostatic)")
    print()
    print(f"Fracture at the top perf     {frac:>8,} psi  ({fracture_gradient_psi_per_ft} x {top_perf_tvd_ft:,})")
    print("Max allowable annulus pressure      formation     equipment     used")
    print(f"  packer fluid in the annulus     {max_packer:>9,}     {limit_psi:>9,}  {min(max_packer, limit_psi):>7,}")
    print(f"  kill fluid in the annulus       {max_kill:>9,}     {limit_psi:>9,}  {min(max_kill, limit_psi):>7,}")
    print(f"  equipment limit: {limit_name} (lowest rating / test)")
    print()
    print(f"Annulus, surface to {point}     {total_volume(annulus):>7.1f} bbl  {annulus_strokes:>6,} stks")
    print(f"Tubing, {point} to surface     {total_volume(tubing):>7.1f} bbl  {tubing_strokes:>6,} stks")
    print(f"Kill rate                    {pump_rate_bbl_per_min:>8.1f} bbl/min = "
          f"{round_to_whole_number(pump_rate_bbl_per_min / pump)} spm")
    print()
    if observed_icp_psi is None:
        print("Observed ICP: not yet read - bring the pump up holding tubing at the SITP, then enter")
        print("the annulus pressure at kill rate to build the schedule.")
        return
    fcp, floored = reverse.final_circulating_pressure(observed_icp_psi, kwf, packer_fluid_ppg, ssd_tvd_ft)
    print(f"Observed ICP                 {observed_icp_psi:>8,} psi  (annulus pressure at kill rate)")
    print(f"FCP                          {fcp:>8,} psi  (ICP - ({kwf:.1f} - {packer_fluid_ppg:.1f}) x 0.052 x "
          f"{ssd_tvd_ft:,}, drop rounded DOWN)")
    if floored:
        print(f"  ! {reverse.FCP_FLOOR_WARNING}")
    print()
    print("Reverse circulation - sides are swapped: pump on the ANNULUS, choke on the TUBING")
    steps = reverse.reverse_circulation_steps(sitp, observed_icp_psi, fcp, annulus_strokes, tubing_strokes)
    print_steps([step._asdict() for step in steps])
    print()
    print("  Annulus pump pressure schedule")
    print("    Strokes   Kill fluid MD ft   TVD ft   Pump psi   Max allowable psi")
    for row in reverse.reverse_schedule(observed_icp_psi, kwf, packer_fluid_ppg, annulus, tubing, pump, frac, gradient,
                                        top_perf_tvd_ft, limit_psi, ssd_tvd_ft=ssd_tvd_ft, key_points=key_points):
        label = "" if row.label == "step" else f"   <- {row.label}"
        print(f"    {row.strokes:>7,}  {row.kill_fluid_md_ft:>16,}  {row.kill_fluid_tvd_ft:>7,}  {row.pump_psi:>9,}"
              f"  {row.max_allowable_psi:>18,}{label}")
    print()
    below = reverse.volume_below_ssd(tubing[-1][0], packer_md - ssd_md, casing_capacity_bbl_per_ft,
                                     top_perf_md - packer_md)
    initial, final = reverse.bullhead_below_ssd_limits(frac, kwf, ssd_tvd_ft, gradient, top_perf_tvd_ft)
    print(f"Optional: bullhead the {below:.1f} bbl below the {point} (tubing to the packer + casing to the top perf)")
    print(f"  max tubing pressure {min(initial, limit_psi):,} psi at the start, {min(final, limit_psi):,} psi "
          "once displaced to the top perf")
