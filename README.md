# ⚙️ IIoT Edge AI Pipeline for Vibration Anomaly Detection

> **Status:** 🚧 Work in Progress (WIP) — Phase 1: Feature Extraction & Telemetry Completed

## 📌 Overview
This project implements a hybrid architecture of **Edge Computing and Industrial Artificial Intelligence (IIoT)** for the monitoring and detection of anomalies in industrial engines.

 The system performs **Digital Signal Processing (DSP)** locally on an ESP32 microcontroller to calculate time domain features (RMS and Standard Deviation) of triaxial acceleration data, streaming them via **MQTT** to an environment inference in **Python**. ---




---

## 🏗️ Architecture Pipeline

```
[ Sensor / Simulation ] ➔ [ ESP32 (C++ / DSP) ] ➔ [ MQTT Broker (Mosquitto) ] ➔ [ Python (inference AI) ]
```
1. **Edge Node (ESP32):** 100 Hz sampling with sliding window ($N=64$).
2. **Feature Extraction:** Calculation of RMS and Standard Deviation ($\sigma$) per axis ($X, Y, Z$). 
3. **Transport Layer:** Upload of JSON payloads using the MQTT protocol. 
4. **AI Processing:** Inference and detection of anomalous patterns on local host. ---

---

## 🛠️ Tech Stack & Tools

* **Firmware:** C++, PlatformIO, Framework Arduino (ESP32).
* **Protocols & Middleware:** MQTT, Mosquitto Broker.
* **Host / AI:** Python, `paho-mqtt`, NumPy.
* **Hardware Target:** ESP32 (DevKit v1).

---

## 🚩 Roadmap & Progress
 - [x]**Fhase 1: Firmware & DSP at the Edge**
 - [x]Configuration of circular buffers for signal acquisition.  
 - [x]Mathematical implementation of RMS and StdDev in C++. 
 - [x]Integration of Wi-Fi connectivity and MQTT client (`PubSubClient`). 

- [ ]**Phase 2: Inference Pipeline in Python** 
- [ ] Creation of MQTT telemetry subscriber script. 
- [ ] Anomaly detection model training (Autoencoder / One-Class SVM). 

- [ ] **Fase 3: Despliegue TinyML (Opcional)**
  - [ ] Migración de inferencia *on-device* usando TensorFlow Lite for Microcontrollers.

---

## 🚀 Getting Started
1. Clone the repository: ```bash git clone [https://github.com/tu-usuario/Anomaly_ESP32.git](https://github.com/tu-usuario/Anomaly_ESP32.git) 
```
 2. Rename `firmware/include/secrets.example.h` to `secrets.h` andenter your Wi-Fi and Broker credentials.
 3. Compile and upload firmware with PlatformIO:
  ```bash 
  python -m platformio run --target upload
   ```