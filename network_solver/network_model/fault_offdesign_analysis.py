from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.optimize import brentq


from network_solver.network_model.n_branch_manifold import (
    solve_n_branch_manifold,
)

from component_rom.coldplate_rom import (
    MAX_CALIBRATED_FLOW_LMIN,
    MIN_CALIBRATED_FLOW_LMIN,
    ROMExtrapolationError,
    evaluate_coldplate,
)


# ============================================================
# Tray geometry
# ============================================================

N_BRANCHES = 8

HEADER_DIAMETER_M = 0.01905

SEGMENT_LENGTH_M = 0.050

K_MANIFOLD = 0.0


# ============================================================
# Design requirements
# ============================================================

T_DEVICE_LIMIT_C = 85.0

MALDISTRIBUTION_LIMIT_PERCENT = 10.0

TARGET_TOTAL_FLOW_LMIN = 8.64

R_TIM_K_W = 0.005

R_PACKAGE_K_W = 0.020


# ============================================================
# Pump model
#
# Still illustrative, NOT vendor-specific.
# ============================================================

PUMP_FREE_FLOW_LMIN = 14.0

PUMP_EFFICIENCY = 0.50

OPERATING_POINT_SCAN_SAMPLES = 241


def pump_head_kpa(
    q_total_lmin,
    shutoff_head_kpa,
):
    """
    Illustrative centrifugal-pump curve.
    """

    head = (
        shutoff_head_kpa
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
# Solve hydraulic tray at prescribed total flow
# ============================================================

def tray_pressure_drop_kpa(
    q_total_lmin,
    branch_resistance_multipliers,
):
    """
    Solve tray hydraulics at one prescribed total flow.
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

        branch_resistance_multipliers=
            branch_resistance_multipliers,
    )


    dp_tray_kpa = (

        result[
            "supply_node_pressure_kPa"
        ][0]

        -

        result[
            "return_node_pressure_kPa"
        ][0]
    )


    return (
        dp_tray_kpa,
        result,
    )


# ============================================================
# Determine actual pump/system operating point
# ============================================================

def solve_operating_point(
    pump_shutoff_head_kpa,
    branch_resistance_multipliers,
):
    """
    Find flow where:

        pump head = tray pressure drop
    """

    def residual(
        q_total_lmin
    ):

        dp_system, _ = (
            tray_pressure_drop_kpa(

                q_total_lmin,

                branch_resistance_multipliers,
            )
        )


        dp_pump = pump_head_kpa(

            q_total_lmin,

            pump_shutoff_head_kpa,
        )


        return (
            dp_pump
            -
            dp_system
        )


    # --------------------------------------------------------
    # Locate an intersection only within the domain for which
    # the bounded network equations have a true solution.
    #
    # Aggregate limits alone are necessary but not sufficient:
    # an asymmetric fault can push one branch outside the ROM
    # even while the average branch flow remains in range.
    # --------------------------------------------------------

    q_search_min_lmin = (
        N_BRANCHES
        *
        MIN_CALIBRATED_FLOW_LMIN
    )

    q_search_max_lmin = min(
        N_BRANCHES
        *
        MAX_CALIBRATED_FLOW_LMIN,
        PUMP_FREE_FLOW_LMIN,
    )

    q_candidates_lmin = np.linspace(
        q_search_min_lmin,
        q_search_max_lmin,
        OPERATING_POINT_SCAN_SAMPLES,
    )

    valid_points = []
    previous_valid_point = None
    operating_bracket = None
    q_operating_lmin = None

    for q_candidate_lmin in q_candidates_lmin:

        try:
            residual_kpa = residual(
                q_candidate_lmin
            )

        except (
            ROMExtrapolationError,
            RuntimeError,
        ):
            # Do not bridge across an invalid portion of the
            # branch-flow domain when constructing a bracket.
            previous_valid_point = None
            continue

        if not np.isfinite(residual_kpa):
            raise RuntimeError(
                "Pump/system residual became non-finite "
                "inside the valid network domain."
            )

        current_valid_point = (
            q_candidate_lmin,
            residual_kpa,
        )

        valid_points.append(
            current_valid_point
        )

        if residual_kpa == 0.0:
            q_operating_lmin = q_candidate_lmin
            break

        if previous_valid_point is not None:
            q_previous_lmin, residual_previous_kpa = (
                previous_valid_point
            )

            if (
                residual_previous_kpa
                *
                residual_kpa
                <
                0.0
            ):
                operating_bracket = (
                    q_previous_lmin,
                    q_candidate_lmin,
                )
                break

        previous_valid_point = current_valid_point

    if q_operating_lmin is None:

        if operating_bracket is None:

            if not valid_points:
                raise RuntimeError(
                    "No physically valid network solutions were found "
                    "within the cold-plate ROM flow range."
                )

            valid_flows_lmin = np.array(
                [point[0] for point in valid_points]
            )

            valid_residuals_kpa = np.array(
                [point[1] for point in valid_points]
            )

            raise RuntimeError(
                "No pump/system curve intersection was found inside "
                "the physically valid branch-flow domain. "
                f"Valid total-flow samples spanned "
                f"{valid_flows_lmin.min():.4f} to "
                f"{valid_flows_lmin.max():.4f} L/min, with "
                f"pump-minus-system residuals from "
                f"{valid_residuals_kpa.min():.4f} to "
                f"{valid_residuals_kpa.max():.4f} kPa."
            )

        q_operating_lmin = brentq(
            residual,
            *operating_bracket,
        )


    (
        dp_operating_kpa,
        hydraulic,
    ) = tray_pressure_drop_kpa(

        q_operating_lmin,

        branch_resistance_multipliers,
    )

    operating_residual_kpa = (
        pump_head_kpa(
            q_operating_lmin,
            pump_shutoff_head_kpa,
        )
        -
        dp_operating_kpa
    )

    if abs(operating_residual_kpa) > 1.0e-8:
        raise RuntimeError(
            "Operating-point solve did not satisfy the pump/system "
            "pressure balance. "
            f"Residual = {operating_residual_kpa:.3e} kPa."
        )


    return (
        q_operating_lmin,
        dp_operating_kpa,
        hydraulic,
    )


# ============================================================
# Evaluate one complete scenario
# ============================================================

def evaluate_scenario(
    *,
    name,
    pump_shutoff_head_kpa,
    inlet_temperature_c,
    heat_loads_w,
    branch_resistance_multipliers,
):
    """
    Solve hydraulic operating point + branch thermal response.
    """


    # ========================================================
    # Hydraulic operating point
    # ========================================================

    (
        q_total_lmin,
        dp_tray_kpa,
        hydraulic,
    ) = solve_operating_point(

        pump_shutoff_head_kpa=
            pump_shutoff_head_kpa,

        branch_resistance_multipliers=
            branch_resistance_multipliers,
    )


    branch_flows = (
        hydraulic[
            "branch_flows_Lmin"
        ]
    )


    # ========================================================
    # Per-branch thermal calculation
    # ========================================================

    branch_results = []


    for i in range(
        N_BRANCHES
    ):

        q_i = (
            branch_flows[i]
        )

        heat_i = (
            heat_loads_w[i]
        )


        try:

            thermal = evaluate_coldplate(

                flow_lmin=
                    q_i,

                heat_load_w=
                    heat_i,

                inlet_temperature_c=
                    inlet_temperature_c,

                tim_resistance_k_per_w=
                    R_TIM_K_W,

                package_resistance_k_per_w=
                    R_PACKAGE_K_W,

                extrapolation="error",
            )


            Tdevice = (
                thermal
                .device_temperature_c
            )


            thermal_status = (

                "PASS"

                if Tdevice
                <=
                T_DEVICE_LIMIT_C

                else
                "FAIL"
            )


        except ValueError:

            Tdevice = np.nan

            thermal_status = (
                "ROM_RANGE_EXCEEDED"
            )


        branch_results.append({

            "branch":
                i + 1,

            "flow_Lmin":
                q_i,

            "heat_load_W":
                heat_i,

            "Tdevice_C":
                Tdevice,

            "thermal_status":
                thermal_status,
        })


    branch_df = pd.DataFrame(
        branch_results
    )


    # ========================================================
    # Scenario metrics
    # ========================================================

    Tmax = (
        branch_df[
            "Tdevice_C"
        ].max()
    )


    Tmin = (
        branch_df[
            "Tdevice_C"
        ].min()
    )


    Tspread = (
        Tmax
        -
        Tmin
    )


    q_min = np.min(
        branch_flows
    )


    q_max = np.max(
        branch_flows
    )


    maldistribution = (
        hydraulic[
            "maldistribution_percent"
        ]
    )


    thermal_margin = (
        T_DEVICE_LIMIT_C
        -
        Tmax
    )


    # ========================================================
    # Pump power
    # ========================================================

    hydraulic_power_w = (

        dp_tray_kpa
        *
        q_total_lmin
        /
        60.0
    )


    electrical_pump_power_w = (

        hydraulic_power_w
        /
        PUMP_EFFICIENCY
    )


    # ========================================================
    # Requirements
    # ========================================================

    thermal_pass = (
        Tmax
        <=
        T_DEVICE_LIMIT_C
    )


    maldistribution_pass = (
        maldistribution
        <=
        MALDISTRIBUTION_LIMIT_PERCENT
    )


    flow_target_pass = (
        q_total_lmin
        >=
        TARGET_TOTAL_FLOW_LMIN
    )


    all_rom_valid = (
        branch_df[
            "thermal_status"
        ]
        .ne(
            "ROM_RANGE_EXCEEDED"
        )
        .all()
    )


    if not all_rom_valid:

        overall_status = (
            "ROM_CHECK_REQUIRED"
        )

    elif (
        thermal_pass
        and
        maldistribution_pass
        and
        flow_target_pass
    ):

        overall_status = "PASS"

    else:

        overall_status = "FAIL"


    return {

        "name":
            name,

        "Qtotal_Lmin":
            q_total_lmin,

        "tray_dp_kPa":
            dp_tray_kpa,

        "q_min_Lmin":
            q_min,

        "q_max_Lmin":
            q_max,

        "Mflow_percent":
            maldistribution,

        "Tmax_C":
            Tmax,

        "Tspread_C":
            Tspread,

        "thermal_margin_C":
            thermal_margin,

        "pump_power_W":
            electrical_pump_power_w,

        "flow_target_pass":
            flow_target_pass,

        "thermal_pass":
            thermal_pass,

        "maldistribution_pass":
            maldistribution_pass,

        "ROM_valid":
            all_rom_valid,

        "overall_status":
            overall_status,

        "branch_df":
            branch_df,
    }


# ============================================================
# Define scenarios
# ============================================================

normal_resistance = np.ones(
    N_BRANCHES
)


restricted_branch_8 = np.ones(
    N_BRANCHES
)

restricted_branch_8[7] = (
    1.30
)


all_750_w = np.full(
    N_BRANCHES,
    750.0,
)


uneven_power_w = np.full(
    N_BRANCHES,
    600.0,
)

uneven_power_w[7] = (
    750.0
)


scenarios = [

    {
        "name":
            "Nominal",

        "pump_shutoff_head_kpa":
            20.0,

        "inlet_temperature_c":
            30.0,

        "heat_loads_w":
            all_750_w,

        "branch_resistance_multipliers":
            normal_resistance,
    },


    {
        "name":
            "Hot coolant",

        "pump_shutoff_head_kpa":
            20.0,

        "inlet_temperature_c":
            35.0,

        "heat_loads_w":
            all_750_w,

        "branch_resistance_multipliers":
            normal_resistance,
    },


    {
        "name":
            "Uneven power",

        "pump_shutoff_head_kpa":
            20.0,

        "inlet_temperature_c":
            30.0,

        "heat_loads_w":
            uneven_power_w,

        "branch_resistance_multipliers":
            normal_resistance,
    },


    {
        "name":
            "Restricted branch",

        "pump_shutoff_head_kpa":
            20.0,

        "inlet_temperature_c":
            30.0,

        "heat_loads_w":
            all_750_w,

        "branch_resistance_multipliers":
            restricted_branch_8,
    },


    {
        "name":
            "Weak pump",

        "pump_shutoff_head_kpa":
            15.0,

        "inlet_temperature_c":
            30.0,

        "heat_loads_w":
            all_750_w,

        "branch_resistance_multipliers":
            normal_resistance,
    },


    {
        "name":
            "Combined stress",

        "pump_shutoff_head_kpa":
            15.0,

        "inlet_temperature_c":
            35.0,

        "heat_loads_w":
            uneven_power_w,

        "branch_resistance_multipliers":
            restricted_branch_8,
    },
]


# ============================================================
# Run scenario matrix
# ============================================================

scenario_results = []


for scenario in scenarios:

    result = evaluate_scenario(
        **scenario
    )

    scenario_results.append(
        result
    )


# ============================================================
# Build summary table
# ============================================================

summary_rows = []


for result in scenario_results:

    summary_rows.append({

        "case":
            result["name"],

        "Qtotal_Lmin":
            result["Qtotal_Lmin"],

        "tray_dp_kPa":
            result["tray_dp_kPa"],

        "q_min_Lmin":
            result["q_min_Lmin"],

        "Mflow_percent":
            result["Mflow_percent"],

        "Tmax_C":
            result["Tmax_C"],

        "Tspread_C":
            result["Tspread_C"],

        "thermal_margin_C":
            result["thermal_margin_C"],

        "pump_power_W":
            result["pump_power_W"],

        "flow_target_pass":
            result["flow_target_pass"],

        "thermal_pass":
            result["thermal_pass"],

        "maldistribution_pass":
            result["maldistribution_pass"],

        "ROM_valid":
            result["ROM_valid"],

        "overall_status":
            result["overall_status"],
    })


df_summary = pd.DataFrame(
    summary_rows
)


print(
    "\n"
    "=============================================================="
)

print(
    "8-ACCELERATOR FAULT / OFF-DESIGN MATRIX"
)

print(
    "==============================================================\n"
)


print(
    df_summary.to_string(
        index=False
    )
)


# ============================================================
# Save results
# ============================================================

script_dir = (
    Path(__file__)
    .resolve()
    .parent
)


csv_path = (
    script_dir
    /
    "fault_offdesign_summary.csv"
)


df_summary.to_csv(
    csv_path,
    index=False,
)


print(
    f"\nSaved summary to:"
    f"\n{csv_path}"
)


# ============================================================
# Plot Tmax by scenario
# ============================================================

plt.figure()


plt.bar(

    df_summary[
        "case"
    ],

    df_summary[
        "Tmax_C"
    ],
)


plt.axhline(
    85.0,
    linestyle="--",
    label="85°C design limit",
)


plt.ylabel(
    "Maximum device temperature (°C)"
)


plt.title(
    "Thermal Robustness Across Off-Design Scenarios"
)


plt.xticks(
    rotation=25,
    ha="right",
)


plt.grid(
    axis="y"
)


plt.legend()

plt.tight_layout()

plt.show()
