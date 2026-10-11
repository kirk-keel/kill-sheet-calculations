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
    Repeat until the bbl lubricated equal the gas volume at surface (pit gain +
    bbl bled in the volumetric method, from the readings) - the gas is then out.

The casing pressure left at that point is NOT assumed to be 0 (user rule v1.3):
    Remaining underbalance = Pf - (lubricated mud x TVD of its column
                                   + original mud x the rest of the TVD), never below 0
    10 psi or less: hydrostatic control regained - the casing pressure left is
    trapped pressure, bled off in small steps. More: the well is NOT dead - a kill
    is required, and casing must not be bled below the underbalance + SF.

There is no dedicated IADC formula for lubricate and bleed; it is built from
the IADC basics: height of fluid = bbl / annular capacity (#12) and
hydrostatic = gradient x height (#13, #14).

Rounding: the hydrostatic added is how much pressure gets bled off - bleeding
MORE loses bottomhole pressure - so it is rounded DOWN to a whole psi (rule 2).

Deviated and horizontal wells: the psi per bbl assumes the lubricated mud sits
in the vertical part of the well. If the kill mud column passes KOP, the sheet
WARNS - each bbl is then worth less psi than calculated.
"""

from typing import NamedTuple

from killsheet.kill_steps import GAUGE_TOLERANCE_PSI
from killsheet.rounding import round_down_to_whole_number, round_to_tenth, round_to_whole_number


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


def kill_mud_column_ft(total_bbl_lubricated, surface_annular_capacity_bbl_per_ft):
    """Length (ft MD) of kill mud lubricated into the annulus at surface, whole feet.

        Column = Total bbl lubricated / Annular capacity at surface
    """
    return round_to_whole_number(total_bbl_lubricated / surface_annular_capacity_bbl_per_ft)


def cycles_past_kop(rows, surface_annular_capacity_bbl_per_ft, kop_md_ft):
    """Cycle numbers where the kill mud column has gone below KOP - WARN.

    The psi bled per bbl assumes the lubricated mud sits in the vertical part
    of the well. Once the column passes KOP, each bbl adds less hydrostatic
    (its TVD is less than its length), so the bleed is overstated.
    Returns [] for a vertical well (kop_md_ft is None).
    """
    if kop_md_ft is None:
        return []
    past = []
    total_bbl = 0
    for row in rows:
        total_bbl += row.bbl_pumped
        if kill_mud_column_ft(total_bbl, surface_annular_capacity_bbl_per_ft) > kop_md_ft:
            past.append(row.cycle)
    return past


def lubricate_and_bleed_to_volume(sicp_gas_at_surface_psi, working_pressure_psi, bbl_pumped_each_cycle,
                                  lubricated_mud_gradient_psi_per_ft, surface_annular_capacity_bbl_per_ft,
                                  stopping_volume_bbl):
    """The lubricate and bleed cycles until the bbl lubricated equal the gas volume at surface.

        Pump to   = Casing pressure before pumping + Working pressure
        Bleed to  = Casing pressure before pumping - Hydrostatic added (never below 0)
        Stop      when the total lubricated = the stopping volume (the last cycle only
                  pumps what is left)

    bbl_pumped_each_cycle: the trip-tank readings. The table stops early if they run out.
    """
    rows, casing_psi, total_bbl = [], sicp_gas_at_surface_psi, 0
    for cycle, bbl in enumerate(bbl_pumped_each_cycle, start=1):
        bbl = min(bbl, round_to_tenth(stopping_volume_bbl - total_bbl))
        if bbl <= 0:
            break
        added_psi = hydrostatic_added(bbl, lubricated_mud_gradient_psi_per_ft, surface_annular_capacity_bbl_per_ft)
        bleed_to_psi = max(casing_psi - added_psi, 0)
        rows.append(LubricateCycle(cycle, casing_psi + working_pressure_psi, bbl, added_psi, bleed_to_psi))
        casing_psi = bleed_to_psi
        total_bbl = round_to_tenth(total_bbl + bbl)
    return rows


def remaining_underbalance(formation_psi, total_bbl_lubricated, lubricated_mud_gradient_psi_per_ft,
                           mud_gradient_psi_per_ft, td_tvd_ft, surface_annular_capacity_bbl_per_ft, tvd_of):
    """Pf - hydrostatic once the gas is out (whole psi, never below 0).

        Column     = Total bbl lubricated / Annular capacity at surface (ft MD) -> its TVD
        Hydrostatic = Lubricated mud gradient x Column TVD + Mud gradient x (TD TVD - Column TVD)

    tvd_of: turns an MD into a TVD (the well path).
    """
    column_tvd = tvd_of(total_bbl_lubricated / surface_annular_capacity_bbl_per_ft)
    hydrostatic = (lubricated_mud_gradient_psi_per_ft * column_tvd
                   + mud_gradient_psi_per_ft * (td_tvd_ft - column_tvd))
    return max(0, round_to_whole_number(formation_psi - hydrostatic))


def end_of_lubricate_and_bleed(casing_psi, underbalance_psi, safety_margin_psi):
    """What the sheet says once the gas is out (user wording)."""
    if underbalance_psi <= GAUGE_TOLERANCE_PSI:
        if casing_psi == 0:
            return "Hydrostatic control regained. Casing 0 psi. Check 0, flow check, then strip to bottom and circulate."
        return (f"Hydrostatic control regained. Casing {casing_psi:,} psi is trapped pressure. Bleed off in small "
                "increments, check 0, flow check, then strip to bottom and circulate.")
    return (f"Casing {casing_psi:,} psi. Remaining underbalance {underbalance_psi:,} psi. Do not bleed casing below "
            f"{underbalance_psi + safety_margin_psi:,} psi. Not dead. Kill required (strip to bottom and circulate, "
            "or bullhead).")
