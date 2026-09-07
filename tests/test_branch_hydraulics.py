"""Regression checks for branch hardware and manifold integration."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from component_rom.coldplate_rom import (  # noqa: E402
    ROMExtrapolationError,
    pressure_drop_kpa as coldplate_pressure_drop_kpa,
)
from network_solver.components.branch_hydraulics import (  # noqa: E402
    branch_pressure_drop_kpa,
    evaluate_branch_hydraulics,
)
from network_solver.network_model.n_branch_manifold import (  # noqa: E402
    solve_n_branch_manifold,
)


def _solve_nominal(**branch_overrides):
    return solve_n_branch_manifold(
        n_branches=8,
        q_total_lmin=8.64,
        supply_diameter_m=0.01905,
        return_diameter_m=0.01905,
        segment_length_m=0.050,
        supply_K_local=0.0,
        return_K_local=0.0,
        **branch_overrides,
    )


def test_complete_branch_budget_and_wrapper_are_consistent() -> None:
    result = evaluate_branch_hydraulics(flow_lmin=1.08)

    assert result.coldplate_dp_kpa == pytest.approx(
        coldplate_pressure_drop_kpa(1.08)
    )
    assert result.total_tube_dp_kpa == pytest.approx(
        result.supply_tube_dp_kpa + result.return_tube_dp_kpa
    )
    assert result.total_branch_dp_kpa == pytest.approx(
        result.coldplate_dp_kpa
        + result.total_tube_dp_kpa
        + result.qd_dp_kpa
        + result.fitting_dp_kpa
    )
    assert branch_pressure_drop_kpa(1.08) == pytest.approx(
        result.total_branch_dp_kpa
    )


def test_zero_hardware_losses_reduce_to_coldplate_rom() -> None:
    branch_dp = branch_pressure_drop_kpa(
        1.08,
        supply_tube_length_m=0.0,
        return_tube_length_m=0.0,
        number_of_qds=0,
        K_fittings_total=0.0,
    )
    assert branch_dp == pytest.approx(coldplate_pressure_drop_kpa(1.08))


def test_branch_model_preserves_rom_domain_enforcement() -> None:
    with pytest.raises(ROMExtrapolationError):
        branch_pressure_drop_kpa(1.21)


def test_manifold_node_pressures_use_complete_branch_drop() -> None:
    result = _solve_nominal()
    driving_dp = (
        result["supply_node_pressure_kPa"]
        - result["return_node_pressure_kPa"]
    )

    np.testing.assert_allclose(driving_dp, result["branch_dp_kPa"], atol=1e-10)
    np.testing.assert_allclose(
        result["coldplate_dp_kPa"],
        [coldplate_pressure_drop_kpa(q) for q in result["branch_flows_Lmin"]],
        atol=1e-12,
    )
    assert np.max(np.abs(result["residuals"])) < 1e-8


def test_equal_branch_hardware_improves_balance_but_adds_pressure_drop() -> None:
    coldplate_only = _solve_nominal(
        branch_supply_tube_length_m=0.0,
        branch_return_tube_length_m=0.0,
        branch_number_of_qds=0,
        branch_K_fittings_total=0.0,
    )
    complete_branch = _solve_nominal()

    assert (
        complete_branch["maldistribution_percent"]
        < coldplate_only["maldistribution_percent"]
    )
    assert (
        complete_branch["system_pressure_drop_kPa"]
        > coldplate_only["system_pressure_drop_kPa"]
    )


def test_fault_multiplier_is_consistent_in_equations_and_results() -> None:
    multipliers = np.ones(8)
    multipliers[-1] = 1.30

    result = _solve_nominal(
        branch_resistance_multipliers=multipliers,
    )
    unmodified_branch_dp = np.array(
        [
            branch_pressure_drop_kpa(flow)
            for flow in result["branch_flows_Lmin"]
        ]
    )
    driving_dp = (
        result["supply_node_pressure_kPa"]
        - result["return_node_pressure_kPa"]
    )

    np.testing.assert_allclose(
        result["branch_dp_kPa"],
        multipliers * unmodified_branch_dp,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        driving_dp,
        result["branch_dp_kPa"],
        atol=1e-10,
    )
    np.testing.assert_allclose(
        result["branch_resistance_multipliers"],
        multipliers,
        atol=0.0,
    )
    assert result["branch_flows_Lmin"][-1] < np.min(
        result["branch_flows_Lmin"][:-1]
    )
    assert np.max(np.abs(result["residuals"])) < 1e-8
