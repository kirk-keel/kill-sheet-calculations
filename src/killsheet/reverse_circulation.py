"""Reverse circulation kill - completion, workover and intervention (CWI) wells.

Kill weight fluid is pumped down the tubing x casing annulus (the PUMP side),
through an opened SSD or a hole punched in the tubing above the production
packer, and back up the tubing (the RETURN side, through the choke). Think of
the SSD as the "bit", the annulus as the work string and the tubing as the
annulus of a drilling kill - the sides are swapped.

There is no dedicated IADC reverse circulation worksheet or formula; this is
built from the IADC basics and the user's rules:

  Kill weight fluid - balanced at the perfs WITH the column below the SSD left
  as formation fluid:
      Tubing fluid gradient = (Formation pressure - SITP) / Mid-perf TVD
      Pressure at the SSD   = Formation pressure - Tubing gradient x (Mid-perf TVD - SSD TVD)
      KWF = Pressure at the SSD / (0.052 x SSD TVD) + margin (default 0),
            rounded UP to the next 0.1 ppg (rule 1)

  Before start-up: open the SSD and let pressures stabilise - SICP isn't known
  until then. It equalises to: Pressure at the SSD - annulus hydrostatic.

  No SCR: on a CWI well circulating IS the kill. Bring the pump up to kill rate
  on the annulus holding TUBING pressure (the choke side) constant at the SITP;
  the annulus pressure read at rate is the OBSERVED ICP.

  FCP = Observed ICP - (KWF - packer fluid) x 0.052 x SSD TVD
  It equals circulating friction minus the overbalance at the SSD, so on a
  low-friction well it can be near zero or negative: then it is floored at 0
  with a warning.

  Limits on the annulus: the lower of the fracture pressure at the TOP perf
  (the weakest exposed point) minus the annulus hydrostatic, and the lowest
  rated or tested completion / surface equipment.

  TVD is used for pressures and MD for volumes and strokes.
"""

from typing import NamedTuple

from killsheet.depths import tvd_at_md
from killsheet.formulas import PSI_PER_FT_PER_PPG
from killsheet.kill_steps import CHECK, GAUGE_TOLERANCE_PSI, HOLD, SHUT_DOWN, START_UP, KillStep
from killsheet.rounding import (
    round_down_to_whole_number,
    round_to_4_places,
    round_to_tenth,
    round_to_whole_number,
    round_up_to_next_tenth,
)
from killsheet.schedule import strokes_per_step_for_ten_steps
from killsheet.strokes import md_after_strokes, strokes_to_length, surface_to_bit_strokes, total_length

FRICTION_WARNING = ("In reverse circulation, the high-friction path is the return side. If the choke is "
                    "wide open and pump pressure still climbs above FCP, BHP is rising. Reduce the rate.")
FCP_FLOOR_WARNING = ("FCP worked out at or below 0: annulus friction is less than the overbalance at the "
                     "SSD. FCP is set to 0.")

# Row labels.
STEP = "step"
ANNULUS_CROSSOVER = "annulus crossover"
AT_SSD = "kill fluid at the SSD - FCP"
TUBING_DISPLACED = "tubing displaced - kill fluid at surface"


def tubing_fluid_gradient(formation_pressure_psi, sitp_psi, mid_perf_tvd_ft):
    """Gradient of the fluid in the tubing (psi/ft), from the SITP, to 4 places.

        Tubing gradient = (Formation pressure - SITP) / Mid-perf TVD
    """
    return round_to_4_places((formation_pressure_psi - sitp_psi) / mid_perf_tvd_ft)


def pressure_at_ssd(formation_pressure_psi, tubing_gradient_psi_per_ft, mid_perf_tvd_ft, ssd_tvd_ft):
    """Pressure at the SSD (psi), whole psi - the column below the SSD stays formation fluid.

        Pressure at the SSD = Formation pressure - Tubing gradient x (Mid-perf TVD - SSD TVD)
    """
    return round_to_whole_number(formation_pressure_psi - tubing_gradient_psi_per_ft * (mid_perf_tvd_ft - ssd_tvd_ft))


def kill_weight_fluid(pressure_at_ssd_psi, ssd_tvd_ft, margin_ppg=0):
    """Kill weight fluid (ppg) that balances at the SSD, rounded UP to the next 0.1 ppg.

        KWF = Pressure at the SSD / (0.052 x SSD TVD) + margin

    The margin (default 0) is added BEFORE the rule-1 round-up.
    """
    return round_up_to_next_tenth(pressure_at_ssd_psi / (PSI_PER_FT_PER_PPG * ssd_tvd_ft) + margin_ppg)


def sicp_after_ssd_opened(pressure_at_ssd_psi, packer_fluid_ppg, ssd_tvd_ft):
    """SICP once the SSD is open and pressures stabilise (psi), whole psi.

        SICP = Pressure at the SSD - Packer fluid x 0.052 x SSD TVD
    """
    return round_to_whole_number(pressure_at_ssd_psi - packer_fluid_ppg * PSI_PER_FT_PER_PPG * ssd_tvd_ft)


def sitp_after_ssd_opened(pressure_at_ssd_psi, tubing_gradient_psi_per_ft, ssd_tvd_ft):
    """SITP once the SSD is open (psi), whole psi.

        SITP = Pressure at the SSD - Tubing gradient x SSD TVD
    """
    return round_to_whole_number(pressure_at_ssd_psi - tubing_gradient_psi_per_ft * ssd_tvd_ft)


def fracture_pressure(fracture_gradient_psi_per_ft, top_perf_tvd_ft):
    """Fracture pressure at the TOP perf (psi), rounded DOWN - IADC workover #7."""
    return round_down_to_whole_number(fracture_gradient_psi_per_ft * top_perf_tvd_ft)


def max_annulus_pressure(fracture_psi, kill_fluid_ppg, packer_fluid_ppg, kill_fluid_tvd_ft, ssd_tvd_ft,
                         tubing_gradient_psi_per_ft, top_perf_tvd_ft):
    """Formation limit on the annulus (psi), rounded DOWN.

        Max = Fracture pressure - annulus hydrostatic to the SSD
              - formation fluid from the SSD to the top perf

    kill_fluid_tvd_ft: how far kill fluid has got down the annulus (TVD); the
    rest of the annulus down to the SSD is still packer fluid.
    """
    annulus_hydrostatic = PSI_PER_FT_PER_PPG * (kill_fluid_ppg * kill_fluid_tvd_ft
                                                + packer_fluid_ppg * (ssd_tvd_ft - kill_fluid_tvd_ft))
    below_ssd = tubing_gradient_psi_per_ft * (top_perf_tvd_ft - ssd_tvd_ft)
    return round_down_to_whole_number(fracture_psi - annulus_hydrostatic - below_ssd)


def final_circulating_pressure(observed_icp_psi, kill_fluid_ppg, packer_fluid_ppg, ssd_tvd_ft):
    """FCP (psi) and whether it had to be floored at 0: (fcp_psi, floored).

        FCP = Observed ICP - (KWF - packer fluid) x 0.052 x SSD TVD

    The drop is rounded DOWN (like the Wait and Weight schedule). FCP is
    friction minus the overbalance at the SSD; at or below 0 it is set to 0.
    """
    drop = round_down_to_whole_number((kill_fluid_ppg - packer_fluid_ppg) * PSI_PER_FT_PER_PPG * ssd_tvd_ft)
    fcp = observed_icp_psi - drop
    if fcp <= 0:
        return 0, True
    return fcp, False


class ReverseRow(NamedTuple):
    """One row of the reverse circulation schedule (annulus pump pressure)."""

    strokes: int
    kill_fluid_md_ft: int           # kill fluid front in the annulus
    kill_fluid_tvd_ft: int
    pump_psi: int                   # annulus pump pressure to hold
    max_allowable_psi: int          # lower of the formation and equipment limits
    label: str


def reverse_schedule(observed_icp_psi, kill_fluid_ppg, packer_fluid_ppg, annulus_sections_top_down,
                     tubing_sections, pump_output_bbl_per_stk, fracture_psi, tubing_gradient_psi_per_ft,
                     top_perf_tvd_ft, equipment_limit_psi, ssd_tvd_ft=None, key_points=()):
    """Annulus pump pressure schedule, ICP down to FCP, then FCP while the tubing is displaced.

        Pump pressure = Observed ICP - (KWF - packer fluid) x 0.052 x TVD of the kill fluid,
                        drop rounded DOWN, never below 0

    annulus_sections_top_down / tubing_sections: (capacity bbl/ft, length ft MD),
    surface to the SSD. Steps: 10 steps of the annulus strokes.
    Vertical well: leave out ssd_tvd_ft and key_points.
    """
    pump = pump_output_bbl_per_stk
    ssd_md_ft = total_length(annulus_sections_top_down)
    ssd_tvd_ft = ssd_md_ft if ssd_tvd_ft is None else ssd_tvd_ft
    survey = [(md, tvd) for _name, md, tvd in key_points] + [(ssd_md_ft, ssd_tvd_ft)]
    annulus_strokes = surface_to_bit_strokes(annulus_sections_top_down, pump)
    tubing_strokes = surface_to_bit_strokes(tubing_sections, pump)
    fcp, _floored = final_circulating_pressure(observed_icp_psi, kill_fluid_ppg, packer_fluid_ppg, ssd_tvd_ft)

    def row(strokes, md_ft, label):
        tvd_ft = tvd_at_md(md_ft, survey)
        drop = round_down_to_whole_number((kill_fluid_ppg - packer_fluid_ppg) * PSI_PER_FT_PER_PPG * tvd_ft)
        pump_psi = max(observed_icp_psi - drop, 0)
        limit = max_annulus_pressure(fracture_psi, kill_fluid_ppg, packer_fluid_ppg, tvd_ft, ssd_tvd_ft,
                                     tubing_gradient_psi_per_ft, top_perf_tvd_ft)
        return ReverseRow(strokes, md_ft, tvd_ft, pump_psi, min(limit, equipment_limit_psi), label)

    rows = []
    strokes_per_step = strokes_per_step_for_ten_steps(annulus_strokes)
    for step in range(10):
        strokes = step * strokes_per_step
        rows.append(row(strokes, md_after_strokes(strokes, annulus_sections_top_down, pump), STEP))
    # Annulus crossovers (a tapered tubing string changes the annulus size): the
    # line bends there, so each gets its own row at its exact depth.
    md_ft = 0
    for _capacity, length_ft in annulus_sections_top_down[:-1]:
        md_ft += length_ft
        rows.append(row(strokes_to_length(annulus_sections_top_down, md_ft, pump), md_ft, ANNULUS_CROSSOVER))
    rows.sort(key=lambda r: r.strokes)
    at_ssd = row(annulus_strokes, ssd_md_ft, AT_SSD)
    rows.append(at_ssd._replace(pump_psi=fcp))
    rows.append(at_ssd._replace(strokes=annulus_strokes + tubing_strokes, pump_psi=fcp, label=TUBING_DISPLACED))
    return rows


def reverse_circulation_steps(sitp_psi, observed_icp_psi, fcp_psi, annulus_strokes, tubing_strokes):
    """Every step of a reverse circulation kill, in order (sides swapped from a drilling kill)."""
    kill = "reverse circulation (kill weight fluid down the annulus, up the tubing)"
    return [
        KillStep(kill, CHECK, "tubing and casing", None, None,
                 "open the SSD (or punch the tubing), let pressures stabilise, record SITP and SICP"),
        KillStep(kill, START_UP, "tubing", sitp_psi, None,
                 "bring the pump to kill rate on the ANNULUS holding TUBING pressure (choke side) constant "
                 "at the SITP"),
        KillStep(kill, HOLD, "annulus", observed_icp_psi, annulus_strokes,
                 f"read the observed ICP at rate, then step down to FCP {fcp_psi:,} psi - kill fluid "
                 "surface to SSD"),
        KillStep(kill, HOLD, "annulus", fcp_psi, tubing_strokes,
                 "hold FCP - kill fluid SSD to surface up the tubing. " + FRICTION_WARNING),
        KillStep(kill, SHUT_DOWN, "tubing", None, None,
                 "slow the pump to 0 holding TUBING pressure (choke side) constant"),
        KillStep(kill, CHECK, "tubing and casing", 0, None,
                 f"both must read 0 psi (+/-{GAUGE_TOLERANCE_PSI} psi)"),
        KillStep(kill, CHECK, "well", None, None, "flow check before declaring the well dead"),
    ]


def volume_below_ssd(tubing_capacity_bbl_per_ft, ssd_to_packer_ft, casing_capacity_bbl_per_ft,
                     packer_to_top_perf_ft):
    """Volume below the SSD that reverse circulation doesn't reach (bbl), to 0.1 bbl.

        Volume = Tubing capacity x (SSD to packer) + Casing capacity x (packer to top perf)
    """
    return round_to_tenth(round_to_tenth(tubing_capacity_bbl_per_ft * ssd_to_packer_ft)
                          + round_to_tenth(casing_capacity_bbl_per_ft * packer_to_top_perf_ft))


def bullhead_below_ssd_limits(fracture_psi, kill_fluid_ppg, ssd_tvd_ft, tubing_gradient_psi_per_ft,
                              top_perf_tvd_ft):
    """Optional bullhead of the volume below the SSD: max tubing pressure (psi), rounded DOWN.

        Initial = Fracture - KWF x 0.052 x SSD TVD - formation fluid from the SSD to the top perf
        Final   = Fracture - KWF x 0.052 x Top perf TVD
    Returns (initial, final).
    """
    initial = (fracture_psi - kill_fluid_ppg * PSI_PER_FT_PER_PPG * ssd_tvd_ft
               - tubing_gradient_psi_per_ft * (top_perf_tvd_ft - ssd_tvd_ft))
    final = fracture_psi - kill_fluid_ppg * PSI_PER_FT_PER_PPG * top_perf_tvd_ft
    return round_down_to_whole_number(initial), round_down_to_whole_number(final)
