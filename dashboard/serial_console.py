import time
import serial
from datetime import datetime

def read_serial(port, baud=115200, seconds=1.0):
    """Open a serial port briefly and return lines. Closes the port afterward."""
    output = []
    with serial.Serial(port, baudrate=baud, timeout=0.15) as ser:
        deadline = time.monotonic() + max(0.2, min(seconds, 4.0))
        while time.monotonic() < deadline:
            raw = ser.readline()
            if raw:
                stamp = datetime.now().astimezone().isoformat(timespec="milliseconds")
                output.append(f"[{stamp}] {raw.decode(errors='replace').rstrip()}")
    return output
