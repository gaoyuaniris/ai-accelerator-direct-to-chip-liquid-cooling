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

## Requested visuals that are not available as Project 2 source artifacts

A clean final Candidate C COMSOL temperature-field export and a verified tray CAD/layout drawing were not available in the accessible Project 2 attachments. No substitute from Project 1 was used. The README therefore uses a textual model workflow rather than implying that a new physical tray drawing was validated.

When those assets are available, lead with the Candidate C field and the same-side manifold schematic, then retain the ROM, header, pump, and fault evidence as the narrative. Replace the screenshot-derived F03/F04 with their original figure exports when practical; do not digitize approximate curve points and call them original data.

## Public-release housekeeping

Selected terminal evidence images are cropped to remove local save paths where possible. Review all evidence files before publishing. The chart source CSVs and source manifest retain their precision and provenance notes. Do not remove those notes to make the evidence look more complete than it is.
