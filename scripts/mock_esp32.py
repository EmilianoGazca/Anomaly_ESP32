import csv
import os
import time
import numpy as np
from datetime import datetime

#configuration
DATA_DIR = "data"
DATASET_PATH = os.path.join(DATA_DIR, "telemetry_dataset.csv")
os.makedirs(DATA_DIR, exist_ok=True)

# Parameters of simulation from a "SANE" motor (state: NORMAL)
# Base values aproximated from the sensor
BASE_RMS_X = 1.2
BASE_RMS_Y = 0.8
BASE_RMS_Z = 9.8 # Z axis gravity

BASE_STD_X = 0.15
BASE_STD_Y = 0.12
BASE_STD_Z = 0.18

# Sensor's noise( Gaussian noise)
SENSOR_NOISE_RMS = 0.05
SENSOR_NOISE_STD = 0.02

t = 0

def generate_normal_data():
    global t
    t += 1
    # LATENT FACTOR 1: Intensity of vibration (shared with the 3 axes)
    # Simulate slow real variance: derivative sinusoidal + micro-noise
    intensity = 1.0 + 0.25 * np.sin(2 * np.pi * t / 240) + np.random.normal(0, 0.05)

    # LATENT FACTOR 2: load of the motor (slower, afeccts RMS from X and Y)
    load = 1.0 + 0.15 * np.sin(2 * np.pi * t / 600 + 1.3) + np.random.normal(0, 0.03)

    #STDs: compiled with the intensity factor (they move TOGETHER)
    std_x = max(0.01, 0.15 * intensity + np.random.normal(0, 0.008))
    std_y = max(0.01, 0.15 * intensity + 0.95 + np.random.normal(0, 0.010))
    std_z = max(0.01, 0.18 * intensity * 0.85 + np.random.normal(0, 0.010))

    # RMS: Dependant of the load + their own vibration (physic correlation)
    rms_x = max(0.01, 0.12 * load + 2.0 * std_x + np.random.normal(0, 0.003))
    rms_y = max(0.01, 0.8 * load + 1.8 * std_y + np.random.normal(0, 0.003))
    rms_z = max(0.01, 9.8 + 0.5 * intensity + np.random.normal(0, 0.05))
    
    return rms_x, rms_y, rms_z, std_x, std_y, std_z

def main():
    print("[MOCK ESP32] Initialize simulation of NORMAL telemetry...")
    print("[MOCK ESP32] Press ctrl+C to stop")

    #Create head filers if doesn't exists
    if not os.path.exists(DATASET_PATH):
        with open(DATASET_PATH, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "rms_x", "rms_y", "rms_z", "std_x", "std_y", "std_z"])

    with open(DATASET_PATH, mode="a", newline="") as f:
        writer = csv.writer(f)

        try:
            while True:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                rms_x, rms_y, rms_z, std_x, std_y, std_z = generate_normal_data()

                #Writting on CSV
                writer.writerow([now,
                             round(rms_x, 4), round(rms_y, 4), round(rms_z, 4),
                             round(std_x, 4), round(std_y, 4), round(std_z, 4),
                             "NORMAL"])
                f.flush() #Inmediately saved
                # Simulate sample frequency from ESP32 (ej 1 Hz)
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n[MOCK ESP32] Simulación detenida por el usuario.")

if __name__ == "__main__":
    main()
        