#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <secrets.h>

// === TENSORFLOW LITE MICRO (desde tflite-micro repo) ===
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"

// === ELOQUENT TINYML v3 ===
#define ELOQUENT_TFLM
#include "model_data.h"
// === CONFIGURATION FLAGS ===
#define USE_MOCK_DATA 1

// === PRE-TRAINED SCALER PARAMETERS ===
// Feature order: [rms_x, rms_y, rms_z, std_x, std_y, std_z]
// Paste your values from scripts/extract_scaler.py below:
#define SCALER_MEAN_X       1.512715f
#define SCALER_MEAN_Y       2.788685f
#define SCALER_MEAN_Z       10.302251f
#define SCALER_MEAN_STD_X   0.150272f
#define SCALER_MEAN_STD_Y   1.100308f
#define SCALER_MEAN_STD_Z   0.153502f

#define SCALER_SCALE_X      0.145694f
#define SCALER_SCALE_Y      0.104139f
#define SCALER_SCALE_Z      0.104370f
#define SCALER_SCALE_STD_X  0.028796f
#define SCALER_SCALE_STD_Y  0.029245f
#define SCALER_SCALE_STD_Z  0.029669f

#define ANOMALY_THRESHOLD   0.5f
// === HARDWARE INSTANCES ===
Adafruit_MPU6050 mpu;

// === NETWORK AND MQTT ===
WiFiClient espClient;
PubSubClient mqttClient(espClient);

const char* mqtt_topic_telemetry = "motor/vibration/telemetry";
const char* mqtt_topic_alerts    = "motor/vibration/alerts";

// === TFLITE MICRO STATE ===
// Pre-allocated workspace for inference. 32 KB is enough for this small model.
constexpr int kTensorArenaSize = 32 * 1024;
uint8_t tensor_arena[kTensorArenaSize] __attribute__((aligned(16)));

const tflite::Model* tfl_model = nullptr;
tflite::MicroInterpreter* interpreter = nullptr;
TfLiteTensor* input_tensor = nullptr;
TfLiteTensor* output_tensor = nullptr;

// === DSP PIPELINE ===
const int window_Size = 64;
float Xaxis[window_Size];
float Yaxis[window_Size];
float Zaxis[window_Size];
int bufferIndex = 0;
bool bufferFull = false;

void pushSample(float ax, float ay, float az) {
    Xaxis[bufferIndex] = ax;
    Yaxis[bufferIndex] = ay;
    Zaxis[bufferIndex] = az;
    bufferIndex++;
    if (bufferIndex == window_Size) {
        bufferIndex = 0;
        bufferFull = true;
    }
}

float calculateRMS(float axis[]) {
    float squareSum = 0.0;
    for (int i = 0; i < window_Size; i++) {
        squareSum += (axis[i] * axis[i]);
    }
    return sqrt(squareSum / window_Size);
}

float calculateStdDev(float axis[]) {
    float sum = 0.0;
    for (int i = 0; i < window_Size; i++) {
        sum += axis[i];
    }
    float mean = sum / window_Size;
    float varianceSum = 0.0;
    for (int i = 0; i < window_Size; i++) {
        varianceSum += (axis[i] - mean) * (axis[i] - mean);
    }
    return sqrt(varianceSum / window_Size);
}

// === CONNECTION FUNCTIONS ===
void setup_wifi() {
    delay(10);
    Serial.print("Connecting to ");
    Serial.println(WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWi-Fi connected.");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
}

void reconnect() {
    while (!mqttClient.connected()) {
        Serial.print("Connecting to MQTT broker...");
        String clientID = "ESP32_Vibration_Node-";
        clientID += String(random(0xffff), HEX);
        if (mqttClient.connect(clientID.c_str())) {
            Serial.println("OK");
        } else {
            Serial.print("Failed rc=");
            Serial.print(mqttClient.state());
            Serial.println(". Retry in 5s...");
            delay(5000);
        }
    }
}

// === TFLITE MICRO INITIALIZATION ===
void setup_tflite() {
    tfl_model = tflite::GetModel(model_data);
    if (tfl_model->version() != TFLITE_SCHEMA_VERSION) {
        Serial.printf("[FATAL] Model schema mismatch: %lu vs %d\n",
                      tfl_model->version(), TFLITE_SCHEMA_VERSION);
        while (1) { delay(10); }
    }

    // AllOpsResolver registers all TFLM ops. Simpler than picking individual ops.
    static tflite::MicroMutableOpResolver<6> resolver;
    resolver.AddFullyConnected();
    resolver.AddRelu();
    resolver.AddReshape();
    resolver.AddDequantize();
    resolver.AddQuantize();

    static tflite::MicroInterpreter static_interpreter(
        tfl_model, resolver, tensor_arena, kTensorArenaSize);
    interpreter = &static_interpreter;

    if (interpreter->AllocateTensors() != kTfLiteOk) {
        Serial.println("[FATAL] AllocateTensors() failed");
        while (1) { delay(10); }
    }

    input_tensor = interpreter->input(0);
    output_tensor = interpreter->output(0);

    Serial.printf("[OK] TFLite loaded. Input: %d dims, Output: %d dims\n",
                  input_tensor->dims->data[1], output_tensor->dims->data[1]);
}

// === MOCK DATA GENERATOR ===
static unsigned long mock_t = 0;
void generateMockFeatures(float features[6]) {
    /*Slow oscilations inside +-1 Sigma of the training distribution*/
    /*mock_t++;

    float s1 = sinf(2.0f * PI * mock_t / 240.0f);
    float s2 = sinf(2.0f * PI * mock_t / 300.0f + 1.0f);
    float s3 = sinf(2.0f * PI * mock_t / 320.0f + 2.0f);
    float s4 = sinf(2.0f * PI * mock_t / 320.0f + 0.5f);
    float s5 = sinf(2.0f * PI * mock_t / 260.0f + 1.7f);
    float s6 = sinf(2.0f * PI * mock_t / 260.0f + 2.4f);

    features[0] = 1.512715f  + 0.145694f * s1; // rms_x
    features[1] = 2.788685f  + 0.104139f * s2; // rms_y
    features[2] = 10.302251f + 0.104370f * s3; // rms_z
    features[3] = 0.150272f  + 0.028796f * s4; // std_x
    features[4] = 1.100308f  + 0.029245f * s5; // std_y
    features[5] = 0.153582f  + 0.029669f * s6; // std_z
    */
   //Two latent factors, the same as the CSV trainning file, to cause the device
   //to read a NORMAL output
   mock_t++;
   float intensity = 1.0f + 0.25f * sinf(2.0f * PI * mock_t / 240.0f);
   float load      = 1.0f + 0.15f * sinf(2.0f * PI * mock_t / 600.0f + 1.3f);

   float stdX = 0.15f * intensity;
   float stdY = 1.10f;
   float stdZ = 0.18f * intensity * 0.85f;
   float rmsX = 1.2f * load + 2.0f * stdX;
   float rmsY = 0.8f * load + 1.8f * stdY;
   float rmsZ = 9.8f + 0.5f * intensity;

   features[0] = rmsX; features[1] = rmsY; features[2] = rmsZ;
   features[3] = stdX; features[4] = stdY; features[5] = stdZ;
   //Simulation of a failure using a x3 multiplier
   for (int i = 0; i < 6; i++) features[i] *= 3.0f;
}
    

// === EDGE AI INFERENCE ===
bool runInference(float rmsX, float rmsY, float rmsZ,
                  float stdX, float stdY, float stdZ, float& mse_out) {
    float scaled[6];
    scaled[0] = (rmsX - SCALER_MEAN_X)     / SCALER_SCALE_X;
    scaled[1] = (rmsY - SCALER_MEAN_Y)     / SCALER_SCALE_Y;
    scaled[2] = (rmsZ - SCALER_MEAN_Z)     / SCALER_SCALE_Z;
    scaled[3] = (stdX - SCALER_MEAN_STD_X) / SCALER_SCALE_STD_X;
    scaled[4] = (stdY - SCALER_MEAN_STD_Y) / SCALER_SCALE_STD_Y;
    scaled[5] = (stdZ - SCALER_MEAN_STD_Z) / SCALER_SCALE_STD_Z;

    // Feed scaled features into the input tensor
    for (int i = 0; i < 6; i++) {
        input_tensor->data.f[i] = scaled[i];
    }

    // Run forward pass
    if (interpreter->Invoke() != kTfLiteOk) {
        Serial.println("[ERROR] TFLite Invoke() failed");
        mse_out = 0.0f;
        return false;
    }

    // Compute MSE between scaled input and reconstruction
    float mse = 0.0f;
    for (int i = 0; i < 6; i++) {
        float diff = scaled[i] - output_tensor->data.f[i];
        mse += diff * diff;
    }
    mse /= 6.0f;
    mse_out = mse;

    return mse > ANOMALY_THRESHOLD;
}

// === SETUP ===
void setup() {
    Serial.begin(115200);
    while (!Serial) { delay(10); }
    Serial.println("\n--- IIOT EDGE AI PIPELINE INITIALIZED ---");

    setup_wifi();
    mqttClient.setServer(MQTT_BROKER_IP, 1883);

#if USE_MOCK_DATA
    Serial.println("[MODE] Mock data enabled — bypassing physical sensor.");
#else
    Wire.begin(21, 22);
    if (!mpu.begin(0x69, &Wire)) {
        Serial.println("[FATAL] MPU6050 not found.");
        while (1) { delay(10); }
    }
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
    Serial.println("[OK] MPU6050 initialized.");
#endif

    setup_tflite();
}

// === MAIN LOOP ===
void loop() {
    if (!mqttClient.connected()) {
        reconnect();
    }
    mqttClient.loop();

    float rmsX, rmsY, rmsZ, stdX, stdY, stdZ;

#if USE_MOCK_DATA
    float mockFeatures[6];
    generateMockFeatures(mockFeatures);
    rmsX = mockFeatures[0]; rmsY = mockFeatures[1]; rmsZ = mockFeatures[2];
    stdX = mockFeatures[3]; stdY = mockFeatures[4]; stdZ = mockFeatures[5];
    delay(640);
#else
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);
    pushSample(a.acceleration.x, a.acceleration.y, a.acceleration.z);
    if (!bufferFull) {
        delay(10);
        return;
    }
    rmsX = calculateRMS(Xaxis); rmsY = calculateRMS(Yaxis); rmsZ = calculateRMS(Zaxis);
    stdX = calculateStdDev(Xaxis); stdY = calculateStdDev(Yaxis); stdZ = calculateStdDev(Zaxis);
#endif

    // Publish telemetry
    String jsonPayload = "{";
    jsonPayload += "\"rms_x\":" + String(rmsX, 4) + ",";
    jsonPayload += "\"rms_y\":" + String(rmsY, 4) + ",";
    jsonPayload += "\"rms_z\":" + String(rmsZ, 4) + ",";
    jsonPayload += "\"std_x\":" + String(stdX, 4) + ",";
    jsonPayload += "\"std_y\":" + String(stdY, 4) + ",";
    jsonPayload += "\"std_z\":" + String(stdZ, 4) + "}";
    mqttClient.publish(mqtt_topic_telemetry, jsonPayload.c_str());

    // Run inference
    float mse = 0.0f;
    bool is_anomaly = runInference(rmsX, rmsY, rmsZ, stdX, stdY, stdZ, mse);

    Serial.printf("MSE: %.6f | Threshold: %.6f | %s\n",
                  mse, ANOMALY_THRESHOLD,
                  is_anomaly ? "*** ANOMALY ***" : "normal");

    if (is_anomaly) {
        String alert = String("{\"mse\":") + String(mse, 6) +
                       ",\"threshold\":" + String(ANOMALY_THRESHOLD, 6) + "}";
        mqttClient.publish(mqtt_topic_alerts, alert.c_str());
        Serial.println(">> ALERT published on MQTT");
    }

#if !USE_MOCK_DATA
    bufferFull = false;
#endif
}