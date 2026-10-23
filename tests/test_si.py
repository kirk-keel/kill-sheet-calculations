"""Tests for SI Metric conversions and wrapper functions."""

import pytest

from killsheet.si import (
    bar_to_psi,
    bbl_per_ft_to_m3_per_m,
    bbl_to_m3,
    fcp_si,
    ft_to_m,
    icp_si,
    kg_m3_to_ppg,
    kill_mud_weight_si,
    kill_sheet_si,
    kpa_to_psi,
    m3_per_m_to_bbl_per_ft,
    m3_to_bbl,
    m_to_ft,
    maasp_si,
    max_allowable_mud_weight_si,
    ppg_to_kg_m3,
    psi_to_bar,
    psi_to_kpa,
)


def test_conversion_helpers_round_trip():
    # Density
    assert abs(kg_m3_to_ppg(ppg_to_kg_m3(12.5)) - 12.5) < 1e-9
    # Pressure
    assert abs(kpa_to_psi(psi_to_kpa(1500.0)) - 1500.0) < 1e-9
    assert abs(bar_to_psi(psi_to_bar(2000.0)) - 2000.0) < 1e-9
    # Length
    assert abs(m_to_ft(ft_to_m(10000.0)) - 10000.0) < 1e-9
    # Volume
    assert abs(m3_to_bbl(bbl_to_m3(500.0)) - 500.0) < 1e-9
    # Capacity
    assert abs(m3_per_m_to_bbl_per_ft(bbl_per_ft_to_m3_per_m(0.0178)) - 0.0178) < 1e-9


def test_si_core_calculations():
    # Hand-checked baseline vertical well in SI:
    # OMW = 10.4 ppg = 1246.2 kg/m3
    # SIDPP = 650 psi = 4481.6 kPa
    # TVD = 11,500 ft = 3505.2 m
    # KMW in field units is 11.5 ppg = 1378.0 kg/m3
    kmw_si = kill_mud_weight_si(sidpp_kpa=4481.6, tvd_m=3505.2, original_mud_weight_kg_m3=1246.2)
    assert kmw_si == 1378.0

    # ICP: SIDPP 4481.6 kPa + SCR 5171.1 kPa (750 psi) = 9652.7 kPa
    assert icp_si(4481.6, 5171.1) == 9652.7

    # FCP: 5171.1 x (1378.0 / 1246.2) = 5718.1 kPa (approx 829 psi = 5715 kPa)
    fcp = fcp_si(5171.1, 1378.0, 1246.2)
    assert round(fcp, 0) == 5718.0

    # MAMW & MAASP
    # LOT = 1350 psi = 9307.9 kPa, Shoe TVD = 5150 ft = 1569.7 m, Test MW = 9.6 ppg = 1150.3 kg/m3
    # MAMW field is 14.6 ppg = 1749.5 kg/m3
    mamw = max_allowable_mud_weight_si(9307.9, 1569.7, 1150.3)
    assert mamw == 1749.5

    # MAASP = (14.6 - 10.4) x 0.052 x 5150 = 1124 psi = 7749.7 kPa -> 7750 kPa
    maasp = maasp_si(1749.5, 1246.2, 1569.7)
    assert abs(maasp - 7750) <= 2


def test_kill_sheet_si_wrapper():
    # Run a complete baseline well using SI inputs
    from killsheet.kill_sheet import DRILLERS

    # Drill string: 10,000 ft 5" DP (0.0178 bbl/ft), 900 ft HWDP (0.0087 bbl/ft), 600 ft DC (0.0077 bbl/ft)
    ds_si = [
        ("DP 5 in", bbl_per_ft_to_m3_per_m(0.0178), ft_to_m(10000)),
        ("HWDP 5 in", bbl_per_ft_to_m3_per_m(0.0087), ft_to_m(900)),
        ("DC 6.5 in", bbl_per_ft_to_m3_per_m(0.0077), ft_to_m(600)),
    ]
    # Annulus: 600 ft DCxOH (0.0291 bbl/ft), 900 ft HWDPxOH (0.0459 bbl/ft), 4,850 ft DPxOH (0.0459 bbl/ft), 5,150 ft DPxCsg (0.0489 bbl/ft)
    oh_si = [
        ("DC x OH", bbl_per_ft_to_m3_per_m(0.0291), ft_to_m(600)),
        ("HWDP x OH", bbl_per_ft_to_m3_per_m(0.0459), ft_to_m(900)),
        ("DP x OH", bbl_per_ft_to_m3_per_m(0.0459), ft_to_m(4850)),
    ]
    ch_si = [
        ("DP x Csg", bbl_per_ft_to_m3_per_m(0.0489), ft_to_m(5150)),
    ]

    res = kill_sheet_si(
        title="Baseline Vertical Well - SI",
        bit_tvd_m=ft_to_m(11500),
        shoe_tvd_m=ft_to_m(5150),
        original_mud_weight_kg_m3=ppg_to_kg_m3(10.4),
        lot_pressure_kpa=psi_to_kpa(1350),
        test_mud_weight_kg_m3=ppg_to_kg_m3(9.6),
        sidpp_kpa=psi_to_kpa(650),
        sicp_kpa=psi_to_kpa(800),
        scr_pressure_kpa=psi_to_kpa(750),
        safety_margin_kpa=psi_to_kpa(50),
        pump_output_m3_per_stk=bbl_to_m3(0.117),
        drill_string_si=ds_si,
        open_hole_annulus_si=oh_si,
        cased_hole_annulus_si=ch_si,
        method=DRILLERS,
    )

    assert res["kill_mud_weight_kg_m3"] == round(ppg_to_kg_m3(11.5), 1)
    assert res["surface_to_bit_strokes"] == 1627
    assert res["drill_string_volume_m3"] > 0
    assert res["annulus_volume_m3"] > 0
    assert "icp_bar" in res
    assert "fcp_bar" in res
