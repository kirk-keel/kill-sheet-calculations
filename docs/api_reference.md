# API Reference & Module Index

`killsheet` is a zero-dependency, high-precision petroleum engineering library implementing classical SPE and IADC WellSharp well control algorithms.

---

## 1. Units & Constants

Core calculations operate in **US Oilfield Units**:
- **Densities & Mud Weights:** $\text{ppg}$ (pounds per gallon)
- **Pressures:** $\text{psi}$
- **Depths & Lengths:** $\text{ft}$ (differentiating between MD and TVD)
- **Volumes:** $\text{bbl}$
- **Capacities & Displacements:** $\text{bbl/ft}$
- **Pump Displacement:** $\text{bbl/stroke}$
- **Hydrostatic Gradient Constant:** $0.052\text{ psi/ft per ppg}$

Dual-unit SI metric conversions are available via `killsheet.si`.

---

## 2. `killsheet.formulas`

Fundamental well control equations with conservative IADC rounding.

### `kill_mud_weight(sidpp_psi, tvd_ft, original_mud_weight_ppg) -> float`
Calculates Kill Mud Weight (ppg), rounded **UP to the NEXT 0.1 ppg** (even integer answers increment by 0.1 ppg for safety factor):
$$\text{KMW} = \text{OMW} + \frac{\text{SIDPP}}{0.052 \times \text{Bit TVD}}$$

### `initial_circulating_pressure(sidpp_psi, scr_pressure_psi) -> int`
Initial circulating pressure (psi), rounded to nearest whole psi:
$$\text{ICP} = \text{SIDPP} + \text{SCR}$$

### `final_circulating_pressure(scr_pressure_psi, kill_mud_weight_ppg, original_mud_weight_ppg) -> int`
Final circulating pressure (psi), rounded to nearest whole psi:
$$\text{FCP} = \text{SCR} \times \left(\frac{\text{KMW}}{\text{OMW}}\right)$$

### `max_allowable_mud_weight(lot_pressure_psi, shoe_tvd_ft, test_mud_weight_ppg) -> float`
Maximum allowable mud weight (ppg), rounded **DOWN** to 0.1 ppg:
$$\text{MAMW} = \text{Test MW} + \frac{\text{LOT Pressure}}{0.052 \times \text{Shoe TVD}}$$

### `maasp(max_allowable_mud_weight_ppg, current_mud_weight_ppg, shoe_tvd_ft) -> int`
Maximum allowable annular surface pressure (psi), rounded **DOWN** to whole psi:
$$\text{MAASP} = (\text{MAMW} - \text{Current MW}) \times 0.052 \times \text{Shoe TVD}$$

### `kill_mud_overbalance(kill_mud_weight_ppg, original_mud_weight_ppg, tvd_ft) -> int`
Additional hydrostatic head (psi) provided by kill mud over original mud:
$$\text{Overbalance} = (\text{KMW} - \text{OMW}) \times 0.052 \times \text{TVD}$$

---

## 3. `killsheet.subsea`

Calculations for subsea BOP stacks and floating drilling operations.

### `dynamic_maasp(static_maasp_psi, clf_psi) -> int`
Allowable surface choke reading while circulating up the choke line:
$$\text{Dynamic MAASP} = \max(0, \text{Static MAASP} - \text{CLF})$$

### `choke_pressure_bringing_pump_up(sicp_psi, clf_psi) -> int`
Surface casing pressure held during pump acceleration:
$$\text{Target} = \max(0, \text{SICP} - \text{CLF})$$

### `riser_margin_mud_weight(original_mud_weight_ppg, tvd_ft, water_depth_ft, air_gap_ft=0, seawater_density_ppg=8.55) -> float`
Mud weight required below the mudline if the riser disconnects:
$$\text{MW}_{\text{rm}} = \frac{0.052 \times \text{OMW} \times \text{TVD} - 0.052 \times \rho_{\text{SW}} \times \text{WD}}{0.052 \times (\text{TVD} - \text{WD} - \text{AG})}$$

### `subsea_kill_summary(...) -> dict`
Runs the complete subsea kill calculation, returning static/dynamic MAASP, choke line volume, pump strokes, and post-disconnect BHP overbalance.

---

## 4. `killsheet.kick_tolerance`

Drilling window and casing seat integrity evaluation.

### `kick_intensity_ppg(sidpp_psi, tvd_ft) -> float`
Equivalent mud weight deficit:
$$\text{KI} = \frac{\text{SIDPP}}{0.052 \times \text{TVD}}$$

### `max_gas_height_at_shoe_ft(mud_weight_ppg, tvd_ft, shoe_tvd_ft, lot_emw_ppg, sidpp_psi, gas_gradient_psi_per_ft=0.10) -> int`
Maximum gas height (ft) at the shoe before exceeding fracture pressure:
$$H_{\text{max}} = \frac{P_{\text{frac}} - P_{\text{form}} + 0.052 \times \text{MW} \times (\text{TVD} - \text{Shoe TVD})}{0.052 \times \text{MW} - G_{\text{gas}}}$$

### `kick_tolerance_bbl(...) -> float`
Maximum gas kick volume (bbl) at bottomhole conditions using Boyle's Law:
$$KT_{\text{bottom}} = (H_{\text{max}} \times C_{\text{ann}}) \times \left(\frac{P_{\text{frac}}}{P_{\text{form}}}\right)$$

### `required_shoe_lot_ppg(target_kick_volume_bbl, ...) -> float`
Minimum LOT fracture gradient (ppg EMW) required to safely handle a designated kick detection volume.

---

## 5. `killsheet.tripping`

Rig-floor pipe displacement, slugging, and trip monitoring.

### `slug_volume_for_dry_pipe(desired_dry_pipe_ft, dp_capacity_bbl_per_ft, original_mud_weight_ppg, slug_weight_ppg) -> float`
Volume of heavy pill required to achieve target dry pipe height:
$$V_{\text{slug}} = \frac{H_{\text{dry}} \times \text{Cap}_{\text{DP}} \times \text{OMW}}{\text{Slug MW} - \text{OMW}}$$

### `slug_pit_gain(slug_volume_bbl, original_mud_weight_ppg, slug_weight_ppg) -> float`
Volume of mud returned to active pits when the slug U-tubes:
$$\text{Pit Gain} = V_{\text{slug}} \times \frac{\text{Slug MW} - \text{OMW}}{\text{OMW}} = H_{\text{dry}} \times \text{Cap}_{\text{DP}}$$

### `dry_pipe_fill_volume(length_pulled_ft, pipe_steel_disp_bbl_per_ft) -> float`
Fill-up volume required when pulling dry pipe (metal displacement only).

### `wet_pipe_fill_volume(length_pulled_ft, pipe_closed_disp_bbl_per_ft) -> float`
Fill-up volume required when pulling wet pipe (closed-end displacement).

### `level_drop_unfilled_hole(volume_unfilled_bbl, casing_or_annulus_cap_bbl_per_ft) -> int`
Fluid level drop (ft) if hole is pulled without filling.

---

## 6. `killsheet.si`

Dual-unit SI metric API wrapper.

- `kill_mud_weight_si(sidpp_kpa, tvd_m, original_mud_weight_kg_m3) -> float`
- `icp_si(sidpp_kpa, scr_pressure_kpa) -> float`
- `fcp_si(scr_pressure_kpa, kill_mud_weight_kg_m3, original_mud_weight_kg_m3) -> float`
- `mamw_si(lot_pressure_kpa, shoe_tvd_m, test_mud_weight_kg_m3) -> float`
- `maasp_si(max_allowable_mud_weight_kg_m3, current_mud_weight_kg_m3, shoe_tvd_m) -> int`
- `kill_sheet_si(...) -> dict`

---

## 7. `killsheet.export`

Serialization and documentation export.

- `to_json(data: dict, indent: int = 2) -> str`: Formatted JSON serialization.
- `schedule_to_csv(schedule_rows, filepath: str = None) -> str`: CSV export of step-down schedules.
- `to_markdown_report(sheet_dict: dict) -> str`: Formatted Markdown report table.

---

## 8. `killsheet.influx`

Kick influx characterization, fluid identification, and real gas properties.

### `influx_height_ft(pit_gain_bbl, annular_capacity_bbl_per_ft) -> float`
Calculates annular influx height ($H = V / C_a$).

### `influx_gradient_psi_per_ft(sicp_psi, sidpp_psi, influx_height_ft, original_mud_weight_ppg) -> float`
Computes pressure gradient of kick fluid from drill pipe and casing shut-in balance:
$$G_{\text{influx}} = 0.052 \times \text{OMW} - \frac{\text{SICP} - \text{SIDPP}}{H_{\text{influx}}}$$

### `influx_density_ppg(gradient_psi_per_ft) -> float`
Converts gradient to equivalent density in ppg.

### `classify_influx_type(density_ppg) -> str`
Classifies kicking fluid: Dry Gas, Gas/Condensate, Oil, Saltwater, or Heavy Brine.

### `gas_z_factor(pressure_psig, temperature_deg_f, gas_gravity=0.65) -> float`
Real gas compressibility factor via Beggs-Brill & Sutton pseudocritical correlations.

### `gas_formation_volume_factor_bg(pressure_psig, temperature_deg_f, z_factor) -> float`
Computes $B_g$ in cu ft / scf.

### `characterize_kick(...) -> dict`
Generates complete kick characterization and PVT properties report.

---

## 9. `killsheet.buckling`

Tubular stress, sinusoidal buckling, and helical lockup analysis.

### `pipe_moment_of_inertia_in4(od_in, id_in) -> float`
Pipe area moment of inertia $I = \frac{\pi}{64} (OD^4 - ID^4)$.

### `buoyancy_factor(mud_weight_ppg) -> float`
Archimedes buoyancy factor $BF = 1 - \frac{\text{MW}}{65.45}$.

### `radial_clearance_in(hole_id_in, pipe_od_in) -> float`
Radial clearance $r = \frac{D_{\text{hole}} - D_{\text{pipe}}}{2}$.

### `sinusoidal_buckling_load_lbf(pipe_od_in, pipe_id_in, hole_id_in, pipe_weight_lb_per_ft, mud_weight_ppg, inclination_deg) -> int`
Paslay-Dawson critical sinusoidal compressive buckling load (or Lubinski for vertical).

### `helical_buckling_load_lbf(...) -> int`
Wu & Juvkam-Wold / Lubinski helical buckling limit ($F_h = \sqrt{2} F_{\text{sin}}$).

### `evaluate_tubular_buckling(...) -> dict`
Evaluates stability under current axial tension or compression.

---

## 10. `killsheet.hydraulics`

Wellbore hydraulics, bit nozzle jet optimization, annular pressure losses, and ECD.

### `total_flow_area_sq_in(nozzle_sizes_in_32nds) -> float`
TFA in square inches for bit nozzle sizes in 32nds.

### `nozzle_velocity_fps(flow_rate_gpm, tfa_sq_in) -> float`
Nozzle exit jet velocity ($V_n = \frac{Q}{3.117 \times \text{TFA}}$).

### `bit_pressure_drop_psi(mud_weight_ppg, flow_rate_gpm, tfa_sq_in) -> int`
Pressure drop across the drill bit nozzles.

### `bit_hydraulic_horsepower(dp_bit_psi, flow_rate_gpm) -> float`
Hydraulic horsepower ($\text{HHP} = \frac{\Delta P \times Q}{1714}$).

### `hydraulic_horsepower_per_sq_in(hhp, bit_diameter_in) -> float`
HSI (Horsepower per square inch of bottomhole area).

### `jet_impact_force_lbf(mud_weight_ppg, flow_rate_gpm, dp_bit_psi) -> int`
Hydraulic jet impact force (lbf).

### `annular_pressure_loss_psi(...) -> int`
Bingham Plastic annular friction loss across wellbore intervals.

### `equivalent_circulating_density_ppg(mud_weight_ppg, annular_loss_psi, tvd_ft) -> float`
Equivalent Circulating Density ($\text{ECD} = \text{MW} + \frac{\Delta P_{\text{ann}}}{0.052 \times \text{TVD}}$).

---

## 11. `killsheet.simulator`

Step-by-step well kill execution simulator.

### `WellKillSimulator(...)`
Simulates Wait & Weight or Driller's Method circulating out kicks.
- `step(delta_strokes: int, choke_psi: Optional[float] = None) -> dict`: Advance pumped strokes, evaluate mud fronts, BHP balance, and casing seat integrity.
- `render_dashboard(latest_step: dict) -> str`: Renders an ASCII rig floor console display.

---

## 12. `killsheet.gas_migration`

Gas percolation rise velocity, bubble slip dynamics, and surface pressure accumulation.

### `gas_migration_velocity_ft_per_hr(mud_weight_ppg, gas_density_ppg=1.5, surface_tension_dynes_per_cm=30.0, inclination_deg=0.0) -> float`
Calculates hydrodynamic bubble rise velocity via Harmathy formulation with Zukoski inclination enhancement.

### `pressure_buildup_rate_psi_per_hr(mud_weight_ppg, migration_velocity_ft_per_hr=1000.0) -> int`
Shut-in casing pressure rise rate ($\frac{dP}{dt} = 0.052 \times \text{MW} \times v_{\text{rise}}$).

### `evaluate_gas_migration(...) -> dict`
Evaluates percolation velocity, pressure buildup rate, time to casing shoe, and time to surface BOP stack.

---

## 13. `killsheet.casing_design`

API 5CT / API 5C3 casing burst, tension-derated collapse, and well control integrity verification.

### `api_burst_pressure_psi(od_in, id_in, yield_strength_psi, apply_wall_tolerance=True) -> int`
Barlow's internal yield pressure with API standard 12.5% wall tolerance (factor 0.875).

### `biaxial_yield_strength_derating(yield_strength_psi, axial_tensile_stress_psi) -> float`
Effective yield strength ($Y_{pa}$) under axial tension via API 5C3 / ISO 10400 yield ellipse.

### `derated_collapse_pressure_psi(nominal_collapse_psi, yield_strength_psi, axial_tensile_load_lbf, cross_section_sq_in) -> int`
Tension-derated casing collapse resistance ($P_{\text{col}} \times \frac{Y_{pa}}{Y_p}$).

### `evaluate_casing_well_control_integrity(...) -> dict`
Evaluates burst safety factor against surface SICP and collapse safety factor against external hydrostatic load.

---

## 14. `killsheet.cementing`

Balanced cement plug placement, spacer hydrostatic balancing, and displacement sizing.

### `cement_slurry_volume_bbl(plug_length_ft, hole_capacity_bbl_per_ft, excess_percent=0.0) -> float`
Theoretical cement slurry volume required (bbl).

### `balanced_plug_height_ft(slurry_volume_bbl, pipe_capacity_bbl_per_ft, annular_capacity_bbl_per_ft) -> float`
Height of balanced cement plug with workstring in place ($h = \frac{V}{C_{\text{pipe}} + C_{\text{ann}}}$).

### `balanced_spacer_behind_bbl(spacer_ahead_bbl, pipe_capacity_bbl_per_ft, annular_capacity_bbl_per_ft) -> float`
Sizes spacer volume behind cement to achieve identical hydrostatic column height and prevent U-tubing.

### `displacement_volume_to_plug_top_bbl(workstring_bottom_md_ft, balanced_plug_height_ft, pipe_capacity_bbl_per_ft) -> float`
Displacement volume to place cement top at balanced height inside pipe.

### `balanced_cement_plug_summary(...) -> dict`
Comprehensive plug placement schedule including slurry barrels, dry cement sacks, mix water, and displacement.
