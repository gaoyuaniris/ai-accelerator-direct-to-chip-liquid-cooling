# Project 2 — Direct-to-chip liquid cooling

Day 1 model for an eight-accelerator liquid-cooled tray at the rack/CDU boundary.

## Run the model

Open Terminal in this folder and run:

```bash
python3 scripts/day1_energy_balance.py
```

No additional Python packages are required. Results are written to `results/`.

## Baseline

- 8 accelerators at 600 W each
- 4.8 kW total liquid heat
- Water at constant `rho = 997 kg/m3` and `cp = 4180 J/(kg K)`
- TCS supply: 30 degC
- Target coolant rise: 10 degC
- Required total flow: approximately 6.911 L/min
- Ideal equal branch flow: approximately 0.864 L/min

## Day 1 files

- `requirements/system_requirements.csv` — frozen assumptions and requirements
- `figures/system_architecture.svg` — labeled coolant architecture
- `calculations/baseline_calculation.md` — hand calculation
- `scripts/day1_energy_balance.py` — runnable Python model
- `scenarios/day1_scenarios.csv` — uniform, nonuniform, and restricted-branch cases
- `results/` — generated calculation outputs
- `tests/test_day1_energy_balance.py` — verification checks

## Run the checks

```bash
python3 -m unittest discover -s tests -v
```

## Portfolio case study

This portfolio covers the later 6.0 kW, eight-device study. The original Day 1 model and its 4.8 kW baseline remain documented above.

Read the [two-page case study](docs/portfolio/portfolio/Project2_Case_Study.pdf) for the engineering objective, modeling workflow, and principal findings.

The [portfolio overview](docs/portfolio/README.md) includes the reported data and figures. See the [figure guide](docs/portfolio/docs/FIGURE_GUIDE.md) and [validation and limitations](docs/portfolio/docs/VALIDATION_AND_LIMITATIONS.md) for source provenance and model assumptions.

This is a model-based study; the portfolio distinguishes CFD-to-ROM agreement from system-level predictions and does not claim hardware qualification.

See the [repository verification and source discrepancies](docs/portfolio/docs/REPOSITORY_INTEGRATION.md) for the current test results and the unresolved difference between packaged fixed-flow sensitivity results and local CSV exports.
