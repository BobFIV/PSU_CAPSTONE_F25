#!/usr/bin/env python3
import requests
import json
import random
import time
import threading
from colorama import Fore, Style, init

# ==========================
# Configuration
# ==========================
init(autoreset=True)

GW_A = "192.168.0.100"
GW_B = "192.168.0.101"
CONTAINER = "temperature"

# List of simulated devices
DEVICES = ["ESP32", "SEEED_XIAO"]

# Assign each device a distinct color for readability
DEVICE_COLORS = {
    "ESP32_1": Fore.CYAN,
    "ESP32_2": Fore.MAGENTA,
    "ESP32_3": Fore.YELLOW,
    "ESP32_4": Fore.GREEN,
}


# ==========================
# Utility
# ==========================
def log(device, message, emoji=""):
    """Print a color-coded log for a given device."""
    color = DEVICE_COLORS.get(device, Fore.WHITE)
    print(f"{color}{emoji} [{device}] {message}{Style.RESET_ALL}")


# ==========================
# oneM2M Helper Functions
# ==========================
def create_ae(gw_ip, ae_name):
    origin = f"C_{ae_name}"
    data = {
        "m2m:ae": {
            "rn": ae_name,
            "api": f"N.{ae_name.lower()}",
            "rr": True,
            "srv": ["3"],
            "lbl": [f"{ae_name} Device"],
            "at": ["/id-in"],
            "aa": ["lbl", "rn", "api"]
        }
    }

    headers = {
        "X-M2M-Origin": origin,
        "X-M2M-RI": f"reqAE_{random.randint(1000,9999)}",
        "X-M2M-RVI": "3",
        "X-M2M-TY": "2",
        "Content-Type": "application/json;ty=2",
        "Accept": "application/json"
    }

    try:
        r = requests.post(f"http://{gw_ip}:8080/cse-mn", headers=headers, json=data, timeout=5)
        log(ae_name, f"Created AE on {gw_ip} → {r.status_code}", "📦")
    except Exception as e:
        log(ae_name, f"⚠️ Error creating AE on {gw_ip}: {e}")


def create_container(gw_ip, ae_name, container_name):
    data = {
        "m2m:cnt": {
            "rn": container_name,
            "lbl": [f"data:{container_name}", "type:sensor"],
            "at": ["/id-in"],
            "aa": ["lbl", "rn"]
        }
    }

    headers = {
        "X-M2M-Origin": "CAdmin",
        "X-M2M-RI": f"reqCNT_{random.randint(1000,9999)}",
        "X-M2M-RVI": "3",
        "X-M2M-TY": "3",
        "Content-Type": "application/json;ty=3",
        "Accept": "application/json"
    }

    try:
        r = requests.post(f"http://{gw_ip}:8080/cse-mn/{ae_name}", headers=headers, json=data, timeout=5)
        log(ae_name, f"Created container '{container_name}' on {gw_ip} → {r.status_code}", "📂")
    except Exception as e:
        log(ae_name, f"⚠️ Error creating container on {gw_ip}: {e}")


def delete_ae(gw_ip, ae_name):
    headers = {
        "X-M2M-Origin": "CAdmin",
        "X-M2M-RI": f"reqDEL_{random.randint(1000,9999)}",
        "X-M2M-RVI": "3",
        "Accept": "application/json"
    }
    try:
        r = requests.delete(f"http://{gw_ip}:8080/cse-mn/{ae_name}", headers=headers, timeout=5)
        log(ae_name, f"Deleted AE from {gw_ip} → {r.status_code}", "🗑️")
    except Exception as e:
        log(ae_name, f"⚠️ Error deleting AE on {gw_ip}: {e}")


def post_temperature(gw_ip, ae_name, tempC):
    data = {
        "m2m:cin": {
            "con": json.dumps({"tempC": tempC}),
            "at": ["/id-in"],
            "aa": ["con"]
        }
    }

    headers = {
        "X-M2M-Origin": "CAdmin",
        "X-M2M-RI": f"reqCIN_{random.randint(1000,9999)}",
        "X-M2M-RVI": "3",
        "X-M2M-TY": "4",
        "Content-Type": "application/json;ty=4",
        "Accept": "application/json"
    }

    try:
        r = requests.post(f"http://{gw_ip}:8080/cse-mn/{ae_name}/{CONTAINER}", headers=headers, json=data, timeout=5)
        log(ae_name, f"Temp {tempC:.1f}°C → {gw_ip} ({r.status_code})", "🌡️")
    except Exception as e:
        log(ae_name, f"⚠️ Error posting CIN to {gw_ip}: {e}")


# ==========================
# RSSI + Handover Logic
# ==========================
def simulate_rssi():
    """Generate random RSSI values for Gateway A and B."""
    rssi_a = random.randint(-80, -45)
    rssi_b = random.randint(-80, -45)
    return rssi_a, rssi_b


def handover_if_needed(device, current_gw, rssi_a, rssi_b):
    """Switch gateways if signal difference > 5 dB."""
    if current_gw == GW_A and rssi_b - rssi_a > 5:
        log(device, "Handover → B (stronger signal)", "🔁")
        delete_ae(GW_A, device)
        setup_device(GW_B, device)
        return GW_B
    elif current_gw == GW_B and rssi_a - rssi_b > 5:
        log(device, "Handover → A (stronger signal)", "🔁")
        delete_ae(GW_B, device)
        setup_device(GW_A, device)
        return GW_A
    return current_gw


def setup_device(gw_ip, device):
    create_ae(gw_ip, device)
    time.sleep(1)
    create_container(gw_ip, device, CONTAINER)
    log(device, f"Device ready on {gw_ip}", "✅")


# ==========================
# Device Simulation Thread
# ==========================
def device_thread(device_name):
    current_gw = random.choice([GW_A, GW_B])  # start randomly
    setup_device(current_gw, device_name)

    while True:
        rssi_a, rssi_b = simulate_rssi()
        log(device_name, f"RSSI_A: {rssi_a}, RSSI_B: {rssi_b}", "📡")

        current_gw = handover_if_needed(device_name, current_gw, rssi_a, rssi_b)

        tempC = random.uniform(20.0, 26.0)
        post_temperature(current_gw, device_name, tempC)
        time.sleep(random.randint(10, 20))  # random interval


# ==========================
# Main
# ==========================
def main():
    print(f"{Fore.WHITE}🚀 Starting Multi-Device RSSI + Handover Simulation\n{Style.RESET_ALL}")
    threads = []

    for dev in DEVICES:
        t = threading.Thread(target=device_thread, args=(dev,), daemon=True)
        threads.append(t)
        t.start()
        time.sleep(1)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}🛑 Simulation stopped.{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
