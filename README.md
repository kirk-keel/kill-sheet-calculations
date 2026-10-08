# Kill Sheet Calculator

[![Tests](https://github.com/kirk-keel/kill-sheet-calculations/actions/workflows/tests.yml/badge.svg)](https://github.com/kirk-keel/kill-sheet-calculations/actions/workflows/tests.yml)

A free Python kill sheet calculator for oilfield hands, using oilfield units
(ppg, psi, ft, bbl, bbl/ft, spm, bbl/stk). Rounding follows the IADC WellSharp
rules, with an extra safety factor on kill mud weight.

**Version 0.1 is the simplest kill:** a vertical well, an untapered string
(one drill pipe size plus a BHA of HWDP and drill collars), a surface BOP stack,
and the Driller's method. Everything after that is built on top of it, one
complication at a time. **Version 0.2** adds tapered strings. See the [roadmap](#roadmap).

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
- **Driller's method:** start-up, what to hold on which gauge and for how many strokes,
  shut-down, and the shut-in checks for both circulations
- **Wait and Weight:** drill pipe pressure schedule from ICP to FCP, every 100
  strokes or in 10 equal steps

## How to run it

You need Python 3.10 or newer.

```bash
git clone https://github.com/kirk-keel/kill-sheet-calculations.git
cd kill-sheet-calculations
pip install -e ".[dev]"

python examples/example_well.py   # baseline well: untapered string
python examples/tapered_well.py   # tapered string
pytest                            # run the tests
```

To work your own well, copy one of the example files and change the numbers.
List the drill string top down and the annulus bit up, one line per pipe size
or hole/casing size. Set `method` to `DRILLERS` or `WAIT_AND_WEIGHT`.

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
| W&W drop per 100 strokes | `(ICP - FCP) / (Surface-to-bit strokes / 100)` |
| W&W drop per step (10 steps) | `(ICP - FCP) / 10`, each step = `Surface-to-bit strokes / 10` |

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

### Rounding: three rules

Based on the [IADC WellSharp Formula Sheet – Field Units, Rev 4 (2025)](https://iadc.org/wp-content/uploads/2025/04/WSP-FormulaSheet_FieldUnits_rev4.pdf).

1. **Kill weight fluid is always rounded UP to the next 0.1 ppg, even if exact.**
   11.0 ppg becomes 11.1 ppg. An exact kill weight only *balances* the formation;
   the extra 0.1 ppg is the minimum safety factor that *kills* the well.
2. **Anything that is a maximum is rounded DOWN.** MAMW to 0.1 ppg and MAASP to
   a whole psi, so a limit is never overstated. The Wait and Weight pressure drop
   per step is also rounded down (IADC), so the schedule never steps pressure down
   faster than the straight line from ICP to FCP.
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

Drill string crossovers (top down)     Depth ft   Strokes
  bottom of 5" 19.5# DP                  10,000     1,521
  bottom of 5" HWDP                      10,900     1,588
  bottom of 6-1/2" DC                    11,500     1,627

Annulus crossovers (bit up)            Depth ft   Strokes
  top of DC x 8-1/2" hole                10,900       150
  top of HWDP x 8-1/2" hole              10,000       503
  top of DP x 8-1/2" hole                 5,150     2,405
  top of DP x 9-5/8" casing                   0     4,557

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

Tapered string, from `python examples/tapered_well.py` (Driller's steps omitted here):

```
KILL SHEET - vertical well, tapered string, surface BOP stack
====================================================
Kill mud weight                  11.5 ppg
Initial circulating pressure    1,400 psi
Final circulating pressure        829 psi
Max allowable mud weight         12.2 ppg
MAASP (original mud)              889 psi
MAASP (after kill)                345 psi

Surface to bit                  1,326 stks
Bit to shoe                       394 stks
Bit to surface                  1,796 stks

Drill string crossovers (top down)     Depth ft   Strokes
  bottom of 5" 19.5# DP                   7,000     1,065
  bottom of 3-1/2" 13.3# DP              10,600     1,292
  bottom of 3-1/2" HWDP                  11,200     1,314
  bottom of 4-3/4" DC                    11,500     1,326

Annulus crossovers (bit up)            Depth ft   Strokes
  top of DC x 6-1/8" hole                11,200        38
  top of HWDP x 6-1/8" hole              10,600       163
  top of 3-1/2" DP x 6-1/8" hole          9,500       394
  top of 3-1/2" DP x 7" casing            7,000       958
  top of 5" DP x 7" casing                    0     1,796
```

## Roadmap

Each step adds one complication to the simplest kill, with hand-worked tests.

- [x] **v0.1:** vertical well, untapered string, surface stack, Driller's method
  (plus a straight-line Wait and Weight schedule)
- [x] **v0.1.1:** Driller's method start-up/shut-down procedure and shut-in checks
- [x] **v0.2:** tapered string, vertical well, Driller's method: strokes to every
  drill string and annulus crossover
- [ ] Deviated and horizontal wells: MD and TVD at key points
- [ ] Volumetric method and bullheading
- [ ] Subsea BOP stack: choke line friction, riser margin, choke line strokes
- [ ] Web page interface, with a kill plot of forecast drill pipe and annulus
  pressure beside the table, showing the inflection at each pipe change

## Project layout

```
src/killsheet/
  rounding.py    the three rounding rules (the only place rounding is done)
  formulas.py    KMW, ICP, FCP, MAMW, MAASP
  strokes.py     volumes and strokes
  drillers.py    Driller's method kill steps
  schedule.py    Wait and Weight drill pipe pressure schedule
tests/           one test file per module, plus a full tapered-well kill sheet;
                 all hand-worked examples
examples/
  example_well.py        baseline well: untapered string
  tapered_well.py        tapered string
  kill_sheet_printer.py  prints a kill sheet (shared by both examples)
.github/workflows/tests.yml   runs the tests on every push
```

## Testing

The tests and both example kill sheets run automatically on GitHub on every push,
on Python 3.10–3.13. The badge at the top of this page shows whether they're passing.

## Disclaimer

This is a free planning and training aid. It is not a replacement for a
site-specific kill sheet, a well control program, or the judgment of the people
on location. See [LICENSE](LICENSE): the software is provided "as is", without
warranty of any kind.

## License

[MIT](LICENSE) © 2026 Kirk Keel
