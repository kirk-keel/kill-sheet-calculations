"""Well control step-by-step simulator demonstration example.

Demonstrates:
  - Wait & Weight well kill procedure execution
  - Real-time tracking of kill mud front progression
  - Drill pipe pressure step-down schedule compliance
  - Dynamic casing shoe pressure monitoring against MAASP
  - Bottomhole pressure balance vs formation pore pressure

Run with:  python examples/example_simulator.py
"""

from killsheet.simulator import WellKillSimulator


def run_example():
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

    print("STARTING RIG-FLOOR WELL KILL SIMULATION RUN")
    # Initial state
    res = sim.step(0)
    print(sim.render_dashboard(res))

    # Advance to half drillstring
    res = sim.step(600)
    print(sim.render_dashboard(res))

    # Kill mud reaches bit
    res = sim.step(600)
    print(sim.render_dashboard(res))

    # Kill mud reaches casing shoe
    res = sim.step(2000)
    print(sim.render_dashboard(res))

    # Well completely circulated to kill mud
    res = sim.step(1500)
    print(sim.render_dashboard(res))


if __name__ == "__main__":
    run_example()
