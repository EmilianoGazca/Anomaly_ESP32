import json
import os
import joblib
import numpy as np
import paho.mqtt.client as mqtt

# This Script's meaning is detecting the anomalies when are on spot, this way you don't need an interpeter
# Is easy and clear to see

#===================================================================
#1. LOADS THE MODEL ON THE MEMORY(AIs "brain")
#===================================================================
MODEL_PATH =os.path.join("models", "vibration_anomaly_model.pkl")
print("[LOADING...]Loading Artificial Inteligence Model")
model = joblib.load(MODEL_PATH)
print("[SUCCESS]Model sucessfully loaded into the memory")

#MQTT Broker configuration
BROKER_IP = "localhost"
PORT = 1883
TOPIC ="motor/vibration/telemetry"

#===================================================================
#2. CALLBACKS FROM MQTT (Real Time Process RTOs)
#===================================================================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[CONNECTED] Listenning Telemetry on the MQTT Broker...")
        client.subscribe(TOPIC)
    else: 
        print(f"[ERRROR] Failed attemting to connect with code: {rc}")


def on_message(client, user, msg):
    try: 
        #A. Decode the message that comes from the net (JSON)
        payload = json.loads(msg.payload.decode("utf-8"))

        #B. Extract the features vector in the exact way it was trained
        features = np.array(
            [
                [
                    payload.get("rms_x", 0.0),
                    payload.get("rms_y", 0.0),
                    payload.get("rms_z", 0.0),
                    payload.get("std_x", 0.0),
                    payload.get("std_y", 0.0),
                    payload.get("std_z", 0.0),
                ]
            ]
        )
        #C. Making the Real Time Inference
        prediction = model.predict(features)[0]

        #D. Evaluate the result and take desicions
        rms_total = np.sqrt(
            payload.get("rms_x", 0) ** 2
            + payload.get("rms_y", 0) ** 2
            + payload.get("rms_z", 0) ** 2
        )
        if prediction == "ANOMALY":
            print(
            f"[ALERT ANOMALY DETECTED] Total RMS: {rms_total:.2f} m/s^2 | State: VIBRATION FAILURE"
        )
        else:
            print(
            f"[NORMAL STATE] Total RMS: {rms_total:.2f} m/s^2 | Operation stable"
        )
    except Exception as e:
        print(f"[ERROR] Error procesing the inferency: {e}")

    #===================================================================
    # 3. MAIN LOOP ( Keep the listenning active)
    #===================================================================
def main():
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect(BROKER_IP, PORT, 60)
        client.loop_forever()

if __name__ == "__main__":
    main()