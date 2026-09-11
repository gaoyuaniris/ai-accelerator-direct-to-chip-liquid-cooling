# Model inputs and methods

The [project overview](../README.md) presents the design decisions and results. This page records the inputs, calculation details, and source records needed to examine those results.

## Network and pump inputs

The nominal same-side manifold uses **19.05 mm supply and return header IDs**, with **0.050 m between branch nodes**. Each branch has **9.5 mm ID tubing**, comprising **0.30 m supply and 0.30 m return lengths**, two quick disconnects with **K = 1 each**, and other fittings with **aggregate K = 1**. These local-loss coefficients use branch-tube mean velocity. They are illustrative inputs rather than vendor pressure-drop curves.

The hydraulic model uses density **996 kg/m³**, viscosity **8.0 × 10⁻⁴ Pa·s**, and zero tube roughness. The thermal component uses **997 kg/m³** and **4,180 J/(kg·K)**. These fixed inputs retain the small density difference in the original model. Nominal header local-loss coefficients are zero; header-junction losses are explored separately as sensitivity inputs.

The illustrative pump characteristic is:

```math
\Delta p_{\mathrm{pump}} = H_0\left[1-\left(\frac{\dot V_T}{14\,\mathrm{L/min}}\right)^2\right]
```

The implementation clips negative pressure rise to zero. Nominal shutoff pressure is **H₀ = 20 kPa**. The weak-pump case changes it to **15 kPa** while retaining the same free-flow parameter; this is a head-capability sensitivity, not an affinity-law speed change. Electrical power divides hydraulic power by an assumed **50% efficiency**.

These settings are recorded in the [model source record](../data/evidence/CONVERSATION_MODEL_RECORD.md) and implemented in [branch hydraulics](../network_solver/components/branch_hydraulics.py) and [pump coupling](../network_solver/network_model/pump_operating_point.py).

## Calculation details

For N branches, the [manifold solver](../network_solver/network_model/n_branch_manifold.py) determines N branch flows using total-flow conservation and N−1 adjacent pressure-compatibility equations:

```math
\sum_{i=1}^{N}\dot V_i=\dot V_T,
\qquad
\Delta p_{b,i}-\Delta p_{b,i+1}=\Delta p_{s,i}+\Delta p_{r,i}.
```

Here, b denotes a complete branch and s/r denote the intervening supply/return segments. Each header segment carries the sum of downstream branch flows. Tube and header pressure losses combine Darcy–Weisbach friction with local-loss terms. The Churchill correlation provides numerical continuity across flow regimes; it does not remove the uncertainty in transitional flow or junction losses.

## CFD calibration and fit records

The seven calibration flows are **0.50, 0.60, 0.65, 0.80, 0.95, 1.10, and 1.20 L/min**, all at 750 W and 30°C inlet. The source map distinguishes fitting inputs from comparisons:

| Record | Available evidence |
|---|---|
| Seven-point fit | [Calibration inputs](../data/reported/rom_calibration_transcribed.csv), [coefficients](../data/reported/reported_rom_coefficients.json), and [reported refit output](../data/evidence/rom_refit_reported.png) |
| Withheld 1.15 L/min point | [COMSOL record](../data/evidence/comsol_validation_1p15_reported.png), [ROM output](../data/evidence/rom_validation_1p15_reported.png), and [comparison table](../data/reported/validation_1p15_comparison.csv) |
| Selected power checks | 450/600/750 W records at [0.65 L/min](../data/evidence/power_check_0p65_reported.png) and [1.10 L/min](../data/evidence/power_check_1p10_reported.png) |

The calibration array is a rounded transcription. At 1.10 L/min, its 0.02600 K/W value differs from the detailed power-check record's 0.0260393 K/W. A separate 0.864 L/min, 600 W point was excluded from fitting but inspected during development; it is not treated as an untouched validation case.

## Figure provenance

The hydraulic, thermal-resistance, and fault charts replot supplied numerical records. The header-sensitivity and pump figures preserve supplied plots. The architecture schematic explains the model boundary; no verified tray CAD layout or final Candidate C temperature-field export is included.

The [source index](../data/sources.csv) identifies the original records and any cropping. See [validation limits](validation.md) for evidence boundaries and [repository verification](verification.md) for current-code checks and unresolved reported-versus-exported differences.
