# Wi-Fi UDP Responder (ESP32)

This is a standalone PlatformIO project for the second ESP32. It joins a Wi-Fi network and echoes UDP datagrams on port 4210 for the Network Analyser dashboard.

## Configure credentials

From this directory:

```bash
cp src/wifi_credentials.example.h src/wifi_credentials.h
```

Edit `src/wifi_credentials.h` locally and set your Wi-Fi SSID and password. The real credentials file is ignored by Git.

## Build and upload

```bash
pio run
pio run -t upload --upload-port /dev/ttyUSB0
pio device monitor --port /dev/ttyUSB0 --baud 115200
```

Adjust the serial port to match the Wi-Fi ESP32. Close any serial monitor before opening the same port in another application.

On startup, the serial monitor prints the assigned IP address and confirms whether UDP port 4210 started. Configure the dashboard with that IP address.

## Protocol

The responder echoes the received UDP payload to the sender's source IP address and source port. This supports round-trip latency and packet-loss measurements. It does not by itself measure one-way latency or physical-layer error counters.
