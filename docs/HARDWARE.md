# Hardware Setup

## Bill of materials

The prototype uses:
- 2 ESP32 DevKit-style development boards
- 1 W5500 Ethernet module
- USB data cables
- Breadboard and jumper wires
- Laptop with Ethernet and Wi-Fi connectivity

Record the exact board/module variants and purchase links here before the final release. Prices depend on supplier and date; no fixed price is claimed.

## Ethernet ESP32 wiring

| W5500 | ESP32 |
|---|---|
| SCLK | GPIO 14 |
| MISO | GPIO 12 |
| MOSI | GPIO 13 |
| CS | GPIO 15 |
| RST | GPIO 5 |
| GND | GND |
| VCC | 3.3 V for the current setup |

The W5500 communicates with the ESP32 over SPI. The Ethernet cable connects the module to the laptop's Ethernet interface.

Verify the board pinout and module voltage before powering the circuit.

## Wi-Fi ESP32

The second ESP32 connects to the configured Wi-Fi network and listens for UDP echo requests on port 4210. Its SSID and password must be configured locally and must not be committed to the repository.

## Development network

The original development setup used:
- Laptop Ethernet: `172.16.15.42/24`
- Ethernet ESP32: `172.16.15.50`
- Laptop Wi-Fi: `10.218.72.180/24`
- Wi-Fi ESP32: `10.218.72.197`

These addresses are documentation examples, not universal defaults. Configure the dashboard and devices for your own network.
