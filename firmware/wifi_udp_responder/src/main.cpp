#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include "wifi_credentials.h"

// Local-only file wifi_credentials.h supplies WIFI_SSID and WIFI_PASSWORD.
WiFiUDP udp;
constexpr uint16_t UDP_PORT = 4210;
char packetBuffer[256];

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\nESP32 Wi-Fi UDP Responder");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWi-Fi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  Serial.print("Signal strength (RSSI): ");
  Serial.print(WiFi.RSSI());
  Serial.println(" dBm");

  if (udp.begin(UDP_PORT)) {
    Serial.printf("UDP responder ready on port %u\n", UDP_PORT);
  } else {
    Serial.println("UDP start failed!");
  }
}

void loop() {
  int packetSize = udp.parsePacket();
  if (packetSize <= 0) {
    delay(1);
    return;
  }

  int len = udp.read(packetBuffer, sizeof(packetBuffer));
  if (len <= 0) {
    return;
  }

  Serial.printf("Received %d bytes from %s:%u\n",
                len, udp.remoteIP().toString().c_str(), udp.remotePort());

  udp.beginPacket(udp.remoteIP(), udp.remotePort());
  udp.write(reinterpret_cast<const uint8_t*>(packetBuffer), len);
  udp.endPacket();
  Serial.println("Reply sent");
}
