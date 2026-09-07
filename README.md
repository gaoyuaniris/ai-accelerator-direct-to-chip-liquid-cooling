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

