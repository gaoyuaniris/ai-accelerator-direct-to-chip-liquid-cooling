import numpy as np
from scipy.optimize import root


A = 6.2644745879
B = 3.0720638374


def coldplate_dp_kpa(flow_lpm):
    """
    Cold-plate pressure drop from the validated hydraulic ROM.

    Parameters
    ----------
    flow_lpm : float
        Branch volumetric flow rate in L/min.

    Returns
    -------
    float
        Pressure drop in kPa.
    """

    return A * flow_lpm + B * flow_lpm**2


def solve_network(
    restriction_factor,
    q_total=1.80
):

    def equations(x):

        q_normal, q_restricted = x

        # Equation 1: mass conservation
        mass_residual = (
            2 * q_normal
            + q_restricted
            - q_total
        )

        # Normal branch pressure drop
        dp_normal = coldplate_dp_kpa(
            q_normal
        )

        # Restricted branch pressure drop
        dp_restricted = (
            restriction_factor
            * coldplate_dp_kpa(
                q_restricted
            )
        )

        # Equation 2: common pressure drop
        pressure_residual = (
            dp_normal
            - dp_restricted
        )

        return [
            mass_residual,
            pressure_residual
        ]

    initial_guess = [
        0.60,
        0.60
    ]

    solution = root(
        equations,
        initial_guess
    )

    solution.x

    if not solution.success:
        raise RuntimeError(
            solution.message
        )

    q_normal, q_restricted = solution.x

    dp_common = coldplate_dp_kpa(
        q_normal
    )

    print("\nSolved branch flows")

    print(
        f"Normal branch 1: "
        f"{q_normal:.4f} L/min"
    )

    print(
        f"Normal branch 2: "
        f"{q_normal:.4f} L/min"
    )

    print(
        f"Restricted branch: "
        f"{q_restricted:.4f} L/min"
    )

    print(
        f"Common pressure drop: "
        f"{dp_common:.4f} kPa"
    )

    q_check = (
        2 * q_normal
        + q_restricted
    )

    mass_error = (
        q_check - q_total
    )

    dp_normal = coldplate_dp_kpa(
        q_normal
    )

    dp_restricted = (
        restriction_factor
        * coldplate_dp_kpa(
            q_restricted
        )
    )

    pressure_error = (
        dp_normal
        - dp_restricted
    )

    print("\nVerification")

    print(
        f"Total reconstructed flow: "
        f"{q_check:.6f} L/min"
    )

    print(
        f"Mass residual: "
        f"{mass_error:.3e} L/min"
    )

    print(
        f"Normal branch dp: "
        f"{dp_normal:.6f} kPa"
    )

    print(
        f"Restricted branch dp: "
        f"{dp_restricted:.6f} kPa"
    )

    print(
        f"Pressure residual: "
        f"{pressure_error:.3e} kPa"
    )

    flows = np.array([
        q_normal,
        q_normal,
        q_restricted
    ])

    q_mean = np.mean(flows)
    q_max = np.max(flows)
    q_min = np.min(flows)

    maldistribution_percent = (
        (q_max - q_min)
        / q_mean
        * 100
    )

    print(
        f"Flow maldistribution: "
        f"{maldistribution_percent:.2f}%"
    )

    flows = np.array([
        q_normal,
        q_normal,
        q_restricted
    ])

    q_mean = np.mean(flows)
    q_max = np.max(flows)
    q_min = np.min(flows)

    maldistribution_percent = (
        (q_max - q_min)
        / q_mean
        * 100
    )

    print(
        f"Flow maldistribution: "
        f"{maldistribution_percent:.2f}%"
    )

    minimum_design_flow = 0.65

    if q_restricted < minimum_design_flow:
        print(
            "WARNING: Restricted branch "
            "is below the 750 W design "
            "minimum flow."
        )


