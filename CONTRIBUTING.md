# Contributing to Kill Sheet Calculations

Thank you for your interest in contributing to `kill-sheet-calculations`! This repository houses an advanced well control, completion, and well intervention (CWI) engineering suite built around strict IADC WellSharp standards.

---

## 1. Architectural Doctrine

The project maintains two decoupled calculation subsystems:

1. **Pure Python Engine (`src/killsheet/`):**
   - **Zero external runtime dependencies** (standard library only).
   - Designed to run client-side in browsers via Pyodide (`web/index.html`) as well as in edge SCADA / rig environments via CLI.
   - Adheres strictly to **IADC WellSharp Rev 4 (2025)** rounding rules:
     - Kill mud weight: always rounded UP to next 0.1 ppg (`math.floor(x * 10) + 1`).
     - Maximums (MAASP, MAMW, pressure reduction schedules): always rounded DOWN (`math.floor(x)`).
     - Standard values (pressures, strokes): academic rounding (`.5` rounds up).
2. **Excel Engineering Suite (`suite/` & `petroleum_engineering_suite.xlsx`):**
   - Generated with `openpyxl`.
   - Contains live, dynamic formulas (no static values).
   - Dual-unit layout: Field Units in Column B, SI Metric in Column E.

---

## 2. Development Setup

Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,suite,verify,docs]"
```

---

## 3. Running the Verification Suites

Before submitting a Pull Request, verify that all three verification tiers pass:

1. **Pytest Unit Test Suite:**
   ```bash
   pytest -v
   ```
2. **34-Calculation Excel Benchmark Spot Check:**
   ```bash
   python spot_check.py
   ```
3. **10-Well Excel Engine Stress Test:**
   ```bash
   python stress_test.py
   ```

---

## 4. Web Application & Pyodide Packaging

Whenever modifying code in `src/killsheet/` or `web/`, rebuild the static distribution:
```bash
python web/build_site.py
```
To test locally:
```bash
python -m http.server --directory _site
```
Then navigate to `http://localhost:8000`.

---

## 5. Coding Standards & File Naming Conventions

- **Type Annotations:** All new Python functions must include PEP 484 type annotations.
- **Example Filenames:**
  - Files named `examples/*_well.py` are reserved exclusively for the 36 dropdown options loaded by Pyodide in `web/index.html` (verified by `tests/test_web_app.py`).
  - Standalone engineering demo scripts must be named `examples/example_*.py`.
