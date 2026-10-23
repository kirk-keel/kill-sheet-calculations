# Field Engineering Case Studies & Case Notebooks

The repository includes five comprehensive Jupyter notebooks demonstrating petroleum engineering calculations across real-world field scenarios:

---

### [01. Deepwater Subsea Well Control](../notebooks/01_deepwater_subsea_well_control.ipynb)
- **Field Scenario:** Deepwater GoM floater with subsea BOP stack in 5,000 ft water depth.
- **Key Concepts:**
  - Choke line friction (CLF) determination and dynamic MAASP derating.
  - Choke pressure management during pump ramp-up ($P_{\text{choke}} = \text{SICP} - \text{CLF}$).
  - Choke line displacement volume and stroke count.
  - Riser margin mud weight calculation and post-emergency-disconnect bottomhole overbalance verification.

---

### [02. Extended-Reach Horizontal Well Kill Schedule](../notebooks/02_extended_reach_horizontal_kill_schedule.ipynb)
- **Field Scenario:** 10,000 ft Permian Wolfcamp horizontal lateral with tapered drill string.
- **Key Concepts:**
  - True Vertical Depth (TVD) vs. Measured Depth (MD) segregation in long horizontals.
  - Step-down pressure schedule behavior: rapid initial drillstring pressure drop followed by flat constant pump pressure through the 0-TVD lateral section.
  - Equivalent circulating density (ECD) and casing seat stress management.

---

### [03. Volumetric Method & Lubricate and Bleed](../notebooks/03_volumetric_method_and_lubricate_bleed.ipynb)
- **Field Scenario:** Bit off-bottom or out of the hole when a severe gas kick is detected.
- **Key Concepts:**
  - Gas bubble migration velocity and Boyle's Law pressure accumulation.
  - Sizing cycle bleed volumes across variable annular geometry.
  - Multi-cycle Lubricate & Bleed execution: mud lubrication to replace lost hydrostatic pressure and gas expansion bleeding to restore bottomhole balance.

---

### [04. Casing Seat Selection & Kick Tolerance Analysis](../notebooks/04_casing_seat_selection_and_kick_tolerance.ipynb)
- **Field Scenario:** Intermediate casing shoe placement and drilling window optimization.
- **Key Concepts:**
  - Kick intensity calculation ($KI = \text{SIDPP} / (0.052 \times \text{TVD})$).
  - Maximum allowable annular surface pressure (MAASP) and fracture gradient limits.
  - Maximum gas influx height ($H_{\text{max}}$) without fracturing the shoe.
  - Boyle's Law bottomhole kick tolerance volume sensitivity ($V_{\text{kick}}$ vs. TVD).

---

### [05. Tubular Buckling & Bit Hydraulics Optimization](../notebooks/05_tubular_buckling_and_hydraulics_optimization.ipynb)
- **Field Scenario:** High-angle lateral milling and extended reach drilling.
- **Key Concepts:**
  - Paslay-Dawson sinusoidal buckling critical loads ($F_{\text{crit, sin}}$).
  - Wu & Juvkam-Wold helical buckling limits ($F_{\text{crit, hel}}$) and spiral lockup risk.
  - Bit nozzle Total Flow Area (TFA), exit jet velocity, and bit pressure drop.
  - Hydraulic horsepower (HHP), power density (HSI), and jet impact cleaning force (JIF).
  - Bingham Plastic annular friction pressure loss and circulating ECD profiling.
