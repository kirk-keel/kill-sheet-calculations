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
surface stack for every well and string type. **Version 0.5** adds Wait and Weight,
**version 0.6** extends it to tapered strings, **version 0.7** to deviated and
horizontal wells, and **version 0.8** completes Wait and Weight on a surface stack for
every well and string type. **Version 0.9** adds the volumetric method and lubricate and
bleed, **version 0.10** extends them to tapered strings, and **version 0.11** to
deviated and horizontal wells. See the [roadmap](#roadmap).

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
- **Volumetric method:** bleed volume per cycle (IADC #35) for the smallest, average and
  longest annulus, and a cycle table driven by the 15-minute SICP readings until the gas
  is at surface. Works with pipe on bottom, pipe above the influx, or pipe out of the hole
- **Lubricate and bleed:** kill weight mud, annulus at surface; turns the bbl the crew
  pumps into the psi to bleed, until hydrostatic control is regained

## How to run it

You need Python 3.10 or newer.

```bash
git clone https://github.com/kirk-keel/kill-sheet-calculations.git
cd kill-sheet-calculations
pip install -e ".[dev]"

python examples/example_well.py      # baseline: vertical, untapered string
python examples/wait_and_weight_well.py   # baseline well, Wait and Weight
python examples/wait_and_weight_tapered_well.py   # vertical tapered string, Wait and Weight
python examples/wait_and_weight_deviated_well.py     # deviated, Wait and Weight
python examples/wait_and_weight_horizontal_well.py   # horizontal, Wait and Weight
python examples/wait_and_weight_deviated_tapered_well.py     # deviated tapered, Wait and Weight
python examples/wait_and_weight_horizontal_tapered_well.py   # horizontal tapered, Wait and Weight
python examples/volumetric_pipe_on_bottom_well.py      # volumetric + L&B, pipe on bottom
python examples/volumetric_pipe_above_influx_well.py   # volumetric + L&B, pipe above the influx
python examples/volumetric_pipe_out_of_hole_well.py    # volumetric + L&B, pipe out of the hole
python examples/volumetric_tapered_pipe_on_bottom_well.py      # tapered string versions of the three
python examples/volumetric_tapered_pipe_above_influx_well.py
python examples/volumetric_tapered_pipe_out_of_hole_well.py
python examples/volumetric_deviated_well.py     # volumetric + L&B, deviated, pipe on bottom
python examples/volumetric_horizontal_well.py   # volumetric + L&B, horizontal, pipe on bottom
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
| W&W drill pipe pressure | `ICP - [SIDPP x (TVD of kill mud / Bit TVD) - (FCP - SCR) x (MD of kill mud / Bit MD)]`, drop rounded down |
| W&W, vertical well | reduces to `ICP - (ICP - FCP) x (MD of kill mud / Bit MD)` |
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

**Deviated and horizontal wells.** The kill mud adds hydrostatic by **TVD** and friction by
**MD**, so the schedule uses both, and every key point (KOP, end of build, heel) gets its
own row. In a horizontal well the drill pipe pressure bottoms out at the heel and then
**climbs back to FCP** along the lateral: TVD stops changing, but friction keeps building.
Follow the schedule up to FCP. Treating the well as vertical would hold too much pressure:
218 psi too much at the heel of the horizontal example, straight onto a shoe with 796 psi
MAASP.

### Volumetric method and lubricate and bleed

Used when the well **can't be circulated**: pipe out of the hole, pipe above the influx
and unable to strip back, pipe in the hole and unable to pump. Describe the annulus
**from the bottom up, including sections with no pipe in them** - one calculator then
covers every situation. The team killing the well chooses the **safety margin** and
**working pressure**.

| Stage | What to do |
|---|---|
| Wait | Let SICP rise by safety margin + working pressure, no bleeding |
| Volumetric cycle | Bleed `(working pressure / mud gradient) x annular capacity` bbl (IADC #35), holding casing constant; let SICP rise by the working pressure; repeat |
| Gas at surface | SICP rises **no more than 10 psi in 15 minutes** |
| Lubricate and bleed | Pump kill weight mud until casing rises by the working pressure; read the bbl pumped; let it lubricate; bleed back to the starting pressure minus `bbl x KWM gradient / annular capacity at surface`; repeat until casing reads **0** |

- **Annular capacity** for the volumetric bleed is the team's choice: there is no single
  industry standard. The default is the **smallest annulus** the gas will pass through,
  which bleeds the least mud per cycle; the average and longest are printed alongside.
- Both the bleed volume and the psi bled are **limits**, so both are rounded **down**.
- Hold pressures above MAASP are **warned, not stopped**: as the gas comes up the casing
  pressure keeps rising. On the tapered example (MAASP 889) a 100 / 50 psi margin puts
  the very first hold at 950, so every cycle is warned.
- The smallest annulus isn't always around the BHA: on the tapered example it is the
  5" DP inside the 7" casing, near surface.
- **Deviated and horizontal wells:** a barrel fills a length of hole along the MD but
  only adds hydrostatic for its TVD, so each barrel is worth less psi. The volume bled
  stays the vertical IADC #35 volume - it bleeds the least mud - and the
  **angle-corrected** volume, `working pressure / (mud gradient x TVD/MD) x capacity`,
  is printed for each section for information.
- **Horizontal wells:** gas in the lateral doesn't migrate the way it does vertically -
  it can sit in high spots. The method applies once the gas is in the build or vertical
  section; the sheet says so, and shows no angle-corrected volume for the lateral.
- **Lubricate and bleed** assumes the kill mud lands in the vertical part of the well.
  The sheet **warns** if the lubricated column (`total bbl / surface capacity`) passes
  KOP, because each barrel is then worth less psi than calculated.
- The tables are driven by what the crew reads - the 15-minute SICP rise after each
  volumetric cycle, and the bbl pumped each lubricate cycle - because no calculator can
  predict when the gas will reach surface.
- IADC gives the volumetric formulas (#34, #35). There is no dedicated IADC lubricate and
  bleed formula; it is built from the IADC basics (#12 height of fluid, #13/#14 hydrostatic).

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

  Drill pipe step-down schedule (10 steps) - pressure follows where the kill mud is
    Strokes    Kill mud MD ft   TVD ft      psi
          0                0        0    1,400
        163            1,073    1,073    1,347
        326            2,140    2,140    1,294
        489            3,213    3,213    1,241
        652            4,287    4,287    1,188
        815            5,360    5,360    1,134
        978            6,427    6,427    1,081
      1,141            7,500    7,500    1,028
      1,304            8,573    8,573      975
      1,467            9,640    9,640      922
      1,521           10,000   10,000      904   <- crossover
      1,588           10,900   10,900      859   <- crossover
      1,627           11,500   11,500      829   <- bit
```

Volumetric method and lubricate and bleed, from `python examples/volumetric_pipe_on_bottom_well.py`:

```
VOLUMETRIC - pipe on bottom, unable to pump (vertical, untapered)
====================================================
Mud gradient                   0.5408 psi/ft  (10.4 ppg)
Kill mud gradient              0.5980 psi/ft  (11.5 ppg)
MAASP                           1,124 psi
Safety margin / working       100 / 50 psi  (team's choice)

Annulus, bottom up                      Capacity  Length ft
  DC x 8-1/2" hole                       0.0291        600
  HWDP x 8-1/2" hole                     0.0459        900
  DP x 8-1/2" hole                       0.0459      4,850
  DP x 9-5/8" casing                     0.0489      5,150

Volume to bleed per 50 psi = (working pressure / mud gradient) x annular capacity
  smallest annulus      0.0291 bbl/ft    2.6 bbl  <- used
  average annulus       0.0464 bbl/ft    4.2 bbl
  longest annulus       0.0489 bbl/ft    4.5 bbl

Volumetric method
  wait: let SICP rise from 800 to 950 psi (safety margin + working pressure)
  Cycle  Hold casing psi  Bleed bbl  Total bbl  15-min rise
      1              950        2.6        2.6        30 psi
      2            1,000        2.6        5.2        28 psi
      3            1,050        2.6        7.8        25 psi
      4            1,100        2.6       10.4        22 psi
      5            1,150        2.6       13.0        20 psi  ! above MAASP - continue
      6            1,200        2.6       15.6        14 psi  ! above MAASP - continue
      7            1,250        2.6       18.2         4 psi  ! above MAASP - continue  GAS AT SURFACE

Lubricate and bleed - kill mud, annulus at surface 0.0489 bbl/ft
  hydrostatic added = bbl pumped x 0.5980 / 0.0489
  Cycle  Pump to psi  bbl pumped  Hydrostatic psi  Bleed to psi
      1        1,304         6.0               73         1,181
      2        1,231         7.0               85         1,096
      3        1,146         8.0               97           999
      4        1,049         9.0              110           889
      5          939        10.0              122           767
      6          817        10.0              122           645
      7          695        11.0              134           511
      8          561        11.0              134           377
      9          427        12.0              146           231
     10          281        12.0              146            85
     11          135        12.0              146             0  hydrostatic control regained
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
- [x] Vertical, tapered string (**v0.6**)
- [x] Deviated and horizontal, untapered string (**v0.7**)
- [x] Deviated and horizontal, tapered string (**v0.8**)

**Volumetric method and lubricate and bleed**
- [x] Vertical, untapered string: pipe on bottom, pipe above the influx, pipe out of the hole (**v0.9**)
- [x] Vertical, tapered string: all three situations (**v0.10**)
- [x] Deviated and horizontal, untapered string: all three situations (**v0.11**)
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
  schedule.py    Wait and Weight drill pipe step-down schedule: hydrostatic by TVD,
                 friction by MD, with a row at every crossover and key point
  volumetric.py  volumetric method: bleed volume per cycle and the cycle table
  lubricate_and_bleed.py  lubricate and bleed cycles
tests/           one test file per module, plus a full kill sheet for each example
                 well; all hand-worked examples
examples/
  example_well.py        baseline: vertical, untapered string
  wait_and_weight_well.py  baseline well, Wait and Weight
  wait_and_weight_tapered_well.py  vertical tapered string, Wait and Weight
  wait_and_weight_deviated_well.py    deviated, Wait and Weight
  wait_and_weight_horizontal_well.py  horizontal, Wait and Weight
  wait_and_weight_deviated_tapered_well.py    deviated tapered, Wait and Weight
  wait_and_weight_horizontal_tapered_well.py  horizontal tapered, Wait and Weight
  volumetric_pipe_on_bottom_well.py      volumetric + L&B, pipe on bottom
  volumetric_pipe_above_influx_well.py   volumetric + L&B, pipe above the influx
  volumetric_pipe_out_of_hole_well.py    volumetric + L&B, pipe out of the hole
  volumetric_tapered_*_well.py           the same three situations, tapered string
  volumetric_deviated_well.py            volumetric + L&B, deviated, pipe on bottom
  volumetric_horizontal_well.py          volumetric + L&B, horizontal, pipe on bottom
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
