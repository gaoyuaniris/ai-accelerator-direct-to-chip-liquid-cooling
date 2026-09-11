# Reproducibility and data checks

This record covers software checks, data provenance and the unresolved difference between two fixed-flow studies. See [methods](methods.md) for model inputs and [validation](validation.md) for the limits of the numerical evidence.

## Run the checks

From the repository root, use a Python environment with NumPy, SciPy, pandas, Matplotlib and pytest installed:

```bash
python -B -m pytest -p no:cacheprovider tests/
python -B scripts/check_evidence.py
```

The retained engineering suite comprises **27 tests**: 21 component-ROM cases and six branch/manifold checks. The recorded passing run used Python 3.14.0, pytest 9.1.1, NumPy 2.5.2, SciPy 1.18.1, pandas 3.0.5 and Matplotlib 3.11.1. This documents the tested environment, not a fresh dependency-installation test.

The evidence checker verifies README and supporting-document links, image references, section anchors, source-file presence, file checksums, reported thermal margins, pump-power arithmetic, and exclusion of the 1.15 L/min withheld point from calibration. The [fitting workflow](../tests/ROM_fitting_workflow.py) preserves the seven fitting inputs; it is not a collected regression test. These checks do not run COMSOL, refit the ROM or experimentally validate a tray.

The current layout passed **27 model tests** and **154 evidence checks**, including all **18 README link/image targets**, section anchors, and **31 file checksums**. The link checker also rejected deliberately broken file and section references in isolated checks.

## Source records and file integrity

[Reported tables](../data/reported/rom_calibration_transcribed.csv) retain their original numerical values and precision. Full-precision solver outputs remain alongside the corresponding model in `network_solver/network_model/`. The [source index](../data/sources.csv) identifies the screenshots and model-setting record behind the reported results; its `repository_path` values resolve from the repository root.

The source index's `original_sha256` values refer to supplied originals before documented screenshot cropping. [Current checksums](../data/checksums.sha256) verify the retained data, evidence images, figures and case-study files at their present paths. The evidence checker verifies these hashes automatically. The PDF and editable Word case study are two formats of the same short report, while the README is the single project overview.

The folder cleanup changes navigation and file locations; it does not alter model coefficients, final numerical results, source screenshots or result figures. Older development materials remain in Git history.

## Unresolved fixed-flow sensitivity discrepancy

The [reported fixed-flow table](../data/reported/fixed_flow_sensitivity_reported.csv) agrees with the [E05 reported screenshot](../data/evidence/tray_fixed_flow_sensitivity_reported.png), but differs from the current [local-loss sensitivity CSV](../network_solver/network_model/tray_local_loss_sensitivity.csv) and [engineering summary CSV](../network_solver/network_model/tray_engineering_summary.csv). The two local exports agree with each other. All three K cases differ beyond output rounding, including flow extrema, flow maldistribution, device temperature, temperature spread, and thermal margin.

| Header K | Metric | Reported E05 | Current local CSV |
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

At K=2, reported maldistribution is higher by 0.207717 percentage points and peak estimated temperature by 0.008242 °C. Both records show eight branches in range and PASS under the adopted criteria. No artifact establishes which run/configuration is authoritative, and no cause or run date has been inferred. Both provenance records are retained without substitution, refitting, or regeneration. Reconcile against the originating run/configuration before treating the reported fixed-flow values as the current model output.

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
