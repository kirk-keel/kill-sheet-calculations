"""Tripping, slug, and pipe displacement calculations for rig-floor operations.

Units:
  - Density: ppg
  - Pressure: psi
  - Depths & Lengths: ft
  - Volumes: bbl
  - Capacities & Displacements: bbl/ft
  - Strokes: whole strokes

Core calculations:
  - Heavy slug volume required for desired dry pipe height
  - Pit gain from U-tubing after pumping a slug
  - Dry vs. wet pipe displacement and fill-up volumes
  - Hydrostatic pressure loss and fluid level drop if hole is not filled
  - Swab pressure margin and trip sheet reconciliation
"""

from killsheet.formulas import PSI_PER_FT_PER_PPG
from killsheet.rounding import round_to_tenth, round_to_whole_number
from killsheet.strokes import strokes_for_volume


def slug_volume_for_dry_pipe(desired_dry_pipe_ft, dp_capacity_bbl_per_ft,
                             original_mud_weight_ppg, slug_weight_ppg):
    """Volume of heavy slug (bbl) required to drop fluid level by desired dry pipe height.

        V_slug = (H_dry x Cap_DP x OMW) / (Slug_MW - OMW)

    Rounded to 0.1 bbl.
    """
    if desired_dry_pipe_ft <= 0:
        raise ValueError(f"Desired dry pipe height must be > 0 ft (got {desired_dry_pipe_ft}).")
    if dp_capacity_bbl_per_ft <= 0:
        raise ValueError(f"Drill pipe capacity must be > 0 bbl/ft (got {dp_capacity_bbl_per_ft}).")
    if original_mud_weight_ppg <= 0:
        raise ValueError(f"Original mud weight must be > 0 ppg (got {original_mud_weight_ppg}).")
    if slug_weight_ppg <= original_mud_weight_ppg:
        raise ValueError(
            f"Slug weight ({slug_weight_ppg} ppg) must be greater than "
            f"original mud weight ({original_mud_weight_ppg} ppg)."
        )

    raw_vol = (desired_dry_pipe_ft * dp_capacity_bbl_per_ft * original_mud_weight_ppg) / (slug_weight_ppg - original_mud_weight_ppg)
    return round_to_tenth(raw_vol)


def slug_pit_gain(slug_volume_bbl, original_mud_weight_ppg, slug_weight_ppg):
    """Pit volume increase (bbl) when the slug U-tubes to equilibrium.

        Pit Gain = V_slug x (Slug_MW - OMW) / OMW = H_dry x Cap_DP

    Rounded to 0.1 bbl.
    """
    if slug_volume_bbl <= 0:
        raise ValueError(f"Slug volume must be > 0 bbl (got {slug_volume_bbl}).")
    if original_mud_weight_ppg <= 0:
        raise ValueError(f"Original mud weight must be > 0 ppg (got {original_mud_weight_ppg}).")
    if slug_weight_ppg <= original_mud_weight_ppg:
        raise ValueError(f"Slug weight must exceed original mud weight.")

    raw_gain = slug_volume_bbl * (slug_weight_ppg - original_mud_weight_ppg) / original_mud_weight_ppg
    return round_to_tenth(raw_gain)


def slug_length_in_pipe(slug_volume_bbl, dp_capacity_bbl_per_ft):
    """Length of the slug inside the drill pipe (ft), rounded to whole feet.

        Length = Volume / Capacity
    """
    if slug_volume_bbl <= 0 or dp_capacity_bbl_per_ft <= 0:
        raise ValueError("Slug volume and DP capacity must be > 0.")
    return round_to_whole_number(slug_volume_bbl / dp_capacity_bbl_per_ft)


def dry_pipe_fill_volume(length_pulled_ft, pipe_steel_disp_bbl_per_ft):
    """Mud required to keep hole full when pulling pipe DRY (bbl), rounded to 0.1 bbl.

        V_fill = Length x Steel Displacement
    """
    if length_pulled_ft <= 0 or pipe_steel_disp_bbl_per_ft <= 0:
        raise ValueError("Length pulled and steel displacement must be > 0.")
    return round_to_tenth(length_pulled_ft * pipe_steel_disp_bbl_per_ft)


def wet_pipe_fill_volume(length_pulled_ft, pipe_closed_disp_bbl_per_ft):
    """Mud required to keep hole full when pulling pipe WET (bbl), rounded to 0.1 bbl.

        V_fill = Length x Closed-End Displacement
        Closed-End Displacement = (Cap_DP + Disp_steel) = OD^2 / 1029.4
    """
    if length_pulled_ft <= 0 or pipe_closed_disp_bbl_per_ft <= 0:
        raise ValueError("Length pulled and closed-end displacement must be > 0.")
    return round_to_tenth(length_pulled_ft * pipe_closed_disp_bbl_per_ft)


def level_drop_unfilled_hole(volume_unfilled_bbl, casing_or_annulus_cap_bbl_per_ft):
    """Fluid level drop inside casing or hole if not filled (ft), whole feet.

        Drop = Volume / Annulus Capacity
    """
    if volume_unfilled_bbl <= 0 or casing_or_annulus_cap_bbl_per_ft <= 0:
        raise ValueError("Volume and capacity must be > 0.")
    return round_to_whole_number(volume_unfilled_bbl / casing_or_annulus_cap_bbl_per_ft)


def hydrostatic_loss_from_level_drop(level_drop_ft, mud_weight_ppg):
    """Hydrostatic pressure lost due to fluid level drop (psi), whole psi.

        dP = 0.052 x MW x Drop
    """
    if level_drop_ft < 0 or mud_weight_ppg <= 0:
        raise ValueError("Level drop cannot be negative and mud weight must be > 0.")
    return round_to_whole_number(PSI_PER_FT_PER_PPG * mud_weight_ppg * level_drop_ft)


def trip_slug_summary(desired_dry_pipe_ft, dp_capacity_bbl_per_ft,
                      original_mud_weight_ppg, slug_weight_ppg,
                      pump_output_bbl_per_stk=None):
    """Complete summary of a heavy slug pumping operation."""
    slug_vol = slug_volume_for_dry_pipe(
        desired_dry_pipe_ft, dp_capacity_bbl_per_ft, original_mud_weight_ppg, slug_weight_ppg
    )
    gain = slug_pit_gain(slug_vol, original_mud_weight_ppg, slug_weight_ppg)
    length = slug_length_in_pipe(slug_vol, dp_capacity_bbl_per_ft)
    stks = strokes_for_volume(slug_vol, pump_output_bbl_per_stk) if pump_output_bbl_per_stk else None

    return {
        "desired_dry_pipe_ft": desired_dry_pipe_ft,
        "slug_volume_bbl": slug_vol,
        "slug_length_ft": length,
        "pit_gain_bbl": gain,
        "pump_strokes": stks,
        "original_mud_weight_ppg": original_mud_weight_ppg,
        "slug_weight_ppg": slug_weight_ppg,
    }
