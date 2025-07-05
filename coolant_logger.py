import serial
import time
from datetime import datetime
import os

PORT = '/dev/ttyUSB0'
ADDRESS = 0xDA5A

def build_request(address):
    hi = (address >> 8) & 0xFF
    lo = address & 0xFF
    cmd = [0x68, 0x6A, 0xF0, 0x58, 0x12, 0x02, hi, lo]
    checksum = sum(cmd) & 0xFF
    return bytearray(cmd + [checksum])

def parse_response(response):
    if len(response) < 6:
        return None
    raw = response[5]
    return raw * 0.747 - 48

def wait_for_serial(port):
    print(f"Waiting for {port} to become available...")
    while True:
        if os.path.exists(port):
            try:
                ser = serial.Serial(port, baudrate=9600, bytesize=8,
                                    parity=serial.PARITY_EVEN, stopbits=1,
                                    timeout=1)
                print("Connected to MS41 ECU via K-Line")
                return ser
            except serial.SerialException:
                pass  # exists but not ready yet
        time.sleep(2)

def main():
    ser = wait_for_serial(PORT)

    try:
        while True:
            req = build_request(ADDRESS)
            ser.write(req)
            time.sleep(0.1)

            resp = ser.read(16)
            now = datetime.now().strftime('%H:%M:%S')

            if len(resp) >= 6:
                temp = parse_response(resp)
                print(f"[{now}] Coolant Temp: {temp:.2f} °C")
            else:
                print(f"[{now}] No response from ECU")

            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped by user.")

if __name__ == "__main__":
    main()
