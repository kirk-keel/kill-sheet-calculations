# ADR 0003: Strict Adherence to IADC WellSharp Rounding Conventions

## Status
Accepted

## Context
Standard IEEE 754 floating-point arithmetic uses "round half to even" (banker's rounding), which can produce unexpected truncations in oilfield safety margins.
The **IADC WellSharp Formula Sheet (Rev 4, 2025)** dictates three strict operational rounding principles:
1. **Kill Mud Weight (KMW):** Always rounded **UP to the next 0.1 ppg**, even if exact (e.g. 10.80 -> 10.9 ppg). An exact weight only balances the formation pore pressure; the extra 0.1 ppg provides the essential safety overbalance that kills the well.
2. **Maximum Allowable Limits (MAASP, MAMW):** Always rounded **DOWN to the previous 0.1 ppg or whole psi** to prevent overestimating fracture resistance. Pressure step-down schedules are also rounded down.
3. **General Pressures & Strokes:** Academic rounding (.5 rounds up) to whole numbers; volumes rounded to 0.1 bbl.

## Decision
All calculations in `src/killsheet/` must pass through standardized helpers in `killsheet.rounding`:
- `round_up_to_next_tenth`
- `round_down_to_tenth`
- `round_down_to_whole_number`
- `round_to_whole_number`
- `round_to_tenth`
- `round_to_4_places`

## Consequences
- Guaranteed mathematical consistency between the Python engine, printed kill sheets, and Excel workbooks.
- Completely eliminates off-by-one or off-by-tenth micro-rounding discrepancies during rig inspections.
