"""Interactive Well Control Step-by-Step Simulator.

Provides a dynamic rig-floor simulation engine for circulating out kicks
using the Wait & Weight or Driller's Method under standard IADC WellSharp rules.

Tracks:
  - Cumulative strokes pumped
  - Kill mud front progression (Drillstring -> Bit -> Shoe -> Surface)
  - Target Drill Pipe Pressure (Step-down schedule)
  - Casing Choke Pressure (SICP)
  - Dynamic Shoe Pressure and MAASP safety margins
  - Bottomhole Pressure (BHP) balance vs formation pore pressure
"""

import math
from typing import Any, Dict, List, Optional

from killsheet.formulas import (
    PSI_PER_FT_PER_PPG,
    final_circulating_pressure,
    initial_circulating_pressure,
    kill_mud_weight,
    maasp,
)
from killsheet.rounding import (
    round_down_to_whole_number,
    round_to_tenth,
    round_to_whole_number,
)


class WellKillSimulator:
    """Rig-floor step-by-step well kill execution simulator."""

    def __init__(
        self,
        method: str = "Wait and Weight",
        bit_tvd_ft: float = 10_000.0,
        shoe_tvd_ft: float = 7_000.0,
        original_mud_weight_ppg: float = 10.0,
        lot_mud_weight_ppg: float = 14.0,
        sidpp_psi: float = 500.0,
        sicp_psi: float = 700.0,
        scr_pressure_psi: float = 350.0,
        surface_to_bit_strokes: int = 1200,
        bit_to_shoe_strokes: int = 2000,
        bit_to_surface_strokes: int = 3500,
        pump_output_bbl_per_stk: float = 0.10,
    ):
        self.method = method
        self.bit_tvd_ft = bit_tvd_ft
        self.shoe_tvd_ft = shoe_tvd_ft
        self.omw_ppg = original_mud_weight_ppg
        self.lot_ppg = lot_mud_weight_ppg
        self.sidpp_psi = sidpp_psi
        self.sicp_psi = sicp_psi
        self.scr_psi = scr_pressure_psi
        self.s2b_stk = surface_to_bit_strokes
        self.b2shoe_stk = bit_to_shoe_strokes
        self.b2s_stk = bit_to_surface_strokes
        self.pump_output = pump_output_bbl_per_stk

        # Calculate initial well control values
        self.kmw_ppg = kill_mud_weight(self.sidpp_psi, self.bit_tvd_ft, self.omw_ppg)
        self.icp_psi = initial_circulating_pressure(self.sidpp_psi, self.scr_psi)
        self.fcp_psi = final_circulating_pressure(self.scr_psi, self.kmw_ppg, self.omw_ppg)
        self.maasp_omw_psi = maasp(self.lot_ppg, self.omw_ppg, self.shoe_tvd_ft)
        self.maasp_kmw_psi = maasp(self.lot_ppg, self.kmw_ppg, self.shoe_tvd_ft)
        self.formation_pressure_psi = round_to_whole_number(
            PSI_PER_FT_PER_PPG * self.omw_ppg * self.bit_tvd_ft + self.sidpp_psi
        )

        # Simulation state
        self.cumulative_strokes = 0
        self.choke_psi = float(self.sicp_psi)
        self.history: List[Dict[str, Any]] = []

    def target_drill_pipe_pressure(self, strokes: int) -> int:
        """Calculates expected target drillpipe pressure at given pumped strokes."""
        if strokes <= 0:
            return int(self.icp_psi)
        if strokes < self.s2b_stk:
            # Step down linearly from ICP to FCP
            progress = strokes / self.s2b_stk
            p = self.icp_psi - progress * (self.icp_psi - self.fcp_psi)
            return round_down_to_whole_number(p)
        return int(self.fcp_psi)

    def step(self, delta_strokes: int, choke_psi: Optional[float] = None) -> Dict[str, Any]:
        """Advances the simulation by delta_strokes, optionally adjusting choke pressure."""
        if delta_strokes < 0:
            raise ValueError("Strokes pumped cannot be negative.")

        self.cumulative_strokes += delta_strokes
        if choke_psi is not None:
            self.choke_psi = max(0.0, float(choke_psi))

        target_dpp = self.target_drill_pipe_pressure(self.cumulative_strokes)
        total_annular_strokes = self.b2s_stk

        # Determine mud front positions
        s2b = self.s2b_stk
        cur = self.cumulative_strokes

        # Drill string state
        if cur <= 0:
            ds_stage = "Static Shut-in"
        elif cur < s2b:
            pct = (cur / s2b) * 100.0
            ds_stage = f"Kill Mud in Drill String ({pct:.0f}%)"
        else:
            ds_stage = "Kill Mud at Bit / Completed"

        # Annulus state
        ann_strokes = max(0, cur - s2b)
        if ann_strokes == 0:
            ann_stage = "Original Mud / Gas Influx at Bottom"
        elif ann_strokes < self.b2shoe_stk:
            ann_stage = f"Kill Mud Displacing Annulus Below Shoe ({ann_strokes}/{self.b2shoe_stk} stk)"
        elif ann_strokes < total_annular_strokes:
            ann_stage = f"Kill Mud Displacing Casing Annulus Above Shoe ({ann_strokes}/{total_annular_strokes} stk)"
        else:
            ann_stage = "Well Completely Killed to Surface"

        # Calculate active shoe pressure
        # Casing shoe pressure = Surface Choke Pressure + Hydrostatic above shoe
        # As kill mud passes shoe, hydrostatic increases
        if ann_strokes < self.b2shoe_stk:
            active_shoe_mud = self.omw_ppg
            active_maasp = self.maasp_omw_psi
        else:
            active_shoe_mud = self.kmw_ppg
            active_maasp = self.maasp_kmw_psi

        shoe_hydrostatic = PSI_PER_FT_PER_PPG * active_shoe_mud * self.shoe_tvd_ft
        shoe_pressure = round_to_whole_number(self.choke_psi + shoe_hydrostatic)
        shoe_margin = round_to_whole_number(active_maasp - self.choke_psi)

        # Dynamic BHP estimation
        bhp = round_to_whole_number(self.formation_pressure_psi + (self.choke_psi - self.sicp_psi))
        is_underbalanced = bhp < self.formation_pressure_psi
        is_shoe_fractured = self.choke_psi > active_maasp

        record = {
            "strokes": self.cumulative_strokes,
            "bbl_pumped": round_to_tenth(self.cumulative_strokes * self.pump_output),
            "drill_pipe_stage": ds_stage,
            "annulus_stage": ann_stage,
            "target_dpp_psi": target_dpp,
            "choke_psi": round_to_whole_number(self.choke_psi),
            "shoe_pressure_psi": shoe_pressure,
            "active_maasp_psi": active_maasp,
            "shoe_margin_psi": shoe_margin,
            "bhp_psi": bhp,
            "is_underbalanced": is_underbalanced,
            "is_shoe_fractured": is_shoe_fractured,
        }
        self.history.append(record)
        return record

    def render_dashboard(self, latest: Dict[str, Any]) -> str:
        """Renders an ASCII rig floor display panel."""
        lines = [
            "=" * 70,
            f" WELL KILL RIG CONSOLE  |  Method: {self.method.upper()}",
            "=" * 70,
            f" Pumped Strokes:     {latest['strokes']:,} stk  ({latest['bbl_pumped']:.1f} bbl)",
            f" Drill String:       {latest['drill_pipe_stage']}",
            f" Annulus:            {latest['annulus_stage']}",
            "-" * 70,
            f" Drill Pipe Target:  {latest['target_dpp_psi']:,} psi",
            f" Choke Pressure:     {latest['choke_psi']:,} psi  (MAASP: {latest['active_maasp_psi']:,} psi, Margin: {latest['shoe_margin_psi']:,} psi)",
            f" Casing Shoe Press:  {latest['shoe_pressure_psi']:,} psi",
            f" Bottom Hole Press:  {latest['bhp_psi']:,} psi  (Formation: {self.formation_pressure_psi:,} psi)",
            "-" * 70,
        ]

        alerts = []
        if latest["is_shoe_fractured"]:
            alerts.append("[CRITICAL ALARM] SHOE FRACTURED! Choke pressure exceeds MAASP!")
        if latest["is_underbalanced"]:
            alerts.append("[WARNING] UNDERBALANCED! BHP is below formation pore pressure!")
        if not alerts:
            alerts.append("[NORMAL] Well control parameters nominal. BHP balanced.")

        lines.extend(alerts)
        lines.append("=" * 70)
        return "\n".join(lines)
