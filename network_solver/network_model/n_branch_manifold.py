import numpy as np
from scipy.optimize import least_squares
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
import sys

# ============================================================
# Add project root to Python import path
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# Component models
# ============================================================

from component_rom.coldplate_rom import (
    MAX_CALIBRATED_FLOW_LMIN as ROM_FLOW_MAX_LMIN,
    MIN_CALIBRATED_FLOW_LMIN as ROM_FLOW_MIN_LMIN,
    pressure_drop_kpa as coldplate_dp_kpa,
)

from network_solver.components.branch_hydraulics import (
    branch_pressure_drop_kpa,
)

# ============================================================
# 2. Churchill Darcy friction factor
# ============================================================

def darcy_friction_factor(
    reynolds,
    relative_roughness=0.0,
):
    """
    Churchill correlation for Darcy friction factor.

    Provides a smooth formulation through laminar,
    transitional, and turbulent regimes.
    """

    if reynolds <= 0:
        raise ValueError(
            "Reynolds number must be positive."
        )

    term_A = (
        2.457
        *
        np.log(
            1.0
            /
            (
                (7.0 / reynolds) ** 0.9
                +
                0.27 * relative_roughness
            )
        )
    ) ** 16

    term_B = (
        37530.0
        /
        reynolds
    ) ** 16

    friction_factor = (
        8.0
        *
        (
            (8.0 / reynolds) ** 12
            +
            1.0
            /
            (term_A + term_B) ** 1.5
        )
        ** (1.0 / 12.0)
    )

    return friction_factor


# ============================================================
# 3. Physical manifold-segment pressure-loss model
# ============================================================

def manifold_segment_dp_kpa(
    flow_lmin,
    diameter_m,
    length_m,
    density_kg_m3=996.0,
    viscosity_pa_s=8.0e-4,
    roughness_m=0.0,
    K_local=0.0,
):
    """
    Calculate pressure loss through one circular
    manifold segment.

    Returns
    -------
    dp_kpa
        Total pressure loss, kPa.

    velocity_m_s
        Mean flow velocity, m/s.

    reynolds
        Reynolds number.

    friction_factor
        Darcy friction factor.
    """

    # Handle a zero-flow segment safely
    if flow_lmin <= 0:

        return (
            0.0,
            0.0,
            0.0,
            0.0,
        )


    # --------------------------------------------------------
    # Convert L/min -> m^3/s
    # --------------------------------------------------------

    flow_m3_s = (
        flow_lmin
        * 1.0e-3
        / 60.0
    )


    # --------------------------------------------------------
    # Circular manifold area
    # --------------------------------------------------------

    area_m2 = (
        np.pi
        * diameter_m**2
        / 4.0
    )


    # --------------------------------------------------------
    # Mean velocity
    # --------------------------------------------------------

    velocity_m_s = (
        flow_m3_s
        /
        area_m2
    )


    # --------------------------------------------------------
    # Reynolds number
    # --------------------------------------------------------

    reynolds = (
        density_kg_m3
        *
        velocity_m_s
        *
        diameter_m
        /
        viscosity_pa_s
    )


    # --------------------------------------------------------
    # Relative roughness
    # --------------------------------------------------------

    relative_roughness = (
        roughness_m
        /
        diameter_m
    )


    # --------------------------------------------------------
    # Darcy friction factor
    # --------------------------------------------------------

    friction_factor = (
        darcy_friction_factor(
            reynolds,
            relative_roughness,
        )
    )


    # --------------------------------------------------------
    # Dynamic pressure
    # --------------------------------------------------------

    dynamic_pressure_pa = (
        0.5
        *
        density_kg_m3
        *
        velocity_m_s**2
    )


    # --------------------------------------------------------
    # Distributed friction loss
    # --------------------------------------------------------

    dp_friction_pa = (
        friction_factor
        *
        (
            length_m
            /
            diameter_m
        )
        *
        dynamic_pressure_pa
    )


    # --------------------------------------------------------
    # Local loss
    # --------------------------------------------------------

    dp_local_pa = (
        K_local
        *
        dynamic_pressure_pa
    )


    # --------------------------------------------------------
    # Total pressure loss
    # --------------------------------------------------------

    dp_total_pa = (
        dp_friction_pa
        +
        dp_local_pa
    )


    return (
        dp_total_pa / 1000.0,
        velocity_m_s,
        reynolds,
        friction_factor,
    )


# ============================================================
# 4. General N-branch physical manifold solver
# ============================================================

def solve_n_branch_manifold(
    n_branches,
    q_total_lmin,
    supply_diameter_m,
    return_diameter_m,
    segment_length_m,
    density_kg_m3=996.0,
    viscosity_pa_s=8.0e-4,
    supply_K_local=0.0,
    return_K_local=0.0,
    branch_tube_diameter_m=0.0095,
    branch_supply_tube_length_m=0.30,
    branch_return_tube_length_m=0.30,
    branch_number_of_qds=2,
    branch_K_qd_each=1.0,
    branch_K_fittings_total=1.0,
    branch_roughness_m=0.0,
    branch_resistance_multipliers=None,
):
    """
    Solve N identical accelerator branches connected to a
    same-side supply / return manifold.

    Unknowns
    --------
    q[0], q[1], ..., q[N-1]

    where q[i] is the flow through branch i+1.  Each branch pressure drop
    includes its cold plate, supply/return tubes, QDs, and fittings.
    """
    if branch_resistance_multipliers is None:

        branch_resistance_multipliers = np.ones(
            n_branches
        )

    else:

        branch_resistance_multipliers = np.asarray(
            branch_resistance_multipliers,
            dtype=float,
        )

        if branch_resistance_multipliers.shape != (n_branches,):

            raise ValueError(
                "branch_resistance_multipliers must have "
                "one value per branch."
            )

        if (
            not np.all(np.isfinite(branch_resistance_multipliers))
            or
            np.any(branch_resistance_multipliers <= 0.0)
        ):

            raise ValueError(
                "branch_resistance_multipliers must contain "
                "finite, positive values."
            )
    
    def complete_branch_dp_kpa(flow_lmin):
        """Evaluate one branch with the hardware configured for this solve."""
        return branch_pressure_drop_kpa(
            flow_lmin,
            tube_diameter_m=branch_tube_diameter_m,
            supply_tube_length_m=branch_supply_tube_length_m,
            return_tube_length_m=branch_return_tube_length_m,
            number_of_qds=branch_number_of_qds,
            K_qd_each=branch_K_qd_each,
            K_fittings_total=branch_K_fittings_total,
            density_kg_m3=density_kg_m3,
            viscosity_pa_s=viscosity_pa_s,
            roughness_m=branch_roughness_m,
            extrapolation="error",
        )


    # ========================================================
    # Nonlinear residual equations
    # ========================================================

    def equations(q):

        residuals = np.zeros(
            n_branches
        )


        # ----------------------------------------------------
        # Equation 1:
        # Overall mass conservation
        # ----------------------------------------------------

        residuals[0] = (
            np.sum(q)
            -
            q_total_lmin
        )


        # ----------------------------------------------------
        # Equations 2 ... N:
        # Adjacent branch pressure compatibility
        # ----------------------------------------------------

        for i in range(
            n_branches - 1
        ):

            q_i = q[i]

            q_next = q[i + 1]


            # -----------------------------------------------
            # Complete branch pressure drops
            # -----------------------------------------------

            dp_branch_i = (
                branch_resistance_multipliers[i]
                *
                complete_branch_dp_kpa(
                    q_i
                )
            )


            dp_branch_next = (
                branch_resistance_multipliers[i + 1]
                *
                complete_branch_dp_kpa(
                    q_next
                )
            )


            # -----------------------------------------------
            # Flow remaining in the header after branch i
            # -----------------------------------------------

            downstream_flow = (
                np.sum(
                    q[i + 1:]
                )
            )


            # -----------------------------------------------
            # Supply segment pressure loss
            # -----------------------------------------------

            dp_supply, _, _, _ = (
                manifold_segment_dp_kpa(
                    flow_lmin=
                        downstream_flow,

                    diameter_m=
                        supply_diameter_m,

                    length_m=
                        segment_length_m,

                    density_kg_m3=
                        density_kg_m3,

                    viscosity_pa_s=
                        viscosity_pa_s,

                    K_local=
                        supply_K_local,
                )
            )


            # -----------------------------------------------
            # Return segment pressure loss
            # -----------------------------------------------

            dp_return, _, _, _ = (
                manifold_segment_dp_kpa(
                    flow_lmin=
                        downstream_flow,

                    diameter_m=
                        return_diameter_m,

                    length_m=
                        segment_length_m,

                    density_kg_m3=
                        density_kg_m3,

                    viscosity_pa_s=
                        viscosity_pa_s,

                    K_local=
                        return_K_local,
                )
            )


            # -----------------------------------------------
            # Hydraulic compatibility
            #
            # dp_branch_i - dp_branch_(i+1)
            #
            # =
            #
            # supply segment loss
            # +
            # return segment loss
            # -----------------------------------------------

            residuals[i + 1] = (
                dp_branch_i
                -
                dp_branch_next
                -
                dp_supply
                -
                dp_return
            )


        return residuals


    # ========================================================
    # Initial guess
    # ========================================================

    equal_flow_guess = (
        q_total_lmin
        /
        n_branches
    )


    # Check whether the requested total flow is even
    # compatible with the validated component-ROM domain.
    minimum_possible_total_flow = (
        n_branches
        *
        ROM_FLOW_MIN_LMIN
    )

    maximum_possible_total_flow = (
        n_branches
        *
        ROM_FLOW_MAX_LMIN
    )


    if not (
        minimum_possible_total_flow
        <=
        q_total_lmin
        <=
        maximum_possible_total_flow
    ):

        raise ValueError(
            "Requested total flow cannot be represented "
            "while keeping every branch inside the "
            "validated cold-plate ROM range."
        )


    # Keep initial point safely inside bounds.
    initial_guess = np.full(
        n_branches,
        equal_flow_guess,
    )

    initial_guess = np.clip(
        initial_guess,
        ROM_FLOW_MIN_LMIN + 1.0e-6,
        ROM_FLOW_MAX_LMIN - 1.0e-6,
    )


    # ========================================================
    # Solve bounded nonlinear system
    #
    # least_squares is used instead of root because root()
    # can temporarily evaluate branch flows outside the
    # validated cold-plate ROM range.
    # ========================================================

    lower_bounds = np.full(
        n_branches,
        ROM_FLOW_MIN_LMIN,
    )

    upper_bounds = np.full(
        n_branches,
        ROM_FLOW_MAX_LMIN,
    )


    solution = least_squares(

        equations,

        initial_guess,

        bounds=(
            lower_bounds,
            upper_bounds,
        ),

        xtol=1.0e-12,
        ftol=1.0e-12,
        gtol=1.0e-12,

        max_nfev=5000,
    )


    if not solution.success:

        raise RuntimeError(
            f"Network solver failed: "
            f"{solution.message}"
        )


    branch_flows = solution.x

    # ========================================================
    # Confirm that this is a true network solution
    # and not merely a constrained least-squares minimum.
    # ========================================================

    final_residuals = equations(
        branch_flows
    )

    max_residual = np.max(
        np.abs(final_residuals)
    )


    if max_residual > 1.0e-8:

        raise RuntimeError(
            "No physically consistent network solution "
            "was found entirely inside the validated "
            "cold-plate ROM range. "
            f"Maximum residual = {max_residual:.3e}. "
            "The component ROM may need to be extended."
        )


    if np.any(
        branch_flows <= 0
    ):

        raise RuntimeError(
            "Solver returned a "
            "nonphysical branch flow."
        )


    # ========================================================
    # 5. Cold-plate pressure drops
    # ========================================================

    coldplate_dp = np.array(
        [
            coldplate_dp_kpa(q)
            for q in branch_flows
        ]
    )


    # ========================================================
    # 5b. Complete branch pressure drops
    # ========================================================

    branch_dp = np.array(
        [
            branch_resistance_multipliers[i]
            *
            complete_branch_dp_kpa(branch_flows[i])
            for i in range(n_branches)
        ]
    )


    # ========================================================
    # 6. Calculate each manifold segment
    # ========================================================

    segment_flows = []

    supply_dp = []
    return_dp = []

    supply_velocity = []
    supply_reynolds = []

    return_velocity = []
    return_reynolds = []


    for i in range(
        n_branches - 1
    ):

        downstream_flow = (
            np.sum(
                branch_flows[
                    i + 1:
                ]
            )
        )


        segment_flows.append(
            downstream_flow
        )


        (
            dp_s,
            U_s,
            Re_s,
            _,
        ) = manifold_segment_dp_kpa(

            flow_lmin=
                downstream_flow,

            diameter_m=
                supply_diameter_m,

            length_m=
                segment_length_m,

            density_kg_m3=
                density_kg_m3,

            viscosity_pa_s=
                viscosity_pa_s,

            K_local=
                supply_K_local,
        )


        (
            dp_r,
            U_r,
            Re_r,
            _,
        ) = manifold_segment_dp_kpa(

            flow_lmin=
                downstream_flow,

            diameter_m=
                return_diameter_m,

            length_m=
                segment_length_m,

            density_kg_m3=
                density_kg_m3,

            viscosity_pa_s=
                viscosity_pa_s,

            K_local=
                return_K_local,
        )


        supply_dp.append(dp_s)
        return_dp.append(dp_r)

        supply_velocity.append(U_s)
        supply_reynolds.append(Re_s)

        return_velocity.append(U_r)
        return_reynolds.append(Re_r)


    segment_flows = np.array(
        segment_flows
    )

    supply_dp = np.array(
        supply_dp
    )

    return_dp = np.array(
        return_dp
    )


    # ========================================================
    # 7. Node pressures
    #
    # Set return node R1 = 0 kPa.
    # ========================================================

    p_return = np.zeros(
        n_branches
    )

    p_supply = np.zeros(
        n_branches
    )


    # Complete branch 1 defines S1 pressure
    p_supply[0] = (
        branch_dp[0]
    )


    # Supply pressure decreases downstream
    for i in range(
        n_branches - 1
    ):

        p_supply[i + 1] = (
            p_supply[i]
            -
            supply_dp[i]
        )


    # Return pressure increases
    # as we move downstream away from outlet
    for i in range(
        n_branches - 1
    ):

        p_return[i + 1] = (
            p_return[i]
            +
            return_dp[i]
        )


    # ========================================================
    # 8. Flow-maldistribution metric
    # ========================================================

    q_mean = np.mean(
        branch_flows
    )

    maldistribution_percent = (
        (
            np.max(branch_flows)
            -
            np.min(branch_flows)
        )
        /
        q_mean
        *
        100.0
    )


    # ========================================================
    # 9. Numerical residuals
    # ========================================================

    final_residuals = (
        equations(
            branch_flows
        )
    )


    return {

        "branch_flows_Lmin":
            branch_flows,

        "coldplate_dp_kPa":
            coldplate_dp,

        "branch_dp_kPa":
            branch_dp,

        "branch_hardware_dp_kPa":
            branch_dp - coldplate_dp,

        "segment_flows_Lmin":
            segment_flows,

        "supply_dp_kPa":
            supply_dp,

        "return_dp_kPa":
            return_dp,

        "supply_velocity_m_s":
            np.array(
                supply_velocity
            ),

        "supply_reynolds":
            np.array(
                supply_reynolds
            ),

        "return_velocity_m_s":
            np.array(
                return_velocity
            ),

        "return_reynolds":
            np.array(
                return_reynolds
            ),

        "supply_node_pressure_kPa":
            p_supply,

        "return_node_pressure_kPa":
            p_return,

        "maldistribution_percent":
            maldistribution_percent,

        "system_pressure_drop_kPa":
            p_supply[0] - p_return[0],

        "residuals":
            final_residuals,

        "branch_resistance_multipliers":
            branch_resistance_multipliers,

    }


# ============================================================
# 10. Eight-accelerator learning case
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Tray configuration
    # --------------------------------------------------------

    N_BRANCHES = 8


    # --------------------------------------------------------
    # Nominal branch target
    #
    # Approximately 1.08 L/min per accelerator
    # corresponds to ~10 C coolant rise at 750 W.
    # --------------------------------------------------------

    NOMINAL_BRANCH_FLOW_LMIN = 1.08


    Q_TOTAL_LMIN = (
        N_BRANCHES
        *
        NOMINAL_BRANCH_FLOW_LMIN
    )


    # --------------------------------------------------------
    # Initial common-header geometry
    #
    # 3/4-inch ID baseline
    # --------------------------------------------------------

    MANIFOLD_DIAMETER_M = (
        0.01905
    )


    # Adjacent accelerator spacing
    SEGMENT_LENGTH_M = (
        0.050
    )


    results = (
        solve_n_branch_manifold(

            n_branches=
                N_BRANCHES,

            q_total_lmin=
                Q_TOTAL_LMIN,

            supply_diameter_m=
                MANIFOLD_DIAMETER_M,

            return_diameter_m=
                MANIFOLD_DIAMETER_M,

            segment_length_m=
                SEGMENT_LENGTH_M,

            supply_K_local=
                0.0,

            return_K_local=
                0.0,
        )
    )


    # ========================================================
    # Print system summary
    # ========================================================

    print(
        "\n"
        "========================================"
    )

    print(
        "8-BRANCH AI ACCELERATOR MANIFOLD"
    )

    print(
        "========================================"
    )


    print(
        f"\nTotal flow = "
        f"{Q_TOTAL_LMIN:.3f} L/min"
    )


    print(
        f"Nominal equal branch flow = "
        f"{NOMINAL_BRANCH_FLOW_LMIN:.3f} L/min"
    )


    print(
        f"Header ID = "
        f"{MANIFOLD_DIAMETER_M * 1000:.2f} mm"
    )


    # ========================================================
    # Branch flows
    # ========================================================

    print(
        "\nBranch flows:"
    )


    for i, q in enumerate(
        results[
            "branch_flows_Lmin"
        ],
        start=1,
    ):

        print(
            f"Branch {i}: "
            f"{q:.6f} L/min"
        )


    # ========================================================
    # Manifold segment results
    # ========================================================

    print(
        "\nSupply manifold segments:"
    )


    for i in range(
        N_BRANCHES - 1
    ):

        print(

            f"S{i+1} -> S{i+2}: "

            f"Q = "
            f"{results['segment_flows_Lmin'][i]:.4f} L/min, "

            f"U = "
            f"{results['supply_velocity_m_s'][i]:.3f} m/s, "

            f"Re = "
            f"{results['supply_reynolds'][i]:.0f}, "

            f"dp = "
            f"{results['supply_dp_kPa'][i] * 1000:.3f} Pa"
        )


    # ========================================================
    # Node pressures
    # ========================================================

    print(
        "\nBranch driving pressures:"
    )


    for i in range(
        N_BRANCHES
    ):

        dp_branch = (

            results[
                "supply_node_pressure_kPa"
            ][i]

            -

            results[
                "return_node_pressure_kPa"
            ][i]
        )


        print(

            f"Branch {i+1}: "

            f"pS = "
            f"{results['supply_node_pressure_kPa'][i]:.5f} kPa, "

            f"pR = "
            f"{results['return_node_pressure_kPa'][i]:.5f} kPa, "

            f"Delta-p = "
            f"{dp_branch:.5f} kPa"
        )


    # ========================================================
    # Maldistribution
    # ========================================================

    print(
        f"\nFlow maldistribution = "
        f"{results['maldistribution_percent']:.4f}%"
    )


    # ========================================================
    # Solver residuals
    # ========================================================

    print(
        "\nSolver residuals:"
    )


    for i, residual in enumerate(
        results["residuals"]
    ):

        print(
            f"Residual {i}: "
            f"{residual:.3e}"
        )



# ============================================================
# Header diameter sweep
# ============================================================

if __name__ == "__main__":

    diameters_mm = [
        12.7,
        15.0,
        19.05,
        25.4,
    ]
    
    sweep_results = []
    
    
    for diameter_mm in diameters_mm:
    
        diameter_m = (
            diameter_mm
            /
            1000.0
        )
    
        result = solve_n_branch_manifold(
    
            n_branches=8,
    
            q_total_lmin=8.64,
    
            supply_diameter_m=diameter_m,
    
            return_diameter_m=diameter_m,
    
            segment_length_m=0.050,
    
            supply_K_local=0.0,
    
            return_K_local=0.0,
        )
    
    
        branch_flows = (
            result["branch_flows_Lmin"]
        )
    
    
        # Total supply pressure variation
        supply_pressure_loss = (
            np.sum(
                result["supply_dp_kPa"]
            )
        )
    
    
        # Total return pressure variation
        return_pressure_loss = (
            np.sum(
                result["return_dp_kPa"]
            )
        )
    
    
        total_header_pressure_variation = (
            supply_pressure_loss
            +
            return_pressure_loss
        )
    
    
        sweep_results.append({
    
            "diameter_mm":
                diameter_mm,
    
            "min_branch_flow_Lmin":
                np.min(branch_flows),
    
            "max_branch_flow_Lmin":
                np.max(branch_flows),
    
            "maldistribution_percent":
                result[
                    "maldistribution_percent"
                ],
    
            "max_header_velocity_m_s":
                np.max(
                    result[
                        "supply_velocity_m_s"
                    ]
                ),
    
            "max_header_Re":
                np.max(
                    result[
                        "supply_reynolds"
                    ]
                ),
    
            "header_pressure_variation_Pa":
                (
                    total_header_pressure_variation
                    *
                    1000.0
                ),
        })
    
    
    # ============================================================
    # DataFrame
    # ============================================================
    
    df_sweep = pd.DataFrame(
        sweep_results
    )
    
    
    print(
        "\n========================================"
    )
    
    print(
        "8-BRANCH HEADER DIAMETER SWEEP"
    )
    
    print(
        "========================================\n"
    )
    
    print(
        df_sweep.to_string(
            index=False
        )
    )
    
    
    # ============================================================
    # Plot:
    # Header diameter vs flow maldistribution
    # ============================================================
    
    plt.figure()
    
    plt.plot(
        df_sweep["diameter_mm"],
        df_sweep["maldistribution_percent"],
        marker="o",
    )
    
    
    plt.axhline(
        10.0,
        linestyle="--",
        label="10% design limit",
    )
    
    plt.xlabel(
        "Header internal diameter (mm)"
    )
    
    plt.ylabel(
        "Flow maldistribution (%)"
    )
    
    
    plt.title(
        "Effect of Header Diameter "
        "on Flow Distribution"
    )
    
    plt.grid(True)
    
    plt.legend()
    
    plt.show()
    
    
    
    # ============================================================
    # Local-loss + header-diameter sensitivity study
    # ============================================================
    
    N_BRANCHES = 8
    Q_TOTAL_LMIN = 8.64
    SEGMENT_LENGTH_M = 0.050
    
    
    # Header diameters
    diameters_mm = [
        12.7,
        15.0,
        19.05,
        25.4,
    ]
    
    
    # Local-loss sensitivity values
    K_local_values = [
        0.0,
        0.5,
        1.0,
        2.0,
    ]
    
    
    sensitivity_results = []
    
    
    # ============================================================
    # Run all diameter / K combinations
    # ============================================================
    
    for K_local in K_local_values:
    
        for diameter_mm in diameters_mm:
    
            diameter_m = (
                diameter_mm
                / 1000.0
            )
    
    
            try:
                result = solve_n_branch_manifold(
    
                    n_branches=N_BRANCHES,
    
                    q_total_lmin=Q_TOTAL_LMIN,
    
                    supply_diameter_m=diameter_m,
    
                    return_diameter_m=diameter_m,
    
                    segment_length_m=SEGMENT_LENGTH_M,
    
                    # Same sensitivity value applied to
                    # supply and return manifold segments
                    supply_K_local=K_local,
    
                    return_K_local=K_local,
                )
    
            except RuntimeError:
                # Keep the component-ROM bounds enforced. Report a
                # design point that has no valid bounded solution
                # instead of extrapolating or aborting the sweep.
                sensitivity_results.append({
                    "K_local": K_local,
                    "diameter_mm": diameter_mm,
                    "min_branch_flow_Lmin": np.nan,
                    "max_branch_flow_Lmin": np.nan,
                    "mean_branch_flow_Lmin": np.nan,
                    "maldistribution_percent": np.nan,
                    "max_header_velocity_m_s": np.nan,
                    "max_header_Re": np.nan,
                    "header_pressure_variation_Pa": np.nan,
                    "solver_status": "NO_SOLUTION_WITHIN_ROM_BOUNDS",
                })
                continue
    
    
            branch_flows = (
                result["branch_flows_Lmin"]
            )
    
    
            # ----------------------------------------------------
            # Total pressure variation created by the manifolds
            #
            # This is the difference between the hydraulic
            # environment of the first and last branches.
            # ----------------------------------------------------
    
            supply_variation_kPa = (
                np.sum(
                    result["supply_dp_kPa"]
                )
            )
    
            return_variation_kPa = (
                np.sum(
                    result["return_dp_kPa"]
                )
            )
    
            total_header_variation_kPa = (
                supply_variation_kPa
                +
                return_variation_kPa
            )
    
    
            # ----------------------------------------------------
            # Store one design point
            # ----------------------------------------------------
    
            sensitivity_results.append({
    
                "K_local":
                    K_local,
    
                "diameter_mm":
                    diameter_mm,
    
                "min_branch_flow_Lmin":
                    np.min(branch_flows),
    
                "max_branch_flow_Lmin":
                    np.max(branch_flows),
    
                "mean_branch_flow_Lmin":
                    np.mean(branch_flows),
    
                "maldistribution_percent":
                    result[
                        "maldistribution_percent"
                    ],
    
                "max_header_velocity_m_s":
                    np.max(
                        result[
                            "supply_velocity_m_s"
                        ]
                    ),
    
                "max_header_Re":
                    np.max(
                        result[
                            "supply_reynolds"
                        ]
                    ),
    
                "header_pressure_variation_Pa":
                    total_header_variation_kPa
                    * 1000.0,
    
                "solver_status":
                    "OK",
            })
    
    
    # ============================================================
    # Convert to DataFrame
    # ============================================================
    
    df_sensitivity = pd.DataFrame(
        sensitivity_results
    )
    
    
    print(
        "\n========================================"
    )
    
    print(
        "LOCAL-LOSS / HEADER-DIAMETER SENSITIVITY"
    )
    
    print(
        "========================================\n"
    )
    
    
    print(
        df_sensitivity.to_string(
            index=False
        )
    )
    
    plt.figure()
    
    
    for K_local in K_local_values:
    
        subset = df_sensitivity[
            df_sensitivity["K_local"]
            ==
            K_local
        ]
    
    
        plt.plot(
    
            subset["diameter_mm"],
    
            subset[
                "maldistribution_percent"
            ],
    
            marker="o",
    
            label=f"K_local = {K_local}",
        )
    
    
    plt.axhline(
        10.0,
        linestyle="--",
        label="10% design limit",
    )
    
    
    plt.xlabel(
        "Header internal diameter (mm)"
    )
    
    plt.ylabel(
        "Flow maldistribution (%)"
    )
    
    plt.title(
        "Effect of Header Diameter and Local Loss "
        "on Flow Distribution"
    )
    
    plt.grid(True)
    
    plt.legend()
    
    plt.show()
    
    
    
    plt.figure()
    
    
    for K_local in K_local_values:
    
        subset = df_sensitivity[
            df_sensitivity["K_local"]
            ==
            K_local
        ]
    
    
        plt.plot(
    
            subset["diameter_mm"],
    
            subset[
                "header_pressure_variation_Pa"
            ],
    
            marker="o",
    
            label=f"K_local = {K_local}",
        )
    
    
    plt.xlabel(
        "Header internal diameter (mm)"
    )
    
    plt.ylabel(
        "First-to-last branch pressure variation (Pa)"
    )
    
    plt.title(
        "Header Diameter and Local-Loss Effect "
        "on Pressure Variation"
    )
    
    plt.grid(True)
    
    plt.legend()
    
    plt.show()
