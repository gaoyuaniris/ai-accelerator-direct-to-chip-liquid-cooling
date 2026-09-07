from pathlib import Path
import sys


# ============================================================
# Add Project 2 root to Python import path
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


from network_solver.network_model.n_branch_manifold import (
    solve_n_branch_manifold,
)


from component_rom.coldplate_rom import (
    evaluate_coldplate,
)


# ============================================================
# 1. Tray-level design assumptions
# ============================================================

N_BRANCHES = 8


# ------------------------------------------------------------
# Accelerator thermal load
# ------------------------------------------------------------

HEAT_LOAD_W = 750.0


# ------------------------------------------------------------
# Coolant condition
# ------------------------------------------------------------

TIN_C = 30.0


# ------------------------------------------------------------
# Package / TIM assumptions
#
# These are generic Project 2 design assumptions,
# not vendor-specific package data.
# ------------------------------------------------------------

R_TIM_K_W = 0.005

R_PACKAGE_K_W = 0.020


# ------------------------------------------------------------
# Thermal design limit
# ------------------------------------------------------------

T_DEVICE_LIMIT_C = 85.0


# ------------------------------------------------------------
# Nominal flow target
#
# ~1.08 L/min per accelerator corresponds approximately
# to a 10 C coolant temperature rise at 750 W.
# ------------------------------------------------------------

NOMINAL_BRANCH_FLOW_LMIN = 1.08


Q_TOTAL_LMIN = (
    N_BRANCHES
    *
    NOMINAL_BRANCH_FLOW_LMIN
)


# ------------------------------------------------------------
# Provisional header design
#
# 19.05 mm = 3/4 inch
# ------------------------------------------------------------

HEADER_DIAMETER_M = 0.01905


# ------------------------------------------------------------
# Distance between adjacent accelerator connections
# ------------------------------------------------------------

SEGMENT_LENGTH_M = 0.050


# ------------------------------------------------------------
# Provisional flow maldistribution design limit
# ------------------------------------------------------------

MALDISTRIBUTION_LIMIT_PERCENT = 10.0


# ============================================================
# 2. Evaluate thermal performance of every branch
# ============================================================

def evaluate_tray_thermal_performance(
    branch_flows_lmin,
    heat_load_w=HEAT_LOAD_W,
    inlet_temperature_c=TIN_C,
    tim_resistance_k_per_w=R_TIM_K_W,
    package_resistance_k_per_w=R_PACKAGE_K_W,
    device_temperature_limit_c=T_DEVICE_LIMIT_C,
):
    """
    Evaluate thermal performance of every accelerator branch.

    Each hydraulic branch flow is passed into the validated
    cold-plate reduced-order model.

    Parameters
    ----------
    branch_flows_lmin : array-like
        Flow rate through each accelerator branch, L/min.

    Returns
    -------
    pandas.DataFrame
        Thermal results for every accelerator.
    """

    thermal_results = []


    for branch_number, flow_lmin in enumerate(
        branch_flows_lmin,
        start=1,
    ):

        # ----------------------------------------------------
        # Default values
        #
        # These remain NaN if the requested operating point
        # lies outside the validated cold-plate ROM range.
        # ----------------------------------------------------

        rth = np.nan
        Tout = np.nan
        Tbulk = np.nan
        Tbase = np.nan
        Tdevice = np.nan

        thermal_status = "ROM_RANGE_EXCEEDED"


        try:

            thermal = evaluate_coldplate(

                flow_lmin=float(flow_lmin),

                heat_load_w=heat_load_w,

                inlet_temperature_c=
                    inlet_temperature_c,

                tim_resistance_k_per_w=
                    tim_resistance_k_per_w,

                package_resistance_k_per_w=
                    package_resistance_k_per_w,

                extrapolation="error",
            )


            # ------------------------------------------------
            # ColdPlateResult is a dataclass.
            # Use dot notation.
            # ------------------------------------------------

            rth = (
                thermal
                .thermal_resistance_k_per_w
            )

            Tout = (
                thermal
                .outlet_temperature_c
            )

            Tbulk = (
                thermal
                .mean_bulk_temperature_c
            )

            Tbase = (
                thermal
                .maximum_base_temperature_c
            )

            Tdevice = (
                thermal
                .device_temperature_c
            )


            # ------------------------------------------------
            # Thermal requirement
            # ------------------------------------------------

            if (
                Tdevice
                <=
                device_temperature_limit_c
            ):

                thermal_status = "PASS"

            else:

                thermal_status = "FAIL"


        except ValueError:

            thermal_status = (
                "ROM_RANGE_EXCEEDED"
            )


        thermal_results.append({

            "branch":
                branch_number,

            "flow_Lmin":
                flow_lmin,

            "Rth_K_W":
                rth,

            "Tout_C":
                Tout,

            "Tbulk_C":
                Tbulk,

            "Tbase_C":
                Tbase,

            "Tdevice_est_C":
                Tdevice,

            "thermal_status":
                thermal_status,
        })


    return pd.DataFrame(
        thermal_results
    )


# ============================================================
# 3. Solve one complete thermal-hydraulic tray case
# ============================================================

def solve_tray_case(
    K_local,
):
    """
    Solve one complete 8-accelerator tray case.

    Workflow
    --------
    Header/local-loss model
        ->
    branch hydraulic distribution
        ->
    cold-plate thermal ROM
        ->
    tray thermal metrics
    """

    # ========================================================
    # Hydraulic network
    # ========================================================

    hydraulic = solve_n_branch_manifold(

        n_branches=
            N_BRANCHES,

        q_total_lmin=
            Q_TOTAL_LMIN,

        supply_diameter_m=
            HEADER_DIAMETER_M,

        return_diameter_m=
            HEADER_DIAMETER_M,

        segment_length_m=
            SEGMENT_LENGTH_M,

        supply_K_local=
            K_local,

        return_K_local=
            K_local,
    )


    branch_flows = (
        hydraulic[
            "branch_flows_Lmin"
        ]
    )


    # ========================================================
    # Thermal evaluation
    # ========================================================

    thermal_df = (
        evaluate_tray_thermal_performance(
            branch_flows_lmin=
                branch_flows
        )
    )


    # ========================================================
    # Tray-level thermal metrics
    # ========================================================

    valid_temperatures = (
        thermal_df[
            "Tdevice_est_C"
        ]
        .dropna()
    )


    if len(valid_temperatures) > 0:

        hottest_device_c = (
            valid_temperatures.max()
        )

        coldest_device_c = (
            valid_temperatures.min()
        )

        temperature_spread_c = (
            hottest_device_c
            -
            coldest_device_c
        )


        hottest_branch = int(

            thermal_df.loc[

                thermal_df[
                    "Tdevice_est_C"
                ].idxmax(),

                "branch"
            ]
        )


        thermal_margin_c = (
            T_DEVICE_LIMIT_C
            -
            hottest_device_c
        )


    else:

        hottest_device_c = np.nan
        coldest_device_c = np.nan
        temperature_spread_c = np.nan
        hottest_branch = None
        thermal_margin_c = np.nan


    # ========================================================
    # Overall case status
    # ========================================================

    all_thermal_pass = (

        thermal_df[
            "thermal_status"
        ]
        .eq("PASS")
        .all()
    )


    maldistribution_pass = (

        hydraulic[
            "maldistribution_percent"
        ]
        <=
        MALDISTRIBUTION_LIMIT_PERCENT
    )


    if (
        all_thermal_pass
        and
        maldistribution_pass
    ):

        overall_status = "PASS"

    else:

        overall_status = "FAIL"


    # ========================================================
    # Return complete case
    # ========================================================

    return {

        "K_local":
            K_local,

        "hydraulic":
            hydraulic,

        "thermal_df":
            thermal_df,

        "hottest_device_C":
            hottest_device_c,

        "coldest_device_C":
            coldest_device_c,

        "temperature_spread_C":
            temperature_spread_c,

        "hottest_branch":
            hottest_branch,

        "thermal_margin_C":
            thermal_margin_c,

        "overall_status":
            overall_status,
    }


# ============================================================
# 4. Print detailed results for one case
# ============================================================

def print_case_summary(
    case,
):
    """
    Print detailed engineering summary for one tray case.
    """

    K_local = (
        case["K_local"]
    )

    hydraulic = (
        case["hydraulic"]
    )

    thermal_df = (
        case["thermal_df"]
    )


    print(
        "\n"
        "========================================"
    )

    print(
        f"8-ACCELERATOR THERMAL-HYDRAULIC TRAY "
        f"(K_local = {K_local})"
    )

    print(
        "========================================"
    )


    print(
        f"\nTotal tray flow = "
        f"{Q_TOTAL_LMIN:.3f} L/min"
    )


    print(
        f"Header ID = "
        f"{HEADER_DIAMETER_M * 1000:.2f} mm"
    )


    print(
        f"Accelerator heat load = "
        f"{HEAT_LOAD_W:.0f} W/device"
    )


    print(
        f"Coolant inlet temperature = "
        f"{TIN_C:.1f} °C"
    )


    # ========================================================
    # Hydraulic summary
    # ========================================================

    print(
        "\nHydraulic summary:"
    )


    print(
        f"Flow maldistribution = "
        f"{hydraulic['maldistribution_percent']:.3f}%"
    )


    print(
        f"Minimum branch flow = "
        f"{np.min(hydraulic['branch_flows_Lmin']):.4f} "
        f"L/min"
    )


    print(
        f"Maximum branch flow = "
        f"{np.max(hydraulic['branch_flows_Lmin']):.4f} "
        f"L/min"
    )


    # ========================================================
    # Thermal table
    # ========================================================

    print(
        "\nPer-accelerator thermal results:\n"
    )


    display_columns = [

        "branch",

        "flow_Lmin",

        "Rth_K_W",

        "Tout_C",

        "Tbase_C",

        "Tdevice_est_C",

        "thermal_status",
    ]


    print(

        thermal_df[
            display_columns
        ]
        .to_string(
            index=False
        )
    )


    # ========================================================
    # Tray thermal summary
    # ========================================================

    print(
        "\nTray thermal summary:"
    )


    print(
        f"Hottest device = "
        f"{case['hottest_device_C']:.3f} °C"
    )


    print(
        f"Coldest device = "
        f"{case['coldest_device_C']:.3f} °C"
    )


    print(
        f"Device temperature spread = "
        f"{case['temperature_spread_C']:.4f} °C"
    )


    print(
        f"Hottest branch = "
        f"{case['hottest_branch']}"
    )


    print(
        f"Thermal margin to 85°C = "
        f"{case['thermal_margin_C']:.3f} °C"
    )


    print(
        f"Overall status = "
        f"{case['overall_status']}"
    )


# ============================================================
# 5. Main program
# ============================================================

if __name__ == "__main__":


    # ========================================================
    # PART A
    # Nominal straight-header baseline
    #
    # K_local = 0
    # ========================================================

    baseline_case = (
        solve_tray_case(
            K_local=0.0
        )
    )


    print_case_summary(
        baseline_case
    )


    # ========================================================
    # Save baseline branch results
    # ========================================================

    script_dir = (
        Path(__file__)
        .resolve()
        .parent
    )


    baseline_csv = (

        script_dir
        /
        "tray_thermal_baseline.csv"
    )


    baseline_case[
        "thermal_df"
    ].to_csv(

        baseline_csv,

        index=False,
    )


    print(
        f"\nSaved baseline results to:"
        f"\n{baseline_csv}"
    )


    # ========================================================
    # PART B
    # Local-loss sensitivity study
    #
    # Compare:
    #
    # K_local = 0
    # K_local = 1
    # K_local = 2
    # ========================================================

    K_local_cases = [
        0.0,
        1.0,
        2.0,
    ]


    sensitivity_summary = []


    all_cases = {}


    for K_local in K_local_cases:


        case = (
            solve_tray_case(
                K_local=K_local
            )
        )


        all_cases[
            K_local
        ] = case


        hydraulic = (
            case["hydraulic"]
        )


        sensitivity_summary.append({

            "K_local":
                K_local,

            "flow_maldistribution_percent":
                hydraulic[
                    "maldistribution_percent"
                ],

            "min_branch_flow_Lmin":
                np.min(
                    hydraulic[
                        "branch_flows_Lmin"
                    ]
                ),

            "max_branch_flow_Lmin":
                np.max(
                    hydraulic[
                        "branch_flows_Lmin"
                    ]
                ),

            "hottest_device_C":
                case[
                    "hottest_device_C"
                ],

            "coldest_device_C":
                case[
                    "coldest_device_C"
                ],

            "device_temperature_spread_C":
                case[
                    "temperature_spread_C"
                ],

            "thermal_margin_C":
                case[
                    "thermal_margin_C"
                ],

            "hottest_branch":
                case[
                    "hottest_branch"
                ],

            "overall_status":
                case[
                    "overall_status"
                ],
        })


    # ========================================================
    # Sensitivity DataFrame
    # ========================================================

    df_sensitivity = (
        pd.DataFrame(
            sensitivity_summary
        )
    )


    print(
        "\n"
        "========================================"
    )

    print(
        "LOCAL-LOSS THERMAL-HYDRAULIC SENSITIVITY"
    )

    print(
        "========================================\n"
    )


    print(
        df_sensitivity.to_string(
            index=False
        )
    )


    # ========================================================
    # Save sensitivity summary
    # ========================================================

    sensitivity_csv = (

        script_dir
        /
        "tray_local_loss_sensitivity.csv"
    )


    df_sensitivity.to_csv(

        sensitivity_csv,

        index=False,
    )


    print(
        f"\nSaved sensitivity results to:"
        f"\n{sensitivity_csv}"
    )


    # ========================================================
    # Plot 1
    #
    # Baseline flow distribution
    # ========================================================

    baseline_df = (
        baseline_case[
            "thermal_df"
        ]
    )


    plt.figure()


    plt.plot(

        baseline_df[
            "branch"
        ],

        baseline_df[
            "flow_Lmin"
        ],

        marker="o",

        label="Actual branch flow",
    )


    plt.axhline(

        NOMINAL_BRANCH_FLOW_LMIN,

        linestyle="--",

        label="Ideal equal flow",
    )


    plt.xlabel(
        "Accelerator branch"
    )


    plt.ylabel(
        "Branch flow (L/min)"
    )


    plt.title(
        "Coolant Flow Distribution Across "
        "8-Accelerator Tray"
    )


    plt.grid(True)

    plt.legend()


    flow_plot = (

        script_dir
        /
        "tray_branch_flow_distribution.png"
    )


    plt.savefig(

        flow_plot,

        dpi=200,

        bbox_inches="tight",
    )


    plt.show()


    # ========================================================
    # Plot 2
    #
    # Baseline device temperature distribution
    # ========================================================

    plt.figure()


    plt.plot(

        baseline_df[
            "branch"
        ],

        baseline_df[
            "Tdevice_est_C"
        ],

        marker="o",

        label="Estimated device temperature",
    )


    plt.axhline(

        T_DEVICE_LIMIT_C,

        linestyle="--",

        label="85°C design limit",
    )


    plt.xlabel(
        "Accelerator branch"
    )


    plt.ylabel(
        "Estimated device temperature (°C)"
    )


    plt.title(
        "Device Temperature Distribution Across "
        "8-Accelerator Tray"
    )


    plt.grid(True)

    plt.legend()


    temperature_plot = (

        script_dir
        /
        "tray_device_temperature_distribution.png"
    )


    plt.savefig(

        temperature_plot,

        dpi=200,

        bbox_inches="tight",
    )


    plt.show()


    # ========================================================
    # Plot 3
    #
    # K_local vs flow maldistribution
    # ========================================================

    plt.figure()


    plt.plot(

        df_sensitivity[
            "K_local"
        ],

        df_sensitivity[
            "flow_maldistribution_percent"
        ],

        marker="o",
    )


    plt.axhline(

        MALDISTRIBUTION_LIMIT_PERCENT,

        linestyle="--",

        label="10% design limit",
    )


    plt.xlabel(
        "Local-loss coefficient K"
    )


    plt.ylabel(
        "Flow maldistribution (%)"
    )


    plt.title(
        "Local-Loss Effect on Tray Flow Distribution"
    )


    plt.grid(True)

    plt.legend()


    maldistribution_plot = (

        script_dir
        /
        "tray_local_loss_vs_maldistribution.png"
    )


    plt.savefig(

        maldistribution_plot,

        dpi=200,

        bbox_inches="tight",
    )


    plt.show()


    # ========================================================
    # Plot 4
    #
    # K_local vs thermal spread
    # ========================================================

    plt.figure()


    plt.plot(

        df_sensitivity[
            "K_local"
        ],

        df_sensitivity[
            "device_temperature_spread_C"
        ],

        marker="o",
    )


    plt.xlabel(
        "Local-loss coefficient K"
    )


    plt.ylabel(
        "Device temperature spread (°C)"
    )


    plt.title(
        "Hydraulic Maldistribution vs "
        "Tray Thermal Nonuniformity"
    )


    plt.grid(True)


    thermal_spread_plot = (

        script_dir
        /
        "tray_local_loss_vs_temperature_spread.png"
    )


    plt.savefig(

        thermal_spread_plot,

        dpi=200,

        bbox_inches="tight",
    )


    plt.show()


    # ========================================================
    # Plot 5
    #
    # Compare device temperature distributions
    # for K = 0, 1, 2
    # ========================================================

    plt.figure()


    for K_local in K_local_cases:

        case_df = (
            all_cases[
                K_local
            ][
                "thermal_df"
            ]
        )


        plt.plot(

            case_df[
                "branch"
            ],

            case_df[
                "Tdevice_est_C"
            ],

            marker="o",

            label=f"K_local = {K_local}",
        )


    plt.axhline(

        T_DEVICE_LIMIT_C,

        linestyle="--",

        label="85°C design limit",
    )


    plt.xlabel(
        "Accelerator branch"
    )


    plt.ylabel(
        "Estimated device temperature (°C)"
    )


    plt.title(
        "Effect of Manifold Local Loss "
        "on Device Temperature Distribution"
    )


    plt.grid(True)

    plt.legend()


    comparison_plot = (

        script_dir
        /
        "tray_temperature_local_loss_comparison.png"
    )


    plt.savefig(

        comparison_plot,

        dpi=200,

        bbox_inches="tight",
    )


    plt.show()


    # ========================================================
    # Final output summary
    # ========================================================

    print(
        "\n========================================"
    )

    print(
        "ANALYSIS COMPLETE"
    )

    print(
        "========================================"
    )


    print(
        "\nGenerated files:"
    )


    print(
        baseline_csv
    )

    print(
        sensitivity_csv
    )

    print(
        flow_plot
    )

    print(
        temperature_plot
    )

    print(
        maldistribution_plot
    )

    print(
        thermal_spread_plot
    )

    print(
        comparison_plot
    )

    # ============================================================
# Compact thermal-hydraulic engineering summary
# ============================================================

if __name__ == "__main__":

    engineering_summary = []
    
    
    for K_local in K_local_cases:
    
        case = all_cases[K_local]
    
        hydraulic = case["hydraulic"]
    
        thermal_df = case["thermal_df"]
    
    
        # --------------------------------------------------------
        # Hydraulic metrics
        # --------------------------------------------------------
    
        branch_flows = (
            hydraulic[
                "branch_flows_Lmin"
            ]
        )
    
        q_min = np.min(
            branch_flows
        )
    
        q_max = np.max(
            branch_flows
        )
    
        q_mean = np.mean(
            branch_flows
        )
    
        M_flow = (
            hydraulic[
                "maldistribution_percent"
            ]
        )
    
    
        # --------------------------------------------------------
        # ROM validity check
        # --------------------------------------------------------
    
        rom_valid_mask = (
            thermal_df[
                "thermal_status"
            ]
            !=
            "ROM_RANGE_EXCEEDED"
        )
    
        number_valid = (
            rom_valid_mask.sum()
        )
    
        number_total = len(
            thermal_df
        )
    
    
        if number_valid == number_total:
    
            rom_range_status = (
                "ALL_VALID"
            )
    
        else:
    
            rom_range_status = (
                "PARTIAL_RANGE_EXCEEDED"
            )
    
    
        # --------------------------------------------------------
        # Thermal metrics
        #
        # Only evaluate temperature statistics using valid
        # ROM predictions.
        # --------------------------------------------------------
    
        valid_temperatures = (
    
            thermal_df.loc[
                rom_valid_mask,
                "Tdevice_est_C"
            ]
    
            .dropna()
        )
    
    
        if len(valid_temperatures) > 0:
    
            Tmax_valid = (
                valid_temperatures.max()
            )
    
            Tmin_valid = (
                valid_temperatures.min()
            )
    
            T_spread_valid = (
                Tmax_valid
                -
                Tmin_valid
            )
    
            thermal_margin = (
                T_DEVICE_LIMIT_C
                -
                Tmax_valid
            )
    
        else:
    
            Tmax_valid = np.nan
            Tmin_valid = np.nan
            T_spread_valid = np.nan
            thermal_margin = np.nan
    
    
        # --------------------------------------------------------
        # Identify lowest-flow branch
        # --------------------------------------------------------
    
        lowest_flow_branch = (
            np.argmin(
                branch_flows
            )
            +
            1
        )
    
    
        # --------------------------------------------------------
        # Overall thermal status
        # --------------------------------------------------------
    
        if rom_range_status != "ALL_VALID":
    
            case_status = (
                "ROM_CHECK_REQUIRED"
            )
    
        elif Tmax_valid <= T_DEVICE_LIMIT_C:
    
            case_status = "PASS"
    
        else:
    
            case_status = "FAIL"
    
    
        # --------------------------------------------------------
        # Store summary
        # --------------------------------------------------------
    
        engineering_summary.append({
    
            "K_local":
                K_local,
    
            "Mflow_percent":
                M_flow,
    
            "q_min_Lmin":
                q_min,
    
            "q_max_Lmin":
                q_max,
    
            "q_mean_Lmin":
                q_mean,
    
            "lowest_flow_branch":
                lowest_flow_branch,
    
            "Tmax_valid_C":
                Tmax_valid,
    
            "Tmin_valid_C":
                Tmin_valid,
    
            "Tspread_valid_C":
                T_spread_valid,
    
            "thermal_margin_C":
                thermal_margin,
    
            "valid_ROM_branches":
                number_valid,
    
            "total_branches":
                number_total,
    
            "ROM_range_status":
                rom_range_status,
    
            "case_status":
                case_status,
        })
    
    
    # ============================================================
    # Create summary DataFrame
    # ============================================================
    
    df_engineering_summary = (
        pd.DataFrame(
            engineering_summary
        )
    )
    
    
    # ============================================================
    # Print compact table
    # ============================================================
    
    print(
        "\n"
        "============================================================"
    )
    
    print(
        "8-ACCELERATOR THERMAL-HYDRAULIC ENGINEERING SUMMARY"
    )
    
    print(
        "============================================================\n"
    )
    
    
    summary_columns = [
    
        "K_local",
    
        "Mflow_percent",
    
        "q_min_Lmin",
    
        "q_max_Lmin",
    
        "Tmax_valid_C",
    
        "Tspread_valid_C",
    
        "thermal_margin_C",
    
        "valid_ROM_branches",
    
        "ROM_range_status",
    
        "case_status",
    ]
    
    
    print(
    
        df_engineering_summary[
            summary_columns
        ]
    
        .to_string(
            index=False
        )
    )
    
    
    # ============================================================
    # Print branches outside ROM range
    # ============================================================
    
    print(
        "\nROM validity details:"
    )
    
    
    for K_local in K_local_cases:
    
        thermal_df = (
            all_cases[
                K_local
            ][
                "thermal_df"
            ]
        )
    
    
        invalid_rows = (
    
            thermal_df[
                thermal_df[
                    "thermal_status"
                ]
                ==
                "ROM_RANGE_EXCEEDED"
            ]
        )
    
    
        if len(invalid_rows) == 0:
    
            print(
                f"K_local = {K_local}: "
                f"all 8 branches within ROM range."
            )
    
        else:
    
            print(
                f"\nK_local = {K_local}: "
                f"ROM range exceeded for:"
            )
    
            print(
    
                invalid_rows[
                    [
                        "branch",
                        "flow_Lmin",
                        "thermal_status",
                    ]
                ]
    
                .to_string(
                    index=False
                )
            )
    
    
    # ============================================================
    # Save engineering summary
    # ============================================================
    
    summary_csv = (
    
        script_dir
        /
        "tray_engineering_summary.csv"
    )
    
    
    df_engineering_summary.to_csv(
    
        summary_csv,
    
        index=False,
    )
    
    
    print(
        f"\nSaved engineering summary to:"
        f"\n{summary_csv}"
    )
