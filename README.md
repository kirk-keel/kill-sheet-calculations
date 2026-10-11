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
bleed, **version 0.10** extends them to tapered strings, **version 0.11** to deviated
and horizontal wells, and **version 0.12** completes them on a surface stack for every
well and string type. **Version 0.13** adds bullheading while drilling, **version
0.14** extends it to tapered strings, **version 0.15** to deviated and horizontal
wells, and **version 0.16** completes bullheading on a surface stack for every well and
string type. **Version 0.17** adds the reverse circulation kill for completion, workover
and intervention (CWI) wells, **version 0.18** extends it to tapered tubing, **version
0.19** to deviated and horizontal completions, and **version 1.0** to deviated and
horizontal completions with tapered tubing.

**Version 1.0 completes the surface BOP stack:** all five methods - Driller's, Wait and
Weight, volumetric and lubricate and bleed, bullheading, and reverse circulation - for
vertical, deviated and horizontal wells with untapered and tapered strings. See the
[roadmap](#roadmap).

**Version 1.1 adds the safety margin and the web page.** Every Driller's and Wait and
Weight kill now carries the team's safety margin (SF) from start-up to shut-in, checks the
trapped pressure, bleeds it off and flow checks. The calculator also runs in your browser:

### **[Open the web page](https://kirk-keel.github.io/kill-sheet-calculations/)**

- Pick one of 24 example wells (Driller's, Wait and Weight, volumetric and lubricate and
  bleed - vertical, deviated and horizontal, untapered and tapered) and change any input.
  The sheet recalculates as you type.
- Page 1: well schematic, kill mud weight, ICP, FCP, MAMW, MAASP, volumes in bbl and strokes.
- Page 2: the kill plot (forecast drill pipe and casing pressure, vertical wells) and the
  kill steps and schedules, with an **Actual** column to record the gauge readings.
- **Print kill sheet** prints it on paper. A link like
  `.../kill-sheet-calculations/#wait_and_weight_well` opens a chosen well.
- Nothing is sent anywhere: the page runs this project's own tested Python code
  in your browser (Pyodide). The first load takes a few seconds.

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
- **Bullheading (drilling):** annular shut, kill fluid down the string and the backside
  at the same rate; a max-pressure chart for each side (formation limit from the LOT,
  capped by the lowest equipment rating or test), with columns for the actual pressures
- **Reverse circulation (CWI wells):** kill weight fluid down the annulus through an opened
  SSD or tubing punch and up the tubing; kill weight balanced at the perfs with formation
  fluid left below the SSD, the annulus pump-pressure schedule from the observed ICP to FCP,
  both annulus limits, and an optional bullhead of the volume below the SSD

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
python examples/volumetric_pipe_on_bottom_no_float_well.py   # pipe on bottom, no float (SIDPP read)
python examples/volumetric_tapered_shoe_at_risk_well.py      # tapered, 10 bbl: shoe at risk at shut-in
python examples/volumetric_pipe_above_influx_well.py   # volumetric + L&B, pipe above the influx
python examples/volumetric_pipe_out_of_hole_well.py    # volumetric + L&B, pipe out of the hole
python examples/volumetric_tapered_pipe_on_bottom_well.py      # tapered string versions of the three
python examples/volumetric_tapered_pipe_above_influx_well.py
python examples/volumetric_tapered_pipe_out_of_hole_well.py
python examples/volumetric_deviated_well.py     # volumetric + L&B, deviated, pipe on bottom
python examples/volumetric_horizontal_well.py   # volumetric + L&B, horizontal, pipe on bottom
python examples/volumetric_deviated_tapered_well.py     # deviated, tapered string
python examples/volumetric_horizontal_tapered_well.py   # horizontal, tapered string
python examples/bullhead_well.py                # bullhead, vertical, untapered string
python examples/bullhead_tapered_well.py        # bullhead, vertical, tapered string
python examples/bullhead_deviated_well.py       # bullhead, deviated, untapered string
python examples/bullhead_horizontal_well.py     # bullhead, horizontal, untapered string
python examples/bullhead_deviated_tapered_well.py     # bullhead, deviated, tapered string
python examples/bullhead_horizontal_tapered_well.py   # bullhead, horizontal, tapered string
python examples/reverse_circulation_well.py     # reverse circulation, CWI well
python examples/reverse_circulation_tapered_well.py   # reverse circulation, tapered tubing
python examples/reverse_circulation_deviated_well.py     # reverse circulation, deviated CWI well
python examples/reverse_circulation_horizontal_well.py   # reverse circulation, horizontal CWI well
python examples/reverse_circulation_deviated_tapered_well.py     # deviated CWI well, tapered tubing
python examples/reverse_circulation_horizontal_tapered_well.py   # horizontal CWI well, tapered tubing
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

### Safety margin, trapped pressure, bleed-off and flow check

Every kill holds a **safety margin (SF)** on bottom, chosen by the team. On start-up the
casing is held at SICP + SF, so the drill pipe reads ICP + SF at kill rate, and the SF is
carried through the whole kill. At the final shut-in both gauges must read the same
**trapped pressure** (if they don't, something is wrong). Then: if there is any pressure
on either gauge, bleed it off through the choke in small increments, shutting in between,
and record the volume bled. More than a few gallons, or pressure building back, means the
well is not dead. Then check both gauges read 0 psi (±10) and **flow check**.

Kill mud is rounded UP, so a full column of it adds a little **more** than SIDPP:
on the baseline well (11.5 - 10.4) x 0.052 x 11,500 = 658 psi, 8 psi more than SIDPP 650.
That is why the trapped pressure isn't simply the SF, and why it differs by method.

### Driller's method

A constant bottomhole pressure kill in two circulations. Both circulations use the
same **start-up** (bring the pump to kill rate holding casing pressure constant) and
**shut-down** (slow the pump to 0 holding casing pressure constant). The pressures
only tell the truth if that procedure is followed.

| Circulation | Mud | Hold | For |
|---|---|---|---|
| 1st | Original | Casing at **SICP + SF** on start-up, then drill pipe at **ICP + SF** | **Minimum** one bottoms up, until the gas is out |
| 2nd | Kill | Casing **constant** at **SIDPP + SF** | Surface-to-bit strokes |
| 2nd | Kill | Drill pipe at its **reading with kill mud at the bit** = FCP + SIDPP + SF - kill mud overbalance (871 psi on the baseline, not FCP + SF = 879) | Bit-to-surface strokes |

**Shut-in checks** (gauges within ±10 psi):

- After the 1st circulation, SIDPP and SICP must both read **SIDPP + SF**.
  If SICP is higher, strung-out gas is still in the annulus, so continue circulating.
- After the 2nd circulation, both read the **trapped pressure** = SIDPP + SF - kill mud
  overbalance (650 + 50 - 658 = 42 psi), never below 0. Bleed it off, check 0 psi
  (the well is dead), flow check.

If the SF is smaller than the kill mud's extra overbalance (SF 0 on the baseline), the
casing reaches 0 with the choke fully open before kill mud reaches surface, and the drill
pipe rises toward FCP. That is expected: BHP ends slightly over formation pressure.

### Wait and Weight

One circulation, with kill mud. Same start-up and shut-down as the Driller's method.

| Stage | Gauge | Hold | For |
|---|---|---|---|
| Weight up | Pits | Weight up the active system to KMW; **retake SIDPP (bump the float) and SICP** just before start-up (gas may have migrated) | — |
| Start-up | Casing | Constant at the **retaken SICP + SF** while bringing the pump to kill rate | — |
| ICP check | Drill pipe | Must read **ICP + SF** ±10 psi. More than 10 psi **high**: **recalculate** ICP, FCP and the schedule from the reading (actual SCR = reading - SF - retaken SIDPP); FCP is **never lower** than calculated. More than 10 psi **low**: a complication, so the calculated values are kept | — |
| Hold | Drill pipe | **Step-down schedule + SF** from ICP + SF to FCP + SF, following the depth of the kill mud | Surface-to-bit strokes |
| Hold | Drill pipe | **FCP + SF** | Bit-to-surface strokes |
| Shut-down / check | Both | Both read the **trapped pressure** = SF (50 psi on the baseline). Bleed it off, check **0 psi** (±10 psi): the well is dead. Flow check | — |

The step-down chart takes off SIDPP, but the kill mud adds the full overbalance (8 psi
more on the baseline), so BHP ends 8 psi above formation pressure + SF and the trapped
pressure is the SF itself. After a high-ICP recalculation that kept the calculated FCP,
the trapped pressure is SF + (FCP - actual friction with kill mud).

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
| Lubricate and bleed | Pump mud until casing rises by the working pressure; read the bbl pumped; let it lubricate; bleed back to the starting pressure minus `bbl x mud gradient / annular capacity at surface`; repeat until the bbl lubricated **equal the gas volume at surface** |

**Version 1.3 adds a single-bubble forecast** (`volumetric_model.py`), worked through
cycle by cycle with the well control specialist. It needs the **pit gain** (and SIDPP if
it can be read - otherwise formation pressure is *estimated* from SICP, and the sheet
says so):

- **Where the gas is:** Boyle's law at the top of the bubble - its pressure is
  `P0 x pit gain / (pit gain + bbl bled)` - and the casing pressure place it. Positions
  by MD, pressures by TVD.
- **Bleed per cycle** is sized on the **annulus the gas is in** - the smallest annulus it
  touches anywhere on its way through the bleed, so any error is an under-bleed, never an
  over-bleed. A table shows the bbl per cycle for each annulus. (Smallest, average and
  longest annulus are still selectable.)
- **Hold to use** is printed beside the **standard** IADC hold (SICP + SF + n x Pw). It is
  raised - never lowered - when the gas will gain vertical height (a narrower annulus or
  the build), which would otherwise pull bottomhole pressure below Pf + SF.
- **Every hold is checked against fracture at the shoe.** If the shoe limits it, the sheet
  says the safety margin is reduced; if even that leaves bottomhole pressure below Pf, it
  prints a **SUPERVISOR DECISION** with both holds and both consequences.
- A **pre-check** warns when SF + Pw is more than the shoe margin at shut-in.
- **Above MAASP** depends on the gas: below the shoe it is a warning (shoe overpressured);
  above the shoe MAASP no longer applies. The plot's MAASP line stops where the gas passes
  the shoe.
- The **readings still drive the table**; the sheet warns when the gas reaches surface more
  than 20% earlier or later than the forecast.
- **Lubricate and bleed stops at the gas volume at surface** and says what is left: the
  remaining underbalance (do not bleed casing below it + SF - a kill is still required),
  or, for a swabbed kick, "hydrostatic control regained" with the casing left as trapped
  pressure.
- Both the bleed volume and the psi bled are **limits**, so both are rounded **down**.
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
  volumetric cycle, and the bbl pumped each lubricate cycle. The forecast is a single-bubble
  model: real gas usually arrives earlier (it disperses, or breaks out of solution in
  oil-based mud).
- IADC gives the volumetric formulas (#34, #35). There is no dedicated IADC lubricate and
  bleed formula; it is built from the IADC basics (#12 height of fluid, #13/#14 hydrostatic).

### Bullheading (drilling)

When the kick is too large to handle at surface, the annular is shut and kill fluid is
pumped down the **drill string and the backside at the same rate, at the same time**, to
push the influx back where it came from. Pressure builds until **injectivity** is
established, then falls as the fluid is pushed away. The goal is injectivity, **not
breaking down the formation**.

| Item | Rule |
|---|---|
| Kill fluid | Kill mud weight - rounded **up** to the next 0.1 ppg, even if exact |
| Formation limit | From the LOT / MAMW at the shoe |
| Equipment limit | The **lowest** rating or tested value of the equipment |
| Max on each row | The lower of the two, rounded **down** |
| Annulus max | `0.052 x [MAMW x shoe TVD - weight of fluid above the shoe x TVD]` |
| String max | `0.052 x [MAMW x shoe TVD - string fluid x TVD to bit + annulus fluid x TVD shoe to bit]` |
| Minimum rate | Gas migration (IADC #34) and IADC #13 with the largest annulus, rounded **up** |

- The influx is treated as original mud - gas is lighter, so the real limits are higher.
- **The string limit depends on both columns.** The shoe is on the annulus side; the
  string reaches it via the bit and the annulus below the shoe. Pumping the same rate down
  both sides, the string reaches the bit first, and its limit falls to **466 psi** on the
  baseline well (string full of kill fluid, open hole still original mud) before climbing
  back to 830 as kill fluid fills the annulus below the shoe.
- The chart steps are 10 steps of the annulus strokes (the longer side), plus a row at every
  string crossover, kill fluid at the bit, kill fluid at the shoe, the kill point and
  overdisplacement (the team's choice).
- The IADC WellCAP Bullhead Worksheet is written for completions (tubing to perforations);
  this is the drilling version, using the same ideas.
- On the tapered example (MAASP 889) the tight 5" DP x 7" casing annulus moves kill fluid
  down faster than the string at first, so the annulus limit falls first; the string
  limit then falls to **231 psi** once it reaches the bit through the 3-1/2" pipe.
- **Deviated and horizontal wells:** every column uses TVD, and the chart adds a row when
  kill fluid passes each key point (KOP, end of build, heel) on each side, showing MD and
  TVD. On the horizontal example (shoe at the heel) the string limit drops to its final
  **99 psi** as soon as kill fluid reaches the heel: the flat lateral adds no hydrostatic,
  and with no open hole below the shoe nothing pushes back on it from below.
- Named points (crossovers, key points, the shoe) are shown at their exact depth.
- **Tapered strings** change *when* kill fluid reaches each point (the strokes), not the
  limit at that point: on the deviated example the string still bottoms out at 466 psi,
  but at 1,603 strokes instead of 1,812.

### Reverse circulation (completion, workover, intervention)

Kill weight fluid is pumped down the tubing x casing **annulus** (the pump side), through an
opened **SSD** or a hole punched in the tubing above the production packer, and back up the
**tubing** (the return side, through the choke). The SSD plays the part of the bit - **the
sides are swapped** from a drilling kill. There is no dedicated IADC reverse circulation
worksheet; this is built from the IADC basics.

| Item | Rule |
|---|---|
| Tubing fluid gradient | `(Formation pressure - SITP) / Mid-perf TVD` |
| Pressure at the SSD | `Formation pressure - tubing gradient x (Mid-perf TVD - SSD TVD)` - formation fluid stays below the SSD |
| Kill weight fluid | `Pressure at SSD / (0.052 x SSD TVD) + margin (default 0)`, rounded **up** to the next 0.1 ppg |
| Before start-up | Open the SSD, let pressures stabilise, record SITP and SICP. SICP isn't known until then: `Pressure at SSD - annulus hydrostatic` |
| Start-up | Bring the pump up on the **annulus** holding **tubing** pressure (the choke side) at the SITP |
| ICP | **Observed** - the annulus pressure read at kill rate. No SCR: on a CWI well circulating *is* the kill |
| FCP | `Observed ICP - (KWF - packer fluid) x 0.052 x SSD TVD`, drop rounded down; at or below 0 it is floored at 0 with a warning |
| Schedule | Annulus pump pressure steps down from ICP to FCP as kill fluid reaches the SSD (TVD), then holds FCP while the tubing is displaced (MD for volumes) |
| Limits | Lower of fracture pressure at the **top perf** minus annulus hydrostatic, and the lowest-rated completion or surface equipment - shown with packer fluid and with kill fluid in the annulus |
| End | Shut down holding tubing; both gauges 0 ±10 psi; **flow check** |
| Optional | Bullhead the volume below the SSD (tubing to the packer + casing to the top perf) |

> In reverse circulation, the high-friction path is the return side. If the choke is wide
> open and pump pressure still climbs above FCP, BHP is rising. Reduce the rate.

Holding pump pressure constant keeps bottom hole pressure constant however much tubing
friction there is, because the choke absorbs it.

**Tapered tubing** changes the annulus size, so the schedule gets a row at every annulus
crossover. On the example (3-1/2" over 2-7/8") the pump pressure drops about 84 psi per step
in the tighter 3-1/2" x 5-1/2" annulus and about 63 below the crossover; the pressures at
the SSD, FCP and the limits don't change.

**Deviated and horizontal completions:** pressures use TVD and volumes use MD, so the
step-down follows the TVD of the kill fluid. On a horizontal well with the SSD above KOP and
the perforations in the lateral, the **heel TVD** is used for the top and mid perf (the
lateral is flat). Because the SSD is well above the perfs, kill weight is heavier (10.8 ppg
on the example, against 9.9 on the deviated well) and the volume below the SSD is much
larger (38.6 bbl against 3.8), so the optional bullhead matters more. The observed ICP has
to be above the SICP once the SSD is open.

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

Safety margin (SF)                 50 psi

Driller's method
  1st circulation (original mud)
    start-up   casing 850 psi
               bring pump to kill rate holding casing pressure constant at SICP + SF
    hold       drill pipe 1,450 psi for 4,557 stks
               ICP + SF; minimum - one bottoms up; continue until the gas is out
    shut-down  casing
               slow pump to 0 holding casing pressure constant
    check      drill pipe and casing 700 psi
               both must read SIDPP + SF (+/-10 psi); if SICP is higher, gas is still in the annulus - continue circulating
  2nd circulation (kill mud)
    start-up   casing 700 psi
               bring pump to kill rate holding casing pressure constant at SIDPP + SF
    hold       casing 700 psi for 1,627 stks
               kill mud surface to bit; drill pipe falls from 1,450 to 871 psi
    hold       drill pipe 871 psi for 4,557 stks
               kill mud bit to surface - hold the drill pipe reading with kill mud at the bit
    shut-down  casing
               slow pump to 0 holding casing pressure constant (expect 42 psi)
    check      drill pipe and casing 42 psi
               both must read the same trapped pressure (+/-10 psi); if they don't match, something is wrong
    bleed      choke
               if any pressure on either gauge, bleed in small increments through the choke, shutting in between; record volume bled; more than a few gallons or pressure building back = well not dead
    check      drill pipe and casing 0 psi
               both must read 0 psi (+/-10 psi) - the well is dead
    flow check well
               flow check before opening the well
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
  Kill mud rounding (11.487 -> 11.5 ppg) adds 8 psi to BHP during the step-down.
  kill circulation (kill mud)
    weight up  pits
               weight up the active system to 11.5 ppg; retake SIDPP (bump the float) and SICP just before pump start-up
    start-up   casing 850 psi
               bring pump to kill rate holding casing pressure constant at the retaken SICP + SF
    check      drill pipe 1,450 psi
               at kill rate the drill pipe must read ICP + SF (+/-10 psi); if high, recalculate (FCP never lower); if low, a complication
    hold       drill pipe 1,450 psi for 1,627 stks
               follow the step-down schedule + SF from 1,450 to 879 psi - kill mud surface to bit
    hold       drill pipe 879 psi for 4,557 stks
               hold FCP + SF - kill mud bit to surface
    shut-down  casing
               slow pump to 0 holding casing pressure constant (expect 50 psi)
    check      drill pipe and casing 50 psi
               both must read the same trapped pressure (+/-10 psi); if they don't match, something is wrong
    bleed      choke
               if any pressure on either gauge, bleed in small increments through the choke, shutting in between; record volume bled; more than a few gallons or pressure building back = well not dead
    check      drill pipe and casing 0 psi
               both must read 0 psi (+/-10 psi) - the well is dead
    flow check well
               flow check before opening the well

  Drill pipe step-down schedule (10 steps) - pressure follows where the kill mud is
    Strokes    Kill mud MD ft   TVD ft      psi   psi + SF
          0                0        0    1,400     1,450
        163            1,073    1,073    1,347     1,397
        326            2,140    2,140    1,294     1,344
        489            3,213    3,213    1,241     1,291
        652            4,287    4,287    1,188     1,238
        815            5,360    5,360    1,134     1,184
        978            6,427    6,427    1,081     1,131
      1,141            7,500    7,500    1,028     1,078
      1,304            8,573    8,573      975     1,025
      1,467            9,640    9,640      922       972
      1,521           10,000   10,000      904       954   <- crossover
      1,588           10,900   10,900      859       909   <- crossover
      1,627           11,500   11,500      829       879   <- bit
```

Volumetric method and lubricate and bleed, from `python examples/volumetric_pipe_on_bottom_well.py`:

```
VOLUMETRIC - pipe on bottom, unable to pump (vertical, untapered)
====================================================
Mud gradient                   0.5408 psi/ft  (10.4 ppg)
Mud lubricated (L&B)           0.5980 psi/ft  (11.5 ppg)
MAASP                           1,124 psi
Fracture at the shoe            3,909 psi
Safety margin / working       100 / 50 psi  (team's choice)
Pit gain                           10 bbl  (influx 344 ft MD / 344 ft TVD, gas 0.1000 psi/ft)
Formation pressure (Pf)         6,868 psi  (estimated: assumes influx at bottom, 0.1 psi/ft, no migration before the SICP reading)
Pipe on bottom, float in the string: no drill pipe reading - casing only.

Annulus, bottom up                      Capacity  Length ft
  DC x 8-1/2" hole                       0.0291        600
  HWDP x 8-1/2" hole                     0.0459        900
  DP x 8-1/2" hole                       0.0459      4,850
  DP x 9-5/8" casing                     0.0489      5,150

Volume to bleed per 50 psi = (working pressure / mud gradient) x annular capacity
  annulus at the gas    (forecast)        see below  <- used
  smallest annulus      0.0291 bbl/ft    2.6 bbl
  average annulus       0.0464 bbl/ft    4.2 bbl
  longest annulus       0.0489 bbl/ft    4.5 bbl
  Bleed per cycle by annulus (the gas top's annulus, conservatively):
    Capacity bbl/ft  bbl per cycle  From cycle  bbl bled before
             0.0291            2.6           1              0.0
             0.0459            4.2           2              2.6
             0.0489            4.5           4             11.0

Volumetric method - casing held at the 'Hold to use' while bleeding
  Tier 0: standard hold, no correction. 1: raised for the gas gaining vertical height. 2: limited by the shoe, BHP still >= Pf + SF. 3: limited by the shoe, SF reduced. 4: supervisor decision.
  Cycle  Standard hold  Hold to use  Tier  Bleed bbl  Total bbl  15-min rise
      1            950          950     0        2.6        2.6       30 psi
      2          1,000        1,000     0        4.2        6.8       28 psi
      3          1,050        1,050     0        4.2       11.0       26 psi
      4          1,100        1,100     0        4.5       15.5       24 psi
      5          1,150        1,150     0        4.5       20.0       22 psi
          above MAASP, gas above shoe, MAASP no longer applies, continue
      6          1,200        1,200     0        4.5       24.5       20 psi
          above MAASP, gas above shoe, MAASP no longer applies, continue
      7          1,250        1,250     0        4.5       29.0       18 psi
          above MAASP, gas above shoe, MAASP no longer applies, continue
      8          1,300        1,300     0        4.5       33.5       16 psi
          above MAASP, gas above shoe, MAASP no longer applies, continue
      9          1,350        1,350     0        4.5       38.0       14 psi
          above MAASP, gas above shoe, MAASP no longer applies, continue
     10          1,400        1,400     0        0.8       38.8        0 psi  GAS AT SURFACE
          above MAASP, gas above shoe, MAASP no longer applies, continue
  Gas at surface: readings 38.8 bbl bled; forecast 38.8 bbl (cycle 10, during the bleed), casing 1,400 psi, gas 48.8 bbl

Lubricate and bleed - 11.5 ppg mud, annulus at surface 0.0489 bbl/ft
  hydrostatic added = bbl pumped x 0.5980 / 0.0489
  stop when the bbl lubricated = the gas volume at surface: 48.8 bbl (pit gain + bbl bled; forecast 48.8 bbl)
  Cycle  Pump to psi  bbl pumped  Hydrostatic psi  Bleed to psi
      1        1,450         1.7               20         1,380
      2        1,430         1.6               19         1,361
      3        1,411         1.6               19         1,342
      4        1,392         1.6               19         1,323
      5        1,373         1.5               18         1,305
    ... 79 cycles ...
     85          892         0.1                1           841
     86          891         0.1                1           840
     87          890         0.1                1           839
  87 cycles, 48.8 bbl lubricated
  Casing 839 psi. Remaining underbalance 592 psi. Do not bleed casing below 692 psi. Not dead. Kill required (strip to bottom and circulate, or bullhead).
```

Bullheading while drilling, from `python examples/bullhead_well.py`:

```
BULLHEAD - annular shut, down the string and the backside (vertical, untapered)
====================================================
Kill fluid density               11.5 ppg  (rounded UP to the next 0.1)
Max allowable mud weight         14.6 ppg  (formation limit, from the LOT)
Equipment limit                 3,000 psi  (9-5/8" casing, tested - lowest rating / test)

Drill string, surface to bit    190.4 bbl   1,627 stks
Annulus, surface to bottom      533.2 bbl   4,557 stks  (kill point)
Overdisplacement                 10.0 bbl  (team's choice)
String keeps pumping after kill fluid reaches the bit: 2,930 stks (342.8 bbl) out the bit by the kill point

Pump rate, SAME on both sides 3.0 bbl/min = 26 spm each side
Time to the kill point            175 min  (4,557 stks / 26 spm)
Gas migration                     185 ft/hr  (100 psi/hr / 0.5408 psi/ft)
Minimum rate to beat it             2 spm  (largest annulus 0.0489 bbl/ft, rounded UP)

Annular shut: pump kill fluid down the string AND the backside at the same rate.
Pressure builds until injectivity is established, then falls as fluid is pushed
away. The goal is injectivity, NOT breaking down the formation - stay below the
max on both sides. Max = lower of the formation limit and the equipment limit.

  Strokes  Kill fluid MD ft    String max  Annulus max   Actual string  Actual annulus
    (each)   string  annulus         psi          psi             psi             psi
        0        0        0       1,124        1,124   ____________    ____________
      456    3,000    1,092         953        1,062   ____________    ____________
      912    5,994    2,182         781          999   ____________    ____________
    1,368    8,994    3,274         610          937   ____________    ____________
    1,521   10,000    3,641         552          916   ____________    ____________  <- string crossover
    1,588   10,900    3,800         501          907   ____________    ____________  <- string crossover
    1,627   11,500    3,894         466          902   ____________    ____________  <- kill fluid at the bit (string)
    1,824   11,500    4,365         466          875   ____________    ____________
    2,152   11,500    5,150         466          830   ____________    ____________  <- kill fluid at the shoe (annulus)
    2,280   11,500    5,477         485          830   ____________    ____________
    2,736   11,500    6,638         552          830   ____________    ____________
    3,192   11,500    7,802         618          830   ____________    ____________
    3,648   11,500    8,963         685          830   ____________    ____________
    4,104   11,500   10,126         751          830   ____________    ____________
    4,557   11,500   11,500         830          830   ____________    ____________  <- kill fluid at bottom (annulus) - kill point
    4,642   11,500   11,500         830          830   ____________    ____________  <- overdisplaced
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
- [x] Deviated and horizontal, tapered string: all three situations (**v0.12**)

**Bullheading**
- [x] Vertical, untapered string (**v0.13**; kill fluid reaches the bit when strokes round down **v0.13.1**)
- [x] Vertical, tapered string (**v0.14**)
- [x] Deviated and horizontal, untapered string (**v0.15**)
- [x] Deviated and horizontal, tapered string (**v0.16**)

**Reverse circulation** (completion, workover, intervention wells)
- [x] Vertical, untapered string (**v0.17**)
- [x] Vertical, tapered string (**v0.18**)
- [x] Deviated and horizontal, untapered string (**v0.19**)
- [x] Deviated and horizontal, tapered string (**v1.0**) - **surface stack complete**

### Web page

- [x] Safety margin, trapped-pressure bleed-off and flow check in Driller's and Wait and
  Weight (**v1.1**)
- [x] [Web page](https://kirk-keel.github.io/kill-sheet-calculations/): Driller's, Wait and
  Weight, volumetric and lubricate and bleed, every well and string type, printable (**v1.1**)
- [x] Kill plot of forecast drill pipe and casing pressure, vertical wells (**v1.1**)
- [x] Kill plot for deviated and horizontal wells (**v1.2**)
- [x] Volumetric plot, and a schematic for volumetric sheets (**v1.3**)
- [ ] Bullheading and reverse circulation on the web page

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
  bullhead.py    bullheading while drilling: limits for each side, equipment limit, chart
  reverse_circulation.py  reverse circulation kill for CWI wells
  kill_plot.py   kill plot: forecast drill pipe and casing pressure (single-bubble gas model)
  kill_sheet.py  the whole kill sheet in one place - used by the printer and the web page
  volumetric_model.py  volumetric forecast: gas position, bleed at the gas, hold to use, shoe check
  volumetric_plot.py  volumetric and lubricate and bleed charts (pressure vs bbl)
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
  volumetric_pipe_on_bottom_no_float_well.py  pipe on bottom, no float (drill pipe readable)
  volumetric_tapered_shoe_at_risk_well.py     tapered, 10 bbl kick: pre-check, supervisor decision
  volumetric_pipe_above_influx_well.py   volumetric + L&B, pipe above the influx
  volumetric_pipe_out_of_hole_well.py    volumetric + L&B, pipe out of the hole
  volumetric_tapered_*_well.py           the same three situations, tapered string
  volumetric_deviated_well.py            volumetric + L&B, deviated, pipe on bottom
  volumetric_horizontal_well.py          volumetric + L&B, horizontal, pipe on bottom
  volumetric_deviated_tapered_well.py    deviated, tapered string
  volumetric_horizontal_tapered_well.py  horizontal, tapered string
  bullhead_well.py                       bullhead, vertical, untapered string
  bullhead_tapered_well.py               bullhead, vertical, tapered string
  bullhead_deviated_well.py              bullhead, deviated, untapered string
  bullhead_horizontal_well.py            bullhead, horizontal, untapered string
  bullhead_deviated_tapered_well.py      bullhead, deviated, tapered string
  bullhead_horizontal_tapered_well.py    bullhead, horizontal, tapered string
  reverse_circulation_well.py            reverse circulation, CWI well
  reverse_circulation_tapered_well.py    reverse circulation, tapered tubing
  reverse_circulation_deviated_well.py   reverse circulation, deviated CWI well
  reverse_circulation_horizontal_well.py reverse circulation, horizontal CWI well
  reverse_circulation_*_tapered_well.py  deviated / horizontal CWI wells, tapered tubing
  tapered_well.py        vertical, tapered string
  deviated_well.py       deviated, untapered string
  horizontal_well.py     horizontal, untapered string
  deviated_tapered_well.py     deviated, tapered string
  horizontal_tapered_well.py   horizontal, tapered string
  kill_sheet_printer.py  prints a kill sheet (shared by both examples)
web/
  index.html     the web page (draws the numbers, calculates nothing)
  app.py         runs the killsheet package in the browser (Pyodide); the example wells and inputs
  build_site.py  builds the page into _site/
.github/workflows/tests.yml   runs the tests on every push
.github/workflows/pages.yml   publishes the web page, only after the tests pass
```

## Testing

The tests and every example kill sheet run automatically on GitHub on every push,
on Python 3.10–3.14 (3.14 is the Python the web page runs in the browser). The badge at the top of this page shows whether they're passing.

## Disclaimer

This is a free planning and training aid. It is not a replacement for a
site-specific kill sheet, a well control program, or the judgment of the people
on location. See [LICENSE](LICENSE): the software is provided "as is", without
warranty of any kind.

## License

[MIT](LICENSE) © 2026 Kirk Keel
