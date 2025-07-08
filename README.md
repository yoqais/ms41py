
# MS41.2 Live Display (Coolant + Battery Voltage)

A lightweight Python project that communicates with the BMW MS41.2 ECU over K-Line (via K+DCAN cable) to display **real-time engine data** on an OLED screen using a Raspberry Pi.

---

## 🧰 What It Does

- 📟 Displays **Coolant Temperature** and **Battery Voltage**
- 🧠 Uses official **MS41.2 definitions** for accurate address mapping
- 🔄 Uses **DS2/KWP protocol** to talk to the ECU
- 🪛 Supports simulation via `socat` and a Python-based **FakeECU**
- ⚡ Auto-start ready via `systemd`

---

## 📦 Requirements

### ✅ Hardware
- Raspberry Pi (any model with USB and I2C)
- K+DCAN USB cable
- SSD1306 OLED Display (I2C, 128x32)
- BMW with MS41.2 ECU (e.g. E36 M3)

### ✅ Software
- Python 3
- Required Python libraries:
  ```bash
  sudo apt install i2c-tools python3-pip python3-venv libjpeg-dev zlib1g-dev
  pip3 install adafruit-circuitpython-ssd1306 pillow pyserial
  ```

---

## 🔌 Hardware Setup

| Component   | Connect To             |
|-------------|------------------------|
| OLED VCC    | Pi 3.3V                |
| OLED GND    | Pi GND                 |
| OLED SCL    | Pi SCL (GPIO 3)        |
| OLED SDA    | Pi SDA (GPIO 2)        |
| K+DCAN USB  | Any USB port on Pi     |

---

## 🚗 Usage (Real ECU)

```bash
python3 coolant_logger.py
```

The script will wait for `/dev/ttyUSB0` to appear (K+DCAN cable). Once detected, it begins polling:
- Coolant temp from address `0xDA5A` (direct)
- Battery voltage from group `0x0B`, offset `0x07` (grouped)

---

## 🧪 Usage (Simulated ECU)

You can test everything without hardware using `socat`:

### 1. Run Bash Script:
```bash
./start_kline.sh
```

You’ll see:
```
pi@raspberrypi:~/ms41py $ ./start_kline.sh
socat: no process found
Terminated previous Socat opps
Virtual serial ports created:
  Logger => /tmp/tty.ms41logger
  Emulator => /tmp/tty.ms41emu
✅ MS41.2 Emulator running on /tmp/tty.ms41emu
```

### 2. Run logger:
```bash
python3 coolant_logger.py
```
Edit `PORT = "/dev/pts/1"` inside `coolant_logger.py`.

---

## ⚠️ Direct vs Grouped DS2 Requests

Not all ECU parameters can be requested the same way.

### 🔹 Direct Address Access (e.g. `0xDA5A`)
These can be read with basic DS2 memory polling:
- Format: `[0x12, 0x02, hi, lo]`
- Coolant temp, RPM, IAT often fall here

📖 Found in XML like:
```xml
<address>0xDA5A</address>
```

---

### 🔸 Grouped Value Access (e.g. `.V_Batt`)
Some parameters (like battery voltage) live in grouped datasets:
- Format: `[0x12, 0x05, group, 0x03, 0x1F]`
- The ECU returns multiple values
- You extract the value using its byte **offset**, **length**, and **expression**

📖 Found in XML like:
```xml
<address>0x00000007</address>
<group="0x0B" subgroup="0x01" />
<storagetype="uint16" expr="x*0.1019" />
```

### 🔍 How to Know Which Is Which?
- ✅ If the address starts with `0xDAxx`, it’s a **direct memory variable**
- ✅ If it uses `<group>` and an internal offset, it’s a **grouped value**
- ❌ Don’t send direct DS2 commands for grouped values — the ECU won't respond correctly

🧠 Always double check the **logger/ECU definition XML files** you're working with!

---

## 🛠 Systemd Autostart (Optional)

```bash
sudo nano /etc/systemd/system/coolant.service
```

```ini
[Unit]
Description=Coolant Logger
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/ms41py/coolant_logger.py
Restart=on-failure
User=pi
WorkingDirectory=/home/pi/ms41py

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reexec
sudo systemctl enable coolant.service
sudo systemctl start coolant.service
```

---

## 🧾 License

MIT License — free to use, modify, and share.  
Credits to MS41 logger community for XML defs and protocol research.

---

## 🧠 Future Plans

- Add RPM, TPS, IAT display support  
- Use ST7701 round display  
- Add WiFi broadcasting (optional web dashboard)  
- Add data logging (CSV)

---

> Built for real-time diagnostics and clean, distraction-free engine monitoring. For any questions, email: qaisdanish6@gmail.com
