"""Lubricate and bleed: remove gas at surface and regain hydrostatic control.

Only done once the gas is at surface (the volumetric method brings it there).
Kill weight mud is lubricated into the well; the annulus AT SURFACE is used,
because that is where the lubricated mud lands.

Each cycle:
    1. Pump kill weight mud until casing pressure rises by the working pressure.
       The volume that goes in is decided by the pressure - the crew reads it
       from the trip tank.
    2. Let the mud lubricate down through the gas.
    3. Bleed gas back to the pressure BEFORE pumping, minus the hydrostatic
       of the mud lubricated:
           Hydrostatic added (psi) = bbl pumped x KWM gradient / Annular capacity at surface
           Bleed down to (psi)     = Casing pressure before pumping - Hydrostatic added
    Repeat until casing pressure is 0 - hydrostatic control regained.

There is no dedicated IADC formula for lubricate and bleed; it is built from
the IADC basics: height of fluid = bbl / annular capacity (#12) and
hydrostatic = gradient x height (#13, #14).

Rounding: the hydrostatic added is how much pressure gets bled off - bleeding
MORE loses bottomhole pressure - so it is rounded DOWN to a whole psi (rule 2).
"""

from typing import NamedTuple

from killsheet.rounding import round_down_to_whole_number


class LubricateCycle(NamedTuple):
    """One lubricate and bleed cycle."""

    cycle: int
    pump_to_psi: int            # pump kill mud until casing reads this
    bbl_pumped: float           # measured in the trip tank
    hydrostatic_added_psi: int  # rounded DOWN
    bleed_to_psi: int           # bleed gas down to this


def hydrostatic_added(bbl_pumped, kill_mud_gradient_psi_per_ft, surface_annular_capacity_bbl_per_ft):
    """Hydrostatic of the kill mud lubricated (psi), rounded DOWN to a whole psi.

        Hydrostatic = bbl pumped x KWM gradient / Annular capacity at surface
    """
    return round_down_to_whole_number(
        bbl_pumped * kill_mud_gradient_psi_per_ft / surface_annular_capacity_bbl_per_ft
    )


def lubricate_and_bleed_table(sicp_gas_at_surface_psi, working_pressure_psi, bbl_pumped_each_cycle,
                              kill_mud_gradient_psi_per_ft, surface_annular_capacity_bbl_per_ft):
    """The lubricate and bleed cycles, from the volumes the crew measures.

        Pump to   = Casing pressure before pumping + Working pressure
        Bleed to  = Casing pressure before pumping - Hydrostatic added (never below 0)

    bbl_pumped_each_cycle: the bbl of kill mud that went in each cycle. The
    table runs until casing pressure reaches 0, or the readings run out.
    """
    rows = []
    casing_psi = sicp_gas_at_surface_psi
    for cycle, bbl in enumerate(bbl_pumped_each_cycle, start=1):
        added_psi = hydrostatic_added(bbl, kill_mud_gradient_psi_per_ft, surface_annular_capacity_bbl_per_ft)
        bleed_to_psi = max(casing_psi - added_psi, 0)
        rows.append(LubricateCycle(cycle, casing_psi + working_pressure_psi, bbl, added_psi, bleed_to_psi))
        casing_psi = bleed_to_psi
        if casing_psi == 0:
            break
    return rows
