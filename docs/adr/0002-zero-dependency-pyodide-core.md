# ADR 0002: Zero External Dependencies for the Core Calculator

## Status
Accepted

## Context
Deploying software to remote rig sites and offshore floaters faces strict IT constraints:
- Rig PCs and field tablets often lack internet access or admin privileges to install native C-extensions (e.g. NumPy, SciPy).
- Running calculation services over cloud APIs risks exposing confidential reservoir pressure data and introduces latency or outage vulnerabilities during active well control emergencies.

## Decision
All modules inside `src/killsheet/` are restricted strictly to the Python 3.10+ standard library (`math`, `typing`, `functools`).

## Consequences
- **Positive:** The package compiles natively into WebAssembly using Pyodide, allowing `web/index.html` to run entirely in the user's browser client-side without any server infrastructure.
- **Positive:** Zero third-party dependency vulnerabilities or supply chain risks.
- **Trade-off:** Numerical routines (such as linear splines for TVD/MD interpolation and real gas equations of state) must be implemented natively rather than importing external packages.
