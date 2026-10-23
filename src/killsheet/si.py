"""SI Metric unit conversions and API wrapper for kill sheet calculations.

Standards & Conventions:
  - Density: kg/m3 (1 ppg = 119.8264 kg/m3)
  - Pressure: kPa (1 psi = 6.894757 kPa) or bar (1 bar = 100 kPa = 14.50377 psi)
  - Depths & Lengths: meters (1 ft = 0.3048 m)
  - Volumes: m3 (1 bbl = 0.1589873 m3)
  - Capacity: m3/m (1 bbl/ft = 0.5216119 m3/m)
  - Pump Output: m3/stroke (1 bbl/stk = 0.1589873 m3/stk)

All calculations delegate to the tested IADC WellSharp rules in the core engine,
guaranteeing consistent safety factor rounding and physics.
"""

from killsheet import formulas
from killsheet.kill_sheet import kill_sheet
from killsheet.rounding import round_to_whole_number

# Conversion factors (US Field -> SI)
PPG_TO_KG_M3 = 119.8264
PSI_TO_KPA = 6.894757
PSI_TO_BAR = 0.06894757
FT_TO_M = 0.3048
BBL_TO_M3 = 0.1589873
BBL_FT_TO_M3_M = 0.5216119


# ---------------------------------------------------------------------------
# Unit conversion helpers
# ---------------------------------------------------------------------------
def ppg_to_kg_m3(ppg: float) -> float:
    """Convert mud weight from ppg to kg/m3."""
    return ppg * PPG_TO_KG_M3


def kg_m3_to_ppg(kg_m3: float) -> float:
    """Convert mud weight from kg/m3 to ppg."""
    return kg_m3 / PPG_TO_KG_M3


def psi_to_kpa(psi: float) -> float:
    """Convert pressure from psi to kPa."""
    return psi * PSI_TO_KPA


def kpa_to_psi(kpa: float) -> float:
    """Convert pressure from kPa to psi."""
    return kpa / PSI_TO_KPA


def psi_to_bar(psi: float) -> float:
    """Convert pressure from psi to bar."""
    return psi * PSI_TO_BAR


def bar_to_psi(bar: float) -> float:
    """Convert pressure from bar to psi."""
    return bar / PSI_TO_BAR


def ft_to_m(ft: float) -> float:
    """Convert depth/length from ft to meters."""
    return ft * FT_TO_M


def m_to_ft(m: float) -> float:
    """Convert depth/length from meters to ft."""
    return m / FT_TO_M


def bbl_to_m3(bbl: float) -> float:
    """Convert volume from bbl to m3."""
    return bbl * BBL_TO_M3


def m3_to_bbl(m3: float) -> float:
    """Convert volume from m3 to bbl."""
    return m3 / BBL_TO_M3


def bbl_per_ft_to_m3_per_m(bbl_ft: float) -> float:
    """Convert capacity from bbl/ft to m3/m."""
    return bbl_ft * BBL_FT_TO_M3_M


def m3_per_m_to_bbl_per_ft(m3_m: float) -> float:
    """Convert capacity from m3/m to bbl/ft."""
    return m3_m / BBL_FT_TO_M3_M


# ---------------------------------------------------------------------------
# SI calculation functions
# ---------------------------------------------------------------------------
def kill_mud_weight_si(sidpp_kpa: float, tvd_m: float, original_mud_weight_kg_m3: float) -> float:
    """Kill mud weight (kg/m3) calculated using IADC rules and returned in kg/m3.

    Internally converts to ppg/ft/psi to apply the standard IADC 0.1 ppg upward safety factor,
    then returns the resulting density in kg/m3 (rounded to 1 decimal place).
    """
    sidpp_psi = kpa_to_psi(sidpp_kpa)
    tvd_ft = m_to_ft(tvd_m)
    omw_ppg = kg_m3_to_ppg(original_mud_weight_kg_m3)
    kmw_ppg = formulas.kill_mud_weight(sidpp_psi, tvd_ft, omw_ppg)
    return round(ppg_to_kg_m3(kmw_ppg), 1)


def initial_circulating_pressure_si(sidpp_kpa: float, scr_pressure_kpa: float) -> float:
    """Initial circulating pressure (ICP) in kPa.

        ICP = SIDPP + SCR
    """
    return round(sidpp_kpa + scr_pressure_kpa, 1)


def final_circulating_pressure_si(scr_pressure_kpa: float, kill_mud_weight_kg_m3: float,
                                  original_mud_weight_kg_m3: float) -> float:
    """Final circulating pressure (FCP) in kPa.

        FCP = SCR x (KMW / OMW)
    """
    if original_mud_weight_kg_m3 <= 0:
        raise ValueError("Original mud weight must be greater than 0.")
    return round(scr_pressure_kpa * (kill_mud_weight_kg_m3 / original_mud_weight_kg_m3), 1)


def max_allowable_mud_weight_si(lot_pressure_kpa: float, shoe_tvd_m: float,
                                test_mud_weight_kg_m3: float) -> float:
    """Maximum allowable mud weight (MAMW) in kg/m3.

    Applies downward truncation per IADC principles.
    """
    lot_psi = kpa_to_psi(lot_pressure_kpa)
    shoe_ft = m_to_ft(shoe_tvd_m)
    test_ppg = kg_m3_to_ppg(test_mud_weight_kg_m3)
    mamw_ppg = formulas.max_allowable_mud_weight(lot_psi, shoe_ft, test_ppg)
    return round(ppg_to_kg_m3(mamw_ppg), 1)


# Aliases
icp_si = initial_circulating_pressure_si
fcp_si = final_circulating_pressure_si
mamw_si = max_allowable_mud_weight_si


def maasp_si(max_allowable_mud_weight_kg_m3: float, current_mud_weight_kg_m3: float,
             shoe_tvd_m: float) -> float:
    """MAASP in kPa, rounded down to whole kPa.

        MAASP = (Max MW - Current MW) x g x Shoe TVD
    """
    mamw_ppg = kg_m3_to_ppg(max_allowable_mud_weight_kg_m3)
    cmw_ppg = kg_m3_to_ppg(current_mud_weight_kg_m3)
    shoe_ft = m_to_ft(shoe_tvd_m)
    maasp_psi = formulas.maasp(mamw_ppg, cmw_ppg, shoe_ft)
    return round_to_whole_number(psi_to_kpa(maasp_psi))


def kill_sheet_si(title: str,
                  bit_tvd_m: float,
                  shoe_tvd_m: float,
                  original_mud_weight_kg_m3: float,
                  lot_pressure_kpa: float,
                  test_mud_weight_kg_m3: float,
                  sidpp_kpa: float,
                  sicp_kpa: float,
                  scr_pressure_kpa: float,
                  safety_margin_kpa: float,
                  pump_output_m3_per_stk: float,
                  drill_string_si: list[tuple[str, float, float]],
                  open_hole_annulus_si: list[tuple[str, float, float]],
                  cased_hole_annulus_si: list[tuple[str, float, float]],
                  bit_md_m: float = None,
                  shoe_md_m: float = None,
                  key_points_si: tuple = (),
                  surface_line_volume_m3: float = 0,
                  method: str = "Driller's method",
                  step_method: str = "10 steps",
                  sidpp_at_start_kpa: float = None,
                  sicp_at_start_kpa: float = None,
                  observed_icp_kpa: float = None,
                  pit_gain_m3: float = None) -> dict:
    """High-level kill sheet calculator using SI metric inputs, returning SI outputs."""
    # Convert inputs to oilfield units
    bit_tvd_ft = m_to_ft(bit_tvd_m)
    shoe_tvd_ft = m_to_ft(shoe_tvd_m)
    omw_ppg = kg_m3_to_ppg(original_mud_weight_kg_m3)
    lot_psi = kpa_to_psi(lot_pressure_kpa)
    test_ppg = kg_m3_to_ppg(test_mud_weight_kg_m3)
    sidpp_psi = kpa_to_psi(sidpp_kpa)
    sicp_psi = kpa_to_psi(sicp_kpa)
    scr_psi = kpa_to_psi(scr_pressure_kpa)
    sf_psi = kpa_to_psi(safety_margin_kpa)
    pump_out_bbl = m3_to_bbl(pump_output_m3_per_stk)

    ds_sections = [(name, m3_per_m_to_bbl_per_ft(cap), m_to_ft(length)) for name, cap, length in drill_string_si]
    oh_sections = [(name, m3_per_m_to_bbl_per_ft(cap), m_to_ft(length)) for name, cap, length in open_hole_annulus_si]
    ch_sections = [(name, m3_per_m_to_bbl_per_ft(cap), m_to_ft(length)) for name, cap, length in cased_hole_annulus_si]

    bit_md_ft = m_to_ft(bit_md_m) if bit_md_m is not None else None
    shoe_md_ft = m_to_ft(shoe_md_m) if shoe_md_m is not None else None
    kp_ft = tuple((name, m_to_ft(md), m_to_ft(tvd)) for name, md, tvd in key_points_si)
    surface_line_bbl = m3_to_bbl(surface_line_volume_m3)

    sidpp_start_psi = kpa_to_psi(sidpp_at_start_kpa) if sidpp_at_start_kpa is not None else None
    sicp_start_psi = kpa_to_psi(sicp_at_start_kpa) if sicp_at_start_kpa is not None else None
    obs_icp_psi = kpa_to_psi(observed_icp_kpa) if observed_icp_kpa is not None else None
    pit_gain_bbl = m3_to_bbl(pit_gain_m3) if pit_gain_m3 is not None else None

    # Call core engine
    field_result = kill_sheet(
        title=title,
        bit_tvd_ft=bit_tvd_ft,
        shoe_tvd_ft=shoe_tvd_ft,
        original_mud_weight_ppg=omw_ppg,
        lot_pressure_psi=lot_psi,
        test_mud_weight_ppg=test_ppg,
        sidpp_psi=sidpp_psi,
        sicp_psi=sicp_psi,
        scr_pressure_psi=scr_psi,
        safety_margin_psi=sf_psi,
        pump_output_bbl_per_stk=pump_out_bbl,
        drill_string=ds_sections,
        open_hole_annulus=oh_sections,
        cased_hole_annulus=ch_sections,
        bit_md_ft=bit_md_ft,
        shoe_md_ft=shoe_md_ft,
        key_points=kp_ft,
        surface_line_volume_bbl=surface_line_bbl,
        method=method,
        step_method=step_method,
        sidpp_at_start_psi=sidpp_start_psi,
        sicp_at_start_psi=sicp_start_psi,
        observed_icp_psi=obs_icp_psi,
        pit_gain_bbl=pit_gain_bbl,
    )

    # Extract drill string volume and annulus volume from volumes
    ds_vol_bbl = next((v["volume_bbl"] for v in field_result["volumes"] if "Surface to bit" in v["name"]), 0.0)
    ann_vol_bbl = next((v["volume_bbl"] for v in field_result["volumes"] if "Total annulus" in v["name"]), 0.0)

    return {
        "title": field_result["title"],
        "method": field_result["method"],
        "kill_mud_weight_kg_m3": round(ppg_to_kg_m3(field_result["kill_mud_weight_ppg"]), 1),
        "kill_mud_weight_sg": round(field_result["kill_mud_weight_ppg"] / 8.3454, 3),
        "icp_kpa": round(psi_to_kpa(field_result["icp_psi"]), 1),
        "icp_bar": round(psi_to_bar(field_result["icp_psi"]), 2),
        "fcp_kpa": round(psi_to_kpa(field_result["fcp_psi"]), 1),
        "fcp_bar": round(psi_to_bar(field_result["fcp_psi"]), 2),
        "max_allowable_mud_weight_kg_m3": round(ppg_to_kg_m3(field_result["max_allowable_mud_weight_ppg"]), 1),
        "maasp_original_kpa": round(psi_to_kpa(field_result["maasp_original_psi"]), 1),
        "maasp_after_kill_kpa": round(psi_to_kpa(field_result["maasp_after_kill_psi"]), 1),
        "surface_to_bit_strokes": field_result["surface_to_bit_strokes"],
        "bit_to_shoe_strokes": field_result["bit_to_shoe_strokes"],
        "bit_to_surface_strokes": field_result["bit_to_surface_strokes"],
        "drill_string_volume_m3": round(bbl_to_m3(ds_vol_bbl), 2),
        "annulus_volume_m3": round(bbl_to_m3(ann_vol_bbl), 2),
        "safety_margin_kpa": round(psi_to_kpa(field_result["safety_margin_psi"]), 1),
        "_field_units": field_result,
    }
