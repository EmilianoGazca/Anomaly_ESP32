import numpy as np
import pandas as pd
import joblib
import tensorflow as tf

# Same data model trained on 
df  = pd.read_csv("data/telemetry_dataset.csv")
scaler = joblib.load("models/scaler.pkl")
x = df[["rms_x", "rms_y", "rms_z", "std_x", "std_y", "std_z"]].values
xs = scaler.transform(x).astype(np.float32)

# The exact artifact that runs on the specific chip quantized
interp = tf.lite.Interpreter(model_path="models/vibration_autoencoder_int8.tflite")
interp.allocate_tensors()
in_d = interp.get_input_details()[0]
out_d = interp.get_output_details()[0]

mse_list = []
for i in range(len(xs)):
    interp.set_tensor(in_d["index"], xs[i:i+1])
    interp.invoke()
    out = interp.get_tensor(out_d["index"])
    mse_list.append(float(np.mean((xs[i] - out[0]) ** 2)))

thr = float(np.percentile(mse_list, 95))
print(f"\n//Threshold adjusted against INT 8 model deployed: ")
print(f"#define ANOMALY_THRESHOLD {thr:.6f}f")
print(f"//(normal typical ~{np.median(mse_list):.4f}, p95 ~ {thr:.4f})")
