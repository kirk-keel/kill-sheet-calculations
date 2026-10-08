# Kill Sheet Calculator

[![Tests](https://github.com/kirk-keel/kill-sheet-calculations/actions/workflows/tests.yml/badge.svg)](https://github.com/kirk-keel/kill-sheet-calculations/actions/workflows/tests.yml)

A free Python kill sheet calculator for oilfield hands, using oilfield units
(ppg, psi, ft, bbl, bbl/ft, spm, bbl/stk). Rounding follows the IADC WellSharp
rules, with an extra safety factor on kill mud weight.

**Version 0.1 is the simplest kill:** a vertical well, an untapered string
(one drill pipe size plus a BHA of HWDP and drill collars), a surface BOP stack,
and the Driller's method. Everything after that is built on top of it, one
complication at a time. **Version 0.2** adds tapered strings, **version 0.3** adds
deviated and horizontal wells, and **version 0.4** completes the Driller's method on a
surface stack for every well and string type. See the [roadmap](#roadmap).

## Why I built it

I built this calculator as a free resource for oilfield hands to plan and kill
all types of wells using every well control technique at their disposal.

## What it calculates

- **Kill mud weight** (KMW)
- **Initial and final circulating pressure** (ICP, FCP)
- **Maximum allowable mud weight** (MAMW) and **MAASP**, before and after the kill
- **Strokes:** surface to bit (with optional surface line volume), bit to shoe, bit to surface
- **Crossovers:** strokes to each pipe change in the drill string (where the kill mud
  is) and in the annulus, bit up. Works for untapered and tapered strings
- **Deviated and horizontal wells:** enter key points (KOP, end of build, heel) with
  MD and TVD. Every point on the kill sheet shows MD, TVD and strokes
- **Driller's method:** start-up, what to hold on which gauge and for how many strokes,
  shut-down, and the shut-in checks for both circulations
- **Wait and Weight:** weight up, start-up on the retaken SICP, an ICP check at kill
  rate (recalculated if the drill pipe reads more than 10 psi off), and a drill pipe
  step-down schedule from ICP to FCP that follows the depth of the kill mud, in 10 equal
  steps (default) or every 100 strokes, with every crossover shown

## How to run it

You need Python 3.10 or newer.

```bash
git clone https://github.com/kirk-keel/kill-sheet-calculations.git
cd kill-sheet-calculations
pip install -e ".[dev]"

python examples/example_well.py      # baseline: vertical, untapered string
python examples/wait_and_weight_well.py   # baseline well, Wait and Weight
python examples/tapered_well.py      # vertical, tapered string
python examples/deviated_well.py     # deviated (build and hold), untapered string
python examples/horizontal_well.py   # horizontal, untapered string
python examples/deviated_tapered_well.py     # deviated, tapered string
python examples/horizontal_tapered_well.py   # horizontal, tapered string
pytest                               # run the tests
```

To work your own well, copy one of the example files and change the numbers.
List the drill string top down and the annulus bit up, one line per pipe size
or hole/casing size, with lengths in MD. For a deviated or horizontal well also give
the bit and shoe MD and the key points as (name, MD, TVD). The calculator stops with
an error if the section lengths don't add up to the bit and shoe MD. Set `method` to `DRILLERS` or `WAIT_AND_WEIGHT`. For Wait and Weight, `step_method` is
`TEN_STEPS` (default) or `EVERY_100_STROKES`; enter the retaken SIDPP and SICP as
`sidpp_at_start_psi` and `sicp_at_start_psi`, and the drill pipe reading at kill rate as
`observed_icp_psi`.

## Conventions

### Formulas

| Calculation | Formula |
|---|---|
| Kill mud weight | `OMW + SIDPP / (0.052 x TVD)` (bit TVD) |
| ICP | `SIDPP + SCR pressure` |
| FCP | `SCR pressure x (KMW / OMW)` |
| Max allowable mud weight | `Test MW + LOT pressure / (0.052 x Shoe TVD)` |
| MAASP | `(MAMW - Current MW) x 0.052 x Shoe TVD` |
| Section volume | `Capacity x Length` |
| Strokes | `Volume / Pump output` |
| Strokes to a crossover | `Running total of rounded section volumes / Pump output` |
| Surface to bit volume | `Surface lines (optional) + Drill string` |
| W&W drill pipe pressure | `ICP - (ICP - FCP) x (MD of kill mud / Bit MD)`, drop rounded down |
| W&W MD of kill mud | Walk down the string: `full sections + section length x (volume left / section volume)` |
| W&W steps | 10 steps of `Surface-to-bit strokes / 10` (default), or every 100 strokes |
| W&W recalculation (reads high) | `Actual SCR = Observed ICP - Retaken SIDPP`, `FCP = Actual SCR x (KMW / OMW)`, never lower than calculated FCP |

### MD and TVD

| Uses **TVD** (pressure) | Uses **MD** (volume) |
|---|---|
| Kill mud weight (bit TVD) | Section lengths, volumes, strokes |
| MAMW and MAASP (shoe TVD) | Crossovers and key point strokes |

TVD at any MD is interpolated in a straight line between the key points either side:
`TVD = TVD1 + (MD - MD1) x (TVD2 - TVD1) / (MD2 - MD1)`. That is exact in vertical,
tangent and horizontal sections. In a build section it's an estimate, so add key
points through the build for a closer answer. Depths are rounded to a whole foot.

### Driller's method

A constant bottomhole pressure kill in two circulations. Both circulations use the
same **start-up** (bring the pump to kill rate holding casing pressure constant) and
**shut-down** (slow the pump to 0 holding casing pressure constant). The pressures
only tell the truth if that procedure is followed.

| Circulation | Mud | Hold | For |
|---|---|---|---|
| 1st | Original | Drill pipe at **ICP** | **Minimum** one bottoms up, until the gas is out |
| 2nd | Kill | Casing **constant** (at the SIDPP value) | Surface-to-bit strokes |
| 2nd | Kill | Drill pipe at **FCP** | Bit-to-surface strokes |

**Shut-in checks** (gauges within ±10 psi):

- After the 1st circulation, SIDPP and SICP must both read the **original SIDPP**.
  If SICP is higher, strung-out gas is still in the annulus, so continue circulating.
- After the 2nd circulation, SIDPP and SICP must both read **0 psi**. The well is dead.

### Wait and Weight

One circulation, with kill mud. Same start-up and shut-down as the Driller's method.

| Stage | Gauge | Hold | For |
|---|---|---|---|
| Weight up | Pits | Weight up the active system to KMW; **retake SIDPP (bump the float) and SICP** just before start-up (gas may have migrated) | — |
| Start-up | Casing | Constant at the **retaken SICP** while bringing the pump to kill rate | — |
| ICP check | Drill pipe | Must read ICP ±10 psi. More than 10 psi **high**: **recalculate** ICP, FCP and the schedule from the reading; FCP is **never lower** than calculated. More than 10 psi **low**: a complication, so the calculated values are kept | — |
| Hold | Drill pipe | **Step-down schedule** from ICP to FCP, following the depth of the kill mud | Surface-to-bit strokes |
| Hold | Drill pipe | **FCP** | Bit-to-surface strokes |
| Shut-down / check | Both | Both read **0 psi** (±10 psi): the well is dead | — |

**Why the schedule follows depth, not strokes.** The drill pipe pressure comes down
because the kill mud adds hydrostatic, and hydrostatic depends on how *deep* the kill
mud is. Strokes only match depth when the whole string has one ID. Drill pipe, HWDP,
collars and tapered strings all have different IDs, so each stroke moves the kill mud
a different distance and the schedule bends at every crossover. A straight line against
strokes takes pressure off before the kill mud is deep enough to replace it: on the
baseline well it is up to 38 psi short at the HWDP crossover, and 112 psi short at the
crossover of a 5" x 3-1/2" tapered string. (Fixed in v0.5.1.)

### Rounding: three rules

Based on the [IADC WellSharp Formula Sheet – Field Units, Rev 4 (2025)](https://iadc.org/wp-content/uploads/2025/04/WSP-FormulaSheet_FieldUnits_rev4.pdf).

1. **Kill weight fluid is always rounded UP to the next 0.1 ppg, even if exact.**
   11.0 ppg becomes 11.1 ppg. An exact kill weight only *balances* the formation;
   the extra 0.1 ppg is the minimum safety factor that *kills* the well.
2. **Anything that is a maximum is rounded DOWN.** MAMW to 0.1 ppg and MAASP to
   a whole psi, so a limit is never overstated. The Wait and Weight drop from ICP
   is also rounded down (IADC), so the drill pipe pressure is never below the exact
   pressure for the depth the kill mud has reached.
3. **Everything else uses academic rounding** (.5 goes up) to IADC's accuracy:
   pressures and strokes to a whole number, volumes to 0.1 bbl.

Rounded values are carried forward into later calculations, just like on paper.

### Safety checks

- **SIDPP must be greater than 0.** A zero drill pipe reading with a float in the
  string is not a true SIDPP. The float must be bumped to find it, so the calculator
  stops with that message instead of calculating from 0.

## Example output

Baseline well, from `python examples/example_well.py`:

```
KILL SHEET - vertical well, untapered string, surface BOP stack
====================================================
Kill mud weight                  11.5 ppg
Initial circulating pressure    1,400 psi
Final circulating pressure        829 psi
Max allowable mud weight         14.6 ppg
MAASP (original mud)            1,124 psi
MAASP (after kill)                830 psi

Surface to bit                  1,627 stks
Bit to shoe                     2,405 stks
Bit to surface                  4,557 stks

Drill string, top down (kill mud)            MD ft    TVD ft   Strokes
  bottom of 5" 19.5# DP                      10,000    10,000     1,521
  bottom of 5" HWDP                          10,900    10,900     1,588
  bit                                        11,500    11,500     1,627

Annulus, bit up                              MD ft    TVD ft   Strokes
  top of DC x 8-1/2" hole                    10,900    10,900       150
  top of HWDP x 8-1/2" hole                  10,000    10,000       503
  shoe / top of DP x 8-1/2" hole              5,150     5,150     2,405
  surface                                         0         0     4,557

Driller's method
  1st circulation (original mud)
    start-up   casing 800 psi
               bring pump to kill rate holding casing pressure constant
    hold       drill pipe 1,400 psi for 4,557 stks
               minimum - one bottoms up; continue until the gas is out
    shut-down  casing
               slow pump to 0 holding casing pressure constant
    check      drill pipe and casing 650 psi
               both must read the original SIDPP (+/-10 psi); if SICP is higher, gas is still in the annulus - continue circulating
  2nd circulation (kill mud)
    start-up   casing 650 psi
               bring pump to kill rate holding casing pressure constant
    hold       casing 650 psi for 1,627 stks
               kill mud surface to bit
    hold       drill pipe 829 psi for 4,557 stks
               kill mud bit to surface
    shut-down  casing
               slow pump to 0 holding casing pressure constant
    check      drill pipe and casing 0 psi
               both must read 0 psi (+/-10 psi) - the well is dead
```

Deviated well, from `python examples/deviated_well.py` (Driller's steps omitted here).
Pressures use TVD, strokes use MD, and TVD between key points is interpolated:

```
KILL SHEET - deviated well, untapered string, surface BOP stack
====================================================
Kill mud weight                  11.5 ppg
Initial circulating pressure    1,400 psi
Final circulating pressure        829 psi
Max allowable mud weight         14.6 ppg
MAASP (original mud)            1,124 psi
MAASP (after kill)                830 psi

Surface to bit                  1,812 stks
Bit to shoe                     2,791 stks
Bit to surface                  5,039 stks

Drill string, top down (kill mud)            MD ft    TVD ft   Strokes
  KOP                                         3,000     3,000       456
  end of build                                4,000     3,955       609
  bottom of 5" 19.5# DP                      11,212    10,201     1,706
  bottom of 5" HWDP                          12,112    10,980     1,773
  bit                                        12,712    11,500     1,812

Annulus, bit up                              MD ft    TVD ft   Strokes
  top of DC x 8-1/2" hole                    12,112    10,980       150
  top of HWDP x 8-1/2" hole                  11,212    10,201       503
  shoe / top of DP x 8-1/2" hole              5,380     5,150     2,791
  end of build                                4,000     3,955     3,368
  KOP                                         3,000     3,000     3,785
  surface                                         0         0     5,039
```

Baseline well, Wait and Weight, from `python examples/wait_and_weight_well.py`
(pressures and strokes are the same as above):

```
Wait and Weight
  kill circulation (kill mud)
    weight up  pits
               weight up the active system to 11.5 ppg; retake SIDPP (bump the float) and SICP just before pump start-up
    start-up   casing 800 psi
               bring pump to kill rate holding casing pressure constant at the retaken SICP
    hold       drill pipe 1,400 psi for 1,627 stks
               follow the step-down schedule from ICP 1,400 to FCP 829 psi - kill mud surface to bit
    hold       drill pipe 829 psi for 4,557 stks
               hold FCP - kill mud bit to surface
    shut-down  casing
               slow pump to 0 holding casing pressure constant
    check      drill pipe and casing 0 psi
               both must read 0 psi (+/-10 psi) - the well is dead

  Drill pipe step-down schedule (10 steps) - pressure follows the depth of the kill mud
    Strokes   Kill mud MD ft      psi
          0                0    1,400
        163            1,073    1,347
        326            2,140    1,294
        489            3,213    1,241
        652            4,287    1,188
        815            5,360    1,134
        978            6,427    1,081
      1,141            7,500    1,028
      1,304            8,573      975
      1,467            9,640      922
      1,521           10,000      904   <- crossover
      1,588           10,900      859   <- crossover
      1,627           11,500      829   <- bit
```

## Roadmap

Each step adds one complication, with hand-worked tests checked before any code is
committed. Every method is covered for every well and string type, first on a
surface BOP stack, then the web page, then the subsea stack.

**Well and string types, for each method:** vertical untapered, vertical tapered,
deviated/horizontal untapered, deviated/horizontal tapered.

### Surface BOP stack

**Driller's method**
- [x] Vertical, untapered string (**v0.1**, start-up/shut-down and shut-in checks **v0.1.1**)
- [x] Vertical, tapered string (**v0.2**)
- [x] Deviated and horizontal, untapered string (**v0.3**)
- [x] Deviated and horizontal, tapered string (**v0.4**)

**Wait and Weight**
- [x] Vertical, untapered string (**v0.5**; schedule by depth of kill mud **v0.5.1**)
- [ ] Vertical, tapered string
- [ ] Deviated and horizontal, untapered string
- [ ] Deviated and horizontal, tapered string

**Volumetric method and lubricate and bleed**
- [ ] Vertical, untapered string
- [ ] Vertical, tapered string
- [ ] Deviated and horizontal, untapered string
- [ ] Deviated and horizontal, tapered string

**Bullheading**
- [ ] Vertical, untapered string
- [ ] Vertical, tapered string
- [ ] Deviated and horizontal, untapered string
- [ ] Deviated and horizontal, tapered string

**Reverse circulation**
- [ ] Vertical, untapered string
- [ ] Vertical, tapered string
- [ ] Deviated and horizontal, untapered string
- [ ] Deviated and horizontal, tapered string

### Web page (after the surface stack is complete)

- [ ] Web page, with a kill plot of forecast drill pipe and annulus pressure beside
  the table, showing the inflection at each pipe change

### Subsea BOP stack

All of the above again, adding choke line friction, riser margin and choke line
volumes and strokes:

- [ ] Driller's method: all four well and string types
- [ ] Wait and Weight: all four well and string types
- [ ] Volumetric method and lubricate and bleed: all four well and string types
- [ ] Bullheading: all four well and string types
- [ ] Reverse circulation: all four well and string types

## Project layout

```
src/killsheet/
  rounding.py    the three rounding rules (the only place rounding is done)
  formulas.py    KMW, ICP, FCP, MAMW, MAASP
  depths.py      MD and TVD: TVD at any MD from the key points
  strokes.py     volumes, strokes, crossovers and section length checks
  kill_steps.py  kill steps, stages and shut-in gauge checks shared by every method
  drillers.py    Driller's method kill steps
  wait_and_weight.py  Wait and Weight kill steps, ICP check and recalculation
  schedule.py    Wait and Weight drill pipe step-down schedule, by depth of kill mud
tests/           one test file per module, plus a full kill sheet for each example
                 well; all hand-worked examples
examples/
  example_well.py        baseline: vertical, untapered string
  wait_and_weight_well.py  baseline well, Wait and Weight
  tapered_well.py        vertical, tapered string
  deviated_well.py       deviated, untapered string
  horizontal_well.py     horizontal, untapered string
  deviated_tapered_well.py     deviated, tapered string
  horizontal_tapered_well.py   horizontal, tapered string
  kill_sheet_printer.py  prints a kill sheet (shared by both examples)
.github/workflows/tests.yml   runs the tests on every push
```

## Testing

The tests and every example kill sheet run automatically on GitHub on every push,
on Python 3.10–3.13. The badge at the top of this page shows whether they're passing.

## Disclaimer

This is a free planning and training aid. It is not a replacement for a
site-specific kill sheet, a well control program, or the judgment of the people
on location. See [LICENSE](LICENSE): the software is provided "as is", without
warranty of any kind.

## License

[MIT](LICENSE) © 2026 Kirk Keel
