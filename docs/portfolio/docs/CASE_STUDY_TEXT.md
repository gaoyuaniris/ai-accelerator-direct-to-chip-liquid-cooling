# Designing a 6 kW AI accelerator cooling tray

**Yuan Gao — Project 2 | Model-based thermal-hydraulic design study**

## Engineering objective

Connect component CFD with system decisions for eight 750 W accelerators: estimate temperature, distribute coolant, size a provisional header, and determine the pump/tray operating point. The project uses an 85°C estimated device-temperature limit, a fixed 8.64 L/min flow target, and a 10% flow-maldistribution criterion.

## Method and decision

Candidate C uses 30 water channels, 0.40 × 1.00 mm, with 50 mm channel length. Reported COMSOL results were converted into a hydraulic ROM and a mean-bulk-referenced thermal-resistance ROM. Targeted power sweeps supported keeping the resistance flow-dependent within the sampled configuration.

A scalable nonlinear network model combines cold plates, branch tubes, illustrative QD/fitting losses, and same-side manifolds. Header sensitivity supported retaining 19.05 mm as a provisional baseline. The model is then coupled to an illustrative pump curve rather than assuming the thermal target is automatically delivered.

## Quantitative component check

At a withheld 1.15 L/min, 750 W, 30°C CFD case, the reported ROM coefficients reproduce pressure drop within 0.0178%, thermal resistance within 0.2493%, and maximum base temperature within 0.0382°C. This is ROM-to-CFD agreement, not hardware validation.

## Nominal modeled outcome

The operating point is 9.1604 L/min at 11.4374 kPa across the modeled tray. Minimum branch flow is 1.1438 L/min; maldistribution is 0.342%. Estimated peak device temperature is 72.72°C, leaving 12.28°C to the adopted limit. Package and TIM resistances are generic lumped assumptions totaling 0.025 K/W.

## Robustness result

The 30% branch-resistance perturbation increases maldistribution to 18.323% and peak temperature to 75.05°C. A weak-pump curve reduces total flow to 8.2056 L/min while the peak remains 74.10°C. Combined stress produces 8.1016 L/min, 18.575% maldistribution and 81.67°C. These cases show hydraulic requirement failures before the estimated temperature threshold.

## Claim boundary

The pump curve and component local-loss coefficients are illustrative; 35°C inlet cases are fixed-property sensitivity estimates; whole-tray CFD/hardware qualification is not supplied. The resulting recommendation is a provisional modeling baseline, not an assembly-ready, vendor-qualified cooling product.

Sources: E01 (scenario results), E02 (operating point), E03/E04 (withheld comparison), E07 (header sensitivity), E10 (model settings); indexed in data/source_manifest.csv.
