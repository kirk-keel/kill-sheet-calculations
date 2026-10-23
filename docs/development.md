# Development Guide

## 1. Quick Setup

```bash
make setup
```
Or manually:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt -e .
pre-commit install
```

---

## 2. Common Development Tasks

```bash
make test         # Run full unit test suite (pytest -v)
make spot-check   # Validate 34 petroleum benchmark formulas against Excel engine
make stress-test  # Run 10-well workbook stress test
make build-suite  # Generate petroleum_engineering_suite.xlsx (46 sheets)
make build-site   # Build Pyodide web application distribution into _site/
make lint         # Run ruff static analysis
make fmt          # Auto-format codebase with ruff
make docs         # Serve MkDocs documentation site locally (http://127.0.0.1:8000)
make clean        # Clean temporary build and cache artifacts
```

---

## 3. Adding New Calculations

1. Implement core formulas in [`src/killsheet/`](../src/killsheet/) using standard library only (`math`, `typing`).
2. Always import and apply rounding helpers from [`killsheet.rounding`](../src/killsheet/rounding.py):
   - Round kill mud weight **UP** to next 0.1 ppg (`round_up_to_next_tenth`).
   - Round maximums (MAASP, MAMW) **DOWN** (`round_down_to_tenth`, `round_down_to_whole_number`).
   - Round standard pressures and strokes to whole numbers (`round_to_whole_number`).
3. Add corresponding unit tests in [`tests/`](../tests/) with both typical field values and defensive edge cases.
4. If adding a standalone example script, name it `examples/example_<name>.py` (files ending in `*_well.py` are reserved exclusively for the 36 web app dropdown options).
5. Rebuild the site distribution with `make build-site` and run `make test`.
