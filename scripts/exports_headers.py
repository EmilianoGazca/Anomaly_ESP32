import os

MODEL_PATH = os.path.join("models", "vibration_autoencoder_int8.tflite")
OUTPUT_PATH = os.path.join("include", "model_data.h")

with open(MODEL_PATH, "rb") as f:
    data = f.read()

lines = []
lines.append("// Auto-generated from vibration_autoencoder_int8.tflite")
lines.append("#ifndef MODEL_DATA_H")
lines.append("#define MODEL_DATA_H")
lines.append("")
lines.append("const unsigned char model_data[] = {")
for i in range(0, len(data), 12):
    chunk = data[i:i+12]
    lines.append("  " + ", ".join(f"0x{b:02x}" for b in chunk) + ",")
lines.append("};")
lines.append("")
lines.append(f"const unsigned int model_data_len = {len(data)};")
lines.append("")
lines.append("#endif")

with open(OUTPUT_PATH, "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"[OK] model_data.h generado: {len(data)} bytes")