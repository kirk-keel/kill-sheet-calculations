"""Subsea well control example with choke line friction and riser margin.

Demonstrates:
  - Choke line capacity, volume, and strokes
  - Dynamic MAASP reduction from choke line friction (CLF)
  - Choke pressure management during pump ramp-up (holding SICP - CLF)
  - Riser margin mud weight and post-disconnect bottomhole overbalance

Run with:  python examples/subsea_well.py
"""

from killsheet.subsea import subsea_kill_summary

SUBSEA_WELL = dict(
    original_mud_weight_ppg=12.0,
    tvd_ft=10_000,
    shoe_tvd_ft=6_000,
    lot_emw_ppg=15.0,
    sidpp_psi=500,
    sicp_psi=700,
    scr_pressure_psi=750,
    pump_output_bbl_per_stk=0.102,
    choke_line_id_in=3.0,
    choke_line_length_ft=1_650,
    clf_psi=250,
    water_depth_ft=1_500,
    air_gap_ft=75,
)


def print_subsea_well():
    summary = subsea_kill_summary(**SUBSEA_WELL)
    print("SUBSEA KILL SHEET - Deepwater Vertical Well, Subsea BOP Stack")
    print("=" * 64)
    print(f"Kill mud weight              {summary['kill_mud_weight_ppg']:>8.1f} ppg")
    print(f"Choke line volume            {summary['choke_line_volume_bbl']:>8.1f} bbl")
    print(f"Choke line strokes           {summary['choke_line_strokes']:>8,} stks")
    print(f"Static MAASP (shut in)       {summary['static_maasp_psi']:>8,} psi")
    print(f"Choke line friction (CLF)    {summary['choke_line_friction_psi']:>8,} psi")
    print(f"Dynamic MAASP (circulating)  {summary['dynamic_maasp_psi']:>8,} psi")
    print(f"Choke pressure start-up      {summary['choke_pressure_at_kill_rate_psi']:>8,} psi (hold SICP - CLF)")
    print(f"Riser margin mud weight      {summary['riser_margin_mud_weight_ppg']:>8.1f} ppg (+{summary['riser_margin_delta_ppg']:.1f} ppg)")
    print(f"Post-disconnect BHP          {summary['post_disconnect_bhp_psi']:>8,} psi")
    print(f"Formation pressure           {summary['formation_pressure_psi']:>8,} psi")
    overbal = summary["disconnect_overbalance_psi"]
    status = "OVERBALANCED" if overbal >= 0 else "UNDERBALANCED (well can flow)"
    print(f"Disconnect condition         {overbal:>8,} psi ({status})")


if __name__ == "__main__":
    print_subsea_well()
