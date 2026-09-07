"""Day 1 energy-balance model for an 8-accelerator liquid-cooled tray.

Run from the project folder with:
    python3 scripts/day1_energy_balance.py

The script uses only Python's standard library and writes CSV results.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
REQUIREMENTS_FILE = PROJECT_DIR / "requirements" / "system_requirements.csv"
SCENARIOS_FILE = PROJECT_DIR / "scenarios" / "day1_scenarios.csv"
RESULTS_DIR = PROJECT_DIR / "results"


def required_flow_lpm(
    heat_load_w: float,
    coolant_delta_t_c: float,
    cp_j_kgk: float = 4180.0,
    density_kg_m3: float = 997.0,
) -> float:
    """Calculate water volume flow in L/min."""
    if heat_load_w < 0:
        raise ValueError("heat_load_w must be nonnegative")
    if coolant_delta_t_c <= 0 or cp_j_kgk <= 0 or density_kg_m3 <= 0:
        raise ValueError("Delta T and coolant properties must be positive")

    mass_flow_kg_s = heat_load_w / (cp_j_kgk * coolant_delta_t_c)
    volume_flow_m3_s = mass_flow_kg_s / density_kg_m3
    return volume_flow_m3_s * 60_000.0


def coolant_rise_c(
    heat_load_w: float,
    flow_lpm: float,
    cp_j_kgk: float = 4180.0,
    density_kg_m3: float = 997.0,
) -> float:
    """Calculate coolant temperature rise across one branch."""
    if flow_lpm <= 0:
        raise ValueError("flow_lpm must be positive")

    volume_flow_m3_s = flow_lpm / 60_000.0
    mass_flow_kg_s = volume_flow_m3_s * density_kg_m3
    return heat_load_w / (mass_flow_kg_s * cp_j_kgk)


def load_requirements() -> dict[str, str]:
    with REQUIREMENTS_FILE.open(newline="", encoding="utf-8") as handle:
        return {row["key"]: row["baseline"] for row in csv.DictReader(handle)}


def load_scenarios() -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    with SCENARIOS_FILE.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            grouped[row["scenario_id"]].append(row)
    return dict(grouped)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    values = load_requirements()
    count = int(values["accelerator_count"])
    chip_power_w = float(values["accelerator_power_w"])
    supply_c = float(values["tcs_supply_temp_c"])
    target_rise_c = float(values["target_coolant_rise_c"])
    cp = float(values["water_cp_j_kgk"])
    density = float(values["water_density_kg_m3"])

    total_heat_w = count * chip_power_w
    mass_flow_kg_s = total_heat_w / (cp * target_rise_c)
    total_flow_lpm = required_flow_lpm(total_heat_w, target_rise_c, cp, density)
    branch_flow_lpm = total_flow_lpm / count

    RESULTS_DIR.mkdir(exist_ok=True)
    baseline = [
        {"quantity": "Total heat load", "value": f"{total_heat_w:.3f}", "unit": "W"},
        {"quantity": "Required mass flow", "value": f"{mass_flow_kg_s:.6f}", "unit": "kg/s"},
        {"quantity": "Required volume flow", "value": f"{total_flow_lpm:.6f}", "unit": "L/min"},
        {"quantity": "Ideal branch flow", "value": f"{branch_flow_lpm:.6f}", "unit": "L/min"},
        {"quantity": "Expected TCS return", "value": f"{supply_c + target_rise_c:.3f}", "unit": "degC"},
    ]
    write_csv(RESULTS_DIR / "baseline_summary.csv", ["quantity", "value", "unit"], baseline)

    sensitivity = []
    for rise in (5.0, 7.5, 10.0, 12.5, 15.0):
        flow = required_flow_lpm(total_heat_w, rise, cp, density)
        sensitivity.append(
            {
                "coolant_rise_c": f"{rise:.1f}",
                "required_total_flow_lpm": f"{flow:.6f}",
                "ideal_branch_flow_lpm": f"{flow / count:.6f}",
            }
        )
    write_csv(
        RESULTS_DIR / "flow_sensitivity.csv",
        ["coolant_rise_c", "required_total_flow_lpm", "ideal_branch_flow_lpm"],
        sensitivity,
    )

    branch_results = []
    summaries = []
    for scenario_id, branches in load_scenarios().items():
        outlets = []
        total_scenario_heat = 0.0
        total_scenario_flow = 0.0
        for branch in branches:
            power_w = float(branch["power_w"])
            flow_lpm = branch_flow_lpm * float(branch["flow_multiplier"])
            rise_c = coolant_rise_c(power_w, flow_lpm, cp, density)
            outlet_c = supply_c + rise_c
            outlets.append(outlet_c)
            total_scenario_heat += power_w
            total_scenario_flow += flow_lpm
            branch_results.append(
                {
                    "scenario_id": scenario_id,
                    "branch_id": branch["branch_id"],
                    "power_w": f"{power_w:.1f}",
                    "flow_lpm": f"{flow_lpm:.6f}",
                    "coolant_rise_c": f"{rise_c:.3f}",
                    "outlet_temp_c": f"{outlet_c:.3f}",
                }
            )
        summaries.append(
            {
                "scenario_id": scenario_id,
                "total_heat_w": f"{total_scenario_heat:.1f}",
                "prescribed_total_flow_lpm": f"{total_scenario_flow:.6f}",
                "minimum_branch_outlet_c": f"{min(outlets):.3f}",
                "maximum_branch_outlet_c": f"{max(outlets):.3f}",
            }
        )

    write_csv(
        RESULTS_DIR / "scenario_branch_results.csv",
        ["scenario_id", "branch_id", "power_w", "flow_lpm", "coolant_rise_c", "outlet_temp_c"],
        branch_results,
    )
    write_csv(
        RESULTS_DIR / "scenario_summary.csv",
        ["scenario_id", "total_heat_w", "prescribed_total_flow_lpm", "minimum_branch_outlet_c", "maximum_branch_outlet_c"],
        summaries,
    )

    print(f"Baseline heat load: {total_heat_w / 1000:.1f} kW")
    print(f"Required total flow: {total_flow_lpm:.3f} L/min")
    print(f"Ideal branch flow: {branch_flow_lpm:.3f} L/min")
    print(f"Expected TCS return: {supply_c + target_rise_c:.1f} degC")
    print(f"Results written to: {RESULTS_DIR}")


if __name__ == "__main__":
    main()

