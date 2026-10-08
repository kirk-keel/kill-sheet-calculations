"""Print a complete kill sheet for the baseline example well.

Baseline = the simplest kill: vertical well, untapered string (one drill pipe
size + BHA), surface BOP stack, Driller's method.

Run it with:  python examples/example_well.py
"""

from killsheet.drillers import drillers_method
from killsheet.formulas import (
    final_circulating_pressure,
    initial_circulating_pressure,
    kill_mud_weight,
    maasp,
    max_allowable_mud_weight,
)
from killsheet.schedule import EVERY_100_STROKES, pressure_schedule
from killsheet.strokes import (
    bit_to_shoe_strokes,
    bit_to_surface_strokes,
    surface_to_bit_strokes,
)

# --- Kill method ---------------------------------------------------------------
DRILLERS = "Driller's method"
WAIT_AND_WEIGHT = "Wait and Weight"
METHOD = DRILLERS                # or WAIT_AND_WEIGHT
STEP_METHOD = EVERY_100_STROKES  # Wait and Weight only: or TEN_STEPS

# --- Well data -----------------------------------------------------------------
TVD_FT = 11_500
SHOE_TVD_FT = 5_150
ORIGINAL_MUD_WEIGHT_PPG = 10.4

# --- Leak-off test -------------------------------------------------------------
LOT_PRESSURE_PSI = 1_350
TEST_MUD_WEIGHT_PPG = 9.6

# --- Kick data -----------------------------------------------------------------
SIDPP_PSI = 650
SICP_PSI = 800
SCR_PRESSURE_PSI = 750          # at 30 spm

# --- Pump and volumes (sections are (capacity bbl/ft, length ft)) ---------------
PUMP_OUTPUT_BBL_PER_STK = 0.117
SURFACE_LINE_VOLUME_BBL = 0     # leave as 0 if unknown
DRILL_STRING = [
    (0.0178, 10_000),           # 5" 19.5# drill pipe
    (0.0087, 900),              # 5" HWDP
    (0.0077, 600),              # 6-1/2" drill collars
]
OPEN_HOLE_ANNULUS = [
    (0.0291, 600),              # collars x 8-1/2" open hole
    (0.0459, 900),              # HWDP x 8-1/2" open hole
    (0.0459, 4_850),            # drill pipe x 8-1/2" open hole
]
CASED_HOLE_ANNULUS = [
    (0.0489, 5_150),            # drill pipe x 9-5/8" 47# casing
]


def main():
    kmw = kill_mud_weight(SIDPP_PSI, TVD_FT, ORIGINAL_MUD_WEIGHT_PPG)
    icp = initial_circulating_pressure(SIDPP_PSI, SCR_PRESSURE_PSI)
    fcp = final_circulating_pressure(SCR_PRESSURE_PSI, kmw, ORIGINAL_MUD_WEIGHT_PPG)
    mamw = max_allowable_mud_weight(LOT_PRESSURE_PSI, SHOE_TVD_FT, TEST_MUD_WEIGHT_PPG)

    stb = surface_to_bit_strokes(DRILL_STRING, PUMP_OUTPUT_BBL_PER_STK, SURFACE_LINE_VOLUME_BBL)
    bts = bit_to_shoe_strokes(OPEN_HOLE_ANNULUS, PUMP_OUTPUT_BBL_PER_STK)
    btsurf = bit_to_surface_strokes(OPEN_HOLE_ANNULUS + CASED_HOLE_ANNULUS, PUMP_OUTPUT_BBL_PER_STK)

    print("KILL SHEET - vertical well, surface BOP stack")
    print("=" * 46)
    print(f"Kill mud weight              {kmw:>8.1f} ppg")
    print(f"Initial circulating pressure {icp:>8,} psi")
    print(f"Final circulating pressure   {fcp:>8,} psi")
    print(f"Max allowable mud weight     {mamw:>8.1f} ppg")
    print(f"MAASP (original mud)         {maasp(mamw, ORIGINAL_MUD_WEIGHT_PPG, SHOE_TVD_FT):>8,} psi")
    print(f"MAASP (after kill)           {maasp(mamw, kmw, SHOE_TVD_FT):>8,} psi")
    print()
    print(f"Surface to bit               {stb:>8,} stks")
    print(f"Bit to shoe                  {bts:>8,} stks")
    print(f"Bit to surface               {btsurf:>8,} stks")
    print()

    if METHOD == DRILLERS:
        print(DRILLERS)
        circulation = None
        for step in drillers_method(SIDPP_PSI, SICP_PSI, icp, fcp, stb, btsurf):
            if step.circulation != circulation:
                circulation = step.circulation
                print(f"  {circulation}")
            line = f"    {step.stage:<11}{step.gauge}"
            if step.hold_psi is not None:
                line += f" {step.hold_psi:,} psi"
            if step.strokes is not None:
                line += f" for {step.strokes:,} stks"
            print(line)
            print(f"{'':15}{step.note}")
    elif METHOD == WAIT_AND_WEIGHT:
        print(f"{WAIT_AND_WEIGHT} - drill pipe pressure schedule ({STEP_METHOD})")
        print("  Strokes      psi")
        for strokes, pressure in pressure_schedule(icp, fcp, stb, STEP_METHOD):
            print(f"  {strokes:>7,}  {pressure:>7,}")
        print(f"  then hold FCP {fcp:,} psi for {btsurf:,} stks, bit to surface")
    else:
        raise ValueError(f"METHOD must be {DRILLERS!r} or {WAIT_AND_WEIGHT!r}")


if __name__ == "__main__":
    main()
