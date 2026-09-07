import numpy as np
from scipy.optimize import root

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def darcy_friction_factor(
    reynolds,
    relative_roughness=0.0,
):

    if reynolds <= 0:
        raise ValueError(
            "Reynolds number must be positive."
        )

    A = (
        2.457
        * np.log(
            1.0
            /
            (
                (7.0 / reynolds) ** 0.9
                +
                0.27 * relative_roughness
            )
        )
    ) ** 16

    B = (
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
            (A + B) ** 1.5
        )
        ** (1.0 / 12.0)
    )

    return friction_factor


# ============================================================
# Physical manifold segment model
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

    # L/min -> m^3/s
    flow_m3_s = (
        flow_lmin
        * 1.0e-3
        / 60.0
    )

    # Pipe area
    area_m2 = (
        np.pi
        * diameter_m**2
        / 4.0
    )

    # Mean velocity
    velocity_m_s = (
        flow_m3_s
        /
        area_m2
    )

    # Reynolds number
    reynolds = (
        density_kg_m3
        *
        velocity_m_s
        *
        diameter_m
        /
        viscosity_pa_s
    )

    # Relative roughness
    relative_roughness = (
        roughness_m
        /
        diameter_m
    )

    # Darcy friction factor
    friction_factor = (
        darcy_friction_factor(
            reynolds,
            relative_roughness,
        )
    )

    # Dynamic pressure
    dynamic_pressure_pa = (
        0.5
        *
        density_kg_m3
        *
        velocity_m_s**2
    )

    # Distributed friction
    dp_friction_pa = (
        friction_factor
        *
        length_m
        /
        diameter_m
        *
        dynamic_pressure_pa
    )

    # Local losses
    dp_local_pa = (
        K_local
        *
        dynamic_pressure_pa
    )

    # Total
    dp_total_kpa = (
        dp_friction_pa
        +
        dp_local_pa
    ) / 1000.0

    return (
        dp_total_kpa,
        velocity_m_s,
        reynolds,
        friction_factor,
    )

def solve_two_branch_physical_manifold(
    q_total_lmin,
    supply_diameter_m,
    return_diameter_m,
    supply_length_m,
    return_length_m,
    density_kg_m3=996.0,
    viscosity_pa_s=8.0e-4,
    supply_K_local=0.0,
    return_K_local=0.0,
):

    def equations(x):

        q1, q2 = x

        # ==========================================
        # Equation 1: mass conservation
        # ==========================================

        mass_residual = (
            q1
            +
            q2
            -
            q_total_lmin
        )


        # ==========================================
        # Cold-plate pressure drops
        # ==========================================

        dp_cp1 = coldplate_dp_kpa(q1)

        dp_cp2 = coldplate_dp_kpa(q2)


        # ==========================================
        # Supply manifold segment
        #
        # S1 -> S2 carries only q2
        # ==========================================

        dp_supply, _, _, _ = (
            manifold_segment_dp_kpa(
                flow_lmin=q2,
                diameter_m=supply_diameter_m,
                length_m=supply_length_m,
                density_kg_m3=density_kg_m3,
                viscosity_pa_s=viscosity_pa_s,
                K_local=supply_K_local,
            )
        )


        # ==========================================
        # Return manifold segment
        #
        # R2 -> R1 also carries only q2
        # ==========================================

        dp_return, _, _, _ = (
            manifold_segment_dp_kpa(
                flow_lmin=q2,
                diameter_m=return_diameter_m,
                length_m=return_length_m,
                density_kg_m3=density_kg_m3,
                viscosity_pa_s=viscosity_pa_s,
                K_local=return_K_local,
            )
        )


        # ==========================================
        # Equation 2: pressure compatibility
        # ==========================================

        pressure_residual = (
            dp_cp1
            -
            dp_cp2
            -
            dp_supply
            -
            dp_return
        )


        return [
            mass_residual,
            pressure_residual,
        ]


    # Equal-flow starting guess
    initial_guess = [
        q_total_lmin / 2.0,
        q_total_lmin / 2.0,
    ]


    solution = root(
        equations,
        initial_guess,
    )


    if not solution.success:

        raise RuntimeError(
            solution.message
        )


    q1, q2 = solution.x


    # ==============================================
    # Recalculate final component results
    # ==============================================

    dp_cp1 = coldplate_dp_kpa(q1)

    dp_cp2 = coldplate_dp_kpa(q2)


    (
        dp_supply,
        U_supply,
        Re_supply,
        f_supply,
    ) = manifold_segment_dp_kpa(
        flow_lmin=q2,
        diameter_m=supply_diameter_m,
        length_m=supply_length_m,
        density_kg_m3=density_kg_m3,
        viscosity_pa_s=viscosity_pa_s,
        K_local=supply_K_local,
    )


    (
        dp_return,
        U_return,
        Re_return,
        f_return,
    ) = manifold_segment_dp_kpa(
        flow_lmin=q2,
        diameter_m=return_diameter_m,
        length_m=return_length_m,
        density_kg_m3=density_kg_m3,
        viscosity_pa_s=viscosity_pa_s,
        K_local=return_K_local,
    )


    # ==============================================
    # Maldistribution
    # ==============================================

    q_mean = (
        q1 + q2
    ) / 2.0


    maldistribution = (
        abs(q1 - q2)
        /
        q_mean
        *
        100.0
    )


    # ==============================================
    # Node pressures
    #
    # Choose p_R1 = 0
    # ==============================================

    p_R1 = 0.0

    p_S1 = (
        p_R1
        +
        dp_cp1
    )

    p_S2 = (
        p_S1
        -
        dp_supply
    )

    p_R2 = (
        p_R1
        +
        dp_return
    )


    return {

        "q1_Lmin":
            q1,

        "q2_Lmin":
            q2,

        "dp_cp1_kPa":
            dp_cp1,

        "dp_cp2_kPa":
            dp_cp2,

        "dp_supply_kPa":
            dp_supply,

        "dp_return_kPa":
            dp_return,

        "U_supply_m_s":
            U_supply,

        "U_return_m_s":
            U_return,

        "Re_supply":
            Re_supply,

        "Re_return":
            Re_return,

        "f_supply":
            f_supply,

        "f_return":
            f_return,

        "p_S1_kPa":
            p_S1,

        "p_S2_kPa":
            p_S2,

        "p_R1_kPa":
            p_R1,

        "p_R2_kPa":
            p_R2,

        "maldistribution_percent":
            maldistribution,
    }






# ============================================================
# 1. Cold-plate hydraulic ROM
#
# Delta-p_cp = A*q + B*q^2
#
# q       : L/min
# Delta-p : kPa
# ============================================================

A = 6.2644745879
B = 3.0720638374


def coldplate_dp_kpa(q_lmin):
    """
    Cold-plate pressure drop.

    Parameters
    ----------
    q_lmin : float
        Cold-plate flow rate in L/min.

    Returns
    -------
    float
        Pressure drop in kPa.
    """

    return (
        A * q_lmin
        +
        B * q_lmin**2
    )

if __name__ == "__main__":

    results = (
        solve_two_branch_physical_manifold(
            q_total_lmin=1.60,

            supply_diameter_m=0.0095,
            return_diameter_m=0.0095,

            supply_length_m=0.050,
            return_length_m=0.050,

            supply_K_local=0.0,
            return_K_local=0.0,
        )
    )


    print(
        "\n========================================"
    )

    print(
        "PHYSICAL TWO-BRANCH MANIFOLD"
    )

    print(
        "========================================"
    )


    print(
        f"\nq1 = "
        f"{results['q1_Lmin']:.6f} L/min"
    )

    print(
        f"q2 = "
        f"{results['q2_Lmin']:.6f} L/min"
    )


    print(
        f"\nSupply segment loss = "
        f"{results['dp_supply_kPa'] * 1000:.3f} Pa"
    )

    print(
        f"Return segment loss = "
        f"{results['dp_return_kPa'] * 1000:.3f} Pa"
    )


    print(
        f"\nSupply velocity = "
        f"{results['U_supply_m_s']:.4f} m/s"
    )

    print(
        f"Supply Re = "
        f"{results['Re_supply']:.1f}"
    )

    print(
        f"Supply f = "
        f"{results['f_supply']:.5f}"
    )


    print(
        f"\nCP1 pressure drop = "
        f"{results['dp_cp1_kPa']:.6f} kPa"
    )

    print(
        f"CP2 pressure drop = "
        f"{results['dp_cp2_kPa']:.6f} kPa"
    )


    print(
        f"\nFlow maldistribution = "
        f"{results['maldistribution_percent']:.4f}%"
    )