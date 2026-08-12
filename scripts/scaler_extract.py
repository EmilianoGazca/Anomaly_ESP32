import joblib
import numpy as np
import os

# Load the StandardScaler trained in Python
scaler = joblib.load(os.path.join("models", "scaler.pkl"))
threshold = float(np.load(os.path.join("models", "threshold.npy")))

# Feature order used during training:
# [rms_x, rms_y, rms_z, std_x, std_y, std_z]
print("// === Paste these constants in main.cpp ===")
print(f"#define SCALER_MEAN_X       {scaler.mean_[0]:.6f}f")
print(f"#define SCALER_MEAN_Y       {scaler.mean_[1]:.6f}f")
print(f"#define SCALER_MEAN_Z       {scaler.mean_[2]:.6f}f")
print(f"#define SCALER_MEAN_STD_X   {scaler.mean_[3]:.6f}f")
print(f"#define SCALER_MEAN_STD_Y   {scaler.mean_[4]:.6f}f")
print(f"#define SCALER_MEAN_STD_Z   {scaler.mean_[5]:.6f}f")
print()
print(f"#define SCALER_SCALE_X      {scaler.scale_[0]:.6f}f")
print(f"#define SCALER_SCALE_Y      {scaler.scale_[1]:.6f}f")
print(f"#define SCALER_SCALE_Z      {scaler.scale_[2]:.6f}f")
print(f"#define SCALER_SCALE_STD_X  {scaler.scale_[3]:.6f}f")
print(f"#define SCALER_SCALE_STD_Y  {scaler.scale_[4]:.6f}f")
print(f"#define SCALER_SCALE_STD_Z  {scaler.scale_[5]:.6f}f")
print()
print(f"#define ANOMALY_THRESHOLD   {threshold:.6f}f")