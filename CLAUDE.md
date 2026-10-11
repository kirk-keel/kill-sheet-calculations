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
  - `kill_plot.py` — kill plot: single-bubble gas model, forecast DP and casing lines, shoe check
    (vertical, deviated, horizontal; checked against tests/reference_model.py)
  - `volumetric_model.py` — volumetric forecast: single bubble, bleed at the gas, hold correction,
    shoe tiers, Pf, wording (checked against tests/reference_model.py reference_volumetric)
  - `volumetric_plot.py` — volumetric and lubricate and bleed charts (pressure vs bbl), pipe position
  - `kill_sheet.py` — every sheet (Driller's / W&W / volumetric / bullhead / reverse) as plain dicts (calls the
    modules above, calculates nothing new); the printer AND the web page draw from it
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
  (IADC #35), rounded DOWN to 0.1 bbl. v1.3 DEFAULT = "annulus at the gas" (see the v1.3 rules
  below); smallest / average / longest stay selectable team choices (same forecast + warnings).
- First hold = SICP + safety margin + working pressure; each cycle adds the working
  pressure. Above MAASP: WARN AND CONTINUE (pressure keeps rising as gas comes up).
- Gas at surface = SICP rises no more than 10 psi over a 15 minute wait. The table is
  driven by those readings and runs until that happens (it can't be predicted).
- Lubricate and bleed only once gas is at surface: kill weight mud, annulus AT SURFACE.
  Pump until casing rises by the working pressure (the pressure decides the volume);
  bleed back to the pre-pump pressure minus bbl x KWM gradient / surface capacity
  (rounded DOWN). v1.3: STOP when bbl lubricated = gas volume at surface (pit gain + bbl bled,
  from the readings) - see the v1.3 rules below (casing is NOT assumed to reach 0).
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

**Volumetric v1.3 - single-bubble forecast** (user-approved, worked cycle by cycle; code in
`volumetric_model.py`, oracle `tests/reference_model.py` reference_volumetric, tests
`tests/test_volumetric_model.py`):
- New inputs: pit_gain_bbl (REQUIRED), sidpp_psi (Pf from SIDPP when given; otherwise Pf
  ESTIMATED from SICP: "estimated: assumes influx at bottom, 0.1 psi/ft, no migration before the
  SICP reading"). kill_mud_weight_ppg = the mud LUBRICATED (original 10.4 for a swabbed kick).
- Gas position: Boyle at the top of the bubble, P = P0 x pit / (pit + bbl bled); gas top TVD =
  (P - casing) / mud gradient; positions by MD (capacities), pressures by TVD. Influx in the lateral:
  bubble starts at the heel, 0.1 psi/ft - and the bleed PATH starts there too (the bubble's bottom
  at the heel, never the DC annulus at the bit).
- Bleed per cycle on the SMALLEST annulus the gas touches anywhere along its PATH (end of the last
  bleed or shut-in, through the end of this bleed); the largest capacity that satisfies it. Any error
  = under-bleed. Sheet prints a bleed table by annulus (capacity, bbl per cycle, from cycle).
- Holds: "Standard hold" (IADC: SICP + SF + n x Pw) and "Hold to use" side by side, with the reason and
  a Tier column (legend printed; tier 0 = standard hold, no correction). After any shoe-limited cycle
  (tier 2-4) the Standard is RE-BASED: previous hold used + Pw ("Standard re-based after shoe-limited
  cycle N"), so a correction is always >= 0 against the column it sits next to.
  Hold to use raised (never lowered for geometry) until the forecast BHP through the coming bleed is
  >= Pf + SF (gas gaining vertical height: narrower annulus / build) - "+X psi: gas will gain vertical
  height during this bleed (narrower annulus / build section)." Includes the first hold.
- Shoe tiers on every hold: 0 standard / 1 corrected, shoe <= fracture; 2 shoe-limited, BHP >= Pf+SF;
  3 shoe-limited, Pf <= BHP < Pf+SF: "Cycle N: hold limited by the shoe. SF reduced from SF to x psi.
  BHP still above Pf."; 4 shoe-limited BHP < Pf: "SUPERVISOR DECISION, cycle N: hold A psi keeps BHP >=
  Pf + x but puts the shoe y psi over fracture. Hold B psi keeps the shoe at fracture but BHP z psi under
  Pf (influx). Constant-BHP doctrine favors A." (A printed). The shoe-limited hold is stepped down
  until the forecast shoe really is <= fracture.
- shoe_margin_psi (team's choice, default 0; examples 0): the shoe tiers and the pre-check use
  fracture - shoe margin as the shoe limit; printed when nonzero (a LOT isn't that precise).
- Pre-check: SF + Pw >= MAASP - SICP - shoe margin: "Shoe margin X psi is less than SF + Pw Y. Volumetric with these
  margins will exceed fracture. Reduce SF/Pw or consider bullheading."
- MAASP by gas position: gas below shoe "ABOVE MAASP, gas below shoe, shoe overpressured"; above
  "above MAASP, gas above shoe, MAASP no longer applies, continue". Plot: MAASP line stops where the
  gas top passes the shoe (labelled). Corrections / tiers = a separate annotated layer; standard hold
  dashed under the hold to use.
- Gas at surface: in a wait when gas P <= hold (casing rises only to P); during a bleed when P falls to
  the hold - the crew stops bleeding at the choke (that row's bleed is partial). Readings still drive
  the table; warn when readings vs forecast bbl bled differ > 20% (early: dispersed / out of solution;
  late: bigger influx or gas in solution - user wording).
- Lubricate and bleed: Pw rule kept; STOP at the gas volume at surface (pit gain + bbl bled, from the
  readings); print first 5 and last 3 cycles + "... N cycles ...". End: remaining underbalance =
  Pf - (lubricated mud x column TVD + mud x the rest); <= 10: "Hydrostatic control regained. Casing X psi
  is trapped pressure. Bleed off in small increments, check 0, flow check, then strip to bottom and
  circulate."; else "Casing X psi. Remaining underbalance U psi. Do not bleed casing below U + SF psi.
  Not dead. Kill required (strip to bottom and circulate, or bullhead)."
- Horizontal sheets: "Gas lying in the lateral may not migrate, so casing can stay flat for a long time.
  Volumetric steps start when casing begins to rise." and "Shoe at the heel: shoe pressure = BHP. Kick
  tolerance is very small. If the pre-check fires, consider bullheading before volumetric."
- Examples (12): on bottom float (SICP 800, Pf 6,868 est.); NEW on bottom NO float (SIDPP 650); tapered
  3 bbl SF 50/Pw 50 (SICP 741); NEW tapered 10 bbl SHOE AT RISK (SICP 885, SF 50/Pw 50: pre-check, tier 3
  c1, SUPERVISOR c2); deviated + tapered (SICP 780); horizontal + tapered (SICP 650, SF 100/Pw 50: pre-check,
  tier 3 every cycle, SF reduced to 67 at c1 then 95-96 - the honest answer, points to bullheading;
  test cases 50/50 +87 raise, shoe margin 16; 75/25 +89, margin 15; shoe margin 50: SF 17-46); swabs (Pf = 10.4 ppg hydrostatic 6,219,
  SICP 62 / 36 tapered 3 bbl, lubricate 10.4). Readings generated from the forecast (rises illustrative).
  Tapered kill sheets now 3 bbl / SICP 741 (peak 1,292 / 1,232, max shoe 5,929, margin 97).
- Approved baseline: gas at surface 38.8 bbl bled / 1,400 psi / 48.8 bbl gas (Boyle 68,336 / 1,400);
  end casing 839, remaining underbalance 592, do not bleed below 692.
- Tier-4 test fixture: tapered shoe-at-risk well with LOT 1,000 (MAASP 790 < SICP 885).

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
- Kill plot (surface stack): drill pipe AND annulus/casing on the same x-y chart whenever the
  drill pipe can be read. NEVER plot 0 unless the gauge reads 0 psi (user rule, v1.1 session):
  pipe out of hole = no DP line, label "pipe out of hole"; off bottom with a float = no DP
  line, label "no reading - float"; off bottom, no float = DP dashed grey, label "not a BHP
  indicator" (gas below the bit).
- Gas: a SINGLE-BUBBLE gas model (user choice) forecasts the casing line while gas is in the
  annulus. Influx = one bubble at the bit, volume = PIT GAIN (new input); moved up with the
  mud stroke by stroke; Boyle's law P1V1 = P2V2 (IADC #32) at constant BHP; casing =
  BHP - hydrostatic of everything in the annulus (mud, gas, kill mud). State its limits on the
  sheet: ignores temperature, Z, dispersion/slip; NOT valid in oil-based mud; usually
  over-predicts the peak (errs safe). Applies to W&W and later subsea too.
  - Influx gradient FROM THE GAUGES (user): height = pit gain / bottom annulus capacity
    (whole ft); gradient = OMW gradient - (SICP - SIDPP) / height (4 places). Above 0.25
    psi/ft WARN: "Influx gradient suggests liquid, not gas. The plot assumes an expanding gas
    bubble, so casing and shoe peaks are overstated (conservative)." If the gradient is <= 0 or >= the mud gradient,
    DON'T use it: fall back to 0.1 psi/ft and WARN that the gauges are inconsistent (bad
    gauges, or the influx isn't at the bottom).
  - Gas pressure at the TOP of the bubble (user: conservative - more expansion, higher
    casing); gas gradient scales with pressure (gradient x P / P at shut-in); iterate since
    the height depends on the volume.
  - Track MAX SHOE PRESSURE across the WHOLE kill (shoe = casing + hydrostatic above the shoe)
    and report the strokes where it occurs - it is NOT always at top of gas at the shoe
    (W&W baseline: max at 1,616 stk, just before kill mud enters the annulus). Check vs
    fracture. Casing over MAASP after gas passes the shoe: say the shoe is the real check.
  - Don't hard-code curve shapes (e.g. the W&W casing dip) - let the model produce them.
  - Forecast pressures ONLY: ACADEMIC rounding (rule 3), depths to whole ft, round once at the
    end. This does NOT change the three rules: KMW still always rounds UP (rule 1), maximums
    still round DOWN (rule 2).
  - Hand example (user-approved), baseline well, pit gain 10 bbl, SF 50: gradient 0.1048,
    height 344 ft, BHP 6,919. Driller's 1st circ: peak casing 1,272 at 4,097 stk (pit gain
    53.6), max shoe 3,681 at 2,240 stk, ends 700. Driller's 2nd circ: casing held 700, DP
    falls 1,450 -> 947 / 901 at the crossovers -> 871 with kill mud at the bit, held 871 to
    surface; trapped 42. Frac 3,909.
    W&W (user-approved v1.1 values; BHP back-calculated from the scheduled DP each stroke,
    ends 6,927 = 6,919 + 8 rounding overbalance): peak casing 1,048 at 4,000 stk (65.1 bbl),
    max shoe 3,648 at 1,618 stk (flat top 3,647-3,648 from ~1,601 to 1,631), casing 806 at
    top of gas at the shoe (2,243 stk), 862 kill mud at the bit, 273 gas out, 50 kill mud at
    surface = trapped (SF). Superseded W&W values (before the fix): 1,044 / 3,640 / 42.
    Module (`kill_plot.py`) strokes move by 1-2 from the hand example because the pumped
    volume is rounded to 0.1 bbl (Driller's peak 4,097 stk, max shoe 2,241).
  - Casing never forecast below 0: if BHP - annulus hydrostatic < 0 the choke is fully open,
    casing = 0 and BHP = annulus hydrostatic (Driller's SF 0: casing 0 at ~10,687 stk, DP
    rises 821 -> 829 at surface).
  - Geometry: the bottom of the gas and the kill mud front move with ROUNDED section volumes
    (so they pass crossovers on crossover strokes); the gas column uses the CAPACITY
    (height = volume / capacity, like the influx height on the kill sheet).
  - DEVIATED / HORIZONTAL (user-approved v1.2): POSITION by MD, PRESSURE by TVD (hydrostatic =
    gradient x TVD height). Influx gradient = mud gradient - (SICP - SIDPP) / TVD HEIGHT of the
    influx (deviated example: 344 ft MD = 298 ft TVD). Driller's 2nd circ DP and W&W BHP: kill mud
    hydrostatic gain by TVD, friction by MD (the W&W schedule already does this).
  - Horizontal, influx in the lateral (TVD height 0): no change in casing until the gas reaches
    the build (user). Gradient 0.1 psi/ft assumed; note (user wording): "Influx in the lateral:
    gas gradient 0.1 psi/ft assumed (can't be read from the gauges; conservative, over-predicts
    casing and shoe pressure)." If SICP - SIDPP > 10 the forecast is INVALID: warning (user
    wording, kill_plot.lateral_gauge_warning) on sheet AND plot, casing line NOT drawn, peak/shoe
    checks dropped - "Use the drill pipe schedule only." Event "top of gas leaves the lateral".
  - Gradient below 0.05 psi/ft: used, with the warning "Influx gradient below 0.05 psi/ft is not
    physical. Check SICP/SIDPP and the influx volume." (0 or less / >= mud: 0.1 fallback, as before.)
  - Peak casing above MAASP with the gas ABOVE the shoe: "This is NOT a shoe exceedance: MAASP
    assumes mud from the shoe to surface. The shoe limit is the max shoe pressure." With the gas
    still BELOW the shoe: "WARNING ... the shoe is at risk".
  - W&W kill mud rounding (user): keep the schedule (crews' hand sheets must match). ALWAYS print
    "Kill mud rounding (11.706 -> 11.8 ppg) adds 47 psi to BHP during the step-down." (= overbalance
    - SIDPP). Warn when the W&W shoe margin (fracture - max shoe) is less than Driller's on the same
    well and gauges: "W&W shoe margin 48 psi is less than Driller's 96 psi because of kill mud
    rounding. Consider a smaller SF, a finer KMW rounding, or Driller's method." NO fixed margin
    threshold (user: not for now).
  - Example gauges fixed (user): deviated wells SICP 780 (650 + (0.5408 - 0.1) x 298 = 781; the
    800 copied from the vertical well gave 0.0374 psi/ft); horizontal wells SICP = SIDPP = 650.
  - Approved hand examples (10 bbl, SF 50): deviated Driller's peak 1,272 at ~4,579 stk (53.7 bbl),
    max shoe 3,656 at ~2,616, trapped 42; deviated W&W peak 1,054 at ~4,484, max shoe 3,624 at
    ~1,795, trapped 50. Horizontal Driller's casing flat 700 to ~1,792 stk, peak 1,211 at ~5,601
    (48.0 bbl), shoe 5,877 the whole kill (shoe at the heel = BHP), DP 854, trapped 3; horizontal
    W&W step-down 900 KOP / 868 heel / 901 bit (+SF), casing 700 -> 747 while gas in the lateral
    (rounding 47 psi), peak 1,080 at ~5,551, max shoe 5,925 (margin 48 vs Driller's 96), trapped
    50. Vertical tapered (0.2583, "suggests liquid"): max shoe 5,988 at start-up (fracture 6,026),
    peak 1,888 (Driller's) / 1,865 (W&W) above MAASP 889 with the gas above the shoe.
  - tests/reference_model.py: an INDEPENDENT second calculation (never imports kill_plot.py);
    tests/test_kill_plot_reference.py requires every plotted point, peak, max shoe and end casing
    to match it exactly on all 12 Driller's/W&W examples. Keep it independent.
- Print: page 1 = well schematic (casing, shoe, open hole, string sections/crossovers, bit,
  KOP/EOB/heel) with KMW, ICP, FCP, MAMW, MAASP (original/after kill), volumes in bbl AND
  strokes. Page 2 = the table WITH an "Actual" column for observed values, plus the plot.
- Plan: plot/table numbers computed in a new TESTED Python module; the page only draws them
  (plain SVG, no plotting library). Dropdown of the example wells; all inputs editable.

Constant BHP start-up with a SAFETY MARGIN (SF, team input), every method (user):
- Casing rises SICP -> SICP + SF and, through the U-tube, drill pipe rises SIDPP -> SIDPP + SF.
  Pump brought up holding casing at SICP + SF; once at kill rate and stable, swap to the drill
  pipe gauge, which now reads ICP + SF. BHP = formation pressure + SF the whole kill.
- SF is CARRIED THROUGH the kill: FCP + SF, step-down chart + SF, 2nd circulation casing held
  at SIDPP + SF. At final shut-in BOTH gauges must read the same trapped pressure - show it as
  a check; if they don't match, something is wrong. Then (always in the step list, user rule
  v1.1): "if any pressure on either gauge, bleed through the choke in small increments; record
  volume bled; more than a few gallons or pressure building back = well not dead", the
  0 +/-10 psi dead-well check and a FLOW CHECK (`kill_steps.final_shut_in_steps`).
- SF is a REQUIRED input (no default). SF 0 tests are the regression baseline; hand examples
  use SF 50.
- KWM rounded UP overbalances by more than SIDPP: OB = (KMW - OMW) x 0.052 x TVD (academic,
  `formulas.kill_mud_overbalance`; baseline 658 vs SIDPP 650). TRAPPED PRESSURE IS
  METHOD-SPECIFIC, clamped >= 0 (user-approved v1.1):
  - Driller's: SIDPP + SF - OB (baseline 42; SF 0 -> 0).
  - W&W: SF + (FCP used - actual friction with kill mud) (baseline 50 = SF; high-ICP case:
    retaken SIDPP 680, reading 1,470, SF 50 -> friction 818, trapped 61).
- Driller's 1st circ: hold DP at ICP + SF until the gas is out (check: both gauges read
  SIDPP + SF); casing rises as gas comes up, peaks with gas at surface, then falls to
  SIDPP + SF. 2nd circ: casing held at SIDPP + SF until KWM at the bit, then DP held at its
  reading with KWM at the bit = FCP + SIDPP + SF - OB (baseline 871, NOT FCP + SF = 879;
  SF 0 -> 821; horizontal wells OB 697 -> 804 at SF 0, 854 at SF 50) until KWM at surface.
  If SIDPP + SF < OB the step note says: "If casing reaches 0 with the choke fully open, drill
  pipe will rise toward FCP (829 here). Expected; BHP ends slightly over formation pressure.
  Continue to surface."
- W&W (engineer's method): from the first stroke KWM goes down the DP while influx + OMW come
  up the annulus. Casing held + SF on start-up/shut-down; ICP check vs ICP + SF (high: actual
  SCR = reading - SF - retaken SIDPP); at rate, DP follows the step-down chart (+ SF) until
  KWM is at the bit, then FCP + SF until KWM is at surface.
- Scope: surface stack only. Subsea choke line friction is a separate change.

Volumetric / L&B plot (user): x-axis = bbl bled / pumped; casing = hold pressures.
- Pipe on bottom, NO float: DP readable -> the sheet says "DP readable - use drill pipe
  pressure method" (bleed holding SIDPP + margin constant). If plotted for illustration: DP
  rises by Pw each build and falls by Pw each bleed (casing flat) - a saw-tooth mirroring BHP.
- Pipe on bottom WITH a float: only casing rises (by SF + Pw, agreed before starting); DP flat.
- Off bottom / out of hole: see the "never plot 0" labels above.
- AS BUILT (user-approved v1.3): two charts. Volumetric = casing vs TOTAL BBL BLED (staircase: flat
  while bleeding at the HOLD TO USE, up while waiting; the standard hold dashed underneath; ends at
  the SICP read with gas at surface). Lubricate and bleed = CASING ONLY vs TOTAL BBL PUMPED (up to pump-to as bbl go in,
  straight down to bleed-to). Points come straight from the approved tables - no new calculation.
- New volumetric inputs: pipe_bottom_md_ft (blank = out of the hole, TD = on bottom, shallower = off
  bottom), float_in_string, sidpp_psi (needed only on bottom with no float). Every volumetric example
  with pipe in the hole has a float (user) - except the NO-float example. Drill pipe line ONLY on bottom
  with no float: DP = SIDPP + (forecast BHP - Pf), and the sheet says "DP readable - use drill pipe
  pressure method (bleed holding SIDPP + safety margin constant). Drill pipe pressure method valid only
  if the string is open. If the string or bit is plugged, the drill pipe gauge is not a BHP indicator.
  Use volumetric on casing." On bottom WITH a float:
  NO line, "no reading - float" (user). Off bottom: float -> "no reading - float"; no float -> "not a
  BHP indicator - gas may enter the string" (label, no line - a predicted line would be a guess). Out of the hole -> "pipe out of hole". The printed sheet gets one
  line saying where the pipe is. Volumetric schematic: TD at the bottom, the pipe to its depth (or
  "no pipe"), drawn straight to scale by MD.

DONE: `kill_plot.py` + `tests/test_kill_plot.py` - Driller's and W&W, VERTICAL wells only
(untapered/tapered). Tests: pressures exact, stroke of each maximum within a window
(+/-30 for the W&W shoe plateau) - exact-stroke asserts break on harmless rounding.
DONE: SF / trapped-pressure bleed / flow check in the Driller's and W&W step lists, plus the
kill_plot W&W BHP fix and the casing-at-0 clamp (exact-value tests: 871/42, 879/50, 821/0,
829/0, SF < OB clamp, high-ICP W&W 61).
DONE: the web page (v1.1.0), the deviated/horizontal kill plot (v1.2.0), and the volumetric plot
+ volumetric schematic (v1.3, see "Volumetric / L&B plot").
DONE: bullhead and reverse circulation on the web page (v1.4, tables only - user: no bullhead plot).
NEXT: the subsea stack - ask before starting.

Web page sub-phases (user-approved; stop after each). DONE: W1-W5, released v1.1.0. W1 plumbing - Pyodide page, Pages
workflow, baseline Driller's table (`web/app.py`, tested in tests/test_web_app.py).
W2 example wells as a tested data module + dropdown + editable inputs + tables with an
"Actual" column (Driller's, W&W, volumetric + L&B). W3 kill plot SVG - VERTICAL wells only
(user OK); others say "plot coming in a later release". W3 as built: optional input
`pit_gain_bbl` on kill_sheet() (no pit gain = no plot); sheet["plot"] from kill_plot.py;
the 12 Driller's/W&W examples carry pit_gain_bbl=10 (not printed - printed output unchanged).
The vertical TAPERED example at 10 bbl gives the "suggests liquid" warning (0.2583 psi/ft) -
the tapered plot has no hand example yet. W4 as built: kill_sheet() adds "volumes" (surface lines and
drill string if lines given, surface to bit, open hole, cased hole, total annulus, total well system;
volume = sum of rounded sections, strokes = volume / pump - total well system too (user: "can't
have .6 of a stroke": 723.6 / 0.117 = 6,185, not 1,627 + 4,557 = 6,184)) and "schematic" (section top/bottom MD).
Schematic drawn straight, to scale by MD (not the well path); points at the same MD share a label.
Volumetric sheets have no schematic yet. W5 as built: print layout (page 1 schematic, numbers,
volumes, depths, entered data; page 2 plot + kill steps with Actual; W&W vertical spills its
step-down schedule onto page 3), Print button, #well_id links, README link and v1.1.0 tag.
v1.2 web: Pyodide runs in a module Web Worker (web/worker.js) so the page never freezes; the
slowest sheet (horizontal W&W, ~22,000 forecast strokes incl. the Driller's comparison) takes ~3 s.

## Git / GitHub

- Repo: https://github.com/kirk-keel/kill-sheet-calculations (public, GitHub account `kirk-keel`)
- Default branch: `main`. Commit at the end of each phase once the user approves.
- License: MIT (`LICENSE`), copyright Kirk Keel.
- CI: `.github/workflows/tests.yml` runs pytest and every `examples/*_well.py` on Python
  3.10–3.14 on every push and PR (3.14 = Pyodide v314.0.7, the browser's Python).
- Web page: `.github/workflows/pages.yml` runs after Tests passes on a push to main
  (workflow_run), builds `web/` with `web/build_site.py` into `_site/` (index.html, app.py,
  killsheet.zip of src/killsheet) and publishes it to GitHub Pages.
- Release tags: v0.1, v0.1.1, v0.2 ... v0.19, v1.0.0 (surface stack complete), v1.1.0 (SF +
  web page), v1.2.0 (deviated/horizontal kill plot), v1.3.0 (volumetric forecast), v1.4.0
  (bullhead and reverse circulation on the web page). Minor
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
python web/build_site.py               # build the web page into _site/
python -m http.server --directory _site   # try it at http://localhost:8000
```

Examples: `examples/kill_sheet_printer.py` holds the shared printing code; each
example file is just the well data: `WELL = dict(...)`, printed under
`if __name__ == "__main__":`. The web page reads the same WELL data (web/app.py
EXAMPLE_WELLS lists all 36 example wells in the dropdown; FORMS
lists every input). After any printer/sheet change, every example's output must be
byte-identical unless the user approved the change. Sections in the examples are
`(name, capacity, length)`; the name is for printing only.
If you change an example well or the output format, update the "Example output"
section of README.md to match.
