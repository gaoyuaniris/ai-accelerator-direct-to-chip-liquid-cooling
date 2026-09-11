# Start here: Project 2 files and portfolio

This guide organizes the existing **AI accelerator liquid-cooling tray** project by purpose. It does not move source files, replace results, or change the model. The [root README](README.md) remains the main technical overview.

## 1. Review or share the project

| What you need | Open this file |
|---|---|
| Quick engineering overview | [Two-page Project 2 case study (PDF)](docs/portfolio/portfolio/Project2_Case_Study.pdf) |
| Editable case study | [Project 2 case study (Word)](docs/portfolio/portfolio/Project2_Case_Study.docx) |
| Full technical narrative | [Portfolio README](docs/portfolio/README.md) |
| Figure order, captions, and sources | [Figure guide](docs/portfolio/docs/FIGURE_GUIDE.md) |
| Modeling assumptions and evidence limits | [Validation and limitations](docs/portfolio/docs/VALIDATION_AND_LIMITATIONS.md) |

The portfolio is a simulation-based engineering study. Its reported device temperatures include assumed package/TIM resistance; pump and QD/fitting inputs are illustrative. See the validation notes before presenting the results as hardware-qualified performance.

## 2. Prepare job applications

| What you need | Open this file |
|---|---|
| Project 1 + Project 2 bullets and categorized technical skills | [Editable projects and skills (Word)](docs/portfolio/portfolio/Selected_Projects_and_Skills.docx) |
| Read-only version | [Projects and skills (PDF)](docs/portfolio/portfolio/Selected_Projects_and_Skills.pdf) |
| Resume alternatives and interview explanation | [Resume and interview notes](docs/portfolio/docs/RESUME_AND_INTERVIEW.md) |

These combined documents are application materials. Their Project 1 content is not part of Project 2's simulation dataset.

## 3. Find results and supporting evidence

| Record | Purpose |
|---|---|
| [Fault/off-design solver export](network_solver/network_model/fault_offdesign_summary.csv) | Export stored with the analysis code |
| [Fixed-flow engineering summary](network_solver/network_model/tray_engineering_summary.csv) | Stored tray summary export |
| [Local-loss sensitivity export](network_solver/network_model/tray_local_loss_sensitivity.csv) | Stored sensitivity results |
| [Pump/system curve export](network_solver/network_model/pump_system_curve.csv) | Stored pump/tray curve data |
| [Portfolio evidence index](docs/portfolio/data/source_manifest.csv) | Maps reported results to their supporting records |
| [Reported nominal operating point](docs/portfolio/data/nominal_operating_point_reported.csv) | Portfolio presentation table, not a new solver export |
| [Reported fault matrix](docs/portfolio/data/fault_offdesign_reported.csv) | Portfolio transcription of supplied results |
| [Withheld 1.15 L/min comparison](docs/portfolio/data/validation_1p15_comparison.csv) | ROM-to-COMSOL comparison; not a calibration row |

**Read the [repository integration and verification record](docs/portfolio/docs/REPOSITORY_INTEGRATION.md) before combining results.** It documents a difference between the packaged historical fixed-flow sensitivity table and current repository CSVs, as well as a thermal-resistance precision discrepancy. Preserve both records until their originating run/configuration is reconciled. Do not silently substitute one for the other.

## 4. Continue development

Follow the component-to-system sequence:

| Layer | File or folder |
|---|---|
| Cold-plate hydraulic and thermal ROM | [component_rom/coldplate_rom.py](component_rom/coldplate_rom.py) |
| Branch-hardware components | [network_solver/components/](network_solver/components/) |
| General manifold/network solver | [n_branch_manifold.py](network_solver/network_model/n_branch_manifold.py) |
| Tray thermal coupling | [tray_thermal_coupling.py](network_solver/network_model/tray_thermal_coupling.py) |
| Pump/tray operating point | [pump_operating_point.py](network_solver/network_model/pump_operating_point.py) |
| Fault/off-design analysis | [fault_offdesign_analysis.py](network_solver/network_model/fault_offdesign_analysis.py) |
| Automated engineering tests | [tests/](tests/) |
| Earlier learning plan | [PROJECT2_DAILY_WORKFLOW.md](PROJECT2_DAILY_WORKFLOW.md) |

The original learning records can use earlier study baselines. For the later 6 kW modeling configuration, start with the root README and check each analysis script's actual inputs.

## 5. Keep these file groups separate

```text
project2-ai-server-liquid-cooling/
├── README.md                         Main technical overview
├── START_HERE.md                     This navigation guide
├── component_rom/                   Cold-plate component implementation
├── network_solver/
│   ├── components/                  Branch-hardware models
│   └── network_model/               System scripts and existing exports
├── tests/                           Engineering tests
├── requirements/                    Requirement records
├── calculations/                    Calculation records
├── scenarios/                       Scenario records
├── notes/                           Learning notes
├── figures/                         Existing project-level figures
└── docs/portfolio/
    ├── README.md                    Detailed portfolio narrative
    ├── portfolio/                   Case study and application documents
    ├── figures/                     Presentation figures
    ├── data/                        Labeled reported/transcribed tables
    ├── evidence/                    Source screenshots and supporting records
    ├── docs/                        Captions, caveats, and integration record
    └── scripts/check_package.py     Documentation checks
```

Keep this existing structure intact: the analysis scripts, portfolio links, and original package manifest depend on it. Do not upload both ZIP bundles as duplicate repository content. The `docs/portfolio/` subtree is the integrated portfolio copy.

When adding future results, record the run configuration and keep solver exports distinguishable from presentation tables. Do not rename or relocate working Python files or outputs without updating imports, paths, links, and tests together. Keep local environments, credentials, caches, and unrelated files out of commits. Large COMSOL source files need a separate storage decision; this repository guide does not establish that they are included.

## 6. Verify before publishing changes

From the repository root, with the required dependencies installed:

```bash
python -B -m pytest -p no:cacheprovider tests/
python -B docs/portfolio/scripts/check_package.py
```

The first command checks the available engineering tests. The second checks the documentation package; it does not run COMSOL or validate hardware. Previous results and their exact scope are recorded in the repository integration document; this navigation-only change does not claim a new engineering test run.

Use the [release checklist](docs/portfolio/docs/RELEASE_CHECKLIST.md) before publishing. Keep the existing evidence limitations and missing-asset notes visible, review the exact staged files, and make documentation changes on a separate branch.
