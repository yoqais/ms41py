import serial
import time
import os
import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont

# K-Line Port
PORT = "/tmp/tty.ms41logger"

# Addresses
COOLANT_ADDR = 0xDA5A
GROUP_ID = 0x0B
SUBGROUP_ID = 0x01

# ────────────── DS2 Request Builders ──────────────

def build_direct_request(address):
    hi = (address >> 8) & 0xFF
    lo = address & 0xFF
    cmd = [0x68, 0x6A, 0xF0, 0x58, 0x12, 0x02, hi, lo]
    return bytearray(cmd + [sum(cmd) & 0xFF])

def build_group_request(group=0x0B, subgroup=0x01):
    cmd = [0x68, 0x6A, 0xF0, 0x58, 0x12, 0x05, group, 0x03, 0x1F]
    return bytearray(cmd + [sum(cmd) & 0xFF])

# ────────────── Parsers ──────────────

def parse_coolant(response):
    if len(response) < 6: return None
    return response[5] * 0.747 - 48

def parse_voltage_from_group(response):
    if len(response) < 10: return None
    raw = (response[7] << 8) | response[8]
    return raw * 0.1019

# ────────────── OLED + Icons ──────────────

def setup_oled():
    i2c = busio.I2C(board.SCL, board.SDA)
    oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
    oled.fill(0)
    oled.show()
    return oled

def draw_with_icons(oled, coolant, voltage, font, bat_icon, clt_icon):
    image = Image.new("1", (128, 32))
    draw = ImageDraw.Draw(image)

    # Paste coolant icon left and text under it
    image.paste(clt_icon, (0, -5))
    draw.text((2, 22), f"{coolant:.1f}C", font=font, fill=255)

    # Paste battery icon right and text under it
    image.paste(bat_icon, (96, -3))
    draw.text((98, 22), f"{voltage:.1f}V", font=font, fill=255)

    oled.image(image)
    oled.show()

# ────────────── Serial Port Wait ──────────────

def wait_for_serial(port, oled, font):
    draw_text(oled, "Waiting for", "K-Line...", font)
    while True:
        if os.path.exists(port):
            try:
                ser = serial.Serial(port, baudrate=9600, bytesize=8,
                                    parity=serial.PARITY_EVEN, stopbits=1, timeout=1)
                draw_text(oled, "Connected to", "MS41 ECU", font)
                time.sleep(1)
                return ser
            except serial.SerialException:
                pass
        time.sleep(2)

def draw_text(oled, line1, line2, font):
    image = Image.new("1", (128, 32))
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), line1, font=font, fill=255)
    draw.text((0, 16), line2, font=font, fill=255)
    oled.image(image)
    oled.show()

# ────────────── MAIN ──────────────

def main():
    oled = setup_oled()
    font = ImageFont.load_default()
    ser = wait_for_serial(PORT, oled, font)

    bat_icon = Image.open("battery_icon_128x32.bmp").resize((32, 32)).convert("1")
    clt_icon = Image.open("coolant_icon_128x32.bmp").resize((32, 32)).convert("1")

    try:
        while True:
            try:
                # Coolant temp (direct)
                ser.write(build_direct_request(COOLANT_ADDR))
                time.sleep(0.1)
                coolant = parse_coolant(ser.read(16))

                # Battery voltage (grouped)
                ser.write(build_group_request(GROUP_ID, SUBGROUP_ID))
                time.sleep(0.1)
                voltage = parse_voltage_from_group(ser.read(32))

                if coolant is not None and voltage is not None:
                    draw_with_icons(oled, coolant, voltage, font, bat_icon, clt_icon)
                else:
                    draw_text(oled, "Reading error", "", font)

            except serial.SerialException as e:
                draw_text(oled, "Serial Error", "Reconnecting...", font)
                time.sleep(2)
                ser.close()
                ser = wait_for_serial(PORT, oled, font)  # retry wait loop

            time.sleep(1)

    except KeyboardInterrupt:
        draw_text(oled, "Stopped by user", "", font)
        time.sleep(2)

if __name__ == "__main__":
    main()

