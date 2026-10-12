
#include <Arduino.h>
#include <SPI.h>
#include <Ethernet.h>
#include <EthernetUdp.h>

#define W5500_CS 15

byte mac[] = {0x02, 0x55, 0x50, 0x00, 0x00, 0x01};

IPAddress ip(172, 16, 15, 50);
IPAddress dns(172, 16, 15, 42);
IPAddress gateway(172, 16, 15, 42);
IPAddress subnet(255, 255, 255, 0);

EthernetUDP udp;
const unsigned int UDP_PORT = 4210;
char packetBuffer[256];

void setup() {
  Serial.begin(115200);
  delay(1500);

  Serial.println("\nW5500 Ethernet UDP Responder");

  SPI.begin(14, 12, 13, W5500_CS);
  Ethernet.init(W5500_CS);
  Ethernet.begin(mac, ip, dns, gateway, subnet);
  delay(500);

  Serial.print("Ethernet IP: ");
  Serial.println(Ethernet.localIP());

  if (udp.begin(UDP_PORT)) {
    Serial.println("UDP responder ready on port 4210");
  } else {
    Serial.println("UDP start failed!");
  }
}

void loop() {
  int packetSize = udp.parsePacket();

  if (packetSize > 0) {
    int len = udp.read(packetBuffer, sizeof(packetBuffer) - 1);

    if (len > 0) {
      packetBuffer[len] = '\0';
    }

    Serial.print("Received: ");
    Serial.println(packetBuffer);

    udp.beginPacket(udp.remoteIP(), udp.remotePort());
    udp.write((const uint8_t*)packetBuffer, len);
    udp.endPacket();

    Serial.println("Reply sent");
  }
}
