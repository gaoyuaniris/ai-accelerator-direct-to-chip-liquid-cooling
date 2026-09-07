from pathlib import Path
import sys


# ============================================================
# Add Project 2 root to Python path
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# Imports
# ============================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.optimize import brentq


from network_solver.network_model.n_branch_manifold import (
    solve_n_branch_manifold,
)


# ============================================================
# 1. Tray configuration
# ============================================================

N_BRANCHES = 8

HEADER_DIAMETER_M = 0.01905

SEGMENT_LENGTH_M = 0.050


# ------------------------------------------------------------
# Manifold local-loss assumption
#
# Keep this as a sensitivity parameter until real junction
# coefficients are selected.
# ------------------------------------------------------------

K_MANIFOLD = 0.0


# ============================================================
# 2. Pump model
#
# Illustrative pump/CDU curve:
#
# dp_pump = dp_shutoff *
#           [1 - (Q / Q_free)^2]
#
# This is NOT a vendor pump specification.
# ============================================================

PUMP_SHUTOFF_HEAD_KPA = 20.0

PUMP_FREE_FLOW_LMIN = 14.0

PUMP_EFFICIENCY = 0.50


def pump_head_kpa(
    q_total_lmin,
):
    """
    Illustrative pump pressure-head curve.

    Parameters
    ----------
    q_total_lmin : float
        Total loop flow rate, L/min.

    Returns
    -------
    float
        Pump differential pressure, kPa.
    """

    head = (
        PUMP_SHUTOFF_HEAD_KPA
        *
        (
            1.0
            -
            (
                q_total_lmin
                /
                PUMP_FREE_FLOW_LMIN
            ) ** 2
        )
    )

    return max(
        head,
        0.0,
    )


# ============================================================
# 3. Tray/system pressure-drop model
# ============================================================

def tray_pressure_drop_kpa(
    q_total_lmin,
):
    """
    Solve the 8-branch tray at a prescribed total flow
    and return the tray differential pressure.

    The pressure difference is defined between the
    first supply and first return nodes.

    This currently represents the tray/manifold network,
    not the entire facility/CDU loop.
    """

    result = solve_n_branch_manifold(

        n_branches=
            N_BRANCHES,

        q_total_lmin=
            q_total_lmin,

        supply_diameter_m=
            HEADER_DIAMETER_M,

        return_diameter_m=
            HEADER_DIAMETER_M,

        segment_length_m=
            SEGMENT_LENGTH_M,

        supply_K_local=
            K_MANIFOLD,

        return_K_local=
            K_MANIFOLD,
    )


    p_supply_inlet = (
        result[
            "supply_node_pressure_kPa"
        ][0]
    )


    p_return_outlet = (
        result[
            "return_node_pressure_kPa"
        ][0]
    )


    dp_tray_kpa = (
        p_supply_inlet
        -
        p_return_outlet
    )


    return (
        dp_tray_kpa,
        result,
    )


# ============================================================
# 4. Build system resistance curve
# ============================================================

flow_sweep_lmin = np.linspace(
    4.5,
    9.2,
    30,
)


system_curve_results = []


for q_total in flow_sweep_lmin:

    try:

        (
            dp_system,
            result,
        ) = tray_pressure_drop_kpa(
            q_total
        )


        system_curve_results.append({

            "flow_Lmin":
                q_total,

            "system_dp_kPa":
                dp_system,

            "pump_dp_kPa":
                pump_head_kpa(
                    q_total
                ),

            "maldistribution_percent":
                result[
                    "maldistribution_percent"
                ],

            "min_branch_flow_Lmin":
                np.min(
                    result[
                        "branch_flows_Lmin"
                    ]
                ),

            "max_branch_flow_Lmin":
                np.max(
                    result[
                        "branch_flows_Lmin"
                    ]
                ),
        })


    except (
        ValueError,
        RuntimeError,
    ):

        # Skip operating points that would require branch
        # flows outside the validated component-ROM domain.
        continue


df_system_curve = pd.DataFrame(
    system_curve_results
)


# ============================================================
# 5. Operating-point residual
#
# Pump pressure - system pressure = 0
# ============================================================

def operating_point_residual(
    q_total_lmin,
):

    dp_system, _ = (
        tray_pressure_drop_kpa(
            q_total_lmin
        )
    )

    dp_pump = (
        pump_head_kpa(
            q_total_lmin
        )
    )

    return (
        dp_pump
        -
        dp_system
    )


# ============================================================
# 6. Solve operating point
# ============================================================

Q_SEARCH_MIN_LMIN = 4.5
Q_SEARCH_MAX_LMIN = 9.2


q_operating_lmin = brentq(

    operating_point_residual,

    Q_SEARCH_MIN_LMIN,

    Q_SEARCH_MAX_LMIN,
)


(
    dp_operating_kpa,
    operating_result,
) = tray_pressure_drop_kpa(
    q_operating_lmin
)


pump_dp_operating_kpa = (
    pump_head_kpa(
        q_operating_lmin
    )
)


# ============================================================
# 7. Operating-point branch metrics
# ============================================================

branch_flows = (
    operating_result[
        "branch_flows_Lmin"
    ]
)


q_min_branch = np.min(
    branch_flows
)

q_max_branch = np.max(
    branch_flows
)


maldistribution = (
    operating_result[
        "maldistribution_percent"
    ]
)


# ============================================================
# 8. Pumping power
#
# kPa * L/min / 60 = W
# ============================================================

hydraulic_power_w = (
    dp_operating_kpa
    *
    q_operating_lmin
    /
    60.0
)


electrical_pump_power_w = (
    hydraulic_power_w
    /
    PUMP_EFFICIENCY
)


# ============================================================
# 9. Print engineering summary
# ============================================================

print(
    "\n"
    "===================================================="
)

print(
    "PUMP / TRAY OPERATING POINT"
)

print(
    "===================================================="
)


print(
    f"\nOperating total flow = "
    f"{q_operating_lmin:.4f} L/min"
)


print(
    f"Tray pressure drop = "
    f"{dp_operating_kpa:.4f} kPa"
)


print(
    f"Pump pressure available = "
    f"{pump_dp_operating_kpa:.4f} kPa"
)


print(
    f"\nMean branch flow = "
    f"{np.mean(branch_flows):.4f} L/min"
)


print(
    f"Minimum branch flow = "
    f"{q_min_branch:.4f} L/min"
)


print(
    f"Maximum branch flow = "
    f"{q_max_branch:.4f} L/min"
)


print(
    f"Flow maldistribution = "
    f"{maldistribution:.3f}%"
)


print(
    f"\nHydraulic pumping power = "
    f"{hydraulic_power_w:.4f} W"
)


print(
    f"Estimated electrical pump power "
    f"(eta = {PUMP_EFFICIENCY:.2f}) = "
    f"{electrical_pump_power_w:.4f} W"
)


# ============================================================
# 10. Compare against thermodynamic target
# ============================================================

TARGET_TOTAL_FLOW_LMIN = 8.64


flow_margin_percent = (
    (
        q_operating_lmin
        -
        TARGET_TOTAL_FLOW_LMIN
    )
    /
    TARGET_TOTAL_FLOW_LMIN
    *
    100.0
)


print(
    f"\nTarget tray flow = "
    f"{TARGET_TOTAL_FLOW_LMIN:.3f} L/min"
)


print(
    f"Operating-point flow margin = "
    f"{flow_margin_percent:.2f}%"
)


# ============================================================
# 11. Plot pump and system curves
# ============================================================

plt.figure()


plt.plot(
    df_system_curve[
        "flow_Lmin"
    ],
    df_system_curve[
        "system_dp_kPa"
    ],
    marker="o",
    label="Tray system curve",
)


plt.plot(
    df_system_curve[
        "flow_Lmin"
    ],
    df_system_curve[
        "pump_dp_kPa"
    ],
    marker="o",
    label="Illustrative pump curve",
)


plt.scatter(
    [q_operating_lmin],
    [dp_operating_kpa],
    s=80,
    label="Operating point",
)


plt.axvline(
    TARGET_TOTAL_FLOW_LMIN,
    linestyle="--",
    label="8.64 L/min thermal target",
)


plt.xlabel(
    "Total tray flow (L/min)"
)


plt.ylabel(
    "Pressure differential (kPa)"
)


plt.title(
    "Pump and 8-Accelerator Tray Operating Point"
)


plt.grid(True)

plt.legend()


script_dir = (
    Path(__file__)
    .resolve()
    .parent
)


figure_path = (
    script_dir
    /
    "pump_system_operating_point.png"
)


plt.savefig(
    figure_path,
    dpi=200,
    bbox_inches="tight",
)


plt.show()


# ============================================================
# 12. Save system-curve data
# ============================================================

csv_path = (
    script_dir
    /
    "pump_system_curve.csv"
)


df_system_curve.to_csv(
    csv_path,
    index=False,
)


print(
    f"\nSaved system curve to:"
    f"\n{csv_path}"
)


print(
    f"\nSaved figure to:"
    f"\n{figure_path}"
)