# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.0] - 2026-10-22

### Added
- **Gas Migration Dynamics (`killsheet.gas_migration`):** Hydrodynamic Harmathy single-bubble slip velocity, Zukoski inclination acceleration factor, shut-in casing pressure rise rate ($dP/dt$), and arrival timelines to shoe and surface BOP.
- **Casing Integrity & Biaxial Collapse Derating (`killsheet.casing_design`):** API Barlow internal yield burst rating (with 87.5% wall tolerance), API 5C3 / ISO 10400 tension-derated collapse resistance envelope, and well control safety factor checks.
- **Balanced Cement Plugs (`killsheet.cementing`):** Slurry volume sizing with excess, balanced plug height with pipe in hole, spacer balancing for U-tube equilibrium, displacement volume, and dry cement sack/water yields.
- **Influx Characterization & Real Gas Dynamics (`killsheet.influx`):** Influx pressure gradient and density, automated fluid classification (Gas, Oil, Saltwater), Beggs-Brill & Sutton pseudocritical gas deviation factor ($Z$), and formation volume factor ($B_g$).
- **Tubular Buckling Limits (`killsheet.buckling`):** Paslay-Dawson sinusoidal waving and Lubinski / Wu & Juvkam-Wold helical lockup limits for drill pipe and coiled tubing in high-angle laterals.
- **Wellbore Hydraulics & Jet Impact (`killsheet.hydraulics`):** Total Flow Area (TFA), nozzle exit velocity, bit pressure drop, Hydraulic Horsepower (HHP/HSI), Jet Impact Force (JIF), and Bingham Plastic annular ECD profiling.
- **Interactive Rig-Floor Simulator (`killsheet simulate`):** Dynamic step-by-step well kill execution simulator with real-time ASCII console tracking mud fronts, target DPP step-downs, dynamic shoe pressure against MAASP, and bottomhole pore pressure balance.
- **Web UI Upgrades:** One-click CSV and Markdown download buttons, plus an interactive 7-tab Quick Rig Tools modal (Subsea, Tripping, Kick Tolerance, Influx, Gas Migration, Casing, Cementing).
- **Material Documentation Site:** Configured `mkdocs.yml` with MathJax LaTeX equation rendering, Mermaid architecture diagrams, and GitHub Pages support.
- **Jupyter Field Case Studies:** Added Case Study 04 (Casing Seat Selection) and Case Study 05 (Tubular Buckling & Hydraulics), expanding the notebook suite to 5 interactive studies.
- **Automated Verification:** Added `tests/test_standalone_examples.py`, expanding the unit test suite to 726 tests.

## [1.5.0] - 2026-10-21

### Added
- **Subsea Well Control (`killsheet.subsea`):** Choke line friction (CLF), dynamic MAASP derating, choke pressure ramp-up management ($SICP - CLF$), and riser disconnect overbalance / margin.
- **Dual-Unit SI Metric API (`killsheet.si`):** Full SI metric wrapper ($\text{kg/m}^3$, $\text{kPa}$, $\text{bar}$, $\text{m}$, $\text{m}^3$) applying standard IADC safety factor rounding.
- **Rig-Floor Tripping & Slugs (`killsheet.tripping`):** Heavy slug volumes for target dry-pipe height, U-tube pit gain, dry vs. wet pipe displacement, and unfilled fluid level drop.
- **Kick Tolerance & Drilling Window (`killsheet.kick_tolerance`):** Boyle's Law gas bubble expansion at casing shoe, kick intensity, and bottomhole kick tolerance volume.
- **Serialization & Reporting (`killsheet.export`):** Formatted JSON, CSV step-down schedules, and Markdown Daily Drilling Reports.
- **PEP 561 Compliance:** Added `py.typed` marker for static type checkers.
- **Initial Case Studies:** Added Deepwater Subsea Well Control, Extended-Reach Horizontal Lateral Step-Down, and Volumetric Gas Migration notebooks.

## [1.1.0] - 2026-10-15

### Added
- **Safety Margin (SF):** Team's safety margin carried from start-up to shut-in across Driller's and Wait & Weight methods.
- **Client-Side Web Application:** In-browser kill sheet calculator powered by Pyodide and WebAssembly.

## [1.0.0] - 2026-10-01

### Added
- **Core Multi-Method Engine:** Complete support for Driller's Method, Wait & Weight, Volumetric Method with Lubricate & Bleed, Bullheading, and Reverse Circulation across vertical, deviated, and horizontal trajectories with untapered and tapered strings.
- **Excel Engineering Suite:** 45 domain worksheets with live formulas and dual US-Oilfield / SI Metric mirroring.
