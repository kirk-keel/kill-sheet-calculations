"""US oilfield -> SI conversion factors (multiply field value by factor).

Keys are the field-unit label used on the sheets. Each entry is
(si_unit_label, factor). Temperature is non-linear and handled separately
by the builder via TEMP_F.
"""

CONV = {
    "ppg":      ("kg/m3", 119.8264),
    "psi":      ("kPa", 6.894757),
    "psi/ft":   ("kPa/m", 22.62059),
    "psi/stk":  ("kPa/stk", 6.894757),
    "ft":       ("m", 0.3048),
    "in":       ("mm", 25.4),
    "in2":      ("cm2", 6.4516),
    "bbl":      ("m3", 0.1589873),
    "bbl/ft":   ("m3/m", 0.5216119),
    "bbl/stk":  ("L/stk", 158.9873),
    "bbl/min":  ("m3/min", 0.1589873),
    "bbl/hr":   ("m3/hr", 0.1589873),
    "gal":      ("L", 3.785412),
    "gal/sk":   ("L/sk", 3.785412),
    "gpm":      ("L/min", 3.785412),
    "ft3":      ("m3", 0.02831685),
    "ft3/sk":   ("m3/sk", 0.02831685),
    "ft3/min":  ("m3/min", 0.02831685),
    "scf":      ("std m3", 0.02831685),
    "scf/bbl":  ("m3/m3", 0.1781076),
    "ft/min":   ("m/min", 0.3048),
    "ft/s":     ("m/s", 0.3048),
    "ft/hr":    ("m/hr", 0.3048),
    "lbf":      ("kN", 0.004448222),
    "klbf":     ("kN", 4.448222),
    "lbm":      ("kg", 0.4535924),
    "klbm":     ("tonne", 0.4535924),
    "lb/ft":    ("kg/m", 1.488164),
    "lb/bbl":   ("kg/m3", 2.853010),
    "sk/bbl":   ("sk/m3", 6.289811),
    "hp":       ("kW", 0.7456999),
    "hp/in2":   ("kW/cm2", 0.1155886),
    "ft-lbf":   ("N-m", 1.355818),
    "psi/bbl":  ("kPa/m3", 43.36638),
    "psi/100ft": ("kPa/30.5m", 6.894757),
    "deg/100ft": ("deg/30m", 0.9842520),
    "bbl/mi":   ("m3/km", 0.09879740),
    "lb/gal":   ("kg/L", 0.1198264),
    "cuft/bbl": ("m3/m3", 0.1781076),
    "mD":       ("um2 x1e-3", 0.9869233),
}

# non-linear: SI cell formula is built from the field cell reference
TEMP_F = ("degC", lambda ref: f"=({ref}-32)/1.8")
TEMP_F_PER_100FT = ("degC/100m", lambda ref: f"={ref}/1.8/0.3048")
