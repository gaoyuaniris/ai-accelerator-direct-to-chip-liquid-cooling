"""Backward-compatible imports for the relocated branch hydraulic model.

New code should import :mod:`network_solver.components.branch_hydraulics`.
"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from network_solver.components.branch_hydraulics import (  # noqa: E402,F401
    BranchHydraulicResult,
    branch_pressure_drop_kpa,
    circular_tube_dp_kpa,
    darcy_friction_factor,
    evaluate_branch_hydraulics,
    local_loss_dp_kpa,
)
from network_solver.components.branch_hydraulics import _main  # noqa: E402


__all__ = [
    "BranchHydraulicResult",
    "branch_pressure_drop_kpa",
    "circular_tube_dp_kpa",
    "darcy_friction_factor",
    "evaluate_branch_hydraulics",
    "local_loss_dp_kpa",
]


if __name__ == "__main__":
    _main()
