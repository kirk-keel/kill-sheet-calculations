"""Command-line interface (CLI) for the Kill Sheet Calculator and Well Engineering Suite."""

import argparse
import sys
from killsheet import __version__
from killsheet.kick_tolerance import kick_tolerance_summary
from killsheet.simulator import WellKillSimulator
from killsheet.subsea import subsea_kill_summary
from killsheet.tripping import trip_slug_summary


def cmd_simulate(args):
    """Run interactive or automated well kill simulation."""
    sim = WellKillSimulator(
        method=args.method,
        bit_tvd_ft=args.tvd,
        shoe_tvd_ft=args.shoe_tvd,
        original_mud_weight_ppg=args.omw,
        lot_mud_weight_ppg=args.lot,
        sidpp_psi=args.sidpp,
        sicp_psi=args.sicp,
        scr_pressure_psi=args.scr,
        surface_to_bit_strokes=args.s2b,
        bit_to_shoe_strokes=args.b2shoe,
        bit_to_surface_strokes=args.b2s,
    )

    if args.interactive:
        print("Starting interactive Well Control Simulator. Type 'quit' or 'q' to exit.")
        res = sim.step(0)
        print(sim.render_dashboard(res))
        while sim.cumulative_strokes < sim.b2s_stk + sim.s2b_stk:
            try:
                user_in = input("\nEnter strokes to pump [e.g. 100] (or 'q' to quit): ").strip()
                if user_in.lower() in ("q", "quit", "exit"):
                    break
                delta = int(user_in) if user_in else 100
                res = sim.step(delta)
                print(sim.render_dashboard(res))
            except (ValueError, EOFError, KeyboardInterrupt):
                break
        print("Simulation session terminated.")
    else:
        # Automated demonstration stepping
        print(f"AUTOMATED WELL KILL SIMULATION ({args.method.upper()})")
        res = sim.step(0)
        print(sim.render_dashboard(res))
        for step_strokes in (int(args.s2b / 2), int(args.s2b / 2), int(args.b2shoe), int(args.b2s - args.b2shoe)):
            if step_strokes > 0:
                res = sim.step(step_strokes)
                print(sim.render_dashboard(res))


def cmd_subsea(args):
    """Run subsea well control calculations."""
    res = subsea_kill_summary(
        original_mud_weight_ppg=args.omw,
        tvd_ft=args.tvd,
        shoe_tvd_ft=args.shoe_tvd,
        lot_emw_ppg=args.lot,
        sidpp_psi=args.sidpp,
        sicp_psi=args.sicp,
        scr_pressure_psi=args.scr,
        pump_output_bbl_per_stk=args.pump_output,
        choke_line_id_in=args.cl_id,
        choke_line_length_ft=args.cl_len,
        clf_psi=args.clf,
        water_depth_ft=args.water_depth,
        air_gap_ft=args.air_gap,
    )
    print("SUBSEA WELL CONTROL SUMMARY")
    print("=" * 60)
    print(f"Kill Mud Weight:             {res['kill_mud_weight_ppg']:.1f} ppg")
    print(f"Static MAASP:                {res['static_maasp_psi']:,} psi")
    print(f"Dynamic MAASP:               {res['dynamic_maasp_psi']:,} psi (CLF: {res['choke_line_friction_psi']:,} psi)")
    print(f"Choke Pressure at Ramp:      {res['choke_pressure_at_kill_rate_psi']:,} psi (SICP - CLF)")
    print(f"Choke Line Volume:           {res['choke_line_volume_bbl']:.1f} bbl ({res['choke_line_strokes']:,} strokes)")
    print(f"Riser Margin MW:             {res['riser_margin_mud_weight_ppg']:.1f} ppg (+{res['riser_margin_delta_ppg']:.1f} ppg)")
    print(f"Post-Disconnect BHP:         {res['post_disconnect_bhp_psi']:,} psi")
    print(f"Disconnect Status:           {res['disconnect_overbalance_psi']:,} psi vs formation")


def cmd_tripping(args):
    """Run tripping and slug calculations."""
    res = trip_slug_summary(
        desired_dry_pipe_ft=args.dry_pipe,
        dp_capacity_bbl_per_ft=args.dp_cap,
        original_mud_weight_ppg=args.omw,
        slug_weight_ppg=args.slug_mw,
        pump_output_bbl_per_stk=args.pump_output,
    )
    print("TRIPPING & SLUG OPERATIONS")
    print("=" * 60)
    print(f"Desired Dry Pipe:            {res['desired_dry_pipe_ft']:,} ft")
    print(f"Slug Volume Required:        {res['slug_volume_bbl']:.1f} bbl")
    print(f"Slug Length in Pipe:         {res['slug_length_ft']:,} ft")
    print(f"Pit Gain from U-Tubing:      {res['pit_gain_bbl']:.1f} bbl")
    if res["pump_strokes"]:
        print(f"Pump Strokes to Displace:    {res['pump_strokes']:,} strokes")


def cmd_kick_tolerance(args):
    """Run kick tolerance calculations."""
    res = kick_tolerance_summary(
        mud_weight_ppg=args.mw,
        tvd_ft=args.tvd,
        shoe_tvd_ft=args.shoe_tvd,
        lot_emw_ppg=args.lot,
        sidpp_psi=args.sidpp,
        annular_capacity_bbl_per_ft=args.ann_cap,
    )
    print("KICK TOLERANCE & CASING SEAT DRILLING WINDOW")
    print("=" * 60)
    print(f"Kick Intensity:              {res['kick_intensity_ppg']:.1f} ppg")
    print(f"Equivalent Pore Pressure:    {res['equivalent_pore_pressure_ppg']:.1f} ppg")
    print(f"Formation Pressure:          {res['formation_pressure_psi']:,} psi")
    print(f"Shoe Fracture Pressure:      {res['shoe_fracture_pressure_psi']:,} psi")
    print(f"Shoe MAASP:                  {res['shoe_maasp_psi']:,} psi")
    print(f"Max Gas Height at Shoe:      {res['max_gas_height_at_shoe_ft']:,} ft")
    print(f"Kick Tolerance (Bottomhole): {res['kick_tolerance_bottomhole_bbl']:.1f} bbl")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="killsheet",
        description="Kill Sheet Calculator & Petroleum Engineering Suite CLI",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Subsea command
    subsea_p = subparsers.add_parser("subsea", help="Calculate subsea well control, CLF, and riser margin")
    subsea_p.add_argument("--omw", type=float, default=12.0, help="Original mud weight (ppg)")
    subsea_p.add_argument("--tvd", type=float, default=10000, help="Total vertical depth (ft)")
    subsea_p.add_argument("--shoe-tvd", type=float, default=6000, help="Casing shoe TVD (ft)")
    subsea_p.add_argument("--lot", type=float, default=15.0, help="Shoe LOT/FIT (ppg EMW)")
    subsea_p.add_argument("--sidpp", type=float, default=500, help="SIDPP (psi)")
    subsea_p.add_argument("--sicp", type=float, default=700, help="SICP (psi)")
    subsea_p.add_argument("--scr", type=float, default=750, help="SCR pressure (psi)")
    subsea_p.add_argument("--pump-output", type=float, default=0.102, help="Pump output (bbl/stk)")
    subsea_p.add_argument("--cl-id", type=float, default=3.0, help="Choke line ID (in)")
    subsea_p.add_argument("--cl-len", type=float, default=1650, help="Choke line length (ft)")
    subsea_p.add_argument("--clf", type=float, default=250, help="Choke line friction (psi)")
    subsea_p.add_argument("--water-depth", type=float, default=1500, help="Water depth (ft)")
    subsea_p.add_argument("--air-gap", type=float, default=75, help="Air gap (ft)")
    subsea_p.set_defaults(func=cmd_subsea)

    # Tripping command
    trip_p = subparsers.add_parser("tripping", help="Calculate heavy slug volume, dry pipe height, and pit gain")
    trip_p.add_argument("--dry-pipe", type=float, default=250, help="Desired dry pipe height (ft)")
    trip_p.add_argument("--dp-cap", type=float, default=0.0178, help="Drill pipe capacity (bbl/ft)")
    trip_p.add_argument("--omw", type=float, default=10.0, help="Original mud weight (ppg)")
    trip_p.add_argument("--slug-mw", type=float, default=12.0, help="Slug mud weight (ppg)")
    trip_p.add_argument("--pump-output", type=float, default=0.102, help="Pump output (bbl/stk)")
    trip_p.set_defaults(func=cmd_tripping)

    # Kick tolerance command
    kt_p = subparsers.add_parser("kick-tolerance", help="Calculate kick tolerance and maximum gas influx volume")
    kt_p.add_argument("--mw", type=float, default=12.5, help="Mud weight (ppg)")
    kt_p.add_argument("--tvd", type=float, default=10000, help="Well TVD (ft)")
    kt_p.add_argument("--shoe-tvd", type=float, default=5000, help="Casing shoe TVD (ft)")
    kt_p.add_argument("--lot", type=float, default=14.5, help="Shoe fracture gradient (ppg EMW)")
    kt_p.add_argument("--sidpp", type=float, default=350, help="Anticipated SIDPP (psi)")
    kt_p.add_argument("--ann-cap", type=float, default=0.0459, help="Annular capacity at shoe (bbl/ft)")
    kt_p.set_defaults(func=cmd_kick_tolerance)

    # Simulator command
    sim_p = subparsers.add_parser("simulate", help="Interactive or automated well kill step-by-step simulator")
    sim_p.add_argument("--method", default="Wait and Weight", choices=["Wait and Weight", "Drillers"], help="Well kill method")
    sim_p.add_argument("--tvd", type=float, default=10000, help="Total vertical depth (ft)")
    sim_p.add_argument("--shoe-tvd", type=float, default=7000, help="Casing shoe TVD (ft)")
    sim_p.add_argument("--omw", type=float, default=10.0, help="Original mud weight (ppg)")
    sim_p.add_argument("--lot", type=float, default=14.0, help="Shoe LOT (ppg EMW)")
    sim_p.add_argument("--sidpp", type=float, default=500, help="SIDPP (psi)")
    sim_p.add_argument("--sicp", type=float, default=700, help="SICP (psi)")
    sim_p.add_argument("--scr", type=float, default=350, help="SCR pressure (psi)")
    sim_p.add_argument("--s2b", type=int, default=1200, help="Surface-to-bit strokes")
    sim_p.add_argument("--b2shoe", type=int, default=2000, help="Bit-to-shoe strokes")
    sim_p.add_argument("--b2s", type=int, default=3500, help="Bit-to-surface strokes")
    sim_p.add_argument("--interactive", action="store_true", help="Launch interactive step console")
    sim_p.set_defaults(func=cmd_simulate)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
