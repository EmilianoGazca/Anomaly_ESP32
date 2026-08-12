from collections import deque
import json
import os
import paho.mqtt.client as mqtt
import plotext as plt

# === BROKER AND TELEMETRY CONFIGURATION ===
BROKER = "localhost"
PORT = 1883
TOPIC = "motor/vibration/telemetry"

# Real-time buffer sliding window (retains last 30 telemetry points)
MAX_LEN = 30
rms_x_vals = deque(maxlen=MAX_LEN)
rms_y_vals = deque(maxlen=MAX_LEN)
rms_z_vals = deque(maxlen=MAX_LEN)


# === MQTT CALLBACK FUNCTIONS ===
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(
            "[MONITOR] Connected. Awaiting telemetry data for real-time visualization..."
        )
        client.subscribe(TOPIC)
    else:
        print(f"[ERROR] Connection failed with return code: {rc}")


def on_message(client, userdata, msg):
    try:
        # 1. Parse JSON telemetry payload
        data = json.loads(msg.payload.decode("utf-8"))

        # 2. Extract RMS telemetry metrics from incoming payload
        rms_x_vals.append(data.get("rms_x", 0.0))
        rms_y_vals.append(data.get("rms_y", 0.0))
        rms_z_vals.append(data.get("rms_z", 0.0))

        # 3. Clear terminal console screen for smooth rendering
        # os.system("cls" if os.name == "nt" else "clear")

        # 4. Re-draw plotext canvas
        plt.clt()
        plt.cld()

        plt.plot(list(rms_x_vals), label="RMS X", color="red")
        plt.plot(list(rms_y_vals), label="RMS Y", color="green")
        plt.plot(list(rms_z_vals), label="RMS Z", color="blue")

        plt.title("Real-Time IIoT Vibration Telemetry Monitor (RMS)")
        plt.xlabel("Recent Samples Window")
        plt.ylabel("Acceleration (m/s²)")
        plt.ylim(
            0, max(max(rms_x_vals, default=1.0), 15.0)
        )  # Dynamic vertical scale adjustment
        plt.show()

    except Exception as e:
        pass


# === CLIENT INITIALIZATION ===
client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION1, client_id="Live_Monitor_Node"
)
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
client.loop_forever()