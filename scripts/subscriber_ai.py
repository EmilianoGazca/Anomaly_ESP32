import paho.mqtt.client as mqtt
import argparse
import os
import json
import csv
from datetime import datetime


#1. Arguments configuration from consol
parser = argparse.ArgumentParser(description = "MQTT subscriber & Telemetry logger ")
parser.add_argument(
    "--label",
    type=str,
    default="NORMAL",
    choices=["NORMAL", "ANOMALY"],
    help="Label for current recolection state: NORMAL or ANOMALY"
)
args = parser.parse_args()

# === Broker and file configuration ===
BROKER_IP = "localhost"  # The IP of your Mosquitto Broker
PORT = 1883
TOPIC = "motor/vibration/telemetry"
DATASET_PATH = os.path.join("..", "data", "telemetry_dataset.csv")

# Build "data" carpet and headers if the file doesn't exists
os.makedirs("data", exist_ok=True)
if not os.path.exists(DATASET_PATH):
    with open(DATASET_PATH, mode="w", newline="") as f:
        writer=csv.writer(f)
        writer.writerow(
            [
                "timestamp",
                "rms_x",
                "rms_y",
                "rms_z",
                "std_x",
                "std_y",
                "std_z",
                "label",

            ]
        )

# === MQTT CALLBACKS ===
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[CONNECTED] Successfully connected to MQTT Broker at {BROKER_IP}:{PORT}")
        client.subscribe(TOPIC)
        print(f"[SUBSCRIBED] Listening to topic: '{TOPIC}'...\n")
    else:
        print(f"[ERROR] Connection failed with return code: {rc}")


def on_message(client, userdata, msg):
    try:
        # 1. Decode incoming JSON payload from ESP32
        payload_str = msg.payload.decode("utf-8")
        data = json.loads(payload_str)

        # 2. Get current timestamp
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 3. Extract metrics (default to 0.0 if missing)
        rms_x = data.get("rms_x", 0.0)
        rms_y = data.get("rms_y", 0.0)
        rms_z = data.get("rms_z", 0.0)
        std_x = data.get("std_x", 0.0)
        std_y = data.get("std_y", 0.0)
        std_z = data.get("std_z", 0.0)

        # 4. Console log prinying the label too
        print(
            f"[{now}] [{args.label}] -> RMS(x,y,z): ({rms_x:.3f}, {rms_y:.3f}, {rms_z:.3f}) | STD(x,y,z): ({std_x:.3f}, {std_y:.3f}, {std_z:.3f})")

        # 5. Append telemetry row to CSV dataset
        with open(DATASET_PATH, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [now, rms_x, rms_y, rms_z, std_x, std_y, std_z, args.label]
                )

    except json.JSONDecodeError:
        print(f"[WARN] Invalid JSON payload received: {msg.payload}")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")

# === MAIN LOOP ===
def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[START] Connecting to {BROKER_IP}...")
    client.connect(BROKER_IP, PORT, 60)

    # Keep subscriber listening in the background
    client.loop_forever()


if __name__ == "__main__":
    main()