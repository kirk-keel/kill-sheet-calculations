# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

A Python kill sheet calculator for a **vertical well with a surface BOP stack**.
Public portfolio project for a well control specialist who is not a programmer
and must be able to explain every file in an interview.

- Package lives in `src/killsheet/`, tests in `tests/` (pytest).
- **Oilfield units only:** ppg, psi, ft, bbl, bbl/ft, spm, bbl/stk.
- Pressure gradient constant: `0.052` psi/ft per ppg.

## Calculation conventions (follow exactly)

| Item | Rule |
|---|---|
| Kill mud weight (KMW) | Calculated from **TVD**, rounded **UP** to 0.1 ppg |
| Max allowable mud weight (MAMW) | `Test MW + LOT / (0.052 x Shoe TVD)`, rounded **DOWN** to 0.1 ppg |
| MAASP | `(MAMW - Current MW) x 0.052 x Shoe TVD`, rounded **DOWN** to whole psi |
| Initial circulating pressure (ICP) | `ICP = SIDPP + SCR pressure` |
| Final circulating pressure (FCP) | `FCP = SCR pressure x (KMW / OMW)` |

Never change a rounding direction or formula without the user's explicit approval.

## Rounding: the three rules (follow exactly)

Based on the IADC WellSharp Formula Sheet – Field Units, Revision 4, 26 March 2025
(https://iadc.org/wp-content/uploads/2025/04/WSP-FormulaSheet_FieldUnits_rev4.pdf)

1. **Kill weight fluid is always rounded UP** to the nearest 0.1 ppg (10.73 -> 10.8).
2. **Anything that is a maximum is always rounded DOWN** — MAMW / LOT equivalent
   mud weight (11.76 -> 11.7 ppg), MAASP (1497.6 -> 1497 psi), etc.
   The IADC pressure reduction schedule is also rounded DOWN to a whole
   number (21.6 -> 21 psi/100 stks).
3. **If there is no rule, use academic rounding** (nearest; .5 goes up) to the
   accuracy in IADC's table below.

Always carry the ROUNDED values forward into later calculations.

Rounding is conservative on purpose: kill mud must be at least heavy enough,
and a maximum must never be overstated.

| Measurement | Unit | Format |
|---|---|---|
| Depth | ft | X |
| Pressure | psi | X |
| Pressure gradient | psi/ft | X.XXXX |
| Mud weight | ppg | X.X |
| Volume | bbl | X.X |
| Capacity / displacement | bbl/ft | X.XXXX |
| Pump speed | spm | X |
| Strokes | stk | X |
| Pressure reduction schedule | psi/100 stks or psi/10 steps | X (round DOWN) |

"10 steps" = surface-to-bit strokes divided by 10.

Do not use Python's built-in `round()` — it rounds .5 to the nearest even
number (894.5 -> 894), which is not academic rounding. Use the helpers in
`formulas.py`.

## Code style

- Simple and readable over clever. Small pure functions, no hidden state.
- Every formula function has a docstring showing the formula and units.
- Descriptive names that match kill sheet terminology (sidpp, scr_pressure, tvd_ft).

## Working rule: phases

Work proceeds in phases. **After each phase, STOP**, explain in plain English
what was built and why, and wait for the user to say "next".

1. Project skeleton (pyproject.toml, src layout, README stub, .gitignore, this file)
2. Core formulas (KMW, ICP, FCP, MAASP) as small pure functions with docstrings
3. pytest tests from one hand-worked example — show inputs and expected
   answers to the user for verification **before** writing the tests
4. Strokes (surface-to-bit, bit-to-shoe, bit-to-surface) and the drill pipe
   pressure schedule from ICP to FCP
5. GitHub Actions workflow running tests on every push, plus complete README

## Git / GitHub

- Repo: https://github.com/kirk-keel/kill-sheet-calculations (public, GitHub account `kirk-keel`)
- Default branch: `main`. Commit at the end of each phase once the user approves.

## Commands

```
pip install -e ".[dev]"   # install package + pytest in editable mode
pytest                    # run tests
```
