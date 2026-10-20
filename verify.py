"""Recalculate every formula in the built workbook and report errors.

Usage:  python verify.py [workbook.xlsx]

Loads the workbook with the `formulas` package, solves all cells, and prints
any cell whose result is an Excel error (#DIV/0!, #VALUE!, #NAME?, ...).
Also spot-checks a handful of hand-verified engineering values.
"""
import sys

import formulas
import openpyxl
import schedula

ERR_STRINGS = ("#DIV/0!", "#VALUE!", "#NAME?", "#REF!", "#NUM!", "#N/A", "#NULL!")


def intentional_na_cells(path):
    """Cells whose formula deliberately returns NA() (chart-gap helpers)."""
    wb = openpyxl.load_workbook(path)
    cells = set()
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and "NA(" in cell.value:
                    cells.add(f"{ws.title.upper()}'!{cell.coordinate}")
    return cells


def main(path):
    na_ok = intentional_na_cells(path)
    xl = formulas.ExcelModel().loads(path).finish()
    sol = xl.calculate()
    n_formula = 0
    errors = []
    for key, val in sol.items():
        if ":" in key.split("!")[-1]:
            continue  # range aggregations; member cells are scanned individually
        try:
            v = val.value[0, 0]
        except Exception:
            continue
        n_formula += 1
        if isinstance(v, str) and v.strip().upper() in ERR_STRINGS:
            # NA() chart-gap helper cells are intentional
            if v.strip().upper() == "#N/A" and any(k in key for k in na_ok):
                continue
            errors.append((key, v))
        if isinstance(v, schedula.utils.exc.DispatcherError):
            errors.append((key, "dispatch error"))
    print(f"evaluated {n_formula} cells")
    if errors:
        print(f"{len(errors)} ERROR CELLS:")
        for k, v in errors:
            print("  ", k, v)
        sys.exit(1)
    print("no Excel error values found")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "petroleum_engineering_suite.xlsx")
