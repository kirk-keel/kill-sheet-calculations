# Architecture & Technical Reference

## Overview

The `kill-sheet-calculations` repository implements a high-precision, production-grade petroleum engineering calculation framework. The codebase is organized into two decoupled engines tailored for distinct operational environments:

1. **The Core Well Control Engine (`src/killsheet/`):** A zero-dependency, pure Python 3.10+ package designed for real-time edge execution, command-line automation, and client-side browser deployment via WebAssembly (Pyodide in [`web/`](../web/)). It focuses on well control methods (Driller's Method, Wait & Weight, Volumetric, Lubricate & Bleed, Bullheading, and Reverse Circulation) across vertical, deviated, and horizontal trajectories with untapered and tapered strings.
2. **The 45-Module Petroleum Engineering & CWI Suite (`suite/`):** An automated generator built on `openpyxl` that builds [`petroleum_engineering_suite.xlsx`](../petroleum_engineering_suite.xlsx). It covers 26 Completion, Production & Well Intervention (CWI) modules and 19 Drilling & Well Control modules, featuring dynamic cell formulas, automated conditional formatting, and dual-unit US Oilfield ↔ SI Metric mirroring.

```
+-----------------------------------------------------------------------------------+
|                                 USER INTERFACES                                   |
|   +-----------------------+   +----------------------+   +--------------------+   |
|   |   Pyodide Web App     |   | CLI Scripts & Demos  |   | 46-Sheet Workbook  |   |
|   |  (web/app.py & HTML)  |   | (examples/*_well.py) |   |    (.xlsx File)    |   |
|   +-----------+-----------+   +----------+-----------+   +---------+----------+   |
+---------------|--------------------------|-------------------------|--------------+
                |                          |                         |
+---------------v--------------------------v-----------+   +---------v--------------+
|             SRC/KILLSHEET CORE ENGINE                |   |     SUITE GENERATOR    |
|  - rounding.py          (IADC WellSharp rules)       |   |  - builder.py (layout) |
|  - formulas.py          (KMW, ICP, FCP, MAASP, MAMW) |   |  - convert.py (SI)     |
|  - strokes.py           (volumes, strokes, xovers)   |   |  - style.py (themes)   |
|  - depths.py            (MD <-> TVD interpolation)   |   |                        |
|  - drillers.py          (1st & 2nd circulations)     |   | 45 Domain Worksheets:  |
|  - wait_and_weight.py   (retaken checks, schedule)   |   |  - CWI & Interventions |
|  - volumetric_model.py  (Boyle's law gas migration)  |   |  - Completions & Lift  |
|  - kill_plot.py         (DP & casing forecasts)      |   |  - Drilling & Well Ctrl|
|  - reverse_circulation.py (annular kill for CWI)     |   |  - Tubular & Library   |
|  - subsea.py            (CLF, dynamic MAASP, riser)  |   |                        |
|  - si.py                (dual-unit SI API wrapper)   |   |                        |
|  - tripping.py          (slugs, dry/wet pipe, drops) |   |                        |
|  - kick_tolerance.py    (gas height Hmax, KT volume) |   |                        |
|  - influx.py            (density, fluid ID, Z-factor)|   |                        |
|  - buckling.py          (Paslay-Dawson & Lubinski)   |   |                        |
|  - hydraulics.py        (TFA, nozzles, JIF, ECD)     |   |                        |
|  - gas_migration.py     (Harmathy slip, dP/dt, times)|   |                        |
|  - casing_design.py     (Barlow burst, derated coll) |   |                        |
|  - cementing.py         (balanced plug, U-tube spc)  |   |                        |
|  - simulator.py         (rig-floor console stepping) |   |                        |
|  - export.py            (JSON, CSV schedules, DDR MD)|   |                        |
+------------------------------------------------------+   +------------------------+
```

---

## Purpose & Engineering Doctrine

### 1. Zero Calculation Gaps & Explicit Physics
Well control decisions directly affect crew safety and well integrity. Consequently:
- **No approximations where exact math exists:** Kill mud weight is rounded up to the next 0.1 ppg (enforcing an explicit safety margin), while MAASP and MAMW are rounded down to avoid overestimating formation fracture limits.
- **TVD vs. MD Segregation:** Hydrostatic pressure calculations strictly use True Vertical Depth (TVD), whereas frictional pressure losses, tubular capacities, and fluid displacement volumes strictly use Measured Depth (MD).
- **Horizontal & Deviated Trajectory Physics:** In deviated and horizontal wells, Wait & Weight drill pipe step-down schedules do not follow a naive linear stroke ramp. Instead, drill pipe pressure follows the depth of the kill mud front: pressure bottoms out at the heel (where TVD stops changing) and climbs toward FCP through the lateral as frictional backpressure accumulates.
- **Single-Bubble Gas Migration Dynamics:** Volumetric gas migration ([`volumetric_model.py`](../src/killsheet/volumetric_model.py)) and kill forecasts ([`kill_plot.py`](../src/killsheet/kill_plot.py)) solve Boyle's law ($P_1 V_1 = P_2 V_2$) at the bubble top, calculate influx height dynamically based on local annular geometry, and track casing shoe pressure through four operational risk tiers.

### 2. Zero Runtime Dependencies for the Core Calculator
[`src/killsheet/`](../src/killsheet/) requires only standard Python libraries (`math`, `typing`, `functools`). This guarantees:
- Fast startup (<1 ms).
- Seamless compilation and execution inside WebAssembly / Pyodide without requiring binary packages.
- Safe execution in air-gapped rig-floor tablets or mission-critical servers.

---

## Data Flow Architecture

The data lifecycle through `src/killsheet/` and `suite/` follows a strict pipeline:

```
[Well Trajectory & Geometry]      [Shut-In Kick Telemetry]      [Mud & Rig Parameters]
  (MD/TVD Key Points, Shoes)         (SIDPP, SICP, Pit Gain)        (OMW, SCR, Pump Output)
               |                                |                              |
               +--------------------------------+------------------------------+
                                                |
                                                v
                              +-----------------------------------+
                              |       1. Input Validation         |
                              |  - check_key_points()             |
                              |  - check_section_lengths()        |
                              |  - sidpp > 0, tvd > 0             |
                              +-----------------+-----------------+
                                                |
                                                v
                              +-----------------------------------+
                              |       2. Volumetrics & Depths     |
                              |  - Section & Annulus Volumes      |
                              |  - Strokes & Crossovers (strokes) |
                              |  - tvd_at_md() Linear Splines     |
                              +-----------------+-----------------+
                                                |
                                                v
                              +-----------------------------------+
                              |     3. Core Well Control Math     |
                              |  - KMW (rounded up to next 0.1)   |
                              |  - ICP, FCP, MAMW, MAASP          |
                              +-----------------+-----------------+
                                                |
                                                v
                              +-----------------------------------+
                              |       4. Operational Modeling     |
                              |  - W&W Step-Down Schedule         |
                              |  - Driller's 1st & 2nd Steps      |
                              |  - Volumetric Cycle Table & Tiers |
                              |  - Bullhead & Reverse Circ Limits |
                              |  - Kill Plot Pressure Forecast    |
                              +-----------------+-----------------+
                                                |
                        +-----------------------+-----------------------+
                        |                                               |
                        v                                               v
          +---------------------------+                   +---------------------------+
          | 5a. UI / Pyodide / CLI    |                   | 5b. Excel Suite Generator |
          | - kill_sheet.py dict      |                   | - builder.py cell layout  |
          | - ANSI terminal tables    |                   | - live Excel formulas     |
          | - Chart DOM canvas render |                   | - SI column D:E mirrors   |
          +---------------------------+                   +---------------------------+
```

### Flow Stages

1. **Input Validation:**
   - Raw well path points are sorted and verified to ensure TVD $\le$ MD everywhere.
   - Section lengths of the drill string, open hole, and cased hole are checked to confirm they reconcile exactly with Bit MD and Shoe MD.
2. **Volumetrics & Depths:**
   - Section volumes ($V = \text{capacity} \times \text{length}$) are calculated and rounded to 0.1 bbl.
   - Strokes are computed from pump displacement ($V / Q_{stk}$) and rounded to whole strokes.
   - Crossovers locate the exact stroke counts when fluid interfaces transition across tubular boundaries.
3. **Core Calculations:**
   - Base parameters (KMW, ICP, FCP, MAMW, MAASP) are evaluated per IADC WellSharp rules.
4. **Method Simulation:**
   - Specific well control workflows produce step-by-step instructions (e.g. pressure schedules, hold cycles, or maximum allowable surface pressure charts).
5. **Presentation & Serialization:**
   - Output data dictionaries are formatted for web consumption, CLI printing, or compiled into dynamic Excel worksheets with conditional alerts.
