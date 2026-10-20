"""Reference: live unit converters and the full conversion-factor table."""
from .. import style as S
from ..builder import SheetBuilder
from ..convert import CONV


def build(wb):
    sb = SheetBuilder(
        wb, "Unit Converter", "reference",
        "Unit Conversions",
        "Live two-way converters for common oilfield quantities, plus the full factor table",
        description="Live converters (density, pressure, volume, flow, force...) and conversion factor table",
    )

    pairs = [
        ("Density", 12.5, "ppg"),
        ("Pressure", 5000, "psi"),
        ("Pressure gradient", 0.65, "psi/ft"),
        ("Length / depth", 10000, "ft"),
        ("Diameter", 8.5, "in"),
        ("Volume", 500, "bbl"),
        ("Volume (small)", 42, "gal"),
        ("Capacity", 0.0459, "bbl/ft"),
        ("Flow rate", 350, "gpm"),
        ("Flow rate", 8.5, "bbl/min"),
        ("Velocity", 150, "ft/min"),
        ("Force", 45000, "lbf"),
        ("Mass", 25000, "lbm"),
        ("Weight per length", 19.5, "lb/ft"),
        ("Power", 1600, "hp"),
    ]
    sb.section("Live Converters (enter a field-unit value; SI computes)")
    c = sb.calc("Field -> SI", note="Yellow cells are inputs; SI Value column converts live.")
    for label, default, unit in pairs:
        fmt = "#,##0.00" if default < 10000 else "#,##0"
        c.inp(f"{label}  ({unit})", default, unit, fmt=fmt)

    c = sb.calc("Temperature", eq="degC = (degF - 32) / 1.8")
    f = c.inp("Temperature", 250, None, fmt="0.0", note="degF")
    c.out("Temperature", f"({f}-32)/1.8", None, fmt="0.0", note="degC")

    c = sb.calc("SI -> Field (generic)",
                eq="Field value = SI value / factor",
                note="Enter an SI value and the factor from the table below.")
    v = c.inp("SI value", 1500.0, None, fmt="#,##0.00")
    k = c.inp("Factor (field -> SI)", 6.894757, None, fmt="0.000000")
    c.out("Field value", f"{v}/{k}", None, fmt="#,##0.00")

    sb.section("Conversion Factor Table (multiply field value by factor to get SI)")
    ws = sb.ws
    sb.row += 1
    hdr = sb.row
    for col, text in [(1, "Field unit"), (2, "Factor"), (3, "SI unit")]:
        cell = ws.cell(row=hdr, column=col, value=text)
        cell.font = S.F_HEADER
        cell.border = S.BORDER_BOX
    r = hdr + 1
    for unit, (si_unit, factor) in sorted(CONV.items()):
        ws.cell(row=r, column=1, value=unit).border = S.BORDER_BOX
        b = ws.cell(row=r, column=2, value=factor)
        b.number_format = "0.0000000"
        b.border = S.BORDER_BOX
        ws.cell(row=r, column=3, value=si_unit).border = S.BORDER_BOX
        r += 1
    sb.row = r
