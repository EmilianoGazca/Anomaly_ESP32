#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <secrets.h>

void setup_wifi();

// === NET AND MQTT CONFIGURATION===
WiFiClient espClient;
PubSubClient mqttClient(espClient);

const char* mqtt_topic = "motor/vibration/telemetry";

//=== NOISE FILTERING PIPELINE USING RMS & STANDARD DEVIATION ===

// Digital Signal Processing (DSP) window size for features extraction
const int window_Size = 64;

// Ring buffers for triaxial accelerometer telemetry
float Xaxis[window_Size];
float Yaxis[window_Size];
float Zaxis[window_Size];

int bufferIndex = 0;
bool bufferFull = false;

// Enqueues a new raw data point into the DSP sliding window
void pushSample(float ax, float ay, float az) {
    Xaxis[bufferIndex] = ax;
    Yaxis[bufferIndex] = ay;
    Zaxis[bufferIndex] = az;
    bufferIndex++;

// Check boundary limitations and reset the index pointer
    if (bufferIndex == window_Size) {
        bufferIndex = 0;
        bufferFull = true;
    }
}

// Computes the Root Mean Square (RMS) to evaluate signal energy
float calculateRMS(float axis[]) {
    float squareSum = 0.0;
    for (int i = 0; i < window_Size; i++) {
        squareSum += (axis[i] * axis[i]);
    }
    float average = squareSum / window_Size;
    return sqrt(average);
}

// Computes the Standard Deviation to measure signal variance and noise distribution
float calculateStdDev(float axis[]) {
// Step 1: Calculate the arithmetic mean (µ)
    float sum = 0.0;
    for (int i = 0; i < window_Size; i++) {
        sum += axis[i];
    }
    float mean = sum / window_Size;

// Step 2: Compute the cumulative variance
    float varianceSum = 0.0;
    for (int i = 0; i < window_Size; i++) {
        varianceSum += (axis[i] - mean) * (axis[i] - mean);
    }
    float variance = varianceSum / window_Size;
    return sqrt(variance);
}
// ===  CONECCTION FUNCTIONS ===
void setup_wifi(){
    delay(10);
    Serial.println();
    Serial.print("coneccting to");
    Serial.println(WIFI_SSID);

    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    

    while(WiFi.status() != WL_CONNECTED){
     delay(500);
     Serial.print(".");
    }
    Serial.println("");
    Serial.println("Wi-Fi succesfully connected.");
    Serial.print("IP asigned to ESP32: ");
    Serial.println(WiFi.localIP());
}
void reconnect() {
 //loop until getting conected with MQTT broker
    while(!mqttClient.connected()){
    Serial.print("Trying MQTT connection in broker ");
        Serial.print(MQTT_BROKER_IP);
        Serial.print("... ");

//We define an unique ID code for our ESP32 client
        String clientID = "ESP32_Vibration_Node-";
        clientID += String(random(0xffff), HEX);

        if(mqttClient.connect(clientID.c_str())){
            Serial.println("¡succesuflly connected to Wifi!");
        }else{
            Serial.print("Fail in state: ");
            Serial.print(mqttClient.state());
            Serial.println(". Retrying in 5 secounds...");
            delay(5000);
        }
    }
}

void setup() {
// Initialize serial communication for Edge telemetry output
    Serial.begin(115200);
    setup_wifi();
//Broker MQTT net configuration
    mqttClient.setServer(MQTT_BROKER_IP, 1883);    
    while (!Serial) {
        ; // Wait for serial port connection (Required for native USB targets)
    }
    Serial.println("--- IIOT EDGE AI PIPELINE INITIALIZED ---");
}
void loop() {
    if(!mqttClient.connected()){
        reconnect();
    }
    mqttClient.loop();// Process intern task-works from MQTT library

// Base physical values representing a healthy industrial motor (in Gs)    
   const float base_x = 0.44;
   const float base_y = 0.32;
   const float base_z = 0.78;
   
// Injecting high-frequency pseudorandom industrial noise (+/- 0.05 Gs)
    float noiseX = ((rand() %101) - 50 ) / 1000.0;
    float noiseY = ((rand() %101) - 50 ) / 1000.0;
    float noiseZ = ((rand() %101) - 50 ) / 1000.0;

// Simulated telemetry payload containing signal + noise
    float ax = base_x + noiseX;
    float ay = base_y + noiseY;
    float az = base_z + noiseZ;

    pushSample(ax, ay, az);

    if (bufferFull) {
    // Feature extraction from raw time-domain signals
        float rmsX = calculateRMS(Xaxis);
        float rmsY = calculateRMS(Yaxis);
        float rmsZ = calculateRMS(Zaxis);

        float stdX = calculateStdDev(Xaxis);
        float stdY = calculateStdDev(Yaxis);
        float stdZ = calculateStdDev(Zaxis);

    // Local console print use in fast depuration
        Serial.print("RMS X: "); Serial.print(rmsX, 4);
        Serial.print(" ||StdDev X"); Serial.print(stdX, 4);
        
    //build format in JSON, the standar used in IoT
        String jsonPayload = "{";
        jsonPayload += "\"rms_x\":" + String(rmsX, 4) + ",";
        jsonPayload += "\"rms_y\":" + String(rmsY, 4) + ",";
        jsonPayload += "\"rms_z\":" + String(rmsZ, 4) + ",";
        jsonPayload += "\"std_x\":" + String(stdX, 4) + ",";
        jsonPayload += "\"std_y\":" + String(stdY, 4) + ",";
        jsonPayload += "\"std_z\":" + String(stdZ, 4);
        jsonPayload += "}";
     //Upload JSON message in the Broker
        if(mqttClient.publish(mqtt_topic, jsonPayload.c_str())){
            Serial.println(">>Data succesuflly deployd in MQTT.");
        }else{
            Serial.println(">> Error to deployd in MQTT.");
        }

     // Reset state machine flag for the next window iteration
        bufferFull = false;
    }

    // Deterministic sampling interval (100 Hz sampling rate equivalent)
    delay(10);
}