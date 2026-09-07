# Resume and interview copy

## Preferred Project 2 entry

### Thermal-Hydraulic Co-Design of a 6 kW AI Accelerator Cooling Tray
*Python | COMSOL Multiphysics | Direct-to-chip cooling | Reduced-order models*

- Developed a scalable Python thermal-hydraulic model of an **8-accelerator, 6 kW** liquid-cooling tray, integrating CFD-derived cold-plate ROMs, manifolds, branch hardware losses, and a representative pump curve.
- Calibrated physics-based cold-plate ROMs over **0.50–1.20 L/min**; reproduced a withheld COMSOL case within **0.25% thermal-resistance error** and **0.04°C maximum-base-temperature error**.
- Evaluated header sizing and six operating/fault scenarios; predicted **72.7°C** nominal peak device temperature with **12.3°C margin**, and identified **18.3% flow maldistribution** under a 30% branch-resistance increase before exceeding the temperature limit.

Use “modeled,” “predicted,” and “representative pump curve.” Do not replace these with hardware-validated / experimentally demonstrated / data-center energy savings.

## Project 1 entry, checked against the supplied final results package

### Physics-Based and ML-Assisted Microchannel Cold-Plate Optimization
*COMSOL Multiphysics | Python | Gaussian process regression | Pareto analysis*

- Built a 3D conjugate heat-transfer model for a **100 W, 10-channel** liquid cold plate and developed a Gaussian-process surrogate from a **45-case** flow/TIM design dataset.
- Used the surrogate to explore thermal–hydraulic tradeoffs and reran **three representative Pareto candidates in COMSOL** for high-fidelity confirmation.
- Selected a balanced **0.188 L/min** candidate with **64.73°C** maximum chip temperature; reduced hydraulic pumping power by **63.5%** versus the minimum-temperature candidate while retaining **20.27°C** temperature margin.

Project 1 final-package geometry is 0.30 × 0.70 mm per channel. Do not substitute the earlier 0.50 × 0.50 mm baseline when describing its confirmed final design. Its system resistance definition is also different from Project 2's mean-bulk-referenced resistance.

## Technical skills—four categories

**Thermal and liquid cooling:** Direct-to-chip cooling; cold plates and microchannels; conjugate heat transfer; thermal-resistance budgeting; lumped TIM/package modeling; thermal design margins.

**CFD and system modeling:** COMSOL Multiphysics; parametric CFD studies; physics-based ROMs; 0D/1D hydraulic networks; manifold flow distribution; Darcy–Weisbach and local-loss models; pump–system operating-point analysis.

**Programming and verification:** Python; NumPy; SciPy; pandas; Matplotlib; nonlinear solvers; pytest; numerical residual and conservation checks; data visualization; Git/GitHub.

**Surrogates and optimization:** Gaussian process regression; design of experiments; model fitting and cross-validation; held-out CFD comparisons; Pareto tradeoff analysis; sensitivity and fault-scenario studies.

## 90-second Project 2 explanation

“I built a model-based liquid-cooling design study for an eight-accelerator, six-kilowatt tray. I started with component CFD, screened cold-plate candidates, and converted the selected design into hydraulic and thermal reduced-order models. I kept energy conservation explicit rather than fitting every output independently.

“I then developed a scalable Python manifold solver, added branch tubing and representative QD losses, and coupled the tray resistance curve to an illustrative pump curve. The nominal prediction was 9.16 liters per minute and a peak estimated device temperature of 72.7 degrees Celsius, around 12.3 degrees below my project limit.

“The most useful result came from fault analysis: a 30 percent branch-resistance increase caused 18.3 percent flow maldistribution while the device remained below its temperature limit. That showed why I needed flow, uniformity, and temperature criteria together. I also kept model limits explicit: component CFD comparisons were quantitative, but the pump and fitting data were illustrative and the complete tray was not hardware-qualified.”

## Evidence mapping

Project 2 bullet 1: E02 and E10. Bullet 2: E03/E04 and `validation_1p15_comparison.csv`. Bullet 3: E01; nominal margin = 85 − 72.72 = 12.28°C. Project 1 bullets: E09, including its supplied README and confirmed-design CSV. The 63.5% reduction compares the knee candidate to the minimum-temperature candidate, not to a generic commercial cold plate.
