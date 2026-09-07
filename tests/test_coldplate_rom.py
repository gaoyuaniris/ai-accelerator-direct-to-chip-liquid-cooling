"""Regression and physics checks for the reusable cold-plate ROM."""

from __future__ import annotations

from dataclasses import fields
import math
from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from component_rom.coldplate_rom import (  # noqa: E402
    DEFAULT_CP_J_KGK,
    DEFAULT_DENSITY_KG_M3,
    MAX_CALIBRATED_FLOW_LMIN,
    MIN_CALIBRATED_FLOW_LMIN,
    NOMINAL_PACKAGE_RESISTANCE_K_PER_W,
    NOMINAL_TIM_RESISTANCE_K_PER_W,
    ColdPlateResult,
    ROMExtrapolationError,
    ROMExtrapolationWarning,
    evaluate_coldplate,
    pressure_drop_kpa,
    thermal_resistance_k_per_w,
)


VALIDATION_FLOW_LMIN = 0.864
VALIDATION_HEAT_LOAD_W = 600.0
VALIDATION_INLET_C = 30.0


def nominal_result() -> ColdPlateResult:
    """Return the unused off-grid COMSOL validation operating point."""
    return evaluate_coldplate(
        flow_lmin=VALIDATION_FLOW_LMIN,
        heat_load_w=VALIDATION_HEAT_LOAD_W,
        inlet_temperature_c=VALIDATION_INLET_C,
    )


def test_known_off_grid_comsol_validation_case() -> None:
    """The fitted ROM should reproduce the independent COMSOL case."""
    result = nominal_result()

    assert result.pressure_drop_kpa == pytest.approx(7.711, rel=0.01)
    assert result.thermal_resistance_k_per_w == pytest.approx(
        0.02868, rel=0.01
    )
    assert result.maximum_base_temperature_c == pytest.approx(52.22, abs=0.2)
    assert result.outlet_temperature_c == pytest.approx(40.02, abs=0.2)


def test_hydraulic_pumping_power_identity_with_unit_conversion() -> None:
    result = nominal_result()

    pressure_drop_pa = result.pressure_drop_kpa * 1_000.0
    volume_flow_m3_s = VALIDATION_FLOW_LMIN / 60_000.0
    independently_calculated_power_w = pressure_drop_pa * volume_flow_m3_s

    assert result.pumping_power_w == pytest.approx(
        independently_calculated_power_w, rel=1e-12
    )


def test_coolant_energy_balance() -> None:
    result = nominal_result()

    volume_flow_m3_s = VALIDATION_FLOW_LMIN / 60_000.0
    mass_flow_kg_s = DEFAULT_DENSITY_KG_M3 * volume_flow_m3_s
    reconstructed_heat_w = (
        mass_flow_kg_s
        * DEFAULT_CP_J_KGK
        * (result.outlet_temperature_c - VALIDATION_INLET_C)
    )

    assert reconstructed_heat_w == pytest.approx(
        VALIDATION_HEAT_LOAD_W, rel=1e-12
    )


def test_increasing_flow_has_expected_physical_trends() -> None:
    low_flow = evaluate_coldplate(
        flow_lmin=0.50,
        heat_load_w=600.0,
        inlet_temperature_c=30.0,
    )
    high_flow = evaluate_coldplate(
        flow_lmin=1.20,
        heat_load_w=600.0,
        inlet_temperature_c=30.0,
    )

    assert high_flow.pressure_drop_kpa > low_flow.pressure_drop_kpa
    assert (
        high_flow.thermal_resistance_k_per_w
        < low_flow.thermal_resistance_k_per_w
    )
    assert high_flow.outlet_temperature_c < low_flow.outlet_temperature_c
    assert (
        high_flow.maximum_base_temperature_c
        < low_flow.maximum_base_temperature_c
    )


def test_increasing_heat_load_has_expected_physical_trends() -> None:
    low_heat = evaluate_coldplate(
        flow_lmin=0.80,
        heat_load_w=450.0,
        inlet_temperature_c=30.0,
    )
    high_heat = evaluate_coldplate(
        flow_lmin=0.80,
        heat_load_w=750.0,
        inlet_temperature_c=30.0,
    )

    assert high_heat.outlet_temperature_c > low_heat.outlet_temperature_c
    assert (
        high_heat.maximum_base_temperature_c
        > low_heat.maximum_base_temperature_c
    )
    assert high_heat.thermal_resistance_k_per_w == pytest.approx(
        low_heat.thermal_resistance_k_per_w, rel=0.0, abs=0.0
    )


@pytest.mark.parametrize("flow_lmin", [0.0, -0.50])
def test_nonpositive_flow_is_rejected(flow_lmin: float) -> None:
    with pytest.raises(ValueError, match="flow_lmin must be positive"):
        pressure_drop_kpa(flow_lmin)


@pytest.mark.parametrize(
    "flow_lmin",
    [MIN_CALIBRATED_FLOW_LMIN - 0.01, MAX_CALIBRATED_FLOW_LMIN + 0.01],
)
def test_out_of_range_flow_is_rejected_by_default(flow_lmin: float) -> None:
    with pytest.raises(ROMExtrapolationError, match="outside the validated range"):
        pressure_drop_kpa(flow_lmin)


@pytest.mark.parametrize("heat_load_w", [449.0, 751.0])
def test_out_of_range_heat_load_is_rejected_by_default(
    heat_load_w: float,
) -> None:
    with pytest.raises(ROMExtrapolationError, match="outside the validated range"):
        evaluate_coldplate(
            flow_lmin=0.80,
            heat_load_w=heat_load_w,
            inlet_temperature_c=30.0,
        )


@pytest.mark.parametrize("heat_load_w", [0.0, -600.0])
def test_nonpositive_heat_load_is_rejected(heat_load_w: float) -> None:
    with pytest.raises(ValueError, match="heat_load_w must be positive"):
        evaluate_coldplate(
            flow_lmin=0.80,
            heat_load_w=heat_load_w,
            inlet_temperature_c=30.0,
        )


@pytest.mark.parametrize("density_kg_m3", [0.0, -997.0])
def test_nonpositive_density_is_rejected(density_kg_m3: float) -> None:
    with pytest.raises(ValueError, match="density_kg_m3 must be positive"):
        evaluate_coldplate(
            flow_lmin=0.80,
            heat_load_w=600.0,
            inlet_temperature_c=30.0,
            density_kg_m3=density_kg_m3,
        )


@pytest.mark.parametrize("cp_j_kgk", [0.0, -4180.0])
def test_nonpositive_heat_capacity_is_rejected(cp_j_kgk: float) -> None:
    with pytest.raises(ValueError, match="cp_j_kgk must be positive"):
        evaluate_coldplate(
            flow_lmin=0.80,
            heat_load_w=600.0,
            inlet_temperature_c=30.0,
            cp_j_kgk=cp_j_kgk,
        )


def test_explicit_flow_extrapolation_warns_and_returns_a_result() -> None:
    with pytest.warns(ROMExtrapolationWarning, match="flow_lmin"):
        pressure = pressure_drop_kpa(0.49, extrapolation="warn")

    assert pressure > 0.0


def test_explicit_heat_load_extrapolation_warns_and_returns_a_result() -> None:
    with pytest.warns(ROMExtrapolationWarning, match="heat_load_w"):
        result = evaluate_coldplate(
            flow_lmin=0.80,
            heat_load_w=800.0,
            inlet_temperature_c=30.0,
            extrapolation="warn",
        )

    assert result.maximum_base_temperature_c > result.mean_bulk_temperature_c


def test_nominal_output_sanity_and_finiteness() -> None:
    result = evaluate_coldplate(
        flow_lmin=VALIDATION_FLOW_LMIN,
        heat_load_w=VALIDATION_HEAT_LOAD_W,
        inlet_temperature_c=VALIDATION_INLET_C,
        tim_resistance_k_per_w=NOMINAL_TIM_RESISTANCE_K_PER_W,
        package_resistance_k_per_w=NOMINAL_PACKAGE_RESISTANCE_K_PER_W,
    )

    assert result.pressure_drop_kpa > 0.0
    assert result.thermal_resistance_k_per_w > 0.0
    assert result.pumping_power_w > 0.0
    assert result.outlet_temperature_c > VALIDATION_INLET_C
    assert result.maximum_base_temperature_c > result.mean_bulk_temperature_c
    assert all(
        math.isfinite(getattr(result, field.name)) for field in fields(result)
    )


def test_nominal_device_temperature_uses_total_added_resistance() -> None:
    result = evaluate_coldplate(
        flow_lmin=VALIDATION_FLOW_LMIN,
        heat_load_w=VALIDATION_HEAT_LOAD_W,
        inlet_temperature_c=VALIDATION_INLET_C,
        tim_resistance_k_per_w=NOMINAL_TIM_RESISTANCE_K_PER_W,
        package_resistance_k_per_w=NOMINAL_PACKAGE_RESISTANCE_K_PER_W,
    )
    total_added_resistance = (
        NOMINAL_TIM_RESISTANCE_K_PER_W
        + NOMINAL_PACKAGE_RESISTANCE_K_PER_W
    )

    assert total_added_resistance == pytest.approx(0.025)
    assert result.device_temperature_c is not None
    assert result.device_temperature_c - result.maximum_base_temperature_c == (
        pytest.approx(VALIDATION_HEAT_LOAD_W * total_added_resistance)
    )
