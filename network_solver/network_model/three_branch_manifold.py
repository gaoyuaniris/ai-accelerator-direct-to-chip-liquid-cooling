import numpy as np
from scipy.optimize import root


# ============================================================
# 1. Cold-plate hydraulic ROM
#
# Delta-p_cp [kPa] = A*q + B*q^2
#
# q is numerically in L/min.
# ============================================================

A_CP = 6.2644745879
B_CP = 3.0720638374


def coldplate_dp_kpa(flow_lmin):
    """
    Pressure drop through one cold plate.

    Parameters
    ----------
    flow_lmin : float
        Cold-plate flow rate in L/min.

    Returns
    -------
    float
        Pressure drop in kPa.
    """

    return (
        A_CP * flow_lmin
        +
        B_CP * flow_lmin**2
    )


# ============================================================
# 2. Churchill Darcy friction-factor correlation
#
# Continuous through laminar, transitional,
# and turbulent regimes.
# ============================================================

def darcy_friction_factor(
    reynolds,
    relative_roughness=0.0,
):
    """
    Calculate Darcy friction factor using
    the Churchill correlation.
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
# 3. Physical manifold-segment model
#
# Delta-p =
#
# [ f*(L/D) + K_local ] * rho*U^2/2
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
        Segment pressure loss, kPa.

    velocity_m_s
        Mean fluid velocity, m/s.

    reynolds
        Reynolds number.

    friction_factor
        Darcy friction factor.
    """

    # --------------------------------------------------------
    # Convert L/min -> m^3/s
    # --------------------------------------------------------

    flow_m3_s = (
        flow_lmin
        * 1.0e-3
        / 60.0
    )


    # --------------------------------------------------------
    # Circular cross-sectional area
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
    # Straight-pipe friction loss
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


    dp_total_kpa = (
        dp_total_pa
        /
        1000.0
    )


    return (
        dp_total_kpa,
        velocity_m_s,
        reynolds,
        friction_factor,
    )


# ============================================================
# 4. Three-branch physical manifold solver
# ============================================================

def solve_three_branch_manifold(
    q_total_lmin,
    supply_diameter_m,
    return_diameter_m,
    segment_length_m,
    density_kg_m3=996.0,
    viscosity_pa_s=8.0e-4,
    supply_K_local=0.0,
    return_K_local=0.0,
):
    """
    Solve three identical cold plates connected to
    same-side supply and return manifolds.

    Geometry:

              Supply →

        S1 ----- S2 ----- S3
        |        |        |
       CP1      CP2      CP3
        |        |        |
        R1 ----- R2 ----- R3

              ← Return

    Unknowns:
        q1, q2, q3
    """

    # ========================================================
    # Nonlinear equations
    # ========================================================

    def equations(x):

        q1, q2, q3 = x


        # ----------------------------------------------------
        # Equation 1:
        # Mass conservation
        #
        # q1 + q2 + q3 = q_total
        # ----------------------------------------------------

        mass_residual = (
            q1
            +
            q2
            +
            q3
            -
            q_total_lmin
        )


        # ----------------------------------------------------
        # Cold-plate pressure drops
        # ----------------------------------------------------

        dp_cp1 = coldplate_dp_kpa(q1)

        dp_cp2 = coldplate_dp_kpa(q2)

        dp_cp3 = coldplate_dp_kpa(q3)


        # ----------------------------------------------------
        # Supply manifold segment flows
        #
        # S1 -> S2 carries q2 + q3
        #
        # S2 -> S3 carries q3
        # ----------------------------------------------------

        q_s12 = (
            q2
            +
            q3
        )

        q_s23 = q3


        # ----------------------------------------------------
        # Return manifold segment flows
        #
        # R3 -> R2 carries q3
        #
        # R2 -> R1 carries q2 + q3
        # ----------------------------------------------------

        q_r32 = q3

        q_r21 = (
            q2
            +
            q3
        )


        # ----------------------------------------------------
        # Supply segment pressure losses
        # ----------------------------------------------------

        dp_s12, _, _, _ = (
            manifold_segment_dp_kpa(
                flow_lmin=q_s12,
                diameter_m=supply_diameter_m,
                length_m=segment_length_m,
                density_kg_m3=density_kg_m3,
                viscosity_pa_s=viscosity_pa_s,
                K_local=supply_K_local,
            )
        )


        dp_s23, _, _, _ = (
            manifold_segment_dp_kpa(
                flow_lmin=q_s23,
                diameter_m=supply_diameter_m,
                length_m=segment_length_m,
                density_kg_m3=density_kg_m3,
                viscosity_pa_s=viscosity_pa_s,
                K_local=supply_K_local,
            )
        )


        # ----------------------------------------------------
        # Return segment pressure losses
        # ----------------------------------------------------

        dp_r32, _, _, _ = (
            manifold_segment_dp_kpa(
                flow_lmin=q_r32,
                diameter_m=return_diameter_m,
                length_m=segment_length_m,
                density_kg_m3=density_kg_m3,
                viscosity_pa_s=viscosity_pa_s,
                K_local=return_K_local,
            )
        )


        dp_r21, _, _, _ = (
            manifold_segment_dp_kpa(
                flow_lmin=q_r21,
                diameter_m=return_diameter_m,
                length_m=segment_length_m,
                density_kg_m3=density_kg_m3,
                viscosity_pa_s=viscosity_pa_s,
                K_local=return_K_local,
            )
        )


        # ----------------------------------------------------
        # Equation 2:
        #
        # CP1 vs CP2 compatibility
        #
        # dp_cp1 - dp_cp2
        #
        # must equal the extra manifold losses
        # experienced by CP2:
        #
        # S1 -> S2
        # +
        # R2 -> R1
        # ----------------------------------------------------

        pressure_residual_12 = (
            dp_cp1
            -
            dp_cp2
            -
            dp_s12
            -
            dp_r21
        )


        # ----------------------------------------------------
        # Equation 3:
        #
        # CP2 vs CP3 compatibility
        #
        # dp_cp2 - dp_cp3
        #
        # equals the additional manifold losses
        # between branch 2 and branch 3:
        #
        # S2 -> S3
        # +
        # R3 -> R2
        # ----------------------------------------------------

        pressure_residual_23 = (
            dp_cp2
            -
            dp_cp3
            -
            dp_s23
            -
            dp_r32
        )


        return [
            mass_residual,
            pressure_residual_12,
            pressure_residual_23,
        ]


    # ========================================================
    # Initial guess
    #
    # Equal-flow condition is a physically reasonable
    # starting point.
    # ========================================================

    initial_guess = [
        q_total_lmin / 3.0,
        q_total_lmin / 3.0,
        q_total_lmin / 3.0,
    ]


    # ========================================================
    # Solve nonlinear system
    # ========================================================

    solution = root(
        equations,
        initial_guess,
    )


    if not solution.success:

        raise RuntimeError(
            f"Solver failed: "
            f"{solution.message}"
        )


    q1, q2, q3 = solution.x


    # ========================================================
    # 5. Recalculate final pressure-drop results
    # ========================================================

    dp_cp1 = coldplate_dp_kpa(q1)

    dp_cp2 = coldplate_dp_kpa(q2)

    dp_cp3 = coldplate_dp_kpa(q3)


    # Manifold segment flows
    q_s12 = q2 + q3
    q_s23 = q3

    q_r32 = q3
    q_r21 = q2 + q3


    # --------------------------------------------------------
    # Supply segments
    # --------------------------------------------------------

    (
        dp_s12,
        U_s12,
        Re_s12,
        f_s12,
    ) = manifold_segment_dp_kpa(
        flow_lmin=q_s12,
        diameter_m=supply_diameter_m,
        length_m=segment_length_m,
        density_kg_m3=density_kg_m3,
        viscosity_pa_s=viscosity_pa_s,
        K_local=supply_K_local,
    )


    (
        dp_s23,
        U_s23,
        Re_s23,
        f_s23,
    ) = manifold_segment_dp_kpa(
        flow_lmin=q_s23,
        diameter_m=supply_diameter_m,
        length_m=segment_length_m,
        density_kg_m3=density_kg_m3,
        viscosity_pa_s=viscosity_pa_s,
        K_local=supply_K_local,
    )


    # --------------------------------------------------------
    # Return segments
    # --------------------------------------------------------

    (
        dp_r32,
        U_r32,
        Re_r32,
        f_r32,
    ) = manifold_segment_dp_kpa(
        flow_lmin=q_r32,
        diameter_m=return_diameter_m,
        length_m=segment_length_m,
        density_kg_m3=density_kg_m3,
        viscosity_pa_s=viscosity_pa_s,
        K_local=return_K_local,
    )


    (
        dp_r21,
        U_r21,
        Re_r21,
        f_r21,
    ) = manifold_segment_dp_kpa(
        flow_lmin=q_r21,
        diameter_m=return_diameter_m,
        length_m=segment_length_m,
        density_kg_m3=density_kg_m3,
        viscosity_pa_s=viscosity_pa_s,
        K_local=return_K_local,
    )


    # ========================================================
    # 6. Flow-maldistribution metric
    # ========================================================

    flows = np.array([
        q1,
        q2,
        q3,
    ])


    q_mean = np.mean(flows)


    maldistribution_percent = (
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


    # ========================================================
    # 7. Node pressures
    #
    # Set p_R1 = 0 kPa as reference.
    # ========================================================

    p_R1 = 0.0


    # CP1
    p_S1 = (
        p_R1
        +
        dp_cp1
    )


    # Supply manifold
    p_S2 = (
        p_S1
        -
        dp_s12
    )

    p_S3 = (
        p_S2
        -
        dp_s23
    )


    # Return manifold
    p_R2 = (
        p_R1
        +
        dp_r21
    )

    p_R3 = (
        p_R2
        +
        dp_r32
    )


    # ========================================================
    # 8. Residual checks
    # ========================================================

    mass_residual = (
        q1
        +
        q2
        +
        q3
        -
        q_total_lmin
    )


    pressure_residual_12 = (
        dp_cp1
        -
        dp_cp2
        -
        dp_s12
        -
        dp_r21
    )


    pressure_residual_23 = (
        dp_cp2
        -
        dp_cp3
        -
        dp_s23
        -
        dp_r32
    )


    # ========================================================
    # 9. Return results
    # ========================================================

    return {

        # Branch flows
        "q1_Lmin": q1,
        "q2_Lmin": q2,
        "q3_Lmin": q3,

        # Cold plates
        "dp_cp1_kPa": dp_cp1,
        "dp_cp2_kPa": dp_cp2,
        "dp_cp3_kPa": dp_cp3,

        # Manifold segment flows
        "q_s12_Lmin": q_s12,
        "q_s23_Lmin": q_s23,
        "q_r32_Lmin": q_r32,
        "q_r21_Lmin": q_r21,

        # Supply losses
        "dp_s12_kPa": dp_s12,
        "dp_s23_kPa": dp_s23,

        # Return losses
        "dp_r32_kPa": dp_r32,
        "dp_r21_kPa": dp_r21,

        # Supply velocities
        "U_s12_m_s": U_s12,
        "U_s23_m_s": U_s23,

        # Reynolds numbers
        "Re_s12": Re_s12,
        "Re_s23": Re_s23,

        # Node pressures
        "p_S1_kPa": p_S1,
        "p_S2_kPa": p_S2,
        "p_S3_kPa": p_S3,

        "p_R1_kPa": p_R1,
        "p_R2_kPa": p_R2,
        "p_R3_kPa": p_R3,

        # Overall metric
        "maldistribution_percent":
            maldistribution_percent,

        # Residuals
        "mass_residual":
            mass_residual,

        "pressure_residual_12":
            pressure_residual_12,

        "pressure_residual_23":
            pressure_residual_23,
    }


# ============================================================
# 10. Learning case
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Three branches at 0.8 L/min ideal average
    # --------------------------------------------------------

    Q_TOTAL_LMIN = 2.40

    # Approximate 3/8-inch ID
    MANIFOLD_DIAMETER_M = 0.0095

    # Distance between adjacent branch connections
    SEGMENT_LENGTH_M = 0.050


    results = solve_three_branch_manifold(

        q_total_lmin=Q_TOTAL_LMIN,

        supply_diameter_m=
            MANIFOLD_DIAMETER_M,

        return_diameter_m=
            MANIFOLD_DIAMETER_M,

        segment_length_m=
            SEGMENT_LENGTH_M,

        supply_K_local=0.0,

        return_K_local=0.0,
    )


    print(
        "\n"
        "========================================"
    )

    print(
        "THREE-BRANCH PHYSICAL MANIFOLD"
    )

    print(
        "========================================"
    )


    print(
        f"\nTotal flow = "
        f"{Q_TOTAL_LMIN:.3f} L/min"
    )


    # ========================================================
    # Branch flows
    # ========================================================

    print(
        "\nBranch flows:"
    )

    print(
        f"q1 = "
        f"{results['q1_Lmin']:.6f} L/min"
    )

    print(
        f"q2 = "
        f"{results['q2_Lmin']:.6f} L/min"
    )

    print(
        f"q3 = "
        f"{results['q3_Lmin']:.6f} L/min"
    )


    # ========================================================
    # Segment flows
    # ========================================================

    print(
        "\nSupply manifold segment flows:"
    )

    print(
        f"S1 -> S2 = "
        f"{results['q_s12_Lmin']:.6f} L/min"
    )

    print(
        f"S2 -> S3 = "
        f"{results['q_s23_Lmin']:.6f} L/min"
    )


    print(
        "\nReturn manifold segment flows:"
    )

    print(
        f"R3 -> R2 = "
        f"{results['q_r32_Lmin']:.6f} L/min"
    )

    print(
        f"R2 -> R1 = "
        f"{results['q_r21_Lmin']:.6f} L/min"
    )


    # ========================================================
    # Pressure losses
    # ========================================================

    print(
        "\nSupply manifold losses:"
    )

    print(
        f"S1 -> S2 = "
        f"{results['dp_s12_kPa'] * 1000:.3f} Pa"
    )

    print(
        f"S2 -> S3 = "
        f"{results['dp_s23_kPa'] * 1000:.3f} Pa"
    )


    print(
        "\nReturn manifold losses:"
    )

    print(
        f"R3 -> R2 = "
        f"{results['dp_r32_kPa'] * 1000:.3f} Pa"
    )

    print(
        f"R2 -> R1 = "
        f"{results['dp_r21_kPa'] * 1000:.3f} Pa"
    )


    # ========================================================
    # Cold-plate pressure drops
    # ========================================================

    print(
        "\nCold-plate pressure drops:"
    )

    print(
        f"CP1 = "
        f"{results['dp_cp1_kPa']:.6f} kPa"
    )

    print(
        f"CP2 = "
        f"{results['dp_cp2_kPa']:.6f} kPa"
    )

    print(
        f"CP3 = "
        f"{results['dp_cp3_kPa']:.6f} kPa"
    )


    # ========================================================
    # Supply velocity / Reynolds number
    # ========================================================

    print(
        "\nSupply segment S1 -> S2:"
    )

    print(
        f"Velocity = "
        f"{results['U_s12_m_s']:.4f} m/s"
    )

    print(
        f"Re = "
        f"{results['Re_s12']:.1f}"
    )


    print(
        "\nSupply segment S2 -> S3:"
    )

    print(
        f"Velocity = "
        f"{results['U_s23_m_s']:.4f} m/s"
    )

    print(
        f"Re = "
        f"{results['Re_s23']:.1f}"
    )


    # ========================================================
    # Node pressures
    # ========================================================

    print(
        "\nNode pressures "
        "(relative to p_R1 = 0):"
    )

    print(
        f"p_S1 = "
        f"{results['p_S1_kPa']:.6f} kPa"
    )

    print(
        f"p_S2 = "
        f"{results['p_S2_kPa']:.6f} kPa"
    )

    print(
        f"p_S3 = "
        f"{results['p_S3_kPa']:.6f} kPa"
    )

    print(
        f"p_R1 = "
        f"{results['p_R1_kPa']:.6f} kPa"
    )

    print(
        f"p_R2 = "
        f"{results['p_R2_kPa']:.6f} kPa"
    )

    print(
        f"p_R3 = "
        f"{results['p_R3_kPa']:.6f} kPa"
    )


    # ========================================================
    # Maldistribution
    # ========================================================

    print(
        f"\nFlow maldistribution = "
        f"{results['maldistribution_percent']:.4f}%"
    )


    # ========================================================
    # Residual checks
    # ========================================================

    print(
        "\nSolver residuals:"
    )

    print(
        f"Mass residual = "
        f"{results['mass_residual']:.3e}"
    )

    print(
        f"Pressure residual 1-2 = "
        f"{results['pressure_residual_12']:.3e}"
    )

    print(
        f"Pressure residual 2-3 = "
        f"{results['pressure_residual_23']:.3e}"
    )