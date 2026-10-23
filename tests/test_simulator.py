"""Unit tests for the Well Kill Simulator."""

import pytest

from killsheet.simulator import WellKillSimulator


def test_simulator_initialization():
    sim = WellKillSimulator(
        method="Wait and Weight",
        bit_tvd_ft=10_000.0,
        shoe_tvd_ft=7_000.0,
        original_mud_weight_ppg=10.0,
        lot_mud_weight_ppg=14.0,
        sidpp_psi=500.0,
        sicp_psi=700.0,
        scr_pressure_psi=350.0,
        surface_to_bit_strokes=1200,
        bit_to_shoe_strokes=2000,
        bit_to_surface_strokes=3500,
    )
    assert sim.kmw_ppg == 11.0
    assert sim.icp_psi == 850
    assert sim.fcp_psi == 385
    assert sim.formation_pressure_psi == 5700
    assert sim.maasp_omw_psi == 1456
    assert sim.maasp_kmw_psi == 1092


def test_simulator_step_down():
    sim = WellKillSimulator(
        method="Wait and Weight",
        bit_tvd_ft=10_000.0,
        shoe_tvd_ft=7_000.0,
        original_mud_weight_ppg=10.0,
        lot_mud_weight_ppg=14.0,
        sidpp_psi=500.0,
        sicp_psi=700.0,
        scr_pressure_psi=350.0,
        surface_to_bit_strokes=1000,
        bit_to_shoe_strokes=1500,
        bit_to_surface_strokes=3000,
    )
    # At 0 strokes: DPP should be ICP (850)
    assert sim.target_drill_pipe_pressure(0) == 850
    # At 500 strokes (halfway): DPP should be (850 + 385)/2 = 617
    assert sim.target_drill_pipe_pressure(500) == 617
    # At 1000 strokes (at bit): DPP should be FCP (385)
    assert sim.target_drill_pipe_pressure(1000) == 385
    # Beyond 1000 strokes: DPP remains FCP
    assert sim.target_drill_pipe_pressure(1500) == 385


def test_simulator_progression_and_dashboard():
    sim = WellKillSimulator(
        surface_to_bit_strokes=1000,
        bit_to_shoe_strokes=1500,
        bit_to_surface_strokes=3000,
    )
    step1 = sim.step(500)
    assert step1["strokes"] == 500
    assert "Kill Mud in Drill String" in step1["drill_pipe_stage"]
    assert step1["is_underbalanced"] is False
    assert step1["is_shoe_fractured"] is False

    dashboard = sim.render_dashboard(step1)
    assert "WELL KILL RIG CONSOLE" in dashboard
    assert "[NORMAL]" in dashboard


def test_simulator_alarms():
    sim = WellKillSimulator(lot_mud_weight_ppg=12.0)
    # If choke psi is set above MAASP
    res = sim.step(100, choke_psi=2000.0)
    assert res["is_shoe_fractured"] is True
    dash = sim.render_dashboard(res)
    assert "[CRITICAL ALARM] SHOE FRACTURED!" in dash

    # If choke is bled down to zero -> underbalanced
    res2 = sim.step(100, choke_psi=0.0)
    assert res2["is_underbalanced"] is True
    dash2 = sim.render_dashboard(res2)
    assert "[WARNING] UNDERBALANCED!" in dash2
