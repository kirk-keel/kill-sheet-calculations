"""Prints a kill sheet. Shared by the example wells in this folder.

Sections here are (name, capacity bbl/ft, length ft) - the name is only for
printing. The calculator itself works with (capacity bbl/ft, length ft).
"""

from killsheet.drillers import drillers_method
from killsheet.formulas import (
    final_circulating_pressure,
    initial_circulating_pressure,
    kill_mud_weight,
    maasp,
    max_allowable_mud_weight,
)
from killsheet.schedule import EVERY_100_STROKES, pressure_schedule
from killsheet.strokes import (
    bit_to_shoe_strokes,
    bit_to_surface_strokes,
    crossover_strokes,
    surface_to_bit_strokes,
)

DRILLERS = "Driller's method"
WAIT_AND_WEIGHT = "Wait and Weight"


def without_names(sections):
    """(name, capacity, length) -> (capacity, length), for the calculator."""
    return [(capacity, length) for _name, capacity, length in sections]


def print_kill_sheet(
    title,
    tvd_ft,
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
    surface_line_volume_bbl=0,
    method=DRILLERS,
    step_method=EVERY_100_STROKES,
):
    """Calculate and print the whole kill sheet for a vertical well."""
    string = without_names(drill_string)
    open_hole = without_names(open_hole_annulus)
    annulus = without_names(open_hole_annulus + cased_hole_annulus)
    pump = pump_output_bbl_per_stk

    kmw = kill_mud_weight(sidpp_psi, tvd_ft, original_mud_weight_ppg)
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

    # Kill mud position: strokes to the bottom of each drill string section.
    print("Drill string crossovers (top down)     Depth ft   Strokes")
    depth_ft = 0
    strokes = crossover_strokes(string, pump, surface_line_volume_bbl)
    for (name, _capacity, length), stks in zip(drill_string, strokes):
        depth_ft += length
        print(f"  bottom of {name:<26}{depth_ft:>9,}  {stks:>8,}")
    print()

    # Annulus: strokes from the bit to the top of each annulus section.
    print("Annulus crossovers (bit up)            Depth ft   Strokes")
    depth_ft = tvd_ft
    strokes = crossover_strokes(annulus, pump)
    for (name, _capacity, length), stks in zip(open_hole_annulus + cased_hole_annulus, strokes):
        depth_ft -= length
        print(f"  top of {name:<29}{depth_ft:>9,}  {stks:>8,}")
    print()

    if method == DRILLERS:
        print(DRILLERS)
        circulation = None
        for step in drillers_method(sidpp_psi, sicp_psi, icp, fcp, stb, btsurf):
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
    elif method == WAIT_AND_WEIGHT:
        print(f"{WAIT_AND_WEIGHT} - drill pipe pressure schedule ({step_method})")
        print("  Strokes      psi")
        for stks, pressure in pressure_schedule(icp, fcp, stb, step_method):
            print(f"  {stks:>7,}  {pressure:>7,}")
        print(f"  then hold FCP {fcp:,} psi for {btsurf:,} stks, bit to surface")
    else:
        raise ValueError(f"method must be {DRILLERS!r} or {WAIT_AND_WEIGHT!r}")
