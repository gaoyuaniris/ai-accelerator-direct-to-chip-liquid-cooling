# Repository verification and data provenance

The repository contains the component ROM, eight-branch hydraulic/thermal model, reported CFD evidence, and pump/fault results for the 6 kW study. The root README remains the engineering overview. This record explains the checks that can be reproduced and the remaining data-provenance limits.

## Current repository checks — 2026-09-11

From the repository root, use a Python environment with NumPy, SciPy, pandas, Matplotlib and pytest installed:

```bash
python -B -m pytest -p no:cacheprovider tests/
python -B docs/portfolio/scripts/check_package.py
```

The retained engineering suite passed **27 tests**: 21 component-ROM cases and six branch/manifold checks. Four tests belonging only to the retired Day 1 energy-balance example were removed with that example; current model tests and tolerances are unchanged. This run used the existing project environment: Python 3.14.0, pytest 9.1.1, NumPy 2.5.2, SciPy 1.18.1, pandas 3.0.5 and Matplotlib 3.11.1. It is not a clean-environment dependency-installation test.

The documentation checker verifies source-file presence, links, reported tables, thermal margins, pump-power arithmetic and separation of the 1.15 L/min withheld point from calibration. `tests/ROM_fitting_workflow.py` preserves the seven fitting inputs; it is a standalone workflow rather than a collected regression test. No CFD solve, model refit, full-tray simulation rerun or hardware test was performed during this cleanup.

The cleanup passed **101 documentation-package checks**, **80 Markdown link/anchor checks**, and **39 package-file hash checks**. A byte comparison against the starting commit also confirmed that all **58 retained README, model, test, data, figure and evidence files** are unchanged.

## Retained evidence and file integrity

The cleanup starts from main commit `3f96cc093bad398de571582e94aeada89ab568a3`. The root README, final model implementations, current tests, calibration/fault/operating-point data, source screenshots, figures, and Project 2 case-study documents are preserved byte-for-byte. The earlier 4.8 kW exercises, unused two/three-branch examples, development plans, and job-preparation materials are available in Git history rather than the current file tree.

[MANIFEST.sha256](../MANIFEST.sha256) records the current supporting-document package, including updated navigation and this verification note. It has been refreshed for the retained files; it no longer describes the original ZIP byte-for-byte. To verify it from the repository root:

```bash
python -c "import hashlib,pathlib; p=pathlib.Path('docs/portfolio'); rows=[line.split('  ',1) for line in (p/'MANIFEST.sha256').read_text().splitlines()]; assert all(hashlib.sha256((p/name).read_bytes()).hexdigest()==digest for digest,name in rows); print('Package hashes match')"
```

The [source index](../data/source_manifest.csv) retains the original Project 2 source identifiers. Its `original_sha256` column refers to the supplied originals, before any documented screenshot cropping; it is not a hash of the current packaged image. The Project 1-only entry E09 was removed without renumbering the remaining sources. Numerical source values and precision notes are unchanged.

## Unresolved fixed-flow sensitivity discrepancy

The [packaged fixed-flow table](../data/fixed_flow_sensitivity_reported.csv) agrees with the [E05 reported screenshot](../evidence/tray_fixed_flow_sensitivity_reported.png), but differs from the current [local-loss sensitivity CSV](../../../network_solver/network_model/tray_local_loss_sensitivity.csv) and [engineering summary CSV](../../../network_solver/network_model/tray_engineering_summary.csv). The two local exports agree with each other. All three K cases differ beyond output rounding, including flow extrema, flow maldistribution, device temperature, temperature spread, and thermal margin.

| Header K | Metric | Packaged E05 | Current local CSV |
|---:|---|---:|---:|
| 0 | Flow maldistribution (%) | 0.346615 | 0.337225793791 |
| 0 | Minimum branch flow (L/min) | 1.078817 | 1.078848881898 |
| 0 | Maximum branch flow (L/min) | 1.082560 | 1.082490920471 |
| 0 | Peak estimated device temperature (°C) | 73.443085 | 73.442712849078 |
| 0 | Full-tray temperature spread (°C) | 0.043362 | 0.042188035896 |
| 0 | Thermal margin (°C) | 11.556915 | 11.557287150922 |
| 1 | Flow maldistribution (%) | 4.261041 | 4.148477770342 |
| 1 | Minimum branch flow (L/min) | 1.066133 | 1.066502474965 |
| 1 | Maximum branch flow (L/min) | 1.112153 | 1.111306034885 |
| 1 | Peak estimated device temperature (°C) | 73.591841 | 73.587472788565 |
| 1 | Full-tray temperature spread (°C) | 0.526503 | 0.512769039198 |
| 1 | Thermal margin (°C) | 11.408159 | 11.412527211435 |
| 2 | Flow maldistribution (%) | 8.039091 | 7.831373600313 |
| 2 | Minimum branch flow (L/min) | 1.053891 | 1.054574692169 |
| 2 | Maximum branch flow (L/min) | 1.140713 | 1.139153527052 |
| 2 | Peak estimated device temperature (°C) | 73.738185 | 73.729942517769 |
| 2 | Full-tray temperature spread (°C) | 0.982132 | 0.957322763313 |
| 2 | Thermal margin (°C) | 11.261815 | 11.270057482231 |

At K=2, packaged maldistribution is higher by 0.207717 percentage points and peak estimated temperature by 0.008242 °C. Both records show eight branches in range and PASS under the adopted criteria. No artifact establishes which run/configuration is authoritative, and no cause or run date has been inferred. Both provenance records are retained without substitution, refitting, or regeneration. Reconcile against the originating run/configuration before treating the packaged fixed-flow values as the current model output.

## Reported-data consistency

The following checks were recorded during source integration. The listed source files remain unchanged in this cleanup.

- Four ROM coefficients and four input bounds match the current component source.
- Seven calibration rows match the literal fitting inputs (21 values). The 1.15 L/min holdout remains absent from calibration.
- Six fault scenarios match the current export at the package's reported precision (30 numeric comparisons and six PASS/FAIL families).
- Five withheld-point outputs reproduce algebraically from the reported coefficients and current thermal defaults to 1e-12 absolute tolerance. No model module was imported for that comparison and no refit was performed.
- Nominal flow, tray pressure, minimum branch flow, maldistribution, estimated peak temperature, thermal margin, and electrical pump power agree with the nominal fault-export row after rounding.

The source hashes at review were:

| Source | SHA-256 |
|---|---|
| `component_rom/coldplate_rom.py` | `8bedbb4cff30cd0f0ee79295c7d06d04615130eb49609a840ab6c1d0e2d54e98` |
| `tests/ROM_fitting_workflow.py` | `3d9afe97091b2bf82b9522f74e062879a19dc12d95287db8618073482765f253` |
| `network_solver/network_model/fault_offdesign_summary.csv` | `65544f377a052b59f340ac2a1e66fde792226134a01d42872e5ca5715b4ecd6e` |
| `network_solver/network_model/tray_engineering_summary.csv` | `177c7a7b4810ae2babb3453a12843d1e823f803530f94dcfbdab3f1b911bb150` |
| `network_solver/network_model/tray_local_loss_sensitivity.csv` | `d19d37a10f73a59c32369ee0a115f9c8400c042572e5c2850b7c19273b26c02e` |

## Remaining engineering and presentation limits

The [validation notes](VALIDATION_AND_LIMITATIONS.md) continue to apply. ROM-to-COMSOL agreement is not hardware validation. Pump/QD/fitting inputs are illustrative; estimated device temperatures include assumed package/TIM resistance. The 35 °C cases are constant-property sensitivity cases. The fixed 8.64 L/min target and 10% maldistribution limit are project criteria. The recorded 1.10 L/min thermal-resistance precision discrepancy (0.02600 versus 0.0260393 K/W) remains unresolved.

No Candidate C COMSOL field export, complete COMSOL source model, or verified tray CAD/layout is included. The architecture schematic illustrates the model, not a released mechanical layout. The [evidence index](../data/source_manifest.csv) distinguishes screenshot transcriptions from original solver exports.
