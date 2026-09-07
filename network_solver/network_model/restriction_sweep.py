from pathlib import Path
import sys

# ============================================================
# Make Project 2 root available for imports
# This allows VS Code "Run Python File" to find component_rom
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

from scipy.optimize import root

from component_rom.coldplate_rom import evaluate_coldplate


# ============================================================
# Validated hydraulic ROM
#
# Delta-p [kPa] = A*q + B*q^2
#
# q is numerically expressed in L/min.
# ============================================================

A = 6.2644745879
B = 3.0720638374


def coldplate_dp_kpa(flow_lpm):
    """
    Calculate cold-plate pressure drop from the validated
    hydraulic reduced-order model.

    Parameters
    ----------
    flow_lpm : float
        Branch volumetric flow rate in L/min.

    Returns
    -------
    float
        Pressure drop in kPa.
    """

    return (
        A * flow_lpm
        +
        B * flow_lpm**2
    )


# ============================================================
# Hydraulic network solver
#
# Two identical normal branches
# +
# one restricted branch
#
# Total flow is fixed.
# ============================================================

def solve_network(
    restriction_factor,
    q_total=1.95,
):
    """
    Solve a three-branch parallel hydraulic network.

    Branch 1 = normal cold plate
    Branch 2 = normal cold plate
    Branch 3 = restricted cold plate

    Parameters
    ----------
    restriction_factor : float
        Hydraulic resistance multiplier applied to
        the restricted branch.

        1.0 = healthy branch
        1.3 = 30% additional pressure-loss behavior

    q_total : float
        Total prescribed flow in L/min.

    Returns
    -------
    q_normal : float
        Flow through each normal branch, L/min.

    q_restricted : float
        Flow through restricted branch, L/min.

    dp_common : float
        Common supply-to-return pressure drop, kPa.
    """

    def equations(x):

        q_normal, q_restricted = x

        # --------------------------------------------
        # Equation 1: mass conservation
        #
        # 2*q_normal + q_restricted = q_total
        # --------------------------------------------

        mass_residual = (
            2.0 * q_normal
            +
            q_restricted
            -
            q_total
        )

        # --------------------------------------------
        # Normal branch pressure drop
        # --------------------------------------------

        dp_normal = coldplate_dp_kpa(
            q_normal
        )

        # --------------------------------------------
        # Restricted branch pressure drop
        #
        # Restriction factor multiplies the normal
        # cold-plate pressure-loss behavior.
        # --------------------------------------------

        dp_restricted = (
            restriction_factor
            *
            coldplate_dp_kpa(
                q_restricted
            )
        )

        # --------------------------------------------
        # Equation 2: equal pressure drop
        #
        # All three branches connect to the same
        # supply and return pressure nodes.
        # --------------------------------------------

        pressure_residual = (
            dp_normal
            -
            dp_restricted
        )

        return [
            mass_residual,
            pressure_residual,
        ]

    # Equal-flow condition is a good initial guess.
    initial_guess = [
        q_total / 3.0,
        q_total / 3.0,
    ]

    solution = root(
        equations,
        initial_guess,
    )

    if not solution.success:
        raise RuntimeError(
            f"Network solver failed: "
            f"{solution.message}"
        )

    q_normal, q_restricted = solution.x

    if q_normal <= 0 or q_restricted <= 0:
        raise RuntimeError(
            "Network solver returned "
            "nonphysical branch flow."
        )

    dp_common = coldplate_dp_kpa(
        q_normal
    )

    return (
        q_normal,
        q_restricted,
        dp_common,
    )


# ============================================================
# Main analysis
# ============================================================

def main():

    # --------------------------------------------------------
    # System operating assumptions
    # --------------------------------------------------------

    Q_TOTAL_LMIN = 1.95

    HEAT_LOAD_W = 750.0
    TIN_C = 30.0

    # Generic Project 2 assumptions,
    # NOT vendor-specific package properties.
    R_TIM_K_W = 0.005
    R_PACKAGE_K_W = 0.020

    T_DEVICE_LIMIT_C = 85.0

    # Provisional design requirements
    MIN_DESIGN_FLOW_LMIN = 0.65
    MALDISTRIBUTION_LIMIT_PERCENT = 10.0

    # --------------------------------------------------------
    # Restriction sweep
    # --------------------------------------------------------

    restriction_factors = [
        1.00,
        1.10,
        1.20,
        1.30,
        1.40,
    ]

    results = []

    for factor in restriction_factors:

        # ====================================================
        # 1. Hydraulic network calculation
        # ====================================================

        q_n, q_r, dp = solve_network(
            restriction_factor=factor,
            q_total=Q_TOTAL_LMIN,
        )

        flows = np.array([
            q_n,
            q_n,
            q_r,
        ])

        q_mean = np.mean(flows)

        maldistribution = (
            (
                np.max(flows)
                -
                np.min(flows)
            )
            /
            q_mean
            *
            100.0
        )

        # ====================================================
        # 2. Thermal ROM calculation for restricted branch
        # ====================================================

        rth = np.nan
        Tout = np.nan
        Tbulk = np.nan
        Tbase = np.nan
        Tdevice = np.nan

        thermal_status = (
            "ROM_RANGE_EXCEEDED"
        )

        try:

            thermal = evaluate_coldplate(
                flow_lmin=q_r,
                heat_load_w=HEAT_LOAD_W,
                inlet_temperature_c=TIN_C,

                tim_resistance_k_per_w=
                    R_TIM_K_W,

                package_resistance_k_per_w=
                    R_PACKAGE_K_W,

                extrapolation="error",
            )

            # ColdPlateResult is a dataclass,
            # therefore use dot notation.
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

            if (
                Tdevice
                <=
                T_DEVICE_LIMIT_C
            ):
                thermal_status = "PASS"

            else:
                thermal_status = "FAIL"

        except ValueError:

            # Example:
            # q_r = 0.495 L/min
            # is below the validated
            # 0.50 L/min ROM range.

            thermal_status = (
                "ROM_RANGE_EXCEEDED"
            )

        # ====================================================
        # 3. Engineering status checks
        # ====================================================

        if (
            q_r
            >=
            MIN_DESIGN_FLOW_LMIN
        ):
            flow_status = "PASS"

        else:
            flow_status = "LOW_FLOW"

        if (
            maldistribution
            <=
            MALDISTRIBUTION_LIMIT_PERCENT
        ):
            maldistribution_status = "PASS"

        else:
            maldistribution_status = "FAIL"

        # ====================================================
        # 4. Overall engineering status
        # ====================================================

        if (
            flow_status == "PASS"
            and
            maldistribution_status == "PASS"
            and
            thermal_status == "PASS"
        ):
            overall_status = "PASS"

        elif (
            thermal_status
            ==
            "ROM_RANGE_EXCEEDED"
        ):
            overall_status = (
                "REQUIRES_HIGH_FIDELITY_CHECK"
            )

        else:
            overall_status = "FAIL"

        # ====================================================
        # 5. Store ONE complete operating point
        # ====================================================

        results.append({

            "restriction_factor":
                factor,

            "normal_flow_Lmin":
                q_n,

            "restricted_flow_Lmin":
                q_r,

            "pressure_drop_kPa":
                dp,

            "maldistribution_percent":
                maldistribution,

            "restricted_Rth_K_W":
                rth,

            "restricted_Tout_C":
                Tout,

            "restricted_Tbulk_C":
                Tbulk,

            "restricted_Tbase_C":
                Tbase,

            "restricted_Tdevice_est_C":
                Tdevice,

            "flow_status":
                flow_status,

            "maldistribution_status":
                maldistribution_status,

            "thermal_status":
                thermal_status,

            "overall_status":
                overall_status,
        })


    # ========================================================
    # Create dataframe AFTER all complete rows are generated
    # ========================================================

    df = pd.DataFrame(results)

    print(
        "\nComplete thermal-hydraulic "
        "restriction sweep:\n"
    )

    print(df)

    print(
        "\nDataFrame columns:"
    )

    print(
        df.columns.tolist()
    )


    # ========================================================
    # Compact engineering summary
    # ========================================================

    print(
        "\nEngineering summary:\n"
    )

    print(
        df[
            [
                "restriction_factor",
                "restricted_flow_Lmin",
                "pressure_drop_kPa",
                "maldistribution_percent",
                "restricted_Tdevice_est_C",
                "flow_status",
                "maldistribution_status",
                "thermal_status",
                "overall_status",
            ]
        ]
    )


    # ========================================================
    # Save CSV
    # ========================================================

    script_dir = (
        Path(__file__)
        .resolve()
        .parent
    )

    output_file = (
        script_dir
        /
        "restriction_sweep.csv"
    )

    df.to_csv(
        output_file,
        index=False,
    )

    print(
        f"\nSaved results to: "
        f"{output_file}"
    )


    # ========================================================
    # Plot 1:
    # Restricted branch flow vs restriction
    # ========================================================

    plt.figure()

    plt.plot(
        df["restriction_factor"],
        df["restricted_flow_Lmin"],
        marker="o",
    )

    plt.axhline(
        MIN_DESIGN_FLOW_LMIN,
        linestyle="--",
        label="0.65 L/min design minimum",
    )

    plt.xlabel(
        "Branch resistance multiplier"
    )

    plt.ylabel(
        "Restricted branch flow (L/min)"
    )

    plt.title(
        "Effect of Branch Restriction on Flow"
    )

    plt.grid(True)
    plt.legend()

    flow_plot = (
        script_dir
        /
        "restriction_vs_flow.png"
    )

    plt.savefig(
        flow_plot,
        dpi=200,
        bbox_inches="tight",
    )

    plt.show()


    # ========================================================
    # Plot 2:
    # Flow maldistribution vs restriction
    # ========================================================

    plt.figure()

    plt.plot(
        df["restriction_factor"],
        df["maldistribution_percent"],
        marker="o",
    )

    plt.axhline(
        MALDISTRIBUTION_LIMIT_PERCENT,
        linestyle="--",
        label="10% maldistribution limit",
    )

    plt.xlabel(
        "Branch resistance multiplier"
    )

    plt.ylabel(
        "Flow maldistribution (%)"
    )

    plt.title(
        "Branch Restriction vs "
        "Flow Maldistribution"
    )

    plt.grid(True)
    plt.legend()

    maldistribution_plot = (
        script_dir
        /
        "restriction_vs_maldistribution.png"
    )

    plt.savefig(
        maldistribution_plot,
        dpi=200,
        bbox_inches="tight",
    )

    plt.show()


    # ========================================================
    # Plot 3:
    # Device temperature vs restriction
    # ========================================================

    plt.figure()

    plt.plot(
        df["restriction_factor"],
        df["restricted_Tdevice_est_C"],
        marker="o",
        label="Restricted branch",
    )

    plt.axhline(
        T_DEVICE_LIMIT_C,
        linestyle="--",
        label="85°C design limit",
    )

    plt.xlabel(
        "Branch resistance multiplier"
    )

    plt.ylabel(
        "Estimated device temperature (°C)"
    )

    plt.title(
        "Branch Restriction vs "
        "Device Temperature"
    )

    plt.grid(True)
    plt.legend()

    temperature_plot = (
        script_dir
        /
        "restriction_vs_device_temperature.png"
    )

    plt.savefig(
        temperature_plot,
        dpi=200,
        bbox_inches="tight",
    )

    plt.show()


    # ========================================================
    # Final output locations
    # ========================================================

    print(
        "\nSaved figures:"
    )

    print(flow_plot)
    print(maldistribution_plot)
    print(temperature_plot)


# ============================================================
# Run only when this file is executed directly
# ============================================================

if __name__ == "__main__":
    main()


