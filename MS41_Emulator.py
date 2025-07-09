import serial
import time
import struct

PORT = "/tmp/tty.ms41emu"
coolant_temp = 85.0
battery_voltage = 13.5

# Map of direct memory addresses and functions that return dynamic values
DIRECT_MEMORY_MAP = {
    0xDA5A: lambda: int((coolant_temp + 48) / 0.747),  # Coolant temp
}

# Group ID -> handler function

def handle_group_0B():
    raw_voltage = int(battery_voltage / 0.1019)
    hi = (raw_voltage >> 8) & 0xFF
    lo = raw_voltage & 0xFF

    payload = [0x6A, 0x68, 0xF0, 0xA0] + [0x00] * 16
    payload += [hi, lo]
    payload += [0x00] * (32 - len(payload))  # pad to 32 bytes total
    return bytes(payload)

GROUP_HANDLERS = {
    0x0B: handle_group_0B
}

def parse_request(data):
    # Basic structure check
    if len(data) < 8:
        return None, None
    length = data[5]
    if length == 0x04:
         return "ecuid", data[0]
    if length == 0x02:
        # Direct memory access
        addr = (data[6] << 8) | data[7]
        return "direct", addr
    elif length == 0x05 and data[6] in GROUP_HANDLERS:
        return "group", data[6]
    return None, None

def run_fake_ecu():
    global coolant_temp, battery_voltage

    ser = serial.Serial(PORT, baudrate=9600, bytesize=8,
                        parity=serial.PARITY_EVEN, stopbits=1,
                        timeout=1)

    print("✅ MS41.2 Emulator running on", PORT)

    while True:
        request = ser.read(16)
        if not request:
            continue

        kind, key = parse_request(request)
        def build_ecu_id_response(ecu_id_str):
            ecu_bytes = [ord(c) for c in ecu_id_str]
            frame = [0x6A, 0x68, 0xF0, 0xA0, len(ecu_bytes)] + ecu_bytes
            checksum = 0
            for b in frame:
                checksum ^= b
            return bytes(frame + [checksum])

        if kind == "direct" and key in DIRECT_MEMORY_MAP:
            raw_val = DIRECT_MEMORY_MAP[key]()
            response = bytes([0x6A, 0x68, 0xF0, 0xA0, 0x01, raw_val])
            ser.write(response)
            print(f"📤 Coolant → {raw_val} from 0x{key:04X}")

            coolant_temp += 0.3
            if coolant_temp > 100:
                coolant_temp = 85.0
        elif kind == "ecuid":
            response = build_ecu_id_response("1429764")
            ser.write(response)
        elif kind == "group" and key in GROUP_HANDLERS:
            response = GROUP_HANDLERS[key]()
            ser.write(response)
            print(f"📤 Voltage Group 0x{key:02X} → {battery_voltage:.2f}V")

            battery_voltage += 0.05
            if battery_voltage > 14.4:
                battery_voltage = 13.5

        else:
            print("⚠️ Unknown request:", request)


if __name__ == "__main__":
    run_fake_ecu()
