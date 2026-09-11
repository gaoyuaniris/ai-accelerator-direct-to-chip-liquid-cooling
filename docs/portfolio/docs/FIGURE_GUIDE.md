# Figure shortlist and captions

The package includes six figures. F01/F02/F05/F06 are new plots of supplied numerical evidence, not new simulation results. F03/F04 preserve original user-supplied plots. Their relative paths are verified by the package checker.

| Order | Asset | Caption / use |
|---|---|---|
| F01 | `../figures/01_hydraulic_rom.png` (+ SVG) | Cold-plate hydraulic ROM fitted to reported calibration inputs; diamond denotes the COMSOL case withheld at 1.15 L/min. Coefficients E10; validation E03. |
| F02 | `../figures/02_thermal_rom.png` (+ SVG) | Maximum-base / mean-bulk thermal resistance versus coolant flow, with the withheld 1.15 L/min CFD check. Fit values are rounded transcriptions. E03/E10. |
| F03 | `../figures/03_header_local_loss_sensitivity.png` | Exploratory flow-maldistribution sensitivity to common-header ID and assumed local losses. Retain the warning that extreme cases may exceed the component ROM flow range. E07. |
| F04 | `../figures/04_pump_tray_operating_point.png` | A representative pump pressure-rise curve intersects the modeled tray curve at 9.1604 L/min and 11.4374 kPa. Pump data are illustrative; complete CDU/facility losses are excluded. E02/E08. |
| F05 | `../figures/05_fault_temperature.png` (+ SVG) | Estimated peak device temperature for six reported scenarios; all remain below the 85°C project criterion under the stated model assumptions. Asterisks identify 35°C inlet sensitivity cases. E01/E10. |
| F06 | `../figures/06_fault_maldistribution.png` (+ SVG) | Restricted-branch and combined-stress cases exceed the adopted 10% uniformity criterion despite remaining below the temperature limit. E01. |

## Geometry-visualization scope

A clean final Candidate C COMSOL temperature-field export and a verified tray CAD/layout drawing are not included. The [system architecture schematic](../../../figures/system_architecture.svg) illustrates the model boundary and components; it is not a verified mechanical layout.

The ROM, header, pump and fault figures document the available numerical evidence. F03/F04 are screenshot-derived plots; the source index records their origin.

## Source precision

Selected terminal evidence images were cropped during the original preparation. The chart CSVs and source manifest distinguish reported values from full-precision model exports. Source-image hashes describe the supplied originals; `MANIFEST.sha256` records the current packaged files.
