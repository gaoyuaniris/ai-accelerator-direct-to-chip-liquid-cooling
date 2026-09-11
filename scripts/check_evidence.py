"""Check project links, source records, checksums and reported arithmetic.

Run from any directory: python path/to/scripts/check_evidence.py
Uses only the Python standard library.
"""
from pathlib import Path
import csv
import hashlib
import json
import math
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'reported'

def rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))

checks = 0

def require(condition: bool, message: str) -> None:
    global checks
    if not condition:
        raise AssertionError(message)
    checks += 1

with (ROOT / 'data' / 'sources.csv').open(newline='', encoding='utf-8') as stream:
    for row in csv.DictReader(stream):
        require((ROOT / row['repository_path']).is_file(), f"Missing evidence: {row['source_id']}")

def without_fences(body: str) -> str:
    return re.sub(r'```.*?```', '', body, flags=re.S)

def heading_ids(body: str) -> set[str]:
    """GitHub-style fragments for the ATX headings used in this repository."""
    seen: dict[str, int] = {}
    result: set[str] = set()
    for heading in re.findall(r'^#{1,6}\s+(.+?)\s*#*$', without_fences(body), re.M):
        heading = re.sub(r'<[^>]+>', '', heading).lower()
        slug = re.sub(r'[^\w\- ]', '', heading).replace(' ', '-')
        number = seen.get(slug, 0)
        result.add(f'{slug}-{number}' if number else slug)
        seen[slug] = number + 1
    return result

link_count = image_count = readme_links = 0
documents = [ROOT / 'README.md', *sorted((ROOT / 'docs').rglob('*.md')),
             *sorted((ROOT / 'data' / 'evidence').rglob('*.md'))]
for doc in documents:
    for image, link in re.findall(r'(!?)\[[^\]]*\]\(([^)]+)\)', without_fences(doc.read_text(encoding='utf-8'))):
        parsed = urlsplit(link.strip('<>'))
        if parsed.scheme in ('http', 'https', 'mailto'):
            continue
        target = (doc.parent / unquote(parsed.path)).resolve() if parsed.path else doc
        require(target.is_file(), f'Broken link in {doc.relative_to(ROOT)}: {link}')
        if parsed.fragment:
            body = target.read_text(encoding='utf-8')
            fragment = unquote(parsed.fragment)
            require(fragment in heading_ids(body) or f'id="{fragment}"' in body,
                    f'Broken section link in {doc.relative_to(ROOT)}: {link}')
        link_count += 1
        image_count += bool(image)
        readme_links += doc == ROOT / 'README.md'

checksum_count = 0
for line in (ROOT / 'data' / 'checksums.sha256').read_text().splitlines():
    digest, name = line.split('  ', 1)
    path = ROOT / name
    require(path.is_file(), f'Missing checksum target: {name}')
    require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, f'Changed evidence file: {name}')
    checksum_count += 1

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

coeff = json.loads((DATA/'reported_rom_coefficients.json').read_text())
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

for filename in ['case-study.pdf','case-study.docx']:
    require((ROOT/'docs'/filename).is_file(), f'Missing case study: {filename}')

print(f'PASS: {checks} evidence checks.')
print(f'Links: {link_count} total, including {readme_links} README targets and {image_count} images; section anchors checked.')
print(f'Checksums: {checksum_count} retained data, evidence, figure and case-study files match.')
print('Checked evidence files, internal Markdown links, six source scenarios, arithmetic, withheld validation separation, and deliverable presence.')
print('Scope: stored evidence and navigation; run pytest separately for model regression checks. No CFD or hardware validation.')
