################################################################################
# Atmospheric Dispersion Model (Gaussian, Total Reflection, [g/m^3] || [curies/m^3])
# Brandon Whittle
# D. B. Turner Model (1967)
################################################################################

from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sb

############################## CONSTANT TABLES #################################

# Atmospheric conditions table


def atmos():
    atmos = [
        ", Wind [m/s]",
        "Day, Strong",
        "Day, Moderate",
        "Day, Slight",
        "|, |",
        "Night, Low",
        "Night, Moderate",
    ]
    atmos = pd.DataFrame(
        [
            ["<2", "A", "A-B", "B", "|", "", ""],
            ["2-3", "A-B", "B", "C", "|", "E", "F"],
            ["3-5", "B", "B-C", "C", "|", "D", "E"],
            ["5-6", "C", "C-D", "D", "|", "D", "D"],
            [">6", "C", "D", "D", "|", "D", "D"],
        ],
        columns=atmos,
    )
    a = atmos.columns.str.split(", ", expand=True).values
    atmos.columns = pd.MultiIndex.from_tuples(
        [("", x[0]) if pd.isnull(x[1]) else x for x in a]
    )

    print("-------------------------------------------------------")
    print("                Atmospheric Conditions")
    print("-------------------------------------------------------")
    print(atmos.rename(index={0: "", 1: "", 2: "", 3: "", 4: ""}))
    print("-------------------------------------------------------")
    print("*Wind speed is at a height of 10m")
    print("*Day is an estimation of solar radiation")
    print("*Night is an estimation of cloud cover")
    print(
        "*Category 'D' can be assumed for all overcast\n\tconditions, regardless of wind speed"
    )
    print("-------------------------------------------------------")


# stability: Stability Class [A,B,C,D,E,F]
# var [a,c,d,f]
# dis downwind distance [km]
def classConsts(stability, var, dis):
    consts = [
        [213, 440.8, 1.941, 9.27, 459.7, 2.094, -9.6],
        [156, 100.6, 1.149, 3.3, 108.2, 1.098, 2],
        [104, 61, 0.911, 0, 61, 0.911, 0],
        [68, 33.2, 0.725, -1.7, 44.5, 0.516, -13],
        [50.5, 22.8, 0.678, 1.3, 55.4, 0.305, -34],
        [34, 14.35, 0.74, -0.35, 62.6, 0.18, -48.6],
    ]

    row = ord(stability) - 65  # See ASCII Table: https://www.asciitable.com/

    if var == "a":
        col = 0
    if dis < 1:
        if var == "c":
            col = 1
        if var == "d":
            col = 2
        if var == "f":
            col = 3
    elif dis >= 1:
        if var == "c":
            col = 4
        if var == "d":
            col = 5
        if var == "f":
            col = 6

    return float(consts[row][col])


################################### FUNCTIONS ##################################

# v_s = 0         # Stack velocity                                      [m/s]
# d = 0           # Stack diameter                                      [m]
# mu = 0          # Wind speed                                          [m/s]
# P = 0           # Pressure                                            [kPa]
# T_s = 0         # Stack temperature                                   [K]
# T_a             # Air Temperature                                     [K]
def get_plume_height(h, v_s, d, mu, P, T_s, T_a):
    return h + (v_s * d / mu) * (
        1.5 + (2.68 * 10 ** (-2) * P * ((T_s - T_a) / T_s) * d)
    )


# a = 0           # Table 12-11 (p566)
# x = 0           # Downwind distance                                      [km]
def get_sigma_y(stability, x):
    if x == 0:
        x += 0.0001
    return classConsts(stability, "a", x) * x ** 0.894


# c = 0           # Table 12-11 (p566)
# d = 0           # Table 12-11 (p566)
# f = 0           # Table 12-11 (p566)
# x = 0           # Downwind distance                                      [km]
def get_sigma_z(stability, x):
    if x == 0:
        x += 0.0001
    return classConsts(stability, "c", x) * x ** classConsts(
        stability, "d", x
    ) + classConsts(stability, "f", x)


# Q = 0           # Uniform emission rate of pollutants                    [g/s] || [curies/s]
# mu = 0          # Mean wind speed affecting plume                        [m/s]
# sigma_y = 0     # Horizontal standard deviation of plume concentration   [m]
# sigma_z = 0     # Vertical standard deviation of plume concentration     [m]
# x = 0           # Downwind coordinate                                    [m]
# y = 0           # Lateral coordinate                                     [m]
# z = 0           # Vertical coordinate                                    [m]
# H = 0           # Plume height (sum of actual height and plume rise)     [m]
def turner(y, z, H, Q, mu, sigma_y, sigma_z):
    return np.round(
        (
            (Q / (2 * np.pi * sigma_y * sigma_z * mu))
            * np.exp(-0.5 * ((y / sigma_y) ** 2))
            * (
                np.exp(-0.5 * (((z - H) / sigma_z) ** 2))
                + np.exp(-0.5 * (((z + H) / sigma_z) ** 2))
            )
        ),
        10,
    )


def validate(prompt, strict=False, tf=False, values=["0", "1"]):
    def float_test(value):
        try:
            float(value)
            return True
        except:
            return False

    attempts = 0
    response = ""
    while attempts < 3:
        if (strict and response not in values) or (
            not strict and not float_test(response)
        ):
            response = input(f"{prompt}")

        if strict and response not in values:
            print(f"'{response}' is not valid. Options: {values}")
        elif not strict and not float_test(response):
            print(
                f"'{response}' is not valid. Argument must be of type integer or float."
            )
        else:
            if tf:
                if response == "0":
                    return False
                else:
                    return True
            return response
        attempts += 1
    print("Maximum number of attempts succeeded.\nExiting...")
    exit(1)


###################################### Main ####################################

# Resolution for dimensions [m]
H_RES = 10
D_RES = 100
L_RES = 100


def main():
    print(
        "*******************************************************\n"
        "Atmospheric Dispersion Model\n"
        "Written by Brandon Whittle\n"
        "*******************************************************"
    )

    # Default constants for demo, testing, etc
    if validate("Use static values [0/1]: ", True, True):
        SINGLE = validate("Single point [0/1]: ", True, True)
        CATEGORY = "D"
        X_DIS = 10
        Y_DIS = 1500
        Z_DIS = 20
        STACK_HEIGHT = 120.0
        STACK_DIAMETER = 1.2
        AIR_PRESSURE = 95.0
        WIND_SPEED = 4.5
        AIR_TEMP = 298.15
        STACK_TEMP = 588.15
        EMISSION_RATE = 1656.2
        EMISSION_VELOCITY = 10.0

    # Constants set from prompts
    else:
        SINGLE = validate("Single point [0/1]: ", True, True)
        atmos()
        CATEGORY = validate(
            "Atmospheric Category [A/B/C/D/E/F]: ",
            True,
            values=["A", "B", "C", "D", "E", "F"],
        )
        X_DIS = int(validate("Downwind distance [km]: ", False))
        Y_DIS = int(validate("Lateral distance [m]: ", False))
        Z_DIS = int(validate("Vertical distance [m]: ", False))
        STACK_HEIGHT = float(validate("Stack height [m]: ", False))
        STACK_DIAMETER = float(validate("Stack diameter [m]: ", False))
        AIR_PRESSURE = float(validate("Ambient air pressure [kPa]: ", False))
        WIND_SPEED = float(validate("Wind speed [m/s]: ", False))
        AIR_TEMP = float(validate("Ambient temperature [K]: ", False))
        STACK_TEMP = float(validate("Stack temperature [K]: ", False))
        EMISSION_RATE = float(validate("Emission rate [g/s]: ", False))
        EMISSION_VELOCITY = float(validate("Emission velocity [m/s]: ", False))

    # Get effective stack height from gathered information
    EFFECTIVE_HEIGHT = get_plume_height(
        STACK_HEIGHT,
        EMISSION_VELOCITY,
        STACK_DIAMETER,
        WIND_SPEED,
        AIR_PRESSURE,
        STACK_TEMP,
        AIR_TEMP,
    )

    # Single point calculation
    if SINGLE:
        print(
            turner(
                Y_DIS,
                Z_DIS,
                EFFECTIVE_HEIGHT,
                EMISSION_RATE,
                WIND_SPEED,
                get_sigma_y(CATEGORY, X_DIS),
                get_sigma_z(CATEGORY, X_DIS),
            )
        )

    # Bounded volume calculation
    else:
        RESULTS = []

        # Generate 3D array
        for height in range(0, Z_DIS + 1, H_RES):
            RESULTS.append([])
            for downwind in range(0, (X_DIS + 1) * 1000 - 999, D_RES):
                RESULTS[int(height / H_RES)].append([])
                for lateral in range(-Y_DIS, Y_DIS + 1, L_RES):
                    RESULTS[int(height / H_RES)][int(downwind / D_RES)].append(
                        turner(
                            lateral,
                            height,
                            EFFECTIVE_HEIGHT,
                            EMISSION_RATE,
                            WIND_SPEED,
                            get_sigma_y(CATEGORY, downwind / 1000),
                            get_sigma_z(CATEGORY, downwind / 1000),
                        )
                    )

        # Generate column and index titles
        cols = {}
        idxs = {}
        for col in range(int((X_DIS * 1000) / D_RES + 1)):
            cols[col] = f"D{str(round(col * (D_RES / 1000), 2))}km"
        for idx in range(int(Z_DIS / H_RES + 1)):
            idxs[idx] = f"H{str(round(idx * H_RES, 2))}m"

        # Create DataFrame and format titles
        out = pd.DataFrame(RESULTS).rename(columns=cols, index=idxs)

        # Optional Ouputs
        if validate("Print preview of results [0/1]: ", True, True):
            print(out)

        if validate("Save [0/1]: ", True, True):
            out.to_csv(f"./{X_DIS}x{Y_DIS}x{Z_DIS}-stack_dispersion.csv")

        if validate("Show heatmap [0/1]: ", True, True):

            # Generate height options
            planes = []
            for h in range(0, Z_DIS + 1, 10):
                planes.append(f"{h}")

            plot = int(
                int(validate(f"Height {planes}: ", True, False, planes)) / H_RES)

            x_ticks = []
            x_tick_labels = []
            for i in range(0, len(RESULTS[0][0]) + 2, 4):
                x_ticks.append(
                    (len(RESULTS[0][0])) / (len(RESULTS[0][0]) + 1) * i)
                x_tick_labels.append(
                    int(-Y_DIS + (Y_DIS * 2 / (len(RESULTS[0][0]) + 1) * i))
                )

            y_ticks = []
            y_tick_labels = []
            for i in range(int(X_DIS + 1)):
                y_ticks.append(i * 10)
                y_tick_labels.append(i)

            fig, ax1 = plt.subplots(1, 1, figsize=(10, 10))
            sb.heatmap(RESULTS[plot], ax=ax1, square=True,
                       robust=True, cmap="coolwarm")
            ax1.set_yticks(y_ticks)
            ax1.set_yticklabels(y_tick_labels)
            ax1.set_ylabel("Downwind Distance [km]")
            ax1.set_xticks(x_ticks)
            ax1.set_xticklabels(x_tick_labels)
            ax1.set_xlabel("Lateral Distance [m]")
            ax1.set_title(f"Stack Dispersion Heatmap | Height: {plot*10}m")

            plt.show()


if __name__ == "__main__":
    main()
