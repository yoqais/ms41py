import serial
import time

PORT = "/tmp/tty.ms41emu"  # change to your virtual port
coolant_temp = 85.0
battery_voltage = 13.5

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

        # Respond to Coolant Temp (0xDA5A)
        if request[6] == 0xDA and request[7] == 0x5A:
            raw = int((coolant_temp + 48) / 0.747)
            response = bytes([0x6A, 0x68, 0xF0, 0xA0, 0x01, raw])
            ser.write(response)

            # Increment coolant temp for demo
            coolant_temp += 0.3
            if coolant_temp > 100:
                coolant_temp = 85.0

        # Respond to Group 0x0B (battery voltage)
        elif request[5] == 0x05 and request[6] == 0x0B:
            raw_voltage = int(battery_voltage / 0.1019)
            hi = (raw_voltage >> 8) & 0xFF
            lo = raw_voltage & 0xFF

            # Send fake payload with voltage at offset 7
            payload = [0x6A, 0x68, 0xF0, 0xA0] + [0x00]*3 + [hi, lo] + [0x00]*12
            ser.write(bytes(payload))

            # Increment battery voltage for demo
            battery_voltage += 0.05
            if battery_voltage > 14.4:
                battery_voltage = 13.5

        else:
            print("⚠️ Unknown request:", request.hex())

if __name__ == "__main__":
    run_fake_ecu()
