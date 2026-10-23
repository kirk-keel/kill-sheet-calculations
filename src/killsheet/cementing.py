"""Balanced cement plug calculations, spacer balancing, and displacement volumes.

Standards & Conventions:
  - Depths & Lengths: feet (ft)
  - Volumes: barrels (bbl)
  - Capacities: bbl/ft
  - Slurry Yield: cubic feet per sack (cu ft/sk)
  - Mix Water: gallons per sack (gal/sk)
  - Density: ppg

Physical Model:
  A balanced cement plug requires hydrostatic and volumetric equilibrium between the
  drillpipe/workstring and the annulus so fluid does not U-tube when the string is pulled:
    1. Slurry Volume:
         V_slurry = Plug_Length x Hole_Capacity x (1 + Excess_Factor)
    2. Height of Balanced Plug with Pipe in Place:
         h_balanced = V_slurry / (Capacity_pipe + Capacity_annulus)
    3. Balanced Spacer Behind (U-tube Hydrostatic Balance):
         V_spacer_behind = V_spacer_ahead x (Capacity_pipe / Capacity_annulus)
    4. Displacement Volume (to top of balanced plug):
         V_disp = (Bottom_MD - h_balanced) x Capacity_pipe
    5. Cement Sacks:
         Sacks = (V_slurry x 5.61458 cu ft/bbl) / Slurry_Yield_cu_ft_per_sk
"""

from typing import Any, Dict

from killsheet.rounding import (
    round_to_hundredth,
    round_to_tenth,
    round_to_whole_number,
)

CU_FT_PER_BBL = 5.61458


def cement_slurry_volume_bbl(
    plug_length_ft: float,
    hole_capacity_bbl_per_ft: float,
    excess_percent: float = 0.0,
) -> float:
    """Calculates theoretical cement slurry volume in barrels including open-hole excess.

        V_slurry = Length x Hole_Capacity x (1 + excess / 100)
    """
    if plug_length_ft <= 0 or hole_capacity_bbl_per_ft <= 0:
        raise ValueError("Plug length and hole capacity must be positive.")
    if excess_percent < 0:
        raise ValueError("Excess percent cannot be negative.")
    vol = plug_length_ft * hole_capacity_bbl_per_ft * (1.0 + excess_percent / 100.0)
    return round_to_tenth(vol)


def balanced_plug_height_ft(
    slurry_volume_bbl: float,
    pipe_capacity_bbl_per_ft: float,
    annular_capacity_bbl_per_ft: float,
) -> float:
    """Calculates height of cement in the hole with workstring in place (ft).

        h_balanced = V_slurry / (C_pipe + C_ann)
    """
    if slurry_volume_bbl <= 0:
        raise ValueError("Slurry volume must be positive.")
    total_cap = pipe_capacity_bbl_per_ft + annular_capacity_bbl_per_ft
    if total_cap <= 0:
        raise ValueError("Combined pipe and annular capacity must be positive.")
    return round_to_tenth(slurry_volume_bbl / total_cap)


def balanced_spacer_behind_bbl(
    spacer_ahead_bbl: float,
    pipe_capacity_bbl_per_ft: float,
    annular_capacity_bbl_per_ft: float,
) -> float:
    """Sizes spacer volume behind cement to achieve identical hydrostatic column height in pipe and annulus.

        V_behind = V_ahead x (C_pipe / C_ann)
    """
    if spacer_ahead_bbl <= 0:
        return 0.0
    if annular_capacity_bbl_per_ft <= 0:
        raise ValueError("Annular capacity must be positive.")
    v_behind = spacer_ahead_bbl * (pipe_capacity_bbl_per_ft / annular_capacity_bbl_per_ft)
    return round_to_tenth(v_behind)


def displacement_volume_to_plug_top_bbl(
    workstring_bottom_md_ft: float,
    balanced_plug_height_ft: float,
    pipe_capacity_bbl_per_ft: float,
) -> float:
    """Calculates mud displacement volume to place top of cement at balanced height inside pipe.

        V_disp = (Bottom_MD - h_balanced) x C_pipe
    """
    if workstring_bottom_md_ft <= balanced_plug_height_ft:
        raise ValueError(
            f"Workstring bottom ({workstring_bottom_md_ft} ft) must be deeper than plug height ({balanced_plug_height_ft} ft)."
        )
    disp = (workstring_bottom_md_ft - balanced_plug_height_ft) * pipe_capacity_bbl_per_ft
    return round_to_tenth(disp)


def calculate_cement_sacks_and_water(
    slurry_volume_bbl: float,
    slurry_yield_cu_ft_per_sk: float = 1.18,
    mix_water_gal_per_sk: float = 5.0,
) -> Dict[str, Any]:
    """Calculates total sacks of dry cement and mix water barrels required."""
    if slurry_volume_bbl <= 0 or slurry_yield_cu_ft_per_sk <= 0:
        raise ValueError("Slurry volume and yield must be positive.")
    total_cu_ft = slurry_volume_bbl * CU_FT_PER_BBL
    sacks = round_to_whole_number(total_cu_ft / slurry_yield_cu_ft_per_sk)
    water_bbl = round_to_tenth((sacks * mix_water_gal_per_sk) / 42.0)
    return {
        "sacks_cement": sacks,
        "slurry_volume_cu_ft": round_to_tenth(total_cu_ft),
        "mix_water_bbl": water_bbl,
    }


def balanced_cement_plug_summary(
    plug_top_md_ft: float,
    plug_bottom_md_ft: float,
    hole_capacity_bbl_per_ft: float,
    pipe_capacity_bbl_per_ft: float,
    annular_capacity_bbl_per_ft: float,
    spacer_ahead_bbl: float = 20.0,
    excess_percent: float = 0.0,
    slurry_yield_cu_ft_per_sk: float = 1.18,
    mix_water_gal_per_sk: float = 5.0,
) -> Dict[str, Any]:
    """Complete engineering schedule for a balanced cement plug."""
    if plug_bottom_md_ft <= plug_top_md_ft:
        raise ValueError("Plug bottom depth must be deeper than plug top depth.")

    plug_len = plug_bottom_md_ft - plug_top_md_ft
    v_slurry = cement_slurry_volume_bbl(plug_len, hole_capacity_bbl_per_ft, excess_percent)
    h_bal = balanced_plug_height_ft(v_slurry, pipe_capacity_bbl_per_ft, annular_capacity_bbl_per_ft)
    v_behind = balanced_spacer_behind_bbl(spacer_ahead_bbl, pipe_capacity_bbl_per_ft, annular_capacity_bbl_per_ft)
    v_disp = displacement_volume_to_plug_top_bbl(plug_bottom_md_ft, h_bal, pipe_capacity_bbl_per_ft)
    mix = calculate_cement_sacks_and_water(v_slurry, slurry_yield_cu_ft_per_sk, mix_water_gal_per_sk)

    return {
        "plug_length_ft": plug_len,
        "slurry_volume_bbl": v_slurry,
        "balanced_plug_height_with_pipe_ft": h_bal,
        "top_of_cement_with_pipe_md_ft": round_to_whole_number(plug_bottom_md_ft - h_bal),
        "spacer_ahead_bbl": spacer_ahead_bbl,
        "balanced_spacer_behind_bbl": v_behind,
        "displacement_volume_bbl": v_disp,
        "sacks_cement": mix["sacks_cement"],
        "mix_water_bbl": mix["mix_water_bbl"],
    }
