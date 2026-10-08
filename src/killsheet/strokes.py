"""Volumes and pump strokes for a vertical well with a surface BOP stack.

Units: bbl/ft (capacity), ft (length), bbl (volume), bbl/stk (pump output).

A "section" is one length of pipe or annulus with a single capacity,
written as a pair: (capacity_bbl_per_ft, length_ft). For example, 10,600 ft
of drill pipe with a capacity of 0.0178 bbl/ft is (0.0178, 10_600).

Rounding (rule 3, academic rounding to IADC's accuracy):
  - each section volume and each total volume to 0.1 bbl
  - strokes to a whole number
"""

from killsheet.rounding import round_to_tenth, round_to_whole_number


def section_volume(capacity_bbl_per_ft, length_ft):
    """Volume of one section (bbl), rounded to 0.1 bbl.

        Volume = Capacity x Length
    """
    return round_to_tenth(capacity_bbl_per_ft * length_ft)


def total_volume(sections):
    """Total volume of a list of sections (bbl), rounded to 0.1 bbl.

        Total volume = sum of each section's rounded volume
    """
    total = 0
    for capacity_bbl_per_ft, length_ft in sections:
        total += section_volume(capacity_bbl_per_ft, length_ft)
    return round_to_tenth(total)


def strokes_for_volume(volume_bbl, pump_output_bbl_per_stk):
    """Pump strokes needed to pump a volume, rounded to a whole stroke.

        Strokes = Volume / Pump output
    """
    return round_to_whole_number(volume_bbl / pump_output_bbl_per_stk)


def surface_to_bit_strokes(drill_string_sections, pump_output_bbl_per_stk, surface_line_volume_bbl=0):
    """Strokes to pump kill mud from surface to the bit.

        Strokes = (Surface line volume + Drill string volume) / Pump output

    drill_string_sections: drill pipe, HWDP, drill collars, etc.
    surface_line_volume_bbl: optional (standpipe, kelly hose / top drive).
    Leave it out if you don't have it and it is counted as 0.
    """
    volume_bbl = round_to_tenth(surface_line_volume_bbl + total_volume(drill_string_sections))
    return strokes_for_volume(volume_bbl, pump_output_bbl_per_stk)


def crossover_strokes(sections, pump_output_bbl_per_stk, starting_volume_bbl=0):
    """Strokes to the END of each section, in the order the sections are listed.

        Strokes to a crossover = Running total volume / Pump output

    The running total adds each section's ROUNDED volume and is rounded to
    0.1 bbl, so the last crossover always matches the total strokes.

    Drill string: list sections top to bottom, and pass any surface line
                  volume as starting_volume_bbl. Shows where the kill mud is.
    Annulus:      list sections from the bit up.
    """
    running_volume_bbl = starting_volume_bbl
    strokes = []
    for capacity_bbl_per_ft, length_ft in sections:
        running_volume_bbl = round_to_tenth(running_volume_bbl + section_volume(capacity_bbl_per_ft, length_ft))
        strokes.append(strokes_for_volume(running_volume_bbl, pump_output_bbl_per_stk))
    return strokes


def bit_to_shoe_strokes(open_hole_annulus_sections, pump_output_bbl_per_stk):
    """Strokes to pump from the bit up to the casing shoe.

        Strokes = Open hole annulus volume / Pump output

    open_hole_annulus_sections: the annulus sections BELOW the shoe only.
    """
    return strokes_for_volume(total_volume(open_hole_annulus_sections), pump_output_bbl_per_stk)


def bit_to_surface_strokes(annulus_sections, pump_output_bbl_per_stk):
    """Strokes to pump from the bit all the way up to surface.

        Strokes = Total annulus volume / Pump output

    annulus_sections: ALL annulus sections, open hole and cased hole.
    """
    return strokes_for_volume(total_volume(annulus_sections), pump_output_bbl_per_stk)
