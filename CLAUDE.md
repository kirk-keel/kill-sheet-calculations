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
  - `depths.py` — MD/TVD: `tvd_at_md` interpolates TVD between key points
  - `strokes.py` — section volumes, strokes, crossovers, partial sections, length checks
  - `kill_steps.py` — KillStep, stage names, ±10 psi tolerance, gauge checks (shared)
  - `drillers.py` — Driller's method kill steps (the baseline method)
  - `wait_and_weight.py` — Wait and Weight kill steps, ICP check, recalculation
  - `volumetric.py` — volumetric method: annular capacity choices, IADC #35, cycle table
  - `lubricate_and_bleed.py` — lubricate and bleed cycles
  - `bullhead.py` — bullheading while drilling: limits for each side, equipment limit, chart
  - `reverse_circulation.py` — reverse circulation kill for CWI wells
  - `schedule.py` — Wait and Weight drill pipe step-down schedule, by depth of kill mud
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

**MD and TVD** (user rule: every point shows MD AND TVD; interpolate what isn't known):
- Pressures use TVD (KMW at bit TVD, MAMW/MAASP at shoe TVD). Volumes/strokes use MD.
- Key points are (name, MD, TVD): KOP, end of build, heel, etc. Surface (0, 0), the
  shoe and the bit are always included. TVD between them = straight-line interpolation,
  rounded to a whole foot. Exact in vertical/tangent/horizontal; an estimate in a build.
- A point partway through a section: partial section volume = capacity x length used,
  rounded to 0.1 bbl, added to the rounded running total (same as crossovers).
- `check_section_lengths` refuses to run if drill string != bit MD, open hole !=
  bit MD - shoe MD, or cased hole != shoe MD. TVD may never exceed MD.
- Vertical well = the case where MD = TVD (bit_md_ft / shoe_md_ft default to TVD).

**Crossovers:** `crossover_strokes(sections, pump_output, starting_volume_bbl=0)` gives
strokes to the END of each section. Running total = sum of ROUNDED section volumes,
rounded to 0.1 bbl, then / pump output -> whole strokes (user-approved), so the last
crossover equals the total strokes. Drill string listed top down (surface lines as
the starting volume); annulus listed bit up.

**Driller's method** (constant bottomhole pressure, user-confirmed):
- Start-up AND shut-down of EVERY circulation: hold CASING pressure constant while
  bringing the pump up to / down from the kill rate.
- 1st circulation (original mud): start up holding casing at SICP, then hold drill
  pipe at ICP. One bottoms up is a MINIMUM — circulate until the gas is out.
  Shut-in check: SIDPP and SICP both read the original SIDPP (±10 psi). SICP higher
  = strung-out gas still in the annulus, continue circulating.
- 2nd circulation (kill mud): start up holding casing at the SIDPP value, hold casing
  constant for surface-to-bit strokes, then hold drill pipe at FCP for bit-to-surface
  strokes. Shut-in check: SIDPP and SICP both read 0 (±10 psi) = well dead.
- Gauge tolerance: ±10 psi (`GAUGE_TOLERANCE_PSI`).

**Wait and Weight** (user-confirmed), one circulation with kill mud:
- Weight up the active system to KMW while shut in. RETAKE SIDPP (float bumped) and
  SICP just before pump start-up (gas may migrate while weighting up) — inputs
  `sidpp_at_start_psi`, `sicp_at_start_psi`. Retaken SIDPP must be > 0.
- Start-up: hold casing constant at the retaken SICP while bringing the pump to kill rate.
- Once at kill rate, follow the step-down chart on the drill pipe until kill mud is at
  the bit, then hold FCP until kill mud is at surface. Same shut-down; check 0 ±10 psi.
- ICP check at kill rate (`kill_pressures_at_kill_rate`):
  - within ±10 psi: use calculated ICP and FCP.
  - more than 10 psi HIGH: RECALCULATE — actual SCR = observed ICP - RETAKEN SIDPP;
    ICP = observed; FCP = actual SCR x (KMW / OMW) but NEVER LOWER than the calculated
    FCP (user rule: "if anything the FCP should be higher"); rebuild the schedule.
  - more than 10 psi LOW: a complication (separate topic) — keep calculated ICP and
    FCP; never recalculate lower. KMW always comes from the original SIDPP.

**Wait and Weight step-down schedule** (user-approved, v0.5.1): pressure follows the
DEPTH of the kill mud, never a straight line against strokes:
- General (user-approved v0.7): `P = ICP - [SIDPP x (TVD/bit TVD) - (FCP - SCR) x (MD/bit MD)]`
  with SCR = ICP - SIDPP — the "FCP form" (user choice): hydrostatic by TVD, friction by
  MD, lands exactly on FCP at the bit. The drop (in brackets) is rounded DOWN.
- Vertical (TVD = MD) reduces to `P = ICP - (ICP - FCP) x (MD of kill mud / bit MD)`.
- Deviated/horizontal: pass `sidpp_psi`, `bit_tvd_ft`, `key_points` (name, MD, TVD) to
  `pressure_schedule`; every key point (KOP, end of build, heel) gets its own row.
  Horizontal: pressure bottoms out at the heel, then CLIMBS to FCP along the lateral —
  user rule: the crew follows the schedule up to FCP (no minimum hold).
- After a high-ICP recalculation, the schedule uses the RETAKEN SIDPP.
- A step row is kept even when a key point or crossover lands a few strokes from it
  (user rule, v0.8): steps stay evenly spaced and the named row marks the inflection.
- MD of kill mud after N strokes (`md_after_strokes`): volume = N x pump output (0.1 bbl)
  minus surface lines; walk the string; inside a section MD = start + section length x
  (volume left / ROUNDED section volume), so crossover strokes land exactly on crossovers.
- Steps: `TEN_STEPS` (DEFAULT, user rule) = 10 steps of `surface-to-bit strokes / 10`
  (whole strokes); `EVERY_100_STROKES` (option).
- Every crossover is its own row (the inflection points, user rule); last row is FCP
  at the bit. The schedule ends at FCP — no rows after.
- WHY: a straight line vs strokes is only right for a single-ID string. With DP+HWDP+DC
  it was up to 38 psi short (v0.5 bug, fixed v0.5.1); a 5" x 3-1/2" taper, 112 psi short.
  Never go back to a straight line against strokes.

**Volumetric method and lubricate and bleed** (user-confirmed, v0.9):
- Used whenever the well can't be circulated (pipe out of the hole, pipe above the
  influx and unable to strip back, pipe in the hole and unable to pump, ...). The user
  describes the annulus BOTTOM UP, including sections with NO pipe; one calculator covers
  every situation, and each roadmap step covers all of them.
- Safety margin and working pressure are chosen by the team killing the well (inputs,
  no defaults).
- Volumetric bleed per cycle = (working pressure / mud gradient) x annular capacity
  (IADC #35), rounded DOWN to 0.1 bbl. Annular capacity is the team's choice (no single
  industry standard); DEFAULT = SMALLEST annulus the gas passes through (least bleed).
  Average (total volume / length, 4 places) and longest are shown for comparison.
- First hold = SICP + safety margin + working pressure; each cycle adds the working
  pressure. Above MAASP: WARN AND CONTINUE (pressure keeps rising as gas comes up).
- Gas at surface = SICP rises no more than 10 psi over a 15 minute wait. The table is
  driven by those readings and runs until that happens (it can't be predicted).
- Lubricate and bleed only once gas is at surface: kill weight mud, annulus AT SURFACE.
  Pump until casing rises by the working pressure (the pressure decides the volume);
  bleed back to the pre-pump pressure minus bbl x KWM gradient / surface capacity
  (rounded DOWN). Repeat until casing = 0 (hydrostatic control regained).
- No dedicated IADC lubricate and bleed formula — built from #12, #13, #14. Say so.
- Deviated/horizontal (user rules, v0.11): volume bled stays the VERTICAL IADC #35
  volume (bleeds the least); the angle-corrected volume
  `Pw / (gradient x TVD/MD of the section) x capacity` is printed for information only.
  Horizontal sections: no angle-corrected volume, plus a NOTE that gas in the lateral
  doesn't migrate like it does vertically — the method applies once gas is in the build
  or vertical section. The SMALLEST annulus is kept as is even if it is in the lateral.
- Lubricate and bleed: WARN when the kill mud column (total bbl / surface capacity)
  passes KOP (deepest key point with TVD = MD) — each bbl is then worth less psi.
- Example sheets: one per well type for pipe on bottom is fine; every situation must be
  covered in the tests.

**Bullheading while drilling** (user-confirmed, v0.13):
- Kick too large to handle at surface: annular SHUT, kill fluid pumped down the drill
  string AND the backside at the SAME RATE, at the same time, the whole way (no shutting
  down a side — different rates on each side would confuse the crew).
- Goal: establish INJECTIVITY and push the influx back where it came from — NOT break down
  the formation. Pressure builds until injectivity, then falls.
- Kill fluid = KMW, rounded UP to the next 0.1 (rule 1). Influx treated as original mud.
- Formation limit from the LOT / MAMW at the shoe. Equipment limit = LOWEST rating or
  tested value of the equipment (team list). Each row uses the lower of the two.
- Annulus max = 0.052 x [MAMW x shoe TVD - fluid above the shoe]; String max =
  0.052 x [MAMW x shoe TVD - string column to bit + annulus column shoe to bit]. Both
  rounded DOWN. The string side MUST use both columns (it falls to 466 psi on the baseline
  well, not 830).
- Chart: 10 steps of the annulus strokes + rows at string crossovers, kill fluid at the bit,
  at the shoe (annulus), the kill point, and overdisplacement (team input). Blank columns
  for the actual string and annulus pressures (as on the IADC worksheet).
- Minimum rate to beat gas migration: IADC #34 then #13 with the LARGEST annulus,
  rounded UP (a minimum — the mirror of rule 2).
- Deviated/horizontal (v0.15): every column by TVD; a row when kill fluid passes each key
  point on EACH side ("KOP (string)", "KOP (annulus)" ...); chart shows MD and TVD.
  Named points (crossovers, key points, shoe) are shown at their EXACT depth on their side.
- Once the strokes reach a side's surface-to-bottom strokes, that side's kill fluid is AT
  the bottom by definition (v0.13.1 fix: working depth back from rounded strokes stopped
  20 ft short of the bit on the tapered well — 1,326 x 0.117 = 155.1 of 155.2 bbl).

**Reverse circulation** (user-confirmed, v0.17) — a COMPLETION / WORKOVER / INTERVENTION
(CWI) well, reversing out with kill weight fluid:
- Circulating point: an opened SSD or a hole punched in the tubing ABOVE the production
  packer. Treat it as the "bit": the annulus is the pump side, the tubing the choke side.
- KWF balances at the perfs WITH formation fluid left below the SSD:
  tubing gradient = (Pform - SITP) / mid-perf TVD; P_SSD = Pform - gradient x (mid-perf - SSD);
  KWF = P_SSD / (0.052 x SSD TVD) + margin; margin is OPTIONAL, default 0, added BEFORE the
  rule-1 round-up. NEVER use ordinary rounding for kill weight.
- NO SCR (user rule — circulating IS the kill; a reverse SCR can't be taken first).
- Pre-start: open the SSD, let pressures stabilise, record SITP and SICP; SICP isn't known
  until then (= P_SSD - annulus hydrostatic).
- Holding rule for ALL constant-BHP kills: hold the side WITHOUT a homogeneous column while
  the pump comes on/off, then swap to the side WITH a consistent column at kill rate.
  Reverse: start-up holds TUBING at SITP (not casing at SICP); annulus pressure at rate =
  OBSERVED ICP; shut-down holds tubing.
- FCP = observed ICP - (KWF - packer fluid) x 0.052 x SSD TVD (drop rounded DOWN); it equals
  friction minus overbalance at the SSD, so if <= 0 floor at 0 and WARN.
- Schedule: annulus pump pressure ICP -> FCP by TVD of the kill fluid; hold FCP while the
  tubing is displaced. TVD for pressures, MD for volumes/strokes.
- Friction warning (user's wording): "In reverse circulation, the high-friction path is the
  return side. If the choke is wide open and pump pressure still climbs above FCP, BHP is
  rising. Reduce the rate." Holding pump pressure keeps BHP constant — the choke absorbs it.
- Limits: lower of fracture at the TOP perf minus annulus hydrostatic, and the lowest-rated
  completion/surface equipment. Show both: packer fluid and kill fluid in the annulus.
- End: both gauges 0 ±10 psi, then a FLOW CHECK. Optional bullhead of the volume below the
  SSD (tubing to packer + casing to top perf).
- Tapered tubing (v0.18): a schedule row at every ANNULUS crossover, at its exact depth.
- Deviated/horizontal (v0.19): SSD, packer and top-perf MD plus key points; TVD for
  pressures, MD for volumes. Horizontal with perfs in the lateral: use the HEEL TVD for
  the top and mid perf (user rule). The observed ICP must be above the SICP.
- Printer: import as `from killsheet import reverse_circulation as reverse` — its
  final_circulating_pressure must NOT shadow formulas.final_circulating_pressure.

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

v0.1.1: Driller's start-up/shut-down procedure and shut-in checks (±10 psi).

Roadmap (user-defined, one complication at a time). Each method is covered for
every well/string type in this order: (a) vertical untapered, (b) vertical tapered,
(c) deviated AND horizontal untapered, (d) deviated AND horizontal tapered.
Order: surface stack (all methods) -> web page -> subsea stack (all methods).

Surface stack:
- Driller's method:      (a) DONE v0.1/v0.1.1, (b) DONE v0.2, (c) DONE v0.3, (d) DONE v0.4
- Wait and Weight:       (a) DONE v0.5 (fixed v0.5.1), (b) DONE v0.6, (c) DONE v0.7, (d) DONE v0.8
- Volumetric method and lubricate and bleed: (a) DONE v0.9, (b) DONE v0.10, (c) DONE v0.11,
                         (d) DONE v0.12 (all three situations each)
- Bullheading:           (a) DONE v0.13 (fixed v0.13.1), (b) DONE v0.14, (c) DONE v0.15, (d) DONE v0.16
- Reverse circulation:   CWI wells. (a) DONE v0.17, (b) DONE v0.18, (c) DONE v0.19, (d) DONE v1.0
SURFACE STACK COMPLETE (v1.0.0). Next: the web page, then the subsea stack.

Web page (user: AFTER the surface stack is complete, BEFORE subsea) - NEXT:
- Including the auto-generated kill plot beside the table: forecast drill pipe AND
  annulus pressure vs strokes, showing the inflection point at each pipe change

Subsea stack (adds choke line friction, riser margin, choke line volume/strokes):
- Every method above, (a)-(d)

## NEXT: web page (hand-off from the v1.0.0 session)

Decided by the user:
- GitHub Pages at https://kirk-keel.github.io/kill-sheet-calculations/, published by a
  GitHub Actions workflow only after the tests pass.
- Pyodide runs the real `killsheet` package in the browser (no JavaScript rewrite of the
  formulas). The user accepts the few-second first load.
- First web release = the complete DRILLING package: Driller's, Wait and Weight, and
  volumetric + lubricate and bleed, every well/string type. (Bullhead and reverse
  circulation come in a later web release.)
- Kill plot: TWO lines, drill pipe and annulus. Plot ONLY what can be calculated without a
  gas model; mark the rest "depends on the influx".
- Print: page 1 = well schematic (casing, shoe, open hole, string sections/crossovers, bit,
  KOP/EOB/heel) with KMW, ICP, FCP, MAMW, MAASP (original/after kill), volumes in bbl AND
  strokes. Page 2 = the table WITH an "Actual" column for observed values, plus the plot.
- Plan: plot/table numbers computed in a new TESTED Python module; the page only draws them
  (plain SVG, no plotting library). Dropdown of the example wells; all inputs editable.

Proposed, AWAITING the user's answers (ask these first in the next session):
1. Annulus line = SIDPP - (KMW - OMW) x 0.052 x TVD of the kill-mud column in the annulus
   (bottom up), drop rounded DOWN, floored at 0, annulus friction ignored; plotted only once
   the annulus is all liquid. Baseline well (0.0572 psi/ft, zero at a 11,364 ft column):
   - Driller's (strokes across both circulations): 1st circ DP flat 1,400, annulus not
     plotted; 2nd circ DP 1,400 -> 829 by 6,184 stks (depth-based), annulus flat 650 until
     kill mud reaches the bit, then 616 (6,334 stks, top of DC), 565 (6,687, top of HWDP),
     287 (8,589, shoe), 0 at ~10,685, kill point 10,741.
   - W&W: DP 1,400 -> 829 by 1,627 then 829; annulus not plotted until gas is out after one
     bottoms-up (4,557 stks): column 7,606 ft -> 215 psi; 0 at ~6,128; kill point 6,184.
   Does this match how the user forecasts casing pressure? (friction ignored; W&W gas out
   after one bottoms-up from the start)
2. Volumetric / L&B: x-axis = bbl bled / pumped; annulus line = hold pressures (staircase /
   saw-tooth). What should the DRILL PIPE line be - SIDPP + safety margin + working pressure
   with pipe on bottom and no float, or annulus line only?
3. Agree the annulus-line drop is rounded DOWN (predicted casing pressure on the high side)?

## Git / GitHub

- Repo: https://github.com/kirk-keel/kill-sheet-calculations (public, GitHub account `kirk-keel`)
- Default branch: `main`. Commit at the end of each phase once the user approves.
- License: MIT (`LICENSE`), copyright Kirk Keel.
- CI: `.github/workflows/tests.yml` runs pytest and every `examples/*_well.py` on Python
  3.10–3.13 on every push and PR.
- Release tags: v0.1, v0.1.1, v0.2 ... v0.19, v1.0.0 (surface stack complete). Minor
  number for each new capability, patch number for fixes.

## Commands

```
pip install -e ".[dev]"            # install package + pytest in editable mode
pytest                             # run tests
python examples/example_well.py    # baseline well (untapered string)
python examples/tapered_well.py    # tapered string
python examples/deviated_well.py   # deviated, untapered
python examples/horizontal_well.py # horizontal, untapered
python examples/deviated_tapered_well.py    # deviated, tapered
python examples/horizontal_tapered_well.py  # horizontal, tapered
```

Examples: `examples/kill_sheet_printer.py` holds the shared printing code; each
example file is just the well data. Sections in the examples are
`(name, capacity, length)`; the name is for printing only.
If you change an example well or the output format, update the "Example output"
section of README.md to match.
