import os
import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import StandardScaler

#1. configuration
DATASET_PATH = os.path.join("data", "telemetry_dataset.csv")
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

print("[INFO] Loading dataset...")
df = pd.read_csv(DATASET_PATH)

#2. CRITIC FILTER_ We are using only "NORMAL" for training
print("[INFO] Filtering only NORMAL state data...")
df_normal = df[df["label"] == "NORMAL"].copy()

if len(df_normal) < 50:
    raise ValueError("Needed 50 'NORMAL' sampleas atleast to train. Recolecting...")

#3. Features selecction(ignore timestamp and label)
features = ["rms_x", "rms_y", "rms_z", "std_x", "std_y", "std_z"]
x = df_normal[features].values

#4. Scalate(Mandatory for Neuronal Networks and INT 8 quantization)
scaler = StandardScaler()
x_scaled = scaler.fit_transform(x)

# Save the scaler to use it on ESP32
joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.pkl"))
print(f"[INFO] scaler saved: mean: {scaler.mean_}")

#5. Autoencoder construction (API functional)
input_dim = x_scaled.shape[1] # it shoould be 6

inputs = tf.keras.Input(shape=(input_dim,))
#Encoder (compressure)
x_enc = tf.keras.layers.Dense(8, activation='relu')(inputs)
bottleneck = tf.keras.layers.Dense(3, activation='relu', name='bottleneck')(x_enc)
#Decoder (Reconstruction)
x_dec = tf.keras.layers.Dense(8, activation='relu')(bottleneck)
outputs = tf.keras.layers.Dense(input_dim, activation='linear')(x_dec) #Linear es estándar para reconstrucción

autoencoder = tf.keras.Model(inputs, outputs)
autoencoder.compile(optimizer='adam', loss='mse')

print("[INFO] Training autoencoder (reconstuction of the input...)")
history = autoencoder.fit(
    x_scaled, x_scaled, #The goal (y) its the same input(x)
    epochs=50,
    batch_size=16,
    validation_split=0.2,
    verbose=1
     )

#6. Calculus of the anomaly umbral (Trheshold)
print("[INFO] Calculating anomaly umbral...")
reconstructions = autoencoder.predict(x_scaled)
mse = np.mean(np.power(x_scaled - reconstructions, 2), axis=1)

# We use the 95 percentil. The 5% of the rarer "Normal" data are considered as the limits
trheshold = float(np.percentile(mse, 95))
print(f"[SUCCES] Anomaly umbral (MSE) stablished on: {trheshold:.6f}")

#Save the umbral
np.save(os.path.join(MODEL_DIR, "threshold.npy"), trheshold)

#7. INT8 quantiation (Post-Training Static Quantization)
print("[INFO] quantization model to INT8 for ESP32...")

# Generative representation data function (Required for TF Lite to INT8)
def representative_data_gen():
    for i in range(min(100, len(x_scaled))):
        yield [x_scaled[i:i+1].astype(np.float32)]

converter = tf.lite.TFLiteConverter.from_keras_model(autoencoder)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_data_gen
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
#converter.inference_input_type = tf.int8
#converter.inference_output_type = tf.int8

try:
    tflite_model = converter.convert()
    tflite_path = os.path.join(MODEL_DIR, "vibration_autoencoder_int8.tflite")
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
    print(f"[SUCCES] Model TFlite INT8 generated: {tflite_path} ({len(tflite_model)}) bytes")
except Exception as e:
    print(f"[WARNING] Failed in the INT8 quantization(Common in new versions of TF): {e}")
    print(f"[INFO] Generating fallback on FLOAT32...")
    converter_fallback = tf.lite.TFLiteConverter.from_keras_model(autoencoder)
    converter_fallback.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model_f32 = converter_fallback.convert()
    tflite_path_f32 = os.path.join(MODEL_DIR, "vibration_autoencoder_f32.tflite")
    with open(tflite_path_f32, "wb") as f:
        f.write(tflite_model_f32)
    print(f"[SUCCESS] Modelo TFLite FLOAT32 generado: {tflite_path_f32} ({len(tflite_model_f32)} bytes)")