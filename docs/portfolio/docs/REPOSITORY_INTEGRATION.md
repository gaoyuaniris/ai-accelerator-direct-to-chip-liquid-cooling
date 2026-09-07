# Repository integration and verification — 2026-09-07

## Bundle completeness follow-up — 2026-09-07

The follow-up documentation branch is based on the newer `main` commit `1a2a6a3a0dcac2b7d38413fc3dc88379837929e8`. It preserves that expanded root README with corrected package-relative links, the repository-level check command, and source/validation context. The historical Day 1 README preservation described below applies to the original documentation commit `1f455218b8cd628fa344637f55ba1f99836c1715`; the owner subsequently replaced the root README on `main`.

All 46 files under the ZIP's `payload/docs/portfolio/` remain byte-for-byte unchanged, including both package navigation files and the 45-entry manifest. The five outer packaging files and the ZIP itself remain excluded as directed by the bundle. The 47 non-README files from the current main branch are unchanged. No simulation or data correction is part of this follow-up.

The follow-up passed 46 ZIP-to-file comparisons, 45 original manifest hashes, all 91 relative links across the root README and portfolio Markdown, and 91 documentation-package checks. The available project suite was rerun in the same existing Python environment: **31 tests passed in 7.25 seconds, exit 0**, using `python -B -m pytest -p no:cacheprovider tests/`. The integration checks below describe the earlier run. Neither run represents a new CFD solve or hardware test.

This dated note records verification against the actual Project 2 source files. The original portfolio package is retained byte-for-byte as a historical snapshot of reported results. Statements in the original packaging checklist about unavailable repository access or tests not run describe that earlier packaging stage; current integration results are recorded here.

## Repository and preservation

The supplied local project had no Git repository or configured remote. With the owner's explicit authorization, a new private repository, `gaoyuaniris/project2-ai-server-liquid-cooling`, was created. A reviewed baseline contains 48 existing Project 2 source, test, documentation, figure, and CSV files. Every baseline file was checked against its original SHA-256 before committing. The documentation branch adds the portfolio and appends links to the root README. The source folder remains unchanged.

The root README retains the original Day 1 4.8 kW / 600 W-per-device model. This portfolio describes the later 6.0 kW / 750 W-per-device study; these are different study baselines.

Virtual environments, caches, ZIP archives, staging task files/reports, credentials, and unrelated files are excluded. No license, solver, model assumption, coefficient, original export, test, or tolerance was changed. The original 45-entry `MANIFEST.sha256` continues to verify the supplied package files; this integration note is an additional repository document outside that original manifest.

## Actual checks and scope

- The included documentation checker passed all 85 original package checks after integration and **91 checks in the final run**, including the six source links added in this note. These are documentation/evidence/arithmetic checks, not model validation.
- The full available collected project suite passed: **31 tests passed in 7.82 seconds, exit 0**. This comprises 6 branch-hydraulics tests, 21 parametrized cold-plate ROM cases, and 4 Day 1 energy-balance tests.
- Tests ran in the isolated repository copy using the original project's existing `.venv/bin/python`: `python -B -m pytest -p no:cacheprovider tests/`. Python 3.14.0; pytest 9.1.1; NumPy 2.5.2; SciPy 1.18.1; pandas 3.0.5; Matplotlib 3.11.1. Bytecode and pytest caches were disabled; Matplotlib and temporary caches were directed outside the repository.
- The root README's historical unittest command alone does not collect the pytest function tests. Use pytest for the available complete test suite. No dependency manifest was present; the successful run used the existing local environment and does not establish clean-environment reproducibility.
- Standalone simulation, fitting, and plotting workflows were not rerun. `tests/ROM_fitting_workflow.py` is a workflow script, not a collected test module. No new CFD solve or hardware experiment was performed.
- The unchanged source baseline has 310 pre-existing whitespace findings under Git's default `diff --check` (exit 2), including CSV line endings and trailing blank/space lines. Those source bytes were preserved.
- The full staged documentation `git diff --cached --check` exits 2 with 3,526 inherited formatting findings: 68 CRLF CSV lines and 3,458 SVG whitespace lines in the original bundle. They are retained to preserve the supplied files and all original manifest hashes. The deliberately authored root README addition and this integration note pass the same whitespace check (exit 0). These formatting findings are distinct from the successful package and engineering tests.
- Both PDFs (three pages total), both DOCX documents (three rendered pages), 17 portfolio PNGs, and four portfolio SVGs passed integrity and visual review. Nine original project PNGs and the Day 1 architecture SVG also passed review. Focused text/metadata and visual privacy review found no credentials or sensitive content; author attribution is Yuan Gao. Some supplied evidence screenshots are cropped fragments, with ancillary lines cut at their edges; originals are retained.

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

## Consistency that was verified

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

No Candidate C COMSOL field export, complete COMSOL source model, or verified tray CAD/layout was available in the inspected project. None was fabricated or replaced by Project 1 imagery. Optional combined Projects and Skills documents and their Project 1 supporting evidence remain separate resume materials; they are not Project 2 model results. The [evidence index](../data/source_manifest.csv) retains the distinction between screenshot transcriptions and original solver exports.
