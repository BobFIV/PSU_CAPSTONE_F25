#!/usr/bin/env python3
import serial
import struct
import threading
import time
import json
import requests
from flask import Flask, request
from werkzeug.serving import make_server

# =============================================================================
# CONFIG
# =============================================================================

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200

# --- OneM2M CSE ---
CSE_IP = "192.168.0.102"
BASE_URL = f"http://{CSE_IP}:8080/cse-in"

MAC_DEVICE_MAP = {
    "D2:29:B2:D0:66:FC": "SEEED_XIAO",
    "7C:DF:A1:FB:72:7D": "ESP32"
}

HEADERS = {
    "X-M2M-Origin": "CAdmin",
    "X-M2M-RI": f"req-{int(time.time()*1000)}",
    "X-M2M-RVI": "3",
    "Content-Type": "application/json;ty=4",
}

FLASK_PORT = 8000
SER = None
SER_LOCK = threading.Lock()
app = Flask(__name__)

# Uart Commands

def uart_send(cmd_str):
    """Thread-safe UART command sender."""
    with SER_LOCK:
        SER.write((cmd_str + "\n").encode("utf-8"))
    print(f"[UART TX] {cmd_str}")


def wl_add(mac):
    uart_send(f"WL_ADD {mac}")


def wl_del(mac):
    uart_send(f"WL_DEL {mac}")


def dc(mac):
    uart_send(f"DC {mac}")


# Flask inbox handler

@app.route("/notify", methods=["POST"])
def notify():
    """
    Receives commands from ACME → executes WL_ADD, WL_DEL, DC on UART.
    """
    try:
        data = request.get_json()
        print("\n📩 [INBOX] Notification:")
        print(json.dumps(data, indent=2))

        cin = data.get("m2m:sgn", {}).get("nev", {}).get("rep", {}).get("m2m:cin")
        if not cin:
            return ("", 204)

        con_raw = cin.get("con")
        if not con_raw:
            return ("", 204)

        if isinstance(con_raw, str):
            payload = json.loads(con_raw)
        else:
            payload = con_raw

        cmd = payload.get("cmd")
        mac = payload.get("mac")

        print(f"➡️ Command Received: {cmd} {mac}")

        if cmd == "WL_ADD":
            wl_add(mac)
        elif cmd == "WL_DEL":
            wl_del(mac)
        elif cmd == "DC":
            dc(mac)
        else:
            print(f"⚠ Unknown command: {cmd}")

        return ("", 204)

    except Exception as e:
        print(f"[ERROR] inbox: {e}")
        return ("", 500)


# =============================================================================
# SENSOR → CSE POSTING
# =============================================================================

def send_to_cse_temperature(device_addr, temp_c):

    
    device_ae = MAC_DEVICE_MAP.get(device_addr, device_addr)
    url = f"{BASE_URL}/{device_ae}/temperature"

    payload = {
        "m2m:cin": {
            "con": json.dumps({
                "device": device_addr,
                "tempC": temp_c
            })
        }
    }

    r = requests.post(url, headers=HEADERS, data=json.dumps(payload))
    if r.status_code in (200, 201):
        print(f"🌡️ Posted temp {temp_c:.2f}°C for {device_addr}")
    else:
        print(f"⚠️ Temp CIN failed {r.status_code}: {r.text}")


def post_scan_rssi(mac, rssi, connected):
    url = f"{BASE_URL}/gw-B/scan"

    payload = {
        "m2m:cin": {
            "con": json.dumps({
                "mac": mac,
                "rssi": rssi,
                "connected": bool(connected)
            })
        }
    }

    r = requests.post(url, headers=HEADERS, data=json.dumps(payload))
    if r.status_code in (200, 201):
        print(f"📡 Posted RSSI {rssi} dBm for {mac}")
    else:
        print(f"[WARN] RSSI CIN failed {r.status_code}: {r.text}")


# Packet parsers

def parse_sensor_payload(payload):
    device_addr = payload[:30].decode("utf-8", errors="ignore").strip("\x00").split()[0]
    print(f"\n📦 SENSOR from {device_addr}")

    idx = 30
    while idx < len(payload):
        field_id = payload[idx]
        idx += 1

        if field_id == 0x01:  # temperature
            raw = struct.unpack_from("<h", payload, idx)[0]
            idx += 2
            temp_c = raw / 100.0
            print(f"  Temp = {temp_c:.2f}°C")
            send_to_cse_temperature(device_addr, temp_c)

        elif field_id == 0x02:
            raw = struct.unpack_from("<I", payload, idx)[0]
            idx += 4
            press = raw / 10.0
            print(f"  Pressure = {press:.1f}")

        elif field_id == 0x03:
            raw = struct.unpack_from("<H", payload, idx)[0]
            idx += 2
            hum = raw / 100.0
            print(f"  Humidity = {hum:.2f}%")

        else:
            print(f"  ⚠ Unknown field {field_id}")
            break

    print("-------------------------------------------")


def parse_rssi_payload(payload):
    if len(payload) < 32:
        print("[WARN] RSSI payload too short")
        return

    mac = payload[:30].decode("utf-8", errors="ignore").strip("\x00")
    rssi = struct.unpack_from("<b", payload, 30)[0]
    connected = payload[31]

    print(f"\n🔎 RSSI Scan")
    print(f"  MAC: {mac}")
    print(f"  RSSI: {rssi}")
    print(f"  Connected: {connected}")

    post_scan_rssi(mac, rssi, connected)
    print("-------------------------------------------")


def parse_framed_packet(packet):
    if len(packet) < 5:
        return
    if packet[0] != 0xAA or packet[-1] != 0x55:
        return

    pkt_type = packet[1]
    payload = packet[3:-2]
    checksum = packet[-2]

    calc = 0
    for b in payload:
        calc ^= b
    if calc != checksum:
        print("[WARN] Bad checksum")
        return

    if pkt_type == 0x01:
        parse_sensor_payload(payload)
    elif pkt_type == 0x02:
        parse_rssi_payload(payload)
    else:
        print(f"[WARN] Unknown type 0x{pkt_type:02X}")


# UART read loop

def uart_read_loop():
    buffer = b""
    while True:
        data = SER.read(128)
        if not data:
            continue
        buffer += data

        while True:
            start = buffer.find(b"\xAA")
            end = buffer.find(b"\x55", start + 1)

            if start == -1 or end == -1:
                break

            pkt = buffer[start:end + 1]
            buffer = buffer[end + 1:]

            parse_framed_packet(pkt)



class FlaskThread(threading.Thread):
    def run(self):
        server = make_server("0.0.0.0", FLASK_PORT, app)
        server.serve_forever()

def main():
    global SER

    print(f"[INFO] Opening serial {SERIAL_PORT}...")
    SER = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.5)

    print("[INFO] Starting UART thread")
    threading.Thread(target=uart_read_loop, daemon=True).start()

    print(f"[INFO] Starting inbox server on port {FLASK_PORT}")
    FlaskThread().start()

    print("\n🚀 Gateway running. UART + Inbox active.\n")

    while True:
        time.sleep(999)


if __name__ == "__main__":
    main()