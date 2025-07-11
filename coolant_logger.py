import serial
import time
import os
import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont

# ────────────── Constants ──────────────
PORT = "/tmp/tty.ms41logger"
COOLANT_ADDR = 0xDA5A
GROUP_ID = 0x0B
SUBGROUP_ID = 0x01
ECU_ID_CMD = [0x12, 0x04, 0x00, 0x16]

# ECU ID → .V_Batt offset
BATTERY_OFFSETS = {
    "default": 7,
    "1429764": 20,
    "1430844": 20,
    "7526753": 20,
    "7500255": 20,
    "7511570": 22,
    "7519308": 22,
    "7545150": 22,
    "7551615": 22,
    "1141414": 5
}

# ────────────── DS2 Helpers ──────────────
def xor_checksum(data):
    checksum = 0
    for b in data:
        checksum ^= b
    return checksum

def build_direct_request(address):
    hi = (address >> 8) & 0xFF
    lo = address & 0xFF
    cmd = [0x68, 0x6A, 0xF0, 0x58, 0x12, 0x02, hi, lo]
    return bytearray(cmd + [xor_checksum(cmd)])

def build_group_request(group=0x0B, subgroup=0x01):
    cmd = [0x68, 0x6A, 0xF0, 0x58, 0x12, 0x05, group, 0x03, 0x1F]
    return bytearray(cmd + [xor_checksum(cmd)])

def build_ecu_id_request():
    cmd = [0x68, 0x6A, 0xF0, 0x58] + ECU_ID_CMD
    return bytearray(cmd + [xor_checksum(cmd)])
# ────────────── Response Parsers ──────────────
def parse_coolant(response):
    if len(response) < 6: return None
    return response[5] * 0.747 - 48

def parse_voltage(response, offset):
    if len(response) < offset + 2: return None
    raw = (response[offset] << 8) | response[offset + 1]
    return raw * 0.1019

def parse_ecu_id(response):
    if len(response) < 12: return None
    return bytes(response[5:12]).decode(errors="ignore")

# ────────────── OLED Setup ──────────────
def setup_oled():
    i2c = busio.I2C(board.SCL, board.SDA)
    oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
    oled.fill(0)
    oled.show()
    return oled

def draw_text(oled, line1, line2, font):
    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), line1, font=font, fill=255)
    draw.text((0, 16), line2, font=font, fill=255)
    oled.image(image)
    oled.show()

# ────────────── Serial Wait ──────────────
def wait_for_serial(port, oled, font):
    draw_text(oled, "Waiting for", "K-Line...", font)
    while True:
        if os.path.exists(port):
            try:
                ser = serial.Serial(port, baudrate=9600, bytesize=8,
                                    parity=serial.PARITY_EVEN, stopbits=1,
                                    timeout=1)
                draw_text(oled, "Connected to", "MS41 ECU", font)
                time.sleep(1)
                return ser
            except serial.SerialException:
                pass
        time.sleep(1)

# ────────────── Main ──────────────
def main():
    oled = setup_oled()
    font = ImageFont.load_default()
    ser = wait_for_serial(PORT, oled, font)

    # Get ECU ID
    ser.write(build_ecu_id_request())
    time.sleep(0.1)
    ecu_id_resp = ser.read(32)
    ecu_id = parse_ecu_id(ecu_id_resp)

    if not ecu_id:
        ecu_id = "default"
    draw_text(oled, "ECU ID:", ecu_id, font)
    time.sleep(1)

    voltage_offset = BATTERY_OFFSETS.get(ecu_id, BATTERY_OFFSETS["default"])
    print(voltage_offset)

    try:
        while True:
            try:
                ser.write(build_direct_request(COOLANT_ADDR))
                time.sleep(0.1)
                coolant = parse_coolant(ser.read(16))

                ser.write(build_group_request(GROUP_ID, SUBGROUP_ID))
                time.sleep(0.1)
                voltage = parse_voltage(ser.read(32), voltage_offset)

                if coolant is not None and voltage is not None:
                    line1 = f"Coolant: {coolant:.1f} C"
                    line2 = f"Voltage: {voltage:.1f} V"
                    draw_text(oled, line1, line2, font)
                else:
                    draw_text(oled, "Reading error", "", font)

            except serial.SerialException:
                draw_text(oled, "Serial error", "Retrying...", font)
                ser.close()
                ser = wait_for_serial(PORT, oled, font)

            time.sleep(1)

    except KeyboardInterrupt:
        draw_text(oled, "Stopped by user", "", font)
        time.sleep(2)

if __name__ == "__main__":
    main()
