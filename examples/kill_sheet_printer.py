"""Prints a kill sheet. Shared by the example wells in this folder.

Sections here are (name, capacity bbl/ft, length ft MD) - the name is only for
printing. The calculator itself works with (capacity bbl/ft, length ft).
Key points are (name, MD ft, TVD ft).
"""

from killsheet.depths import tvd_at_md
from killsheet.drillers import drillers_method
from killsheet.formulas import (
    final_circulating_pressure,
    initial_circulating_pressure,
    kill_mud_weight,
    maasp,
    max_allowable_mud_weight,
)
from killsheet.schedule import STEP, TEN_STEPS, pressure_schedule
from killsheet.strokes import (
    bit_to_shoe_strokes,
    bit_to_surface_strokes,
    check_section_lengths,
    strokes_to_length,
    surface_to_bit_strokes,
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
        print(f"  Drill pipe step-down schedule ({step_method}) - pressure follows the depth of the kill mud")
        print("    Strokes   Kill mud MD ft      psi")
        for row in pressure_schedule(icp, fcp, string, pump, surface_line_volume_bbl, step_method):
            label = "" if row.label == STEP else f"   <- {row.label}"
            print(f"    {row.strokes:>7,}  {row.md_ft:>15,}  {row.pressure_psi:>7,}{label}")
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
