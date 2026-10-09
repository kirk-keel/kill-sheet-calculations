"""Prints a kill sheet. Shared by the example wells in this folder.

Sections here are (name, capacity bbl/ft, length ft MD) - the name is only for
printing. The calculator itself works with (capacity bbl/ft, length ft).
Key points are (name, MD ft, TVD ft).
"""

from killsheet.bullhead import (
    bullhead_chart,
    equipment_limit,
    gas_migration_rate,
    minimum_spm_to_beat_gas_migration,
)
from killsheet.depths import tvd_at_md
from killsheet.drillers import drillers_method
from killsheet.formulas import (
    final_circulating_pressure,
    initial_circulating_pressure,
    kill_mud_weight,
    maasp,
    max_allowable_mud_weight,
)
from killsheet.rounding import round_to_tenth, round_to_whole_number
from killsheet.schedule import STEP, TEN_STEPS, pressure_schedule
from killsheet.strokes import (
    bit_to_shoe_strokes,
    bit_to_surface_strokes,
    check_section_lengths,
    strokes_to_length,
    surface_to_bit_strokes,
    total_volume,
)
from killsheet.lubricate_and_bleed import cycles_past_kop, kill_mud_column_ft, lubricate_and_bleed_table
from killsheet.volumetric import (
    SMALLEST,
    angle_corrected_volume_to_bleed,
    annular_capacity_choices,
    mud_gradient,
    volume_to_bleed_per_cycle,
    volumetric_table,
)
from killsheet.wait_and_weight import (
    ICP_MATCHES,
    ICP_RECALCULATED,
    kill_pressures_at_kill_rate,
    wait_and_weight_method,
)

DRILLERS = "Driller's method"
WAIT_AND_WEIGHT = "Wait and Weight"


def without_names(sections):
    """(name, capacity, length) -> (capacity, length), for the calculator."""
    return [(capacity, length) for _name, capacity, length in sections]


def depth_rows(rows, survey):
    """Group (name, MD) rows by MD - names at the same MD are joined - and add TVD."""
    by_md = {}
    for name, md_ft in rows:
        by_md.setdefault(md_ft, []).append(name)
    return [(" / ".join(names), md_ft, tvd_at_md(md_ft, survey)) for md_ft, names in by_md.items()]


def print_kill_sheet(
    title,
    bit_tvd_ft,
    shoe_tvd_ft,
    original_mud_weight_ppg,
    lot_pressure_psi,
    test_mud_weight_ppg,
    sidpp_psi,
    sicp_psi,
    scr_pressure_psi,
    pump_output_bbl_per_stk,
    drill_string,
    open_hole_annulus,
    cased_hole_annulus,
    bit_md_ft=None,
    shoe_md_ft=None,
    key_points=(),
    surface_line_volume_bbl=0,
    method=DRILLERS,
    step_method=TEN_STEPS,
    sidpp_at_start_psi=None,
    sicp_at_start_psi=None,
    observed_icp_psi=None,
):
    """Calculate and print the whole kill sheet.

    Vertical well: leave out bit_md_ft, shoe_md_ft and key_points (MD = TVD).
    Deviated or horizontal well: give the bit and shoe MD, and key points
    such as KOP, end of build and the heel as (name, MD, TVD).

    Wait and Weight only:
      sidpp_at_start_psi - SIDPP retaken (float bumped) just before pump start-up
                           (defaults to sidpp_psi)
      sicp_at_start_psi  - SICP retaken just before pump start-up (defaults to sicp_psi)
      observed_icp_psi   - drill pipe reading once at kill rate; if it reads more than
                           10 psi HIGH, ICP/FCP are recalculated (FCP never lower)
    """
    bit_md_ft = bit_tvd_ft if bit_md_ft is None else bit_md_ft
    shoe_md_ft = shoe_tvd_ft if shoe_md_ft is None else shoe_md_ft
    survey = [(md, tvd) for _name, md, tvd in key_points]
    survey += [(shoe_md_ft, shoe_tvd_ft), (bit_md_ft, bit_tvd_ft)]

    string = without_names(drill_string)
    open_hole = without_names(open_hole_annulus)
    annulus = without_names(open_hole_annulus + cased_hole_annulus)
    pump = pump_output_bbl_per_stk
    check_section_lengths(string, open_hole, without_names(cased_hole_annulus), bit_md_ft, shoe_md_ft)

    kmw = kill_mud_weight(sidpp_psi, bit_tvd_ft, original_mud_weight_ppg)
    icp = initial_circulating_pressure(sidpp_psi, scr_pressure_psi)
    fcp = final_circulating_pressure(scr_pressure_psi, kmw, original_mud_weight_ppg)
    mamw = max_allowable_mud_weight(lot_pressure_psi, shoe_tvd_ft, test_mud_weight_ppg)

    stb = surface_to_bit_strokes(string, pump, surface_line_volume_bbl)
    bts = bit_to_shoe_strokes(open_hole, pump)
    btsurf = bit_to_surface_strokes(annulus, pump)

    print(title)
    print("=" * 52)
    print(f"Kill mud weight              {kmw:>8.1f} ppg")
    print(f"Initial circulating pressure {icp:>8,} psi")
    print(f"Final circulating pressure   {fcp:>8,} psi")
    print(f"Max allowable mud weight     {mamw:>8.1f} ppg")
    print(f"MAASP (original mud)         {maasp(mamw, original_mud_weight_ppg, shoe_tvd_ft):>8,} psi")
    print(f"MAASP (after kill)           {maasp(mamw, kmw, shoe_tvd_ft):>8,} psi")
    print()
    print(f"Surface to bit               {stb:>8,} stks")
    print(f"Bit to shoe                  {bts:>8,} stks")
    print(f"Bit to surface               {btsurf:>8,} stks")
    print()

    # Drill string, top down: key points and the bottom of each section.
    rows = [(name, md) for name, md, _tvd in key_points]
    md_ft = 0
    for name, _capacity, length in drill_string:
        md_ft += length
        rows.append((f"bottom of {name}", md_ft))
    rows[-1] = ("bit", bit_md_ft)
    print("Drill string, top down (kill mud)            MD ft    TVD ft   Strokes")
    for name, md_ft, tvd_ft in sorted(depth_rows(rows, survey), key=lambda row: row[1]):
        stks = strokes_to_length(string, md_ft, pump, surface_line_volume_bbl)
        print(f"  {name:<40}{md_ft:>9,} {tvd_ft:>9,} {stks:>9,}")
    print()

    # Annulus, bit up: key points, the shoe and the top of each section.
    rows = [(name, md) for name, md, _tvd in key_points if md < bit_md_ft]
    rows.append(("shoe", shoe_md_ft))
    md_ft = bit_md_ft
    for name, _capacity, length in open_hole_annulus + cased_hole_annulus:
        md_ft -= length
        rows.append((f"top of {name}", md_ft))
    rows[-1] = ("surface", 0)
    print("Annulus, bit up                              MD ft    TVD ft   Strokes")
    for name, md_ft, tvd_ft in sorted(depth_rows(rows, survey), key=lambda row: -row[1]):
        stks = strokes_to_length(annulus, bit_md_ft - md_ft, pump)
        print(f"  {name:<40}{md_ft:>9,} {tvd_ft:>9,} {stks:>9,}")
    print()

    if method == DRILLERS:
        print(DRILLERS)
        print_steps(drillers_method(sidpp_psi, sicp_psi, icp, fcp, stb, btsurf))
    elif method == WAIT_AND_WEIGHT:
        print(WAIT_AND_WEIGHT)
        sidpp_at_start = sidpp_psi if sidpp_at_start_psi is None else sidpp_at_start_psi
        sicp_at_start = sicp_psi if sicp_at_start_psi is None else sicp_at_start_psi
        if observed_icp_psi is not None:
            print(f"  ICP check at kill rate: calculated {icp:,} psi, drill pipe reads {observed_icp_psi:,} psi")
            icp, fcp, status = kill_pressures_at_kill_rate(
                icp, fcp, observed_icp_psi, sidpp_at_start, kmw, original_mud_weight_ppg
            )
            if status == ICP_MATCHES:
                print("  within +/-10 psi - use the calculated ICP and FCP")
            elif status == ICP_RECALCULATED:
                print(f"  more than 10 psi high - RECALCULATED from retaken SIDPP {sidpp_at_start:,} psi: "
                      f"ICP {icp:,} psi, FCP {fcp:,} psi (FCP is never lower than calculated)")
            else:
                print("  more than 10 psi low - a complication; calculated ICP and FCP are kept "
                      "(never recalculated lower)")
        print_steps(wait_and_weight_method(sicp_at_start, icp, fcp, kmw, stb, btsurf))
        print()
        print(f"  Drill pipe step-down schedule ({step_method}) - pressure follows where the kill mud is")
        print("    Strokes    Kill mud MD ft   TVD ft      psi")
        schedule = pressure_schedule(icp, fcp, string, pump, surface_line_volume_bbl, step_method,
                                     sidpp_psi=sidpp_at_start, bit_tvd_ft=bit_tvd_ft, key_points=key_points)
        for row in schedule:
            label = "" if row.label == STEP else f"   <- {row.label}"
            print(f"    {row.strokes:>7,}  {row.md_ft:>15,}  {row.tvd_ft:>7,}  {row.pressure_psi:>7,}{label}")
    else:
        raise ValueError(f"method must be {DRILLERS!r} or {WAIT_AND_WEIGHT!r}")


def print_steps(steps):
    """Print kill steps grouped by circulation."""
    circulation = None
    for step in steps:
        if step.circulation != circulation:
            circulation = step.circulation
            print(f"  {circulation}")
        line = f"    {step.stage:<11}{step.gauge}"
        if step.hold_psi is not None:
            line += f" {step.hold_psi:,} psi"
        if step.strokes is not None:
            line += f" for {step.strokes:,} stks"
        print(line)
        print(f"{'':15}{step.note}")


def print_volumetric_sheet(
    title,
    original_mud_weight_ppg,
    kill_mud_weight_ppg,
    shoe_tvd_ft,
    lot_pressure_psi,
    test_mud_weight_ppg,
    sicp_psi,
    safety_margin_psi,
    working_pressure_psi,
    annulus_bottom_up,
    sicp_rises_after_each_cycle,
    sicp_gas_at_surface_psi,
    bbl_pumped_each_cycle,
    capacity_choice=SMALLEST,
    td_md_ft=None,
    td_tvd_ft=None,
    shoe_md_ft=None,
    key_points=(),
):
    """Volumetric method, then lubricate and bleed, for any situation.

    annulus_bottom_up: (name, capacity bbl/ft, length ft MD) from the BOTTOM UP,
    including sections with no pipe in them. The top section is the annulus
    at surface, used for lubricate and bleed.

    Vertical well: leave out td_md_ft, td_tvd_ft, shoe_md_ft and key_points.
    Deviated or horizontal well: give the TD and shoe MD/TVD and the key points
    as (name, MD, TVD). The bleed used stays the vertical (IADC #35) volume; the
    angle-corrected volume for each section is printed for information.
    """
    annulus = without_names(annulus_bottom_up)
    gradient = mud_gradient(original_mud_weight_ppg)
    kill_gradient = mud_gradient(kill_mud_weight_ppg)
    maasp_psi = maasp(max_allowable_mud_weight(lot_pressure_psi, shoe_tvd_ft, test_mud_weight_ppg),
                      original_mud_weight_ppg, shoe_tvd_ft)
    choices = annular_capacity_choices(annulus)
    bleed_bbl = volume_to_bleed_per_cycle(working_pressure_psi, gradient, choices[capacity_choice])

    print(title)
    print("=" * 52)
    print(f"Mud gradient                 {gradient:>8.4f} psi/ft  ({original_mud_weight_ppg:.1f} ppg)")
    print(f"Kill mud gradient            {kill_gradient:>8.4f} psi/ft  ({kill_mud_weight_ppg:.1f} ppg)")
    print(f"MAASP                        {maasp_psi:>8,} psi")
    print(f"Safety margin / working      {safety_margin_psi:>4,} / {working_pressure_psi:,} psi  (team's choice)")
    print()
    td_md = td_md_ft if td_md_ft is not None else sum(length for _name, _cap, length in annulus_bottom_up)
    td_tvd = td_tvd_ft if td_tvd_ft is not None else td_md
    shoe_md = shoe_md_ft if shoe_md_ft is not None else shoe_tvd_ft
    vertical = td_md == td_tvd and not key_points
    if vertical:
        print("Annulus, bottom up                      Capacity  Length ft")
        for name, capacity, length in annulus_bottom_up:
            print(f"  {name:<36}{capacity:>9.4f}  {length:>9,}")
    else:
        survey = [(md, tvd) for _name, md, tvd in key_points] + [(shoe_md, shoe_tvd_ft), (td_md, td_tvd)]
        print("Annulus, bottom up              Capacity   MD ft  TVD ft  TVD/MD  Bleed bbl (angle corrected)")
        bottom_md = td_md
        horizontal = False
        for name, capacity, length in annulus_bottom_up:
            top_md = bottom_md - length
            section_tvd = tvd_at_md(bottom_md, survey) - tvd_at_md(top_md, survey)
            corrected = angle_corrected_volume_to_bleed(working_pressure_psi, gradient, capacity, length, section_tvd)
            shown = "n/a - horizontal" if corrected is None else f"{corrected:.1f}"
            horizontal = horizontal or corrected is None
            print(f"  {name:<28}{capacity:>9.4f} {length:>7,} {section_tvd:>7,}  {section_tvd / length:>6.3f}  {shown}")
            bottom_md = top_md
        print("  Angle-corrected volumes are for information only - the volume bled is the")
        print("  vertical IADC #35 volume below, which bleeds the least mud.")
        if horizontal:
            print("  NOTE: gas in the horizontal section doesn't migrate the way it does vertically -")
            print("  it can sit in high spots. The volumetric method applies once the gas is in the")
            print("  build or vertical section.")
    print()
    print(f"Volume to bleed per {working_pressure_psi} psi = (working pressure / mud gradient) x annular capacity")
    for choice, capacity in choices.items():
        marker = "  <- used" if choice == capacity_choice else ""
        bbl = volume_to_bleed_per_cycle(working_pressure_psi, gradient, capacity)
        print(f"  {choice:<20}{capacity:>8.4f} bbl/ft  {bbl:>5.1f} bbl{marker}")
    print()

    print("Volumetric method")
    print(f"  wait: let SICP rise from {sicp_psi:,} to "
          f"{sicp_psi + safety_margin_psi + working_pressure_psi:,} psi (safety margin + working pressure)")
    print("  Cycle  Hold casing psi  Bleed bbl  Total bbl  15-min rise")
    for row in volumetric_table(sicp_psi, safety_margin_psi, working_pressure_psi, bleed_bbl,
                                maasp_psi, sicp_rises_after_each_cycle):
        note = "  GAS AT SURFACE" if row.gas_at_surface else ""
        warning = "  ! above MAASP - continue" if row.above_maasp else ""
        print(f"  {row.cycle:>5}  {row.hold_psi:>15,}  {row.bleed_bbl:>9.1f}  {row.total_bled_bbl:>9.1f}"
              f"  {row.sicp_rise_psi:>8} psi{warning}{note}")
    print()

    surface_capacity = annulus[-1][0]
    # KOP: the deepest key point that is still vertical (TVD = MD).
    vertical_points = [md for _name, md, tvd in key_points if md == tvd]
    kop_md = max(vertical_points) if vertical_points else None
    print(f"Lubricate and bleed - kill mud, annulus at surface {surface_capacity:.4f} bbl/ft")
    print(f"  hydrostatic added = bbl pumped x {kill_gradient:.4f} / {surface_capacity:.4f}")
    print("  Cycle  Pump to psi  bbl pumped  Hydrostatic psi  Bleed to psi")
    lube = lubricate_and_bleed_table(sicp_gas_at_surface_psi, working_pressure_psi, bbl_pumped_each_cycle,
                                     kill_gradient, surface_capacity)
    past_kop = cycles_past_kop(lube, surface_capacity, kop_md)
    for row in lube:
        done = "  hydrostatic control regained" if row.bleed_to_psi == 0 else ""
        warning = "  ! kill mud below KOP - less psi per bbl" if row.cycle in past_kop else ""
        print(f"  {row.cycle:>5}  {row.pump_to_psi:>11,}  {row.bbl_pumped:>10.1f}  {row.hydrostatic_added_psi:>15,}"
              f"  {row.bleed_to_psi:>12,}{warning}{done}")
    if kop_md is not None:
        column = kill_mud_column_ft(sum(row.bbl_pumped for row in lube), surface_capacity)
        print(f"  kill mud column {column:,} ft vs KOP {kop_md:,} ft"
              + (" - PASSED KOP" if past_kop else " - stays above KOP"))


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
