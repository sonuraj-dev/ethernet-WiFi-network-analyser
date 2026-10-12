# Repository Structure

- `src/main.cpp` — Ethernet ESP32 + W5500 UDP responder.
- `platformio.ini` — PlatformIO configuration for the Ethernet ESP32.
- `firmware/wifi_udp_responder/` — independent Wi-Fi ESP32 UDP responder project.
- `firmware/wifi_udp_responder/src/wifi_credentials.example.h` — safe credentials template.
- `dashboard/app.py` — Streamlit dashboard and user interface.
- `dashboard/network_tests.py` — UDP tests and RTT statistics.
- `dashboard/storage.py` — SQLite experiment persistence and CSV export.
- `dashboard/serial_console.py` — serial console support.
- `tests/` — automated Python tests.
- `docs/HARDWARE.md` — wiring and components.
- `docs/SOFTWARE.md` — software architecture.
- `docs/METRICS.md` — measurement definitions and limitations.
