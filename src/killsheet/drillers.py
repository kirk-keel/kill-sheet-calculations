"""Driller's method: the simplest kill (vertical well, untapered string).

Two circulations at the kill rate:

  1st circulation - ORIGINAL mud, circulate the kick out:
      Hold DRILL PIPE pressure at ICP for bottoms up (bit-to-surface strokes).
      Shut in: SIDPP and SICP should now both read the original SIDPP.

  2nd circulation - KILL mud:
      a) Hold CASING pressure constant (at the SIDPP value) while kill mud
         is pumped from surface to the bit (surface-to-bit strokes).
      b) Hold DRILL PIPE pressure at FCP while kill mud is pumped from the
         bit back to surface (bit-to-surface strokes).

No pressure schedule is needed - that's what makes it the simplest kill.
All pressures and strokes passed in are already rounded.
"""

from typing import NamedTuple


class KillStep(NamedTuple):
    """One leg of the kill: which gauge to hold, at what pressure, for how many strokes."""

    circulation: str
    gauge: str
    hold_psi: int
    strokes: int


def drillers_method(sidpp_psi, icp_psi, fcp_psi, surface_to_bit_strokes, bit_to_surface_strokes):
    """The three legs of a Driller's method kill, in order.

        1st circulation:           hold drill pipe at ICP   for bit-to-surface strokes
        2nd circulation, leg 1:    hold casing at SIDPP     for surface-to-bit strokes
        2nd circulation, leg 2:    hold drill pipe at FCP   for bit-to-surface strokes
    """
    return [
        KillStep("1st circulation (original mud)", "drill pipe", icp_psi, bit_to_surface_strokes),
        KillStep("2nd circulation (kill mud), surface to bit", "casing", sidpp_psi, surface_to_bit_strokes),
        KillStep("2nd circulation (kill mud), bit to surface", "drill pipe", fcp_psi, bit_to_surface_strokes),
    ]
