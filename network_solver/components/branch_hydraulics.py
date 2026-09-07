"""Hydraulic model for one complete accelerator branch.

The cold-plate contribution is delegated to :mod:`component_rom.coldplate_rom`.
This module adds the supply/return tubes and provisional local losses for quick
disconnects and fittings.  The local-loss coefficients remain sensitivity
assumptions until vendor pressure-drop curves are available.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, log, pi
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from component_rom.coldplate_rom import (
    ExtrapolationPolicy,
    pressure_drop_kpa as coldplate_pressure_drop_kpa,
)


DEFAULT_TUBE_DIAMETER_M = 0.0095
DEFAULT_SUPPLY_TUBE_LENGTH_M = 0.30
DEFAULT_RETURN_TUBE_LENGTH_M = 0.30
DEFAULT_NUMBER_OF_QDS = 2
DEFAULT_QD_LOSS_COEFFICIENT = 1.0
DEFAULT_FITTINGS_LOSS_COEFFICIENT = 1.0
DEFAULT_DENSITY_KG_M3 = 996.0
DEFAULT_VISCOSITY_PA_S = 8.0e-4
DEFAULT_ROUGHNESS_M = 0.0


@dataclass(frozen=True, slots=True)
class BranchHydraulicResult:
    """Pressure-drop budget for one accelerator branch."""

    flow_lmin: float
    coldplate_dp_kpa: float
    supply_tube_dp_kpa: float
    return_tube_dp_kpa: float
    total_tube_dp_kpa: float
    qd_dp_kpa: float
    fitting_dp_kpa: float
    total_branch_dp_kpa: float
    tube_velocity_m_s: float
    tube_reynolds: float
    tube_friction_factor: float
    hydraulic_power_w: float


def _finite_float(name: str, value: float) -> float:
    """Return *value* as a finite float, or raise a clear input error."""
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a real number, not bool")
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must be a real number") from exc
    if not isfinite(numeric_value):
        raise ValueError(f"{name} must be finite")
    return numeric_value


def _positive_float(name: str, value: float) -> float:
    numeric_value = _finite_float(name, value)
    if numeric_value <= 0.0:
        raise ValueError(f"{name} must be positive")
    return numeric_value


def _nonnegative_float(name: str, value: float) -> float:
    numeric_value = _finite_float(name, value)
    if numeric_value < 0.0:
        raise ValueError(f"{name} must be nonnegative")
    return numeric_value


def _nonnegative_integer(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def darcy_friction_factor(
    reynolds: float,
    relative_roughness: float = 0.0,
) -> float:
    """Return the Darcy friction factor using the Churchill correlation."""
    re = _positive_float("reynolds", reynolds)
    relative_roughness = _nonnegative_float(
        "relative_roughness", relative_roughness
    )

    term_a = (
        2.457
        * log(
            1.0
            / ((7.0 / re) ** 0.9 + 0.27 * relative_roughness)
        )
    ) ** 16
    term_b = (37530.0 / re) ** 16
    return 8.0 * (
        (8.0 / re) ** 12 + 1.0 / (term_a + term_b) ** 1.5
    ) ** (1.0 / 12.0)


def circular_tube_dp_kpa(
    flow_lmin: float,
    diameter_m: float,
    length_m: float,
    density_kg_m3: float = DEFAULT_DENSITY_KG_M3,
    viscosity_pa_s: float = DEFAULT_VISCOSITY_PA_S,
    roughness_m: float = DEFAULT_ROUGHNESS_M,
) -> tuple[float, float, float, float]:
    """Return tube pressure drop, velocity, Reynolds number, and Darcy factor."""
    flow = _positive_float("flow_lmin", flow_lmin)
    diameter = _positive_float("diameter_m", diameter_m)
    length = _nonnegative_float("length_m", length_m)
    density = _positive_float("density_kg_m3", density_kg_m3)
    viscosity = _positive_float("viscosity_pa_s", viscosity_pa_s)
    roughness = _nonnegative_float("roughness_m", roughness_m)

    flow_m3_s = flow / 60_000.0
    area_m2 = pi * diameter**2 / 4.0
    velocity_m_s = flow_m3_s / area_m2
    reynolds = density * velocity_m_s * diameter / viscosity
    friction_factor = darcy_friction_factor(
        reynolds,
        roughness / diameter,
    )
    dynamic_pressure_pa = 0.5 * density * velocity_m_s**2
    dp_kpa = (
        friction_factor * (length / diameter) * dynamic_pressure_pa / 1_000.0
    )
    return dp_kpa, velocity_m_s, reynolds, friction_factor


def local_loss_dp_kpa(
    flow_lmin: float,
    diameter_m: float,
    K_local: float,
    density_kg_m3: float = DEFAULT_DENSITY_KG_M3,
) -> float:
    """Return ``K * rho * velocity**2 / 2`` in kPa."""
    flow = _positive_float("flow_lmin", flow_lmin)
    diameter = _positive_float("diameter_m", diameter_m)
    loss_coefficient = _nonnegative_float("K_local", K_local)
    density = _positive_float("density_kg_m3", density_kg_m3)

    flow_m3_s = flow / 60_000.0
    area_m2 = pi * diameter**2 / 4.0
    velocity_m_s = flow_m3_s / area_m2
    return loss_coefficient * 0.5 * density * velocity_m_s**2 / 1_000.0


def evaluate_branch_hydraulics(
    *,
    flow_lmin: float,
    tube_diameter_m: float = DEFAULT_TUBE_DIAMETER_M,
    supply_tube_length_m: float = DEFAULT_SUPPLY_TUBE_LENGTH_M,
    return_tube_length_m: float = DEFAULT_RETURN_TUBE_LENGTH_M,
    number_of_qds: int = DEFAULT_NUMBER_OF_QDS,
    K_qd_each: float = DEFAULT_QD_LOSS_COEFFICIENT,
    K_fittings_total: float = DEFAULT_FITTINGS_LOSS_COEFFICIENT,
    density_kg_m3: float = DEFAULT_DENSITY_KG_M3,
    viscosity_pa_s: float = DEFAULT_VISCOSITY_PA_S,
    roughness_m: float = DEFAULT_ROUGHNESS_M,
    extrapolation: ExtrapolationPolicy = "error",
) -> BranchHydraulicResult:
    """Evaluate the complete branch pressure-drop budget.

    ``K_qd_each`` and ``K_fittings_total`` are provisional sensitivity inputs,
    not vendor specifications.  Cold-plate flow validation and extrapolation
    policy are enforced by :func:`component_rom.coldplate_rom.pressure_drop_kpa`.
    """
    flow = _positive_float("flow_lmin", flow_lmin)
    diameter = _positive_float("tube_diameter_m", tube_diameter_m)
    supply_length = _nonnegative_float(
        "supply_tube_length_m", supply_tube_length_m
    )
    return_length = _nonnegative_float(
        "return_tube_length_m", return_tube_length_m
    )
    qd_count = _nonnegative_integer("number_of_qds", number_of_qds)
    qd_coefficient = _nonnegative_float("K_qd_each", K_qd_each)
    fittings_coefficient = _nonnegative_float(
        "K_fittings_total", K_fittings_total
    )
    density = _positive_float("density_kg_m3", density_kg_m3)
    viscosity = _positive_float("viscosity_pa_s", viscosity_pa_s)
    roughness = _nonnegative_float("roughness_m", roughness_m)

    coldplate_dp = coldplate_pressure_drop_kpa(
        flow,
        extrapolation=extrapolation,
    )
    supply_dp, velocity, reynolds, friction_factor = circular_tube_dp_kpa(
        flow,
        diameter,
        supply_length,
        density,
        viscosity,
        roughness,
    )
    return_dp, _, _, _ = circular_tube_dp_kpa(
        flow,
        diameter,
        return_length,
        density,
        viscosity,
        roughness,
    )
    qd_dp = qd_count * local_loss_dp_kpa(
        flow,
        diameter,
        qd_coefficient,
        density,
    )
    fitting_dp = local_loss_dp_kpa(
        flow,
        diameter,
        fittings_coefficient,
        density,
    )
    total_tube_dp = supply_dp + return_dp
    total_branch_dp = coldplate_dp + total_tube_dp + qd_dp + fitting_dp

    return BranchHydraulicResult(
        flow_lmin=flow,
        coldplate_dp_kpa=coldplate_dp,
        supply_tube_dp_kpa=supply_dp,
        return_tube_dp_kpa=return_dp,
        total_tube_dp_kpa=total_tube_dp,
        qd_dp_kpa=qd_dp,
        fitting_dp_kpa=fitting_dp,
        total_branch_dp_kpa=total_branch_dp,
        tube_velocity_m_s=velocity,
        tube_reynolds=reynolds,
        tube_friction_factor=friction_factor,
        hydraulic_power_w=total_branch_dp * flow / 60.0,
    )


def branch_pressure_drop_kpa(
    flow_lmin: float,
    tube_diameter_m: float = DEFAULT_TUBE_DIAMETER_M,
    supply_tube_length_m: float = DEFAULT_SUPPLY_TUBE_LENGTH_M,
    return_tube_length_m: float = DEFAULT_RETURN_TUBE_LENGTH_M,
    number_of_qds: int = DEFAULT_NUMBER_OF_QDS,
    K_qd_each: float = DEFAULT_QD_LOSS_COEFFICIENT,
    K_fittings_total: float = DEFAULT_FITTINGS_LOSS_COEFFICIENT,
    density_kg_m3: float = DEFAULT_DENSITY_KG_M3,
    viscosity_pa_s: float = DEFAULT_VISCOSITY_PA_S,
    roughness_m: float = DEFAULT_ROUGHNESS_M,
    extrapolation: ExtrapolationPolicy = "error",
) -> float:
    """Return total pressure drop for a complete accelerator branch in kPa."""
    return evaluate_branch_hydraulics(
        flow_lmin=flow_lmin,
        tube_diameter_m=tube_diameter_m,
        supply_tube_length_m=supply_tube_length_m,
        return_tube_length_m=return_tube_length_m,
        number_of_qds=number_of_qds,
        K_qd_each=K_qd_each,
        K_fittings_total=K_fittings_total,
        density_kg_m3=density_kg_m3,
        viscosity_pa_s=viscosity_pa_s,
        roughness_m=roughness_m,
        extrapolation=extrapolation,
    ).total_branch_dp_kpa


def _main() -> None:
    result = evaluate_branch_hydraulics(flow_lmin=1.08)
    print("Accelerator branch hydraulic pressure budget at 1.08 L/min")
    print(f"Cold plate:      {result.coldplate_dp_kpa:.6f} kPa")
    print(f"Supply tube:     {result.supply_tube_dp_kpa:.6f} kPa")
    print(f"Return tube:     {result.return_tube_dp_kpa:.6f} kPa")
    print(f"Two QDs:         {result.qd_dp_kpa:.6f} kPa")
    print(f"Other fittings:  {result.fitting_dp_kpa:.6f} kPa")
    print(f"Total branch:    {result.total_branch_dp_kpa:.6f} kPa")
    print(f"Hydraulic power: {result.hydraulic_power_w:.6f} W")


if __name__ == "__main__":
    _main()
