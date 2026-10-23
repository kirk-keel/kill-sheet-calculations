# ADR 0001: Decoupled Dual-Engine Architecture

## Status
Accepted

## Context
Petroleum engineers and rig hands operate across vastly different computational environments:
1. Field engineers on rig floors, offices, and client presentations rely extensively on Microsoft Excel workbooks with dynamic, auditable cell formulas and dual US/SI units.
2. Web users, field tablets, and automated SCADA systems require fast, lightweight, programmatic Python APIs that run locally without software installation.

## Decision
We decouple the codebase into two distinct systems:
- **`src/killsheet/`**: A zero-dependency, pure Python engine responsible for all well control simulation, step-down scheduling, and client-side browser execution via Pyodide.
- **`suite/`**: An automated OpenPyXL generator that constructs `petroleum_engineering_suite.xlsx` (45 domain sheets) with live Excel formulas, automated conditional alerts, and dual Field/SI mirroring.

## Consequences
- **Positive:** Neither subsystem compromises the other. The Python engine stays ultralight (<1 ms startup), while the Excel suite delivers complete formula transparency for auditability.
- **Maintenance:** Formula changes must be verified across both systems using `spot_check.py` and `stress_test.py`.
