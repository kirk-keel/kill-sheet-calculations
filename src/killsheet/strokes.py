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


def volume_to_length(sections, length_ft):
    """Volume (bbl) of the first length_ft of a list of sections, rounded to 0.1 bbl.

    Used for a point partway through a section (e.g. KOP in the drill pipe):
    only the part of that section up to the point is counted.

        Partial section volume = Capacity x Length used (rounded to 0.1 bbl)
        Volume = Running total of rounded section volumes
    """
    remaining_ft = length_ft
    running_volume_bbl = 0
    for capacity_bbl_per_ft, section_length_ft in sections:
        if remaining_ft <= 0:
            break
        used_ft = min(section_length_ft, remaining_ft)
        running_volume_bbl = round_to_tenth(running_volume_bbl + section_volume(capacity_bbl_per_ft, used_ft))
        remaining_ft -= used_ft
    if remaining_ft > 0:
        raise ValueError(f"{length_ft:,} ft is longer than the sections ({length_ft - remaining_ft:,} ft)")
    return running_volume_bbl


def strokes_to_length(sections, length_ft, pump_output_bbl_per_stk, starting_volume_bbl=0):
    """Strokes to pump through the first length_ft of a list of sections.

        Strokes = (Starting volume + Volume to that length) / Pump output

    Drill string: length = MD of the point (sections top down; surface
                  lines as the starting volume). Shows where the kill mud is.
    Annulus:      length = bit MD - MD of the point (sections bit up).
    """
    volume_bbl = round_to_tenth(starting_volume_bbl + volume_to_length(sections, length_ft))
    return strokes_for_volume(volume_bbl, pump_output_bbl_per_stk)


def total_length(sections):
    """Total length (ft) of a list of sections."""
    return sum(length_ft for _capacity, length_ft in sections)


def check_section_lengths(drill_string_sections, open_hole_annulus_sections,
                          cased_hole_annulus_sections, bit_md_ft, shoe_md_ft):
    """Raise ValueError if the section lengths don't add up - a typo in a
    length would otherwise give wrong strokes without any warning.

        Drill string length       = Bit MD
        Open hole annulus length  = Bit MD - Shoe MD
        Cased hole annulus length = Shoe MD
    """
    checks = [
        ("Drill string", total_length(drill_string_sections), bit_md_ft),
        ("Open hole annulus", total_length(open_hole_annulus_sections), bit_md_ft - shoe_md_ft),
        ("Cased hole annulus", total_length(cased_hole_annulus_sections), shoe_md_ft),
    ]
    for name, actual_ft, expected_ft in checks:
        if actual_ft != expected_ft:
            raise ValueError(f"{name} sections add up to {actual_ft:,} ft MD but should be {expected_ft:,} ft")


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
