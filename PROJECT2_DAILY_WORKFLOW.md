# Project 2 Daily Workflow

## Thermal-Hydraulic Optimization of a Parallel Liquid-Cooling Network for High-Power AI Servers

This nine-day plan is designed to produce three outcomes every day:

> **Knowledge + engineering result + portfolio evidence**

The objective is not only to finish the repository. By the end, you should be able to reason independently from heat load to coolant flow, pressure drop, device temperature, pump selection, optimization, and validation—and defend your choices in an interview.

## Project scope

### Engineering question

How should coolant flow be distributed through eight parallel cold plates to keep every accelerator below its temperature limit while minimizing flow maldistribution and pumping power?

### Included

- Eight accelerator cold plates
- Supply and return manifolds
- Variable device heat loads
- Parallel hydraulic-network modeling
- Pressure losses and pump/system curves
- Cold-plate reduced-order modeling (ROM)
- Thermal-hydraulic coupling
- Flow-maldistribution analysis
- Constrained design optimization
- Targeted COMSOL validation
- Instrumentation and product-validation planning

### Boundary conditions

- The CDU supplies a specified coolant temperature.
- The CDU/pump is represented by an available pressure or pump curve.
- The detailed CDU and facility cooling plant are outside the model boundary.

### Excluded

- Detailed CDU design or controls
- Chillers, cooling towers, and facility-water systems
- Full data-center airflow or CFD
- Two-phase and immersion cooling
- Detailed coolant chemistry or economic/TCO analysis

## Core learning method

Use this loop for every major task:

```text
Learn the concept
      ↓
Solve a small example yourself
      ↓
Build the first version yourself
      ↓
Ask ChatGPT to review it
      ↓
Use Work mode to scale and organize it
      ↓
Interpret the results yourself
      ↓
Explain the result back to ChatGPT
      ↓
Answer interview-style challenges
      ↓
Revise
```

Apply the **20-minute struggle rule**: before requesting a complete solution, spend 15–20 focused minutes defining the problem, attempting the derivation or implementation, and recording exactly where you became stuck.

> Do not outsource anything that you expect an interviewer to ask you to explain.

## Daily routine

Use the full routine for a serious project day. Shorten the scale or documentation blocks when only 5 hours are available; do not remove the derive, build, or interpret blocks.

| Block | Time | Purpose | Lead |
|---|---:|---|---|
| 1. Learn | 45 min | Understand the day's physics or engineering concept | You + ChatGPT |
| 2. Derive | 30–45 min | Work one representative example manually | **You** |
| 3. Build | 60–90 min | Create the first simple model, script, or setup | **You** |
| 4. Review | 30 min | Check assumptions, equations, units, and physics | ChatGPT |
| 5. Scale | 60–90 min | Run sweeps, automate calculations, and organize outputs | Work mode |
| 6. Interpret | 30–45 min | Explain the physical meaning and trade-offs | **You** |
| 7. Document | 20–30 min | Save results, decisions, and the learning log | You + Work mode |
| 8. Interview | 15–20 min | Explain the work without notes and answer challenges | You + ChatGPT |

Never let Work mode perform Blocks 2, 3, or 6 before you understand them. Those blocks create most of the transferable skill.

## Division of responsibilities

| Activity | You | ChatGPT | Work mode |
|---|---|---|---|
| Understand the physical architecture | Own understanding | Explain and challenge | — |
| Derive important equations | Derive first | Check the derivation | — |
| Define assumptions | Decide and justify | Test realism and completeness | Record them |
| Hand-calculate the first example | Calculate first | Verify independently | — |
| Write the first simple model | Build first | Review and help debug | — |
| Run parameter sweeps | Understand the setup | Review sweep design | Automate execution |
| Set up COMSOL physics | Own setup and boundary choices | Review strategy | Process exported data |
| Diagnose unexpected results | Think and form hypotheses first | Challenge hypotheses | Reproduce and compare cases |
| Generate repetitive plots | Choose what matters and interpret | Review clarity | Generate consistently |
| Organize files and results | Supervise | Suggest structure | Maintain artifacts |
| Write conclusions | Draft the engineering claims | Edit and challenge | Package the report |
| Prepare for interviews | Explain without notes | Act as interviewer | Organize question bank |

## Nine-day task plan

### Day 1 — Requirements and system architecture

**Learn**

- Direct-to-chip liquid cooling
- TCS/CDU model boundary
- Supply and return manifolds
- Parallel cold plates
- Coolant energy balance and supply/return temperature

Core equation:

$$Q=\dot m c_p\Delta T$$

**You do**

1. Calculate the total heat load for eight 600 W devices:

   $$Q_{total}=8\times600=4.8\ \text{kW}$$

2. Calculate required total flow, ideal branch flow, and return temperature.
3. Repeat the flow calculation for coolant temperature rises of 8°C, 10°C, and 12°C.
4. Write the first small energy-balance script yourself.
5. State every design assumption and classify it as requirement, boundary condition, estimate, or unknown.

**ChatGPT review**

Ask for a senior-engineer review of unclear, unrealistic, or incorrectly classified assumptions.

**Work mode outputs**

```text
system_requirements.csv
workload_scenarios.csv
system_architecture.png
day1_energy_balance.py
```

**End-of-day check**

- Explain why 4.8 kW requires about 6.9 L/min for a 10°C water temperature rise.
- Explain why that total flow may not divide equally among eight branches.

### Day 2 — Cold-plate reduced-order model

**Learn**

- Thermal resistance
- Pressure-drop curves
- Curve fitting and fit error
- Interpolation versus extrapolation

Core relationships:

$$R_\theta=\frac{T_{max}-T_{coolant}}{Q}$$

$$\Delta p=f(\dot V)$$

**You do**

1. Select representative cold-plate flows, such as 0.5–1.1 L/min, and several device powers.
2. Run a small set of COMSOL calibration cases.
3. Define and justify models for $R_\theta=f(\dot V,Q)$ and $\Delta p=f(\dot V)$.
4. Inspect residuals and establish the model's valid domain.

Do not reuse a Project 1 surrogate outside its validated power and flow range. Reuse the methodology, not unsupported extrapolation.

**Work mode outputs**

```text
coldplate_calibration.csv
coldplate_rom.py
Rth_vs_flow.png
pressure_drop_vs_flow.png
fit_validation.csv
```

**End-of-day check**

Explain why a component ROM is preferable to placing eight detailed microchannel cold plates inside the rack CFD model.

### Day 3 — Hydraulic component modeling

**Learn**

$$Re=\frac{\rho VD}{\mu}$$

$$\Delta p=f\frac{L}{D}\frac{\rho V^2}{2}$$

$$\Delta p=K\frac{\rho V^2}{2}$$

Study resistance from straight tubing, bends, quick disconnects, valves, cold plates, manifold segments, and branch restrictions.

**You do**

1. Hand-calculate one complete branch: tube + QD + cold plate + return tube.
2. Calculate Reynolds number, select the friction-factor relation, and show units.
3. Calculate every loss separately and verify:

   $$\Delta p_{branch}=\sum_j\Delta p_j$$

4. Identify which inputs are measured, vendor-provided, correlated, or assumed.

**ChatGPT review**

Request a check of Reynolds number, friction factor, units, loss coefficients, and modeling assumptions.

**Work mode outputs**

```text
hydraulic_components.py
component_pressure_losses.csv
pressure_loss_breakdown.png
```

**End-of-day check**

Identify the dominant branch pressure loss and explain at least two ways to reduce it.

### Day 4 — Eight-branch hydraulic network

**Learn**

$$\dot V_{total}=\sum_{i=1}^{8}\dot V_i$$

Parallel branches share pressure boundary conditions, but differing manifold node pressures can produce unequal branch flows even when branch geometry is nominally identical.

**You do**

1. Solve a two-branch network first.
2. Check mass conservation and pressure compatibility explicitly.
3. Extend the understood equations to eight branches.
4. Define flow maldistribution:

   $$M=\frac{\dot V_{max}-\dot V_{min}}{\dot V_{avg}}\times100\%$$

5. Create at least one hand-checkable limiting case for solver verification.

**Work mode outputs**

```text
branch_flow_rates.csv
manifold_node_pressure.csv
mass_balance_check.csv
flow_distribution.png
```

**End-of-day check**

Explain why an equal-geometry system can still develop flow maldistribution and how you know the nonlinear solver is correct.

### Day 5 — Thermal-hydraulic coupling

**Learn**

$$T_{max,i}=T_{coolant,i}+Q_iR_{\theta,i}$$

$$T_{out,i}=T_{in,i}+\frac{Q_i}{\dot m_i c_p}$$

**You do**

Evaluate at least three scenarios:

1. Uniform power: $Q_i=600\ \text{W}$.
2. Nonuniform power: 450, 550, 650, 750, 750, 650, 550, and 450 W.
3. A partially restricted branch.

For each scenario, identify the hottest device and separate the contributions from heat load, coolant flow, and inlet coolant temperature.

**Work mode outputs**

```text
device_temperature_distribution.png
flow_vs_temperature.png
scenario_comparison.csv
thermal_margin.csv
```

**End-of-day check**

Do not stop at “device 4 was hottest.” Explain the physical chain that made it hottest and identify the most effective corrective action.

### Day 6 — Pump curve and constrained optimization

**Learn**

$$\Delta p_{system}=f(\dot V)$$

$$\Delta p_{pump}=g(\dot V)$$

Their intersection is the operating point. Also use:

$$P_{hyd}=\Delta p\dot V$$

$$P_{electrical}\approx\frac{\Delta p\dot V}{\eta_{pump}}$$

**You do**

1. Sketch one pump curve and one system curve manually.
2. Explain how a resistance change moves the operating point.
3. Define design variables such as total flow, supply diameter, return diameter, and balancing resistance.
4. Formulate the primary objective:

   $$\min P_{pump}$$

   subject to:

   $$T_{max,i}\le85^\circ\text{C}\quad\forall i$$

   $$M_{flow}\le10\%$$

5. Select and defend three designs: lowest pumping power, lowest temperature, and a balanced recommendation.

**Work mode outputs**

```text
candidate_design_space.csv
pareto_front.csv
selected_designs.csv
pareto_front.png
pump_system_curve.png
```

**End-of-day check**

Defend why the selected balanced design is preferable to both extreme designs.

### Day 7 — COMSOL validation

**Learn**

- Manifold CFD strategy
- Inlet and outlet boundary conditions
- Branch-flow integration
- Mesh independence
- Mass balance
- Pressure-drop and flow-distribution comparison

**You do**

1. Build only the supply manifold, eight simplified branches, and return manifold.
2. Validate baseline, optimized, and restricted-branch cases.
3. Compare Python and COMSOL branch flows.
4. Complete a mesh-independence and mass-balance check.
5. Investigate discrepancies before changing the model.

Potential discrepancy sources include junction losses, 3D manifold effects, recirculation, simplified loss coefficients, and entrance effects.

**Work mode outputs**

```text
comsol_python_comparison.csv
validation_error_summary.csv
branch_flow_parity.png
mesh_independence.csv
```

**End-of-day check**

Explain where the reduced-order model disagrees most with CFD, why, and whether the difference affects the engineering decision.

### Day 8 — Product engineering and validation plan

**Learn**

- Quick disconnects and serviceability
- Leak and proof-pressure testing
- Sensors and data acquisition
- Manufacturing tolerances
- Material compatibility and filtration
- Rack/OCP interface awareness

**You do**

Create an instrumentation and test plan covering at least:

| Quantity | Example measurement |
|---|---|
| Total flow | Main flow meter |
| Branch flow | Branch flow meter or inferred hydraulic measurement |
| Pressure drop | Differential-pressure sensor |
| Coolant inlet/outlet temperature | RTD or thermocouple |
| Device temperature | Calibrated temperature sensor |
| Pump power | Electrical power meter |

For every sensor, define range, accuracy, location, and purpose. Add a test matrix for normal operation, uneven loads, a restricted branch, startup/shutdown, and sensor uncertainty.

**Work mode outputs**

```text
instrumentation_plan.csv
test_matrix.csv
failure_modes.csv
serviceability_review.md
```

**End-of-day check**

Explain which measurements would reveal a branch beginning to clog and how you would distinguish clogging from a faulty sensor.

### Day 9 — Portfolio and interview package

No new physics today. Freeze the technical work and make it defensible.

**You do**

1. Audit requirements, physics, network model, optimization, COMSOL validation, uncertainties, and limitations.
2. Write the engineering conclusions before asking for editorial help.
3. Prepare a two-minute explanation:

   ```text
   Problem → Method → Key challenge → Result → Validation → Recommendation
   ```

4. Prepare a five-minute explanation that adds equations, trade-offs, optimization, CFD correlation, uncertainty, and limitations.
5. Answer progressively harder interview questions without notes.

Example questions:

- Why use eight parallel branches?
- How did you calculate manifold pressure variation?
- Why is Darcy–Weisbach appropriate here?
- How did you verify the Python solver?
- How would manufacturing tolerances change the result?
- What happens if a QD partially blocks?
- How would that fault be detected experimentally?
- Why did the ROM and CFD disagree?
- How would this architecture scale to a rack?

**Work mode outputs**

- Consistent repository structure and filenames
- Reproducible figures and tables
- Final README and methods summary
- Curated validation and optimization results
- Interview question bank

**End-of-day check**

Give the two-minute explanation cleanly, defend the recommended design, and name the model's three most important limitations.

## Daily definition of done

Do not mark a day complete until all of the following are true:

- [ ] I can state the day's engineering question in one sentence.
- [ ] I completed at least one derivation or hand calculation myself.
- [ ] I built or configured the first simple version myself.
- [ ] Units, conservation laws, and limiting cases were checked.
- [ ] I reviewed automated outputs instead of accepting them blindly.
- [ ] I can explain the physical meaning of the result without notes.
- [ ] I saved one engineering result and one portfolio-quality artifact.
- [ ] I recorded assumptions, problems, decisions, and open questions.
- [ ] I answered the day's interview question.

## Daily learning log template

Save one log per day under `notes/`, for example `notes/day01_learning_log.md`.

```markdown
# Day X Learning Log

**Date:** YYYY-MM-DD
**Today's engineering question:**

## What I learned

## Most important equation

## Physical intuition

## Hand calculation or limiting-case check

## Engineering decision I made

## Assumptions I used

| Assumption | Basis | Sensitivity | Validation needed? |
|---|---|---|---|
| | | | |

## Mistake or unexpected result

## My first hypothesis

## How I investigated and resolved it

## Key result and why it matters

## Portfolio evidence created

## What I can now explain in an interview

## Question I still cannot answer

## First task for tomorrow
```

Complete the log yourself in 10–15 minutes. ChatGPT may challenge or edit it afterward, but should not generate the initial reflection for you.

## Project success criteria

### Technical

- [ ] The total heat/flow balance is correct and unit-checked.
- [ ] Component pressure losses are traceable to equations, data, or documented assumptions.
- [ ] The eight-branch solver satisfies mass conservation and pressure compatibility.
- [ ] The solver passes simple limiting and hand-checkable cases.
- [ ] The cold-plate ROM has a stated validation domain and quantified fit error.
- [ ] The coupled model predicts flow, coolant temperature, and device temperature for each branch.
- [ ] Uniform, asymmetric-load, and restricted-branch scenarios are evaluated.
- [ ] Pump/system operating points and pumping power are calculated correctly.
- [ ] Optimization constraints include $T_{max,i}\le85^\circ\text{C}$ and $M_{flow}\le10\%$.
- [ ] The recommended design is justified against low-power and low-temperature alternatives.
- [ ] Python predictions are compared with targeted COMSOL cases, including quantified error.
- [ ] Important uncertainty, model limitations, and validation needs are stated honestly.

### Learning and interview readiness

- [ ] I can derive the heat/flow relation and the main pressure-loss equations without notes.
- [ ] I can explain why parallel branches maldistribute flow.
- [ ] I can diagnose whether a hot device is driven by load, flow, inlet temperature, or a combination.
- [ ] I can sketch pump and system curves and explain their intersection.
- [ ] I can explain how the solver was verified and the model was validated.
- [ ] I can defend every major assumption and design choice.
- [ ] I can explain discrepancies rather than only report them.
- [ ] I can give clear two-minute and five-minute project explanations.

### Portfolio and reproducibility

- [ ] The repository has a clear README, requirements, methods, results, validation, and limitations.
- [ ] Scripts run from documented inputs and reproduce the reported outputs.
- [ ] Units, variable names, figures, and filenames are consistent.
- [ ] Figures have readable labels, units, captions, and an engineering takeaway.
- [ ] Raw inputs are separated from processed results.
- [ ] Each of the nine daily learning logs is complete.
- [ ] The final package shows the progression from cold-plate component model to eight-branch system model to CFD validation.

## Final standard

The project is successful when you can receive a whiteboard problem about a high-power accelerator cooling loop and independently reason through:

```text
Heat load
→ required coolant flow
→ component and network pressure drop
→ branch-flow distribution
→ device temperatures
→ pump operating point
→ constrained design choice
→ verification and validation plan
```

The working repository is evidence. Your ability to explain, challenge, and defend the engineering is the outcome.
