# E10 — Model settings and coefficient record

This record transcribes the settings and user-reported fitting results available in the current Project 2 conversation. It is not an inspected copy of the final local Python repository and is not a raw COMSOL export.

## System and boundaries
- Eight identical Candidate C cold plates in a same-side supply / return arrangement.
- Candidate C: 30 channels, 0.40 mm width, 1.00 mm height, 50 mm length; reported pitch about 1.30 mm. The discussion used a 60 × 60 mm plate and 40 × 40 mm heated footprint. No final CAD file is included here.
- Header internal diameter: 19.05 mm; inter-branch segment length: 0.050 m (network-model input, not a verified mechanical layout).
- Branch tubing: 9.5 mm internal diameter; 0.30 m supply plus 0.30 m return; two QDs.
- Branch QD coefficient: K = 1 per QD; other fittings: aggregate K = 1; referenced to branch-tube mean velocity. These are illustrative local-loss assumptions, not vendor data.
- Nominal pump/tray analysis uses header K_local = 0. Earlier fixed-flow sensitivity uses 0, 1 and 2 per supply and return inter-branch segment.
- Pump curve: Δp_pump[kPa] = H0 [1 − (Q_total / 14 L/min)^2], with H0 = 20 kPa nominal and 15 kPa for the weak-pump scenario. This change is a head-capability sensitivity; it is not an affinity-law speed change.
- Assumed overall pump efficiency: 0.50. Pressure boundary: first supply node S1 to first return node R1. Common upstream and downstream piping, CDU heat exchanger, filters, and facility losses are not represented by the reported tray pressure.
- Header/tube model uses density 996 kg/m³ and viscosity 8.0e−4 Pa·s; thermal component default is 997 kg/m³ and cp = 4180 J/(kg·K). These are fixed modeling inputs. The small density mismatch is recorded rather than silently reconciled.

## Thermal assumptions and project criteria
- Nominal 750 W per accelerator, 6.0 kW tray; inlet temperature 30°C.
- Additional TIM resistance 0.005 K/W and package resistance 0.020 K/W, added to maximum base temperature. These are lumped project assumptions; the result is an estimated device temperature, not a package-resolved junction solution.
- Project criteria: device temperature at most 85°C; max-minus-min branch flow divided by mean at most 10%; fixed total-flow target 8.64 L/min; provisional 750 W branch-flow design threshold 0.65 L/min.
- The 0.65 L/min value is a margin-oriented criterion, not the exact temperature-crossing flow or a universal component limit.

## Revised cold-plate ROM
With q* = flow / (1 L/min):
- Δp[kPa] = 6.275834320181083 q* + 3.0569321326501875 (q*)².
- Rθ[K/W] = 0.027023939579912205 (q*)^(−0.38230560298064653).
- Rθ = [T_base,max − (T_in + T_out)/2] / P_heat.
- Calibration flows: 0.50, 0.60, 0.65, 0.80, 0.95, 1.10, 1.20 L/min at 750 W and 30°C inlet.
- Hydraulic inputs [kPa]: 3.894, 4.864, 5.371, 6.983, 8.727, 10.604, 11.927.
- Thermal inputs [K/W]: 0.03512, 0.03286, 0.03192, 0.02955, 0.02765, 0.02600, 0.0250856.
- Reported updated hydraulic MAPE 0.0676%, max error 0.2093%; thermal MAPE 0.2753%, max error 0.4738%.
- Power-dependence checks: 450, 600 and 750 W at 0.65 and 1.10 L/min; approximately 0.02% resistance variation at each flow.
- Additional off-grid case: 0.864 L/min at 600 W; original COMSOL Δp about 7.711 kPa, Rθ about 0.02868 K/W, maximum base temperature about 52.22°C, outlet about 40.02°C. This point was excluded from coefficient fitting but had already been inspected during development.
- Independent extension check: 1.15 L/min at 750 W / 30°C, excluded from fitting; see E03 and E04.
- The 1.10 L/min detailed screenshot previously reported 0.0260393 K/W, whereas the fitting array used 0.02600. The package preserves the actual reported fitting array and records the difference. Refit from a full-precision source export before a precision-focused release.

## Fault definitions
- Nominal: eight devices at 750 W, 30°C inlet, nominal pump.
- Hot coolant: 35°C inlet, all other inputs unchanged; constant-property sensitivity only, outside the sampled inlet-temperature condition.
- Uneven power: branches 1–7 at 600 W, branch 8 at 750 W; 4.95 kW total.
- Restricted branch: branch 8 complete hydraulic characteristic multiplied by 1.30. This is a generic resistance perturbation, not 30% blocked area and not a validated internal cold-plate obstruction model.
- Weak pump: shutoff pressure changed to 15 kPa while free-flow parameter remains 14 L/min.
- Combined stress: weak pump, branch 8 multiplier 1.30, 35°C inlet, and the 600/750 W uneven-power vector.

## Implementation and testing evidence
The user reported 21 cold-plate tests and 25 tests in the then-current complete suite passing before later network integration. Later Work-mode outputs reported successful debugging and the final scenario table (E01). A final repository-wide test log after every integration change was not supplied. No final project code, COMSOL model, or raw Project 2 export was rerun during portfolio preparation.

## Supporting screenshot excerpts

The coefficient record above is also directly supported by [E11, revised fitting output](rom_refit_reported.png). The selected-flow power checks are preserved as [E12, 0.65 L/min](power_check_0p65_reported.png) and [E13, 1.10 L/min](power_check_1p10_reported.png).
