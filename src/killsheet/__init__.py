"""Kill sheet calculator and advanced well engineering suite.

Oilfield units throughout core modules; dual-unit SI metric support via `killsheet.si`.
Subsea BOP calculations via `killsheet.subsea`.
Tripping and slug calculations via `killsheet.tripping`.
Kick tolerance and drilling window via `killsheet.kick_tolerance`.
Influx characterization & real gas via `killsheet.influx`.
Tubular buckling & lockup via `killsheet.buckling`.
Wellbore hydraulics & nozzle jets via `killsheet.hydraulics`.
Export utilities via `killsheet.export`.
"""

from killsheet import buckling
from killsheet import casing_design
from killsheet import cementing
from killsheet import export
from killsheet import formulas
from killsheet import gas_migration
from killsheet import hydraulics
from killsheet import influx
from killsheet import kick_tolerance
from killsheet import si
from killsheet import simulator
from killsheet import subsea
from killsheet import tripping
from killsheet.kill_sheet import DRILLERS, WAIT_AND_WEIGHT, kill_sheet

__version__ = "1.6.0"
__all__ = [
    "DRILLERS",
    "WAIT_AND_WEIGHT",
    "buckling",
    "casing_design",
    "cementing",
    "export",
    "formulas",
    "gas_migration",
    "hydraulics",
    "influx",
    "kick_tolerance",
    "kill_sheet",
    "si",
    "simulator",
    "subsea",
    "tripping",
    "__version__",
]
