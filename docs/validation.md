# Validation and limitations

## Evidence levels

| Level | What is supported | What is not established |
|---|---|---|
| Reported component CFD | Candidate C flow results and the withheld 1.15 L/min comparison | Hardware agreement or all mesh settings independently inspected here |
| CFD-derived ROM | Reported seven-point fit and off-grid comparison; clear input/output definitions | Guaranteed accuracy everywhere in a multidimensional rectangular envelope |
| Python consistency | Component ROM and branch/manifold regression tests; recorded solver outputs | Full-tray experimental validation or a reproduced CFD study |
| Tray system | Reported flow/temperature/pump/fault predictions under the stated assumptions | A physically built or CFD-qualified complete tray |
| 35°C inlet cases | Fixed-property sensitivity results | Validation of material/property behavior at 35°C |

## Interpretation of the results

**“In range” is not the same as hardware-validated.** The extended flow range is 0.50–1.20 L/min at the fixed Candidate C geometry. The main flow sweep is at 750 W and 30°C. Power dependence was sampled at selected flows, not every combination. The 35°C fault cases must not acquire an unqualified “ROM validated” label merely because the software accepts their input.

**The hottest valid subset is not automatically the complete tray maximum.** Earlier local-loss cases had missing high-flow branches. The E05 updated analysis includes all eight branches; only that complete version is used for final fixed-flow thermal-spread numbers.

**Pump power is boundary-specific.** The reported 11.4374 kPa is S1-to-R1 tray differential pressure. Common inlet/outlet lines, CDU heat exchanger/filter losses, and facility plumbing are excluded. The 3.4924 W estimate uses 50% efficiency and an illustrative curve, not a measured motor/pump map. The weak-pump curve changes only its head parameter; it is not a validated speed-control simulation.

**Hydraulic assumptions are not component qualification data.** The QD/fitting K values are sensitivity inputs. They are referenced to a defined branch-tube area. Header local-loss coefficients are separate from branch losses; they should not be double-counted. No manufacturer Δp-flow data was supplied for a final QD selection.

**The network is a simplified resistive model.** Darcy–Weisbach / Churchill segment losses do not, by themselves, establish junction-specific static-pressure recovery, division/combination losses, entry effects, or actual manifold CFD behavior. Continuous friction-factor evaluation removes a numerical discontinuity; it does not eliminate physical transition uncertainty. The nominal low maldistribution should remain an idealized baseline.

**Temperature terminology matters.** Package/TIM resistance is added to maximum base temperature using a lumped series estimate. The result is “estimated device temperature,” not a resolved junction temperature or vendor-qualified package thermal path. The 85°C threshold and 10% flow-maldistribution threshold are project criteria.

**Restriction is not blocked-area percentage.** The multiplier 1.30 perturbs the total branch pressure-flow curve. It does not resolve blockage inside the cold plate or the resulting local heat-transfer changes. Interpreting it as an upstream/downstream hydraulic restriction leaves the thermal cold-plate map unchanged; an internal obstruction would need separate evidence.

**Fixed target versus thermal failure.** The reported fault status uses a fixed 8.64 L/min design target. The uneven-power and combined scenarios total 4.95 kW, but the target is unchanged. Thus “FAIL—flow target” records the chosen requirement, not proof that the coolant cannot remove that heat load. A load-following requirement would be a separate analysis, not a silent replacement of the reported result.

## Data precision

The tables in `data/reported/` are transcribed from supplied screenshots / fitting arrays; original available solver exports remain under `network_solver/network_model/`. The reported fitting array uses Rθ = 0.02600 K/W at 1.10 L/min, while a more detailed earlier screenshot reports 0.0260393 K/W. No correction or refit was made during packaging. This discrepancy should be reconciled against the authoritative export if higher-precision model maintenance is performed.

The 1.15 L/min comparison uses the reported coefficient values and the thermal component defaults rho = 997 kg/m³, cp = 4180 J/(kg·K). It reproduces Δp = 11.260002 kPa, Rθ = 0.0256179 K/W, Tout = 39.3895°C, and Tbase,max = 53.9082°C. The corresponding pump-power calculation is 0.2158167 W; earlier conversational rounding should not replace this arithmetic.

## Recommended next validation gates—not completed claims

1. Maintain the component and branch/manifold regression suite as the model changes. The current test scope and run are recorded in [repository verification](verification.md).
2. Replace source transcriptions with raw CSV exports and keep the withheld 1.15 L/min point out of calibration.
3. Add vendor QD/pump data and a complete loop pressure budget before selecting hardware.
4. Validate selected manifold / junction cases with independent CFD or experiment.
5. Extend or qualify inlet-temperature behavior and transient/fault thermal behavior before claims of physical robustness.
6. Check the final mechanical arrangement. The numerical 50 mm inter-branch segment input is not evidence of mechanical fit or an assembly-ready CAD model.

Sources are indexed in [data/sources.csv](../data/sources.csv), especially E01–E08 and E10. The [model inputs and source map](methods.md) connect those records to the implementation.

The [architecture schematic](../figures/system_architecture.svg) describes the model boundary and components. A final Candidate C temperature-field export and verified mechanical CAD/layout are not included.
