# Software Architecture

## Firmware

The Ethernet ESP32 uses PlatformIO, the Arduino framework, SPI and the Ethernet library to initialize the W5500 and provide a UDP echo responder on port 4210.

The Wi-Fi ESP32 connects to a configured wireless network and echoes valid UDP payloads on port 4210.

## Dashboard

The Streamlit application provides:
- Live test controls
- UDP test execution
- Live packet progress and latency charts
- Endpoint comparison
- SQLite experiment persistence
- Packet history and CSV export
- Serial-console access
- Firmware and Git information

## Python modules

- `dashboard/app.py`: dashboard and user interface
- `dashboard/network_tests.py`: UDP probes, measurements and statistics
- `dashboard/storage.py`: SQLite persistence and export
- `dashboard/serial_console.py`: bounded serial log capture
- `requirements-dashboard.txt`: Python dependencies

## Data handling

The dashboard stores experiments locally. Generated databases, raw results, logs and local configuration should remain untracked unless explicitly sanitized for a reproducible example.
