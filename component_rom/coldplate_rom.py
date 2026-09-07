"""Reduced-order model (ROM) for the Project 2 liquid cold plate.

The hydraulic and thermal correlations in this module were fitted to COMSOL
calibration data over 0.50--1.20 L/min and 450--750 W.  They are intended for
interpolation within those ranges.  Extrapolation raises an error by default;
callers must explicitly select ``extrapolation="warn"`` to proceed outside a
validated range.

All calculations use SI units except where a function name explicitly states
``_lmin``, ``_kpa``, or ``_c``.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Literal
import warnings


HYDRAULIC_LINEAR_COEFFICIENT = 6.275834320181083
HYDRAULIC_QUADRATIC_COEFFICIENT = 3.0569321326501875
THERMAL_COEFFICIENT_K_PER_W = 0.027023939579912205
THERMAL_EXPONENT = -0.38230560298064653

MIN_CALIBRATED_FLOW_LMIN = 0.50
MAX_CALIBRATED_FLOW_LMIN = 1.20
MIN_VALIDATED_HEAT_LOAD_W = 450.0
MAX_VALIDATED_HEAT_LOAD_W = 750.0

DEFAULT_DENSITY_KG_M3 = 997.0
DEFAULT_CP_J_KGK = 4180.0

# Generic nominal assumptions for example-level device temperature estimates.
# These are not coefficients from the validated cold-plate ROM.
NOMINAL_TIM_RESISTANCE_K_PER_W = 0.005
NOMINAL_PACKAGE_RESISTANCE_K_PER_W = 0.020

ExtrapolationPolicy = Literal["error", "warn"]


class ROMExtrapolationError(ValueError):
    """Raised when an input is outside a validated ROM range."""


class ROMExtrapolationWarning(UserWarning):
    """Warns that a ROM result is outside its validated range."""


@dataclass(frozen=True, slots=True)
class ColdPlateResult:
    """Calculated performance of one cold plate at one operating point.

    ``device_temperature_c`` is ``None`` unless both TIM and package thermal
    resistances were supplied to :func:`evaluate_coldplate`.
    """

    flow_lmin: float
    heat_load_w: float
    pressure_drop_kpa: float
    pumping_power_w: float
    mass_flow_kg_s: float
    coolant_temperature_rise_c: float
    outlet_temperature_c: float
    mean_bulk_temperature_c: float
    thermal_resistance_k_per_w: float
    maximum_base_temperature_c: float
    device_temperature_c: float | None


def _finite_float(name: str, value: float) -> float:
    """Return *value* as a finite float, or raise a clear input error."""
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a real number, not bool")
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must be a real number") from exc
    if not isfinite(numeric_value):
        raise ValueError(f"{name} must be finite")
    return numeric_value


def _positive_float(name: str, value: float) -> float:
    """Return *value* as a finite, strictly positive float."""
    numeric_value = _finite_float(name, value)
    if numeric_value <= 0.0:
        raise ValueError(f"{name} must be positive")
    return numeric_value


def _nonnegative_float(name: str, value: float) -> float:
    """Return *value* as a finite, nonnegative float."""
    numeric_value = _finite_float(name, value)
    if numeric_value < 0.0:
        raise ValueError(f"{name} must be nonnegative")
    return numeric_value


def _check_range(
    *,
    name: str,
    value: float,
    lower: float,
    upper: float,
    unit: str,
    extrapolation: ExtrapolationPolicy,
) -> None:
    """Enforce or warn about a validated input range."""
    if extrapolation not in ("error", "warn"):
        raise ValueError('extrapolation must be either "error" or "warn"')
    if lower <= value <= upper:
        return

    message = (
        f"{name}={value:g} {unit} is outside the validated range "
        f"[{lower:g}, {upper:g}] {unit}; the ROM result is an extrapolation"
    )
    if extrapolation == "error":
        raise ROMExtrapolationError(message)
    warnings.warn(message, ROMExtrapolationWarning, stacklevel=3)


def _validate_flow(
    flow_lmin: float,
    extrapolation: ExtrapolationPolicy,
) -> float:
    """Validate flow positivity and the hydraulic/thermal calibration range."""
    flow = _positive_float("flow_lmin", flow_lmin)
    _check_range(
        name="flow_lmin",
        value=flow,
        lower=MIN_CALIBRATED_FLOW_LMIN,
        upper=MAX_CALIBRATED_FLOW_LMIN,
        unit="L/min",
        extrapolation=extrapolation,
    )
    return flow


def _validate_heat_load(
    heat_load_w: float,
    extrapolation: ExtrapolationPolicy,
) -> float:
    """Validate heat-load positivity and the thermal validation range."""
    heat_load = _positive_float("heat_load_w", heat_load_w)
    _check_range(
        name="heat_load_w",
        value=heat_load,
        lower=MIN_VALIDATED_HEAT_LOAD_W,
        upper=MAX_VALIDATED_HEAT_LOAD_W,
        unit="W",
        extrapolation=extrapolation,
    )
    return heat_load


def _pressure_drop_unchecked_kpa(flow_lmin: float) -> float:
    """Evaluate the hydraulic fit after its inputs have been validated."""
    q = flow_lmin / 1.0  # Dimensionless: flow normalized by 1 L/min.
    return (
        HYDRAULIC_LINEAR_COEFFICIENT * q
        + HYDRAULIC_QUADRATIC_COEFFICIENT * q**2
    )


def _thermal_resistance_unchecked_k_per_w(flow_lmin: float) -> float:
    """Evaluate the thermal fit after its inputs have been validated."""
    q = flow_lmin / 1.0  # Dimensionless: flow normalized by 1 L/min.
    return THERMAL_COEFFICIENT_K_PER_W * q**THERMAL_EXPONENT


def pressure_drop_kpa(
    flow_lmin: float,
    *,
    extrapolation: ExtrapolationPolicy = "error",
) -> float:
    """Return cold-plate pressure drop in kPa.

    The validated hydraulic ROM is

        delta_p [kPa] = 6.2758343202 q + 3.0569321327 q**2,

    where ``q = flow_lmin / (1 L/min)`` is dimensionless.

    Args:
        flow_lmin: Volumetric flow through one cold plate in L/min.
        extrapolation: ``"error"`` (default) rejects flow outside
            0.50--1.20 L/min. ``"warn"`` evaluates it and emits
            :class:`ROMExtrapolationWarning`.
    """
    flow = _validate_flow(flow_lmin, extrapolation)
    return _pressure_drop_unchecked_kpa(flow)


def thermal_resistance_k_per_w(
    flow_lmin: float,
    *,
    extrapolation: ExtrapolationPolicy = "error",
) -> float:
    """Return maximum-base thermal resistance in K/W.

    The validated thermal ROM is

        R_th [K/W] = 0.02702393958 q**(-0.3823056030),

    where ``q = flow_lmin / (1 L/min)`` is dimensionless.

    The resistance is used with mean bulk coolant temperature as its reference.
    """
    flow = _validate_flow(flow_lmin, extrapolation)
    return _thermal_resistance_unchecked_k_per_w(flow)


def outlet_temperature_c(
    inlet_temperature_c: float,
    heat_load_w: float,
    flow_lmin: float,
    *,
    density_kg_m3: float = DEFAULT_DENSITY_KG_M3,
    cp_j_kgk: float = DEFAULT_CP_J_KGK,
    extrapolation: ExtrapolationPolicy = "error",
) -> float:
    """Return coolant outlet temperature in degrees Celsius.

    The calculation applies ``Q = mass_flow * cp * delta_T`` with
    ``mass_flow = density * volume_flow``.  Constant coolant properties and no
    external heat loss are assumed.
    """
    inlet = _finite_float("inlet_temperature_c", inlet_temperature_c)
    heat_load = _validate_heat_load(heat_load_w, extrapolation)
    flow = _validate_flow(flow_lmin, extrapolation)
    density = _positive_float("density_kg_m3", density_kg_m3)
    cp = _positive_float("cp_j_kgk", cp_j_kgk)

    volume_flow_m3_s = flow / 60_000.0
    mass_flow_kg_s = density * volume_flow_m3_s
    coolant_rise_c = heat_load / (mass_flow_kg_s * cp)
    return inlet + coolant_rise_c


def mean_bulk_temperature_c(
    inlet_temperature_c: float,
    heat_load_w: float,
    flow_lmin: float,
    *,
    density_kg_m3: float = DEFAULT_DENSITY_KG_M3,
    cp_j_kgk: float = DEFAULT_CP_J_KGK,
    extrapolation: ExtrapolationPolicy = "error",
) -> float:
    """Return the arithmetic mean of coolant inlet and outlet temperatures."""
    inlet = _finite_float("inlet_temperature_c", inlet_temperature_c)
    outlet = outlet_temperature_c(
        inlet,
        heat_load_w,
        flow_lmin,
        density_kg_m3=density_kg_m3,
        cp_j_kgk=cp_j_kgk,
        extrapolation=extrapolation,
    )
    return 0.5 * (inlet + outlet)


def maximum_cold_plate_base_temperature_c(
    inlet_temperature_c: float,
    heat_load_w: float,
    flow_lmin: float,
    *,
    density_kg_m3: float = DEFAULT_DENSITY_KG_M3,
    cp_j_kgk: float = DEFAULT_CP_J_KGK,
    extrapolation: ExtrapolationPolicy = "error",
) -> float:
    """Return estimated maximum cold-plate base temperature in degC.

    ``T_base,max = T_bulk,mean + heat_load * R_th(flow)``.
    """
    inlet = _finite_float("inlet_temperature_c", inlet_temperature_c)
    heat_load = _validate_heat_load(heat_load_w, extrapolation)
    flow = _validate_flow(flow_lmin, extrapolation)
    density = _positive_float("density_kg_m3", density_kg_m3)
    cp = _positive_float("cp_j_kgk", cp_j_kgk)

    mass_flow_kg_s = density * flow / 60_000.0
    coolant_rise_c = heat_load / (mass_flow_kg_s * cp)
    bulk_mean = inlet + 0.5 * coolant_rise_c
    rth = _thermal_resistance_unchecked_k_per_w(flow)
    return bulk_mean + heat_load * rth


def hydraulic_pumping_power_w(
    flow_lmin: float,
    *,
    extrapolation: ExtrapolationPolicy = "error",
) -> float:
    """Return ideal hydraulic pumping power in W for one cold plate.

    This is fluid power, ``pressure_drop * volume_flow``.  Electrical pump
    input power would be higher and requires a pump-efficiency model.
    """
    flow = _validate_flow(flow_lmin, extrapolation)
    pressure_drop = _pressure_drop_unchecked_kpa(flow)
    return pressure_drop * flow / 60.0  # kPa * L/min converted to W.


def device_temperature_c(
    maximum_base_temperature_c: float,
    heat_load_w: float,
    tim_resistance_k_per_w: float,
    package_resistance_k_per_w: float,
    *,
    extrapolation: ExtrapolationPolicy = "error",
) -> float:
    """Return an optional device-temperature estimate in degC.

    ``T_device = T_base,max + heat_load * (R_TIM + R_package)``.

    Both resistances must be nonnegative and must describe the same heat path
    and thermal-resistance basis as ``heat_load_w``.
    """
    base_temperature = _finite_float(
        "maximum_base_temperature_c", maximum_base_temperature_c
    )
    heat_load = _validate_heat_load(heat_load_w, extrapolation)
    tim_rth = _nonnegative_float(
        "tim_resistance_k_per_w", tim_resistance_k_per_w
    )
    package_rth = _nonnegative_float(
        "package_resistance_k_per_w", package_resistance_k_per_w
    )
    return base_temperature + heat_load * (tim_rth + package_rth)


def evaluate_coldplate(
    *,
    flow_lmin: float,
    heat_load_w: float,
    inlet_temperature_c: float,
    density_kg_m3: float = DEFAULT_DENSITY_KG_M3,
    cp_j_kgk: float = DEFAULT_CP_J_KGK,
    tim_resistance_k_per_w: float | None = None,
    package_resistance_k_per_w: float | None = None,
    extrapolation: ExtrapolationPolicy = "error",
) -> ColdPlateResult:
    """Evaluate the complete cold-plate ROM at one operating point.

    Supply both ``tim_resistance_k_per_w`` and
    ``package_resistance_k_per_w`` to include a device-temperature estimate;
    omit both to leave that result as ``None``.  Providing only one is an
    input error so that a missing thermal resistance is never silently treated
    as zero.
    """
    flow = _validate_flow(flow_lmin, extrapolation)
    heat_load = _validate_heat_load(heat_load_w, extrapolation)
    inlet = _finite_float("inlet_temperature_c", inlet_temperature_c)
    density = _positive_float("density_kg_m3", density_kg_m3)
    cp = _positive_float("cp_j_kgk", cp_j_kgk)

    if (tim_resistance_k_per_w is None) != (
        package_resistance_k_per_w is None
    ):
        raise ValueError(
            "provide both tim_resistance_k_per_w and "
            "package_resistance_k_per_w, or omit both"
        )

    volume_flow_m3_s = flow / 60_000.0
    mass_flow_kg_s = density * volume_flow_m3_s
    coolant_rise_c = heat_load / (mass_flow_kg_s * cp)
    outlet_c = inlet + coolant_rise_c
    mean_bulk_c = 0.5 * (inlet + outlet_c)

    pressure_drop = _pressure_drop_unchecked_kpa(flow)
    pumping_power = pressure_drop * volume_flow_m3_s * 1_000.0
    rth = _thermal_resistance_unchecked_k_per_w(flow)
    maximum_base_c = mean_bulk_c + heat_load * rth

    estimated_device_c: float | None = None
    if tim_resistance_k_per_w is not None:
        tim_rth = _nonnegative_float(
            "tim_resistance_k_per_w", tim_resistance_k_per_w
        )
        package_rth = _nonnegative_float(
            "package_resistance_k_per_w", package_resistance_k_per_w
        )
        estimated_device_c = maximum_base_c + heat_load * (
            tim_rth + package_rth
        )

    return ColdPlateResult(
        flow_lmin=flow,
        heat_load_w=heat_load,
        pressure_drop_kpa=pressure_drop,
        pumping_power_w=pumping_power,
        mass_flow_kg_s=mass_flow_kg_s,
        coolant_temperature_rise_c=coolant_rise_c,
        outlet_temperature_c=outlet_c,
        mean_bulk_temperature_c=mean_bulk_c,
        thermal_resistance_k_per_w=rth,
        maximum_base_temperature_c=maximum_base_c,
        device_temperature_c=estimated_device_c,
    )


def _main() -> None:
    """Run a small in-range example when this module is executed directly."""
    result = evaluate_coldplate(
        flow_lmin=1.15,
        heat_load_w=750.0,
        inlet_temperature_c=30.0,
        tim_resistance_k_per_w=NOMINAL_TIM_RESISTANCE_K_PER_W,
        package_resistance_k_per_w=NOMINAL_PACKAGE_RESISTANCE_K_PER_W,
    )

    print("Project 2 cold-plate ROM example")
    print(f"Pressure drop:             {result.pressure_drop_kpa:.3f} kPa")
    print(f"Hydraulic pumping power:  {result.pumping_power_w:.3f} W")
    print(f"Coolant outlet:           {result.outlet_temperature_c:.2f} degC")
    print(f"Mean bulk temperature:    {result.mean_bulk_temperature_c:.2f} degC")
    print(f"Maximum base temperature: {result.maximum_base_temperature_c:.2f} degC")
    print(f"Estimated device temp:    {result.device_temperature_c:.2f} degC")


if __name__ == "__main__":
    _main()
