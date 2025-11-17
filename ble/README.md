# 🛰️ BLE IoT System — Seeed Peripheral & nRF7002 Central

This project implements a **Bluetooth Low Energy (BLE)** sensor network using the **Nordic nRF Connect SDK (Zephyr)** and **Visual Studio Code** with the **nRF Connect for VS Code** extension.

It includes two main applications:

- **Seeed Peripheral Application** — BLE sensor node that advertises and sends sensor data.
- **nRF7002 Central Application** — BLE central that connects to peripherals, collects their data, and forwards it via USB to a Raspberry Pi.

---

## 🧭 Overview

### 🟩 Seeed Peripheral
- Acts as a **BLE Peripheral** (GATT Server).  
- Advertises with a unique name (e.g. `SEEED_XX`).  
- Sends temperature, humidity, and pressure readings via **GATT notifications** every second.  
- Periodically broadcasts a **secondary “test” advertisement** (`SEEED_TEST`) that contains its MAC address for proximity detection.  
- RSSI data is used in higher decision making regarding handover.

### 🟦 nRF7002 Central
- Acts as a **BLE Central** (GATT Client).  
- Scans for and connects to multiple BLE peripheral devices simultaneously.  
- Subscribes to GATT notifications for each connected node.  
- Continuously scans for `SEEED_TEST` beacons to measure RSSI (signal strength).  
- Sends all received sensor data and RSSI reports to a **Raspberry Pi** via **USB CDC (virtual COM port)**.  
- Packets are wrapped with **start/end markers** and a **checksum** for robust data framing.

---

## 🧩 Project Structure
```
BLE_Project/
│
├── Seeed/
| ├── boards/
| | ├── xiao_nrf54l15_nrf54l15_cpuapp.overlay
│ ├── inc/
| | ├── mlx90614.h # mlx90614 sensor header file
│ │ ├── sense_collect.h # sense_collect header file
│ ├── src/
│ │ ├── main.c # BLE advertising, connection, and sensor logic
| | ├── mlx90614.c # mlx90614 sensor handler
│ │ ├── sense_collect.c # Sensor reading and GATT notification handler
│ ├── CMakeLists.txt
| ├── Kconfig
│ └── prj.conf
│
├── central_multilink/
| ├── boards/
| | ├── nrf7002dk_nrf5340_cpuapp.overlay
│ ├── inc/
| | ├── main.h # header file for full logic implementation
│ ├── src/
│ │ ├── central_multilink.c # BLE connection and GATT subscription logic
│ │ ├── led_control.c # LED management
│ │ ├── listing.c # Scanning for beacon advertisements
│ │ ├── main.c # Central initialization and main loop
│ │ ├── uart_comm.c # USB CDC data framing and transmission
│ ├── CMakeLists.txt
| ├── Kconfig
│ └── prj.conf
│
├── peripheral_extra
| └── esp32.ino
|
└── uart.py # Raspberry Pi receiver script
```

---

## ⚙️ Prerequisites

1. **nRF Connect SDK v3.1.0 or newer**  
   [Install Guide → Nordic Docs](https://developer.nordicsemi.com/nRF_Connect_SDK/doc/latest/nrf/getting_started/install.html)

2. **VS Code + Nordic nRF Connect Extension Pack**

3. **Board connections**
   - **Seeed Peripheral Board** → USB to PC  
   - **nRF7002 DK (Central)** → Connect **nRF5340 USB** port (for USB CDC communication)  
   - **Raspberry Pi** → Connected via USB to nRF5340 USB port

---

## 🧱 Building and Flashing

### 🟩 Seeed Peripheral
1. Connect the seeed via USB
2. Open the `seeed/` folder in VS Code.  
3. In the **nRF Connect** panel:
   - Click "Add build configuration" in the applications tab.
   - Select the xiao_nrf54l15/nrf54l15/cpuapp Board Target. (Not included in SDK, must be obtained from seeed site)
   - Choose `prj.conf` as configuration.
   - Select xiao_nrf54l15_nrf54l15_cpuapp.overlay for the Base Devicetree overlay.  
4. Click **Generate and Build** at the bottom of the configuration.
5. Run "west flash" from the seeed folder directory.  
6. Once flashed, the board will start BLE advertising automatically.  

---

### 🟦 nRF7002 Central
1. Connect the nrf7002 via the MCU USB
2. Open the `central_multilink/` folder in VS Code.  
3. In the **nRF Connect** panel:
   - Click "Add build configuration" in the applications tab.
   - Select the nrf7002dk/nrf5340/cpuapp Board target
   - Choose `prj.conf` as configuration.
   - Select nrf7002dk_nrf5340_cpuapp.overlay for the Base Devicetree overlay. 
4. Click **Generate and Build** at the bottom of the configuration.
5. Click **Flash** from the Actions tab.  
6. Open a terminal on the MCU USB COM port for vis.  
7. Once Flashed the board will start BLE scanning automatically.

---

## 🧾 USB Data Packet Format

All data sent from the **nRF7002 DK** to the **Raspberry Pi** is framed for integrity.

| Byte(s) | Description |
|----------|-------------|
| `0xAA` | Start byte |
| **Type** | `0x01` = Sensor data, `0x02` = RSSI beacon |
| **Payload** | Sensor or RSSI data |
| **Checksum** | XOR of all payload bytes |
| `0x55` | End byte |

Each packet ≤ 64 bytes (USB CDC frame size).

---

## 🧠 Raspberry Pi Receiver (`uart.py`)

The `uart.py` script:
- Opens the USB serial port (`/dev/ttyACM0`, or `COMx` on Windows).  
- Reads and parses packets using start (`0xAA`) and end (`0x55`) markers.  
- Verifies checksum integrity.  
- Distinguishes between:
  - **Type 0x01** → Sensor data packets  
  - **Type 0x02** → RSSI beacon packets  
- Prints or logs the parsed results.  

Run it with:

```bash
python3 uart.py

```
