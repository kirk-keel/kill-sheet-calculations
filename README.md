# Kill Sheet Calculator

[![Tests](https://github.com/kirk-keel/kill-sheet-calculations/actions/workflows/tests.yml/badge.svg)](https://github.com/kirk-keel/kill-sheet-calculations/actions/workflows/tests.yml)

A free Python kill sheet calculator for oilfield hands, using oilfield units
(ppg, psi, ft, bbl, bbl/ft, spm, bbl/stk). Rounding follows the IADC WellSharp
rules, with an extra safety factor on kill mud weight.

**Version 0.1 covers the simplest kill:** a vertical well, an untapered string
(one drill pipe size plus a BHA of HWDP and drill collars), a surface BOP stack,
and the Driller's method. Everything after that is built on top of it, one
complication at a time. See the [roadmap](#roadmap).

## Why I built it

I built this calculator as a free resource for oilfield hands to plan and kill
all types of wells using every well control technique at their disposal.

## What it calculates

- **Kill mud weight** (KMW)
- **Initial and final circulating pressure** (ICP, FCP)
- **Maximum allowable mud weight** (MAMW) and **MAASP**, before and after the kill
- **Strokes:** surface to bit (with optional surface line volume), bit to shoe, bit to surface
- **Driller's method:** what to hold, on which gauge, for how many strokes, for both circulations
- **Wait and Weight:** drill pipe pressure schedule from ICP to FCP, every 100
  strokes or in 10 equal steps

## How to run it

You need Python 3.10 or newer.

```bash
git clone https://github.com/kirk-keel/kill-sheet-calculations.git
cd kill-sheet-calculations
pip install -e ".[dev]"

python examples/example_well.py   # print a full kill sheet for the example well
pytest                            # run the tests
```

To work your own well, copy `examples/example_well.py` and change the numbers at
the top. Set `METHOD` to `DRILLERS` or `WAIT_AND_WEIGHT`.

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
| Surface to bit volume | `Surface lines (optional) + Drill string` |
| W&W drop per 100 strokes | `(ICP - FCP) / (Surface-to-bit strokes / 100)` |
| W&W drop per step (10 steps) | `(ICP - FCP) / 10`, each step = `Surface-to-bit strokes / 10` |

### Driller's method

| Circulation | Mud | Hold | For |
|---|---|---|---|
| 1st | Original | Drill pipe at **ICP** | Bit-to-surface strokes (kick out) |
| 2nd | Kill | Casing **constant** (at the SIDPP value) | Surface-to-bit strokes |
| 2nd | Kill | Drill pipe at **FCP** | Bit-to-surface strokes |

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

From `python examples/example_well.py`:

```
KILL SHEET - vertical well, surface BOP stack
==============================================
Kill mud weight                  11.5 ppg
Initial circulating pressure    1,400 psi
Final circulating pressure        829 psi
Max allowable mud weight         14.6 ppg
MAASP (original mud)            1,124 psi
MAASP (after kill)                830 psi

Surface to bit                  1,627 stks
Bit to shoe                     2,405 stks
Bit to surface                  4,557 stks

Driller's method
  1st circulation (original mud)
      hold drill pipe at 1,400 psi for 4,557 stks
  2nd circulation (kill mud), surface to bit
      hold casing at 650 psi for 1,627 stks
  2nd circulation (kill mud), bit to surface
      hold drill pipe at 829 psi for 4,557 stks
```

## Roadmap

Each step adds one complication to the simplest kill, with hand-worked tests.

- [x] **v0.1:** vertical well, untapered string, surface stack, Driller's method
  (plus a straight-line Wait and Weight schedule)
- [ ] Tapered strings: Wait and Weight schedule calculated per pipe section
- [ ] Deviated and horizontal wells: MD and TVD at key points
- [ ] Volumetric method and bullheading
- [ ] Subsea BOP stack: choke line friction, riser margin, choke line strokes
- [ ] Web page interface

## Project layout

```
src/killsheet/
  rounding.py    the three rounding rules (the only place rounding is done)
  formulas.py    KMW, ICP, FCP, MAMW, MAASP
  strokes.py     volumes and strokes
  drillers.py    Driller's method kill steps
  schedule.py    Wait and Weight drill pipe pressure schedule
tests/           one test file per module, all hand-worked examples
examples/        example_well.py - prints a complete kill sheet
.github/workflows/tests.yml   runs the tests on every push
```

## Testing

The tests run automatically on GitHub on every push, on Python 3.10–3.13. The
badge at the top of this page shows whether they're passing.

## Disclaimer

This is a free planning and training aid. It is not a replacement for a
site-specific kill sheet, a well control program, or the judgment of the people
on location. See [LICENSE](LICENSE): the software is provided "as is", without
warranty of any kind.

## License

[MIT](LICENSE) © 2026 Kirk Keel
