#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

const char* ssid = "Home2";
const char* password = "Ma054054or";

// Change this to your Flask server's IP address
const char* BASE_URL = "https://aquagrow.hack-ops.net/api/update"; // Changed to HTTP and base URL

const int sensorPin = A0;
const int wetValue = 300;
const int dryValue = 900;
const String sensorName = "Outside Garden"; // Use a consistent name, e.g., "Outside garden sensor" or "OutsideGardenSensor"

// Time variables for non-blocking delay
unsigned long lastReportTime = 0;
// const long reportInterval = 10 * 60 * 1000; // 5 seconds in milliseconds (for quicker testing, change to 5 * 60 * 1000 for 5 minutes)
const long reportInterval = 5000; // 5 seconds in milliseconds (for quicker testing, change to 5 * 60 * 1000 for 5 minutes)

// Create a WiFiClient object globally
WiFiClient client; // Declare WiFiClient here

void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println("\n[SETUP] Starting Moisture Sensor with WiFi...");

  WiFi.begin(ssid, password);
  Serial.print("[SETUP] Connecting to WiFi");

  int tries = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    tries++;
    if (tries > 40) { // Timeout after 20 seconds (40 * 500ms)
      Serial.println("\n[SETUP] Initial WiFi connection failed. Retrying indefinitely...");
      // Do not restart here, just continue the loop below to retry indefinitely
      break; // Exit this initial setup loop to let loop() handle reconnection
    }
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[SETUP] WiFi connected!");
    Serial.print("[SETUP] IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[SETUP] Initial WiFi connection failed. Will keep retrying in loop().");
  }
  Serial.println("[SETUP] Setup complete.");
}

void loop() {
  // --- WiFi Connection Management ---
  // Always ensure WiFi is connected before proceeding with sensor reading and reporting.
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[LOOP] WiFi not connected. Attempting to reconnect...");
    WiFi.reconnect(); // Attempt to reconnect

    // Loop indefinitely until connected
    while (WiFi.status() != WL_CONNECTED) {
      delay(1000); // Wait 1 second before next retry attempt
      Serial.print("[LOOP] Still trying to connect to WiFi...");
      Serial.println(WiFi.status()); // Print current status code
    }
    Serial.println("\n[LOOP] WiFi reconnected!");
    Serial.print("[LOOP] New IP Address: ");
    Serial.println(WiFi.localIP());
    // Reset lastReportTime immediately after re-connection to send a report soon
    lastReportTime = millis();
  }

  // --- Sensor Reporting Logic ---
  // Only proceed if WiFi is connected
  if (WiFi.status() == WL_CONNECTED) {
    // Check if it's time to send a report
    if (millis() - lastReportTime >= reportInterval) {
      lastReportTime = millis(); // Update the last report time
      Serial.println("\n[LOOP] Time to send sensor report.");

      int sensorValue = analogRead(sensorPin);
      // Ensure dryValue > wetValue for correct mapping,
      // as lower analogRead means higher moisture (wetter)
      // and higher analogRead means lower moisture (drier).
      int moisturePercent = map(sensorValue, dryValue, wetValue, 0, 100);
      moisturePercent = constrain(moisturePercent, 0, 100); // Keep percentage between 0 and 100

      Serial.print("[LOOP] Raw Value: ");
      Serial.print(sensorValue);
      Serial.print(" | Moisture: ");
      Serial.print(moisturePercent);
      Serial.println("%");

      // Send GET request
      HTTPClient http;

      // Construct the URL with parameters for GET request
      String url = String(BASE_URL);
      url += "?name=" + sensorName;
      url += "&ip=" + WiFi.localIP().toString();
      url += "&moisture=" + String(sensorValue); // Send raw sensor value (0-1023)

      Serial.print("[LOOP] Full URL for GET request: ");
      Serial.println(url);

      if (http.begin(client, url)) { // Pass the global WiFiClient object
        Serial.println("[LOOP] HTTPClient begin successful.");
        int httpCode = http.GET(); // Send the GET request
        Serial.print("[LOOP] HTTP GET request sent. Code: ");
        Serial.println(httpCode);

        if (httpCode > 0) {
          Serial.print("[LOOP] Server response code: ");
          Serial.println(httpCode);
          String response = http.getString();
          Serial.println("[LOOP] Response:");
          Serial.println(response);
        } else {
          Serial.print("[LOOP] GET failed, error: ");
          Serial.println(http.errorToString(httpCode));
        }

        http.end(); // Free resources
        Serial.println("[LOOP] HTTPClient end called.");
      } else {
        Serial.println("[LOOP] HTTPClient begin failed. Check URL or network.");
      }
    }
  }

  // A small delay to prevent rapid looping when not sending data
  // and to allow other ESP tasks to run.
  delay(100);
}