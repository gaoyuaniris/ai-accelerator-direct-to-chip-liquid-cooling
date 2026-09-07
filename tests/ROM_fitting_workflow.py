import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.optimize import curve_fit

flow = np.array([
    0.50,
    0.60,
    0.65,
    0.80,
    0.95,
    1.10,
    1.20,
])

pressure_drop = np.array([
    3.894,
    4.864,
    5.371,
    6.983,
    8.727,
    10.604,
    11.927,
])

rth = np.array([
    0.03512,
    0.03286,
    0.03192,
    0.02955,
    0.02765,
    0.02600,
    0.0250856,
])

plt.figure()

plt.scatter(flow, pressure_drop)

plt.xlabel("Flow rate (L/min)")
plt.ylabel("Pressure drop (kPa)")
plt.title("COMSOL Hydraulic Calibration Data")

plt.grid(True)

plt.show()

# pressure resistance vs flow rate (comsol)
plt.figure()

plt.scatter(flow, rth)

plt.xlabel("Flow rate (L/min)")
plt.ylabel("Maximum thermal resistance (K/W)")
plt.title("COMSOL Thermal Calibration Data")

plt.grid(True)

plt.show()

# define a function to fit the data
def hydraulic_rom(flow, a, b):
    return a * flow + b * flow**2

hydraulic_coefficients, hydraulic_covariance = curve_fit(
    hydraulic_rom,
    flow,
    pressure_drop
)

print(hydraulic_coefficients)

a, b = hydraulic_coefficients

print("a =", a)
print("b =", b)


# calculate the predicted pressure drop using the fitted model

pressure_predicted = hydraulic_rom(
    flow,
    a,
    b
)

print(pressure_predicted)

# calculate the residuals

pressure_residual = (
    pressure_predicted - pressure_drop
)


for q, actual, predicted, error in zip(
    flow,
    pressure_drop,
    pressure_predicted,
    pressure_residual
):
    print(
        q,
        actual,
        predicted,
        error
    )


# calcualte the fitting metrics

def calculate_metrics(actual, predicted):

    residual = predicted - actual

    mae = np.mean(
        np.abs(residual)
    )

    rmse = np.sqrt(
        np.mean(residual**2)
    )

    mape = np.mean(
        np.abs(residual / actual)
    ) * 100

    max_percent_error = np.max(
        np.abs(residual / actual)
    ) * 100

    ss_res = np.sum(
        (actual - predicted)**2
    )

    ss_tot = np.sum(
        (actual - np.mean(actual))**2
    )

    r2 = 1 - ss_res / ss_tot

    return {
        "MAE": mae,
        "RMSE": rmse,
        "MAPE_percent": mape,
        "Max_percent_error": max_percent_error,
        "R2": r2
    }

hydraulic_metrics = calculate_metrics(
    pressure_drop,
    pressure_predicted
)

print(hydraulic_metrics)

# plot the predicted vs actual pressure drop

flow_smooth = np.linspace(
    0.50,
    1.10,
    200
)

pressure_smooth = hydraulic_rom(
    flow_smooth,
    a,
    b
)

plt.figure()

plt.scatter(
    flow,
    pressure_drop,
    label="COMSOL"
)

plt.plot(
    flow_smooth,
    pressure_smooth,
    label="Hydraulic ROM"
)

plt.xlabel("Flow rate (L/min)")
plt.ylabel("Pressure drop (kPa)")
plt.title("Cold-Plate Hydraulic ROM")

plt.grid(True)
plt.legend()

plt.show()

# Fit the thermal ROM

# Fit thermal ROM
def thermal_rom(flow, C, m):
    return C * flow**(-m)


thermal_coefficients, thermal_covariance = curve_fit(
    thermal_rom,
    flow,
    rth,
    p0=[0.027, 0.38]
)

C, m = thermal_coefficients

print("Thermal C =", C)
print("Thermal m =", m)


# Predictions at calibration points
rth_predicted = thermal_rom(
    flow,
    C,
    m
)


# Smooth curve for plotting
flow_smooth = np.linspace(
    0.50,
    1.10,
    200
)

rth_smooth = thermal_rom(
    flow_smooth,
    C,
    m
)


plt.figure()

plt.scatter(
    flow,
    rth,
    label="COMSOL"
)

plt.plot(
    flow_smooth,
    rth_smooth,
    label="Thermal ROM"
)

plt.xlabel("Flow rate (L/min)")
plt.ylabel("Maximum thermal resistance (K/W)")
plt.title("Cold-Plate Thermal ROM")

plt.grid(True)
plt.legend()

plt.show()

# Calculate metrics for thermal ROM


thermal_metrics = calculate_metrics(
    rth,
    rth_predicted
)


print("\nThermal ROM metrics:")
print(thermal_metrics)


# plot residuals for hydrolic and thermal ROMs

hydraulic_residuals = (
    pressure_predicted - pressure_drop
)

plt.figure()

plt.scatter(
    flow,
    hydraulic_residuals
)

plt.axhline(
    0,
    linestyle="--"
)

plt.xlabel("Flow rate (L/min)")
plt.ylabel("ROM - COMSOL pressure drop (kPa)")
plt.title("Hydraulic ROM Residuals")

plt.grid(True)

plt.show()


thermal_residuals = (
    rth_predicted - rth
)

plt.figure()

plt.scatter(
    flow,
    thermal_residuals
)

plt.axhline(
    0,
    linestyle="--"
)

plt.xlabel("Flow rate (L/min)")
plt.ylabel("ROM - COMSOL Rth (K/W)")
plt.title("Thermal ROM Residuals")

plt.grid(True)

plt.show()


# validation of the ROMs with new data

validation_flow = 0.864

dp_validation_pred = hydraulic_rom(
    validation_flow,
    a,
    b
)

rth_validation_pred = thermal_rom(
    validation_flow,
    C,
    m
)

print("\nOff-grid validation:")
print(
    "Predicted pressure drop =",
    dp_validation_pred,
    "kPa"
)

print(
    "Predicted Rth =",
    rth_validation_pred,
    "K/W"
)

