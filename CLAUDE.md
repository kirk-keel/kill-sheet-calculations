# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

A free Python kill sheet calculator for oilfield hands. The goal is to plan and
kill all types of wells using every well control technique. Public portfolio
project for a well control specialist who is not a programmer and must be able
to explain every file in an interview.

**Baseline = the simplest kill:** vertical well, untapered string (ONE drill pipe
size + BHA, where BHA = HWDP + drill collars), surface BOP stack, Driller's method.
Every later feature adds one complication on top of the baseline, and the
baseline must keep working and keep its tests.

- Package lives in `src/killsheet/`, tests in `tests/` (pytest), one test file per module:
  - `rounding.py` — the rounding helpers (the only place rounding is done)
  - `formulas.py` — KMW, ICP, FCP, MAMW, MAASP
  - `strokes.py` — section volumes and surface-to-bit / bit-to-shoe / bit-to-surface strokes
  - `drillers.py` — Driller's method kill steps (the baseline method)
  - `schedule.py` — Wait and Weight drill pipe pressure schedule, ICP to FCP
- **Oilfield units only:** ppg, psi, ft, bbl, bbl/ft, spm, bbl/stk.
- Pressure gradient constant: `0.052` psi/ft per ppg.

## Calculation conventions (follow exactly)

| Item | Rule |
|---|---|
| Kill mud weight (KMW) | Calculated from **TVD**, rounded **UP to the NEXT** 0.1 ppg (exact values still go up 0.1) |
| Max allowable mud weight (MAMW) | `Test MW + LOT / (0.052 x Shoe TVD)`, rounded **DOWN** to 0.1 ppg |
| MAASP | `(MAMW - Current MW) x 0.052 x Shoe TVD`, rounded **DOWN** to whole psi |
| Initial circulating pressure (ICP) | `ICP = SIDPP + SCR pressure` |
| Final circulating pressure (FCP) | `FCP = SCR pressure x (KMW / OMW)` |

**Strokes:** a section is `(capacity_bbl_per_ft, length_ft)`. Each section volume
is rounded to 0.1 bbl, totals are the sum of rounded section volumes, and strokes
= total volume / pump output, rounded to a whole stroke. Surface line volume is an
optional input to surface-to-bit strokes; if the user doesn't have it, it is 0.

**Driller's method:** 1st circulation (original mud): hold drill pipe at ICP for
bit-to-surface strokes. 2nd circulation (kill mud): hold casing constant at the
SIDPP value for surface-to-bit strokes, then hold drill pipe at FCP for
bit-to-surface strokes.

**Wait and Weight pressure schedule:** the user chooses the step method:
- `EVERY_100_STROKES` (default): drop = `(ICP - FCP) / (surface-to-bit strokes / 100)`
- `TEN_STEPS`: exactly 10 steps of `surface-to-bit strokes / 10` (rounded to a whole
  stroke); drop = `(ICP - FCP) / 10`

The drop is always rounded **DOWN** to a whole psi. Each row = `ICP - drop x steps`;
the last row is FCP at surface-to-bit strokes. The schedule ends at FCP — no rows after.

**SIDPP must be > 0.** A zero drill pipe reading with a float in the string is not a
true SIDPP — the float must be bumped to find it. `kill_mud_weight` raises a
`ValueError` saying so rather than calculating from 0.

Never change a rounding direction or formula without the user's explicit approval.

## Rounding: the three rules (follow exactly)

Based on the IADC WellSharp Formula Sheet – Field Units, Revision 4, 26 March 2025
(https://iadc.org/wp-content/uploads/2025/04/WSP-FormulaSheet_FieldUnits_rev4.pdf)

1. **Kill weight fluid is always rounded UP to the NEXT 0.1 ppg** (10.73 -> 10.8).
   An exact value still goes up (10.8 -> 10.9): an exact KMW only balances the
   formation, it doesn't kill the well. The 0.1 ppg is the minimum safety factor.
   This is stricter than the literal IADC wording — it is the user's rule; keep it.
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
`rounding.py`.

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
5. GitHub Actions workflow, complete README, and v0.1 matched to the baseline
   (Driller's method, untapered example well) — released as v0.1

Every phase that adds calculations: show a hand-worked example to the user and
get it verified before committing.

Roadmap after v0.1 (one complication at a time):
6. Tapered strings — Wait and Weight schedule calculated per pipe section
7. Deviated and horizontal wells — MD and TVD at key points
8. Volumetric method and bullheading
9. Subsea BOP stack — choke line friction, riser margin, choke line strokes
10. Web page interface

## Git / GitHub

- Repo: https://github.com/kirk-keel/kill-sheet-calculations (public, GitHub account `kirk-keel`)
- Default branch: `main`. Commit at the end of each phase once the user approves.
- License: MIT (`LICENSE`), copyright Kirk Keel.
- CI: `.github/workflows/tests.yml` runs pytest on Python 3.10–3.13 on every push and PR.

## Commands

```
pip install -e ".[dev]"            # install package + pytest in editable mode
pytest                             # run tests
python examples/example_well.py    # print a full kill sheet for the example well
```

If you change the example well or the output format, update the "Example output"
section of README.md to match.
