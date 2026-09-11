"""Check the documentation package, not the original engineering model.

Run from any directory: python path/to/scripts/check_package.py
Uses only the Python standard library.
"""
from pathlib import Path
import csv
import json
import math
import re

ROOT = Path(__file__).resolve().parents[1]

def rows(name: str) -> list[dict[str, str]]:
    with (ROOT / 'data' / name).open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))

checks = 0

def require(condition: bool, message: str) -> None:
    global checks
    if not condition:
        raise AssertionError(message)
    checks += 1

for row in rows('source_manifest.csv'):
    require((ROOT / row['package_path']).is_file(), f"Missing evidence: {row['source_id']}")

for doc in ROOT.rglob('*.md'):
    for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
        if link.startswith(('http:', 'https:', '#', 'mailto:')):
            continue
        target = (doc.parent / link.split('#')[0]).resolve()
        require(target.is_file(), f'Broken link in {doc.name}: {link}')

faults = rows('fault_offdesign_reported.csv')
require(len(faults) == 6, 'Expected six source scenarios.')
for row in faults:
    t = float(row['Tmax_device_est_C'])
    require(math.isclose(85.0 - t, float(row['thermal_margin_to_85C_C']), abs_tol=1e-9), 'Thermal margin mismatch.')
    q = float(row['total_flow_Lmin'])
    m = float(row['maldistribution_percent'])
    expected = 'PASS' if q >= 8.64 and m <= 10.0 and t <= 85.0 else 'FAIL'
    require(row['reported_status'].startswith(expected), f"Status differs from adopted criteria: {row['scenario']}")

nominal = rows('nominal_operating_point_reported.csv')[0]
q = float(nominal['total_flow_Lmin'])
p = float(nominal['tray_dp_kPa'])
require(abs(q*p/60 - float(nominal['hydraulic_power_W'])) < 1e-4, 'P=dp*flow check failed.')
require(abs(float(nominal['hydraulic_power_W'])/.5 - float(nominal['electrical_pump_power_W_est'])) < 1e-7, 'Pump-efficiency check failed.')

coeff = json.loads((ROOT/'data'/'reported_rom_coefficients.json').read_text())
cal = rows('rom_calibration_transcribed.csv')
require(len(cal)==7, 'Expected seven calibration points.')
require(all(float(x['flow_Lmin']) != 1.15 for x in cal), '1.15 L/min holdout appears in calibration.')
val = rows('validation_1p15_comparison.csv')
q=1.15
pred = coeff['dp_linear_kPa']*q + coeff['dp_quadratic_kPa']*q*q
require(abs(pred-float(val[0]['ROM_recalculated_from_reported_coefficients']))<1e-12,'Hydraulic validation reconstruction mismatch.')
require(float(val[1]['relative_error_percent']) < .3, 'Thermal resistance validation is not below 0.3%.')

for stem in ['01_hydraulic_rom','02_thermal_rom','03_header_local_loss_sensitivity','04_pump_tray_operating_point','05_fault_temperature','06_fault_maldistribution']:
    require((ROOT/'figures'/f'{stem}.png').is_file(), f'Missing figure: {stem}')

for filename in ['Project2_Case_Study.pdf','Project2_Case_Study.docx']:
    require((ROOT/'portfolio'/filename).is_file(), f'Missing portfolio file: {filename}')

print(f'PASS: {checks} documentation-package checks.')
print('Checked evidence files, internal Markdown links, six source scenarios, arithmetic, withheld validation separation, and deliverable presence.')
print('Not checked: live Project 2 repository execution, CFD solutions, vendor hardware, or final integrated pytest suite.')
