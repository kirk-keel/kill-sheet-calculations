"""Volumetric method: bring migrating gas to surface without circulating.

Used whenever the well can't be circulated: pipe out of the hole, pipe above
the influx and unable to strip back to bottom, pipe in the hole and unable
to pump, and so on. One calculator covers them all: describe the annulus
from the BOTTOM UP, including sections with no pipe in them
(capacity bbl/ft, length ft).

The team killing the well chooses the safety margin and the working pressure.

    Wait:    let SICP rise by safety margin + working pressure (no bleeding)
    Cycle:   bleed the volume equivalent to the working pressure, holding
             casing pressure constant
    Wait:    let SICP rise by the working pressure again ... and repeat
    Stop:    the gas is at surface when SICP rises no more than 10 psi over a
             15 minute wait - then lubricate and bleed takes over.

IADC formula #35:
    Volume to bleed per cycle (bbl) = (Working pressure / Mud gradient) x Annular capacity

Which annular capacity? There is no single industry standard - the hydrostatic
per barrel changes with the annulus the gas is in, and its position can't be
known. It is the team's choice; the DEFAULT is the SMALLEST annulus the gas
will pass through, because it bleeds the least mud per cycle. The average and
the longest annulus are given for comparison.

Rounding: the volume to bleed is a limit (bleeding MORE loses bottomhole
pressure), so it is rounded DOWN to 0.1 bbl (rule 2).

Hold pressures above MAASP are WARNED, not stopped: as the gas comes up the
casing pressure keeps rising, and the team continues the operation.
"""

from typing import NamedTuple

from killsheet.formulas import PSI_PER_FT_PER_PPG
from killsheet.kill_steps import GAUGE_TOLERANCE_PSI
from killsheet.rounding import round_down_to_tenth, round_to_4_places, round_to_tenth

SMALLEST = "smallest annulus"
AVERAGE = "average annulus"
LONGEST = "longest annulus"

# The gas is at surface when SICP rises no more than 10 psi over this wait.
GAS_AT_SURFACE_WAIT_MINUTES = 15


def mud_gradient(mud_weight_ppg):
    """Mud gradient (psi/ft) = Mud weight x 0.052, to 4 decimal places (IADC table)."""
    return round_to_4_places(mud_weight_ppg * PSI_PER_FT_PER_PPG)


def annular_capacity_choices(annulus_sections_bottom_up):
    """The three annular capacities a team can choose from (bbl/ft).

        Smallest: the smallest capacity the gas will pass through (DEFAULT)
        Average:  total annulus volume / total annulus length
        Longest:  the capacity of the longest single section
    """
    total_volume_bbl = sum(round_to_tenth(cap * length) for cap, length in annulus_sections_bottom_up)
    total_length_ft = sum(length for _cap, length in annulus_sections_bottom_up)
    return {
        SMALLEST: min(cap for cap, _length in annulus_sections_bottom_up),
        AVERAGE: round_to_4_places(total_volume_bbl / total_length_ft),
        LONGEST: max(annulus_sections_bottom_up, key=lambda section: section[1])[0],
    }


def volume_to_bleed_per_cycle(working_pressure_psi, mud_gradient_psi_per_ft, annular_capacity_bbl_per_ft):
    """Volume to bleed per cycle (bbl), rounded DOWN to 0.1 bbl - IADC #35.

        Volume = (Working pressure / Mud gradient) x Annular capacity
    """
    return round_down_to_tenth(working_pressure_psi / mud_gradient_psi_per_ft * annular_capacity_bbl_per_ft)


def gas_at_surface(sicp_rise_in_15_minutes_psi):
    """True if SICP rose no more than 10 psi over a 15 minute wait - the gas is at surface."""
    return sicp_rise_in_15_minutes_psi <= GAUGE_TOLERANCE_PSI


class VolumetricCycle(NamedTuple):
    """One volumetric cycle."""

    cycle: int
    hold_psi: int               # casing pressure to hold while bleeding
    bleed_bbl: float            # bbl to bleed this cycle
    total_bled_bbl: float       # running total bled
    above_maasp: bool           # warn - but continue
    sicp_rise_psi: int          # SICP rise over the 15 minute wait after the cycle
    gas_at_surface: bool        # True ends the volumetric method


def volumetric_table(sicp_at_shut_in_psi, safety_margin_psi, working_pressure_psi,
                     bleed_bbl_per_cycle, maasp_psi, sicp_rises_after_each_cycle):
    """The volumetric cycles, driven by what the casing gauge does.

        Hold pressure, cycle 1 = SICP + Safety margin + Working pressure
        Hold pressure, cycle n = Hold pressure, cycle 1 + (n - 1) x Working pressure

    sicp_rises_after_each_cycle: the SICP rise (psi) the crew reads over the
    15 minute wait after each cycle. The table runs until a rise of 10 psi or
    less shows the gas is at surface. If the readings run out first, the
    table stops there - the next cycle needs the next reading.
    """
    rows = []
    hold_psi = sicp_at_shut_in_psi + safety_margin_psi + working_pressure_psi
    total_bled_bbl = 0
    for cycle, rise_psi in enumerate(sicp_rises_after_each_cycle, start=1):
        total_bled_bbl = round_to_tenth(total_bled_bbl + bleed_bbl_per_cycle)
        at_surface = gas_at_surface(rise_psi)
        rows.append(VolumetricCycle(cycle, hold_psi, bleed_bbl_per_cycle, total_bled_bbl,
                                    hold_psi > maasp_psi, rise_psi, at_surface))
        if at_surface:
            break
        hold_psi += working_pressure_psi
    return rows
