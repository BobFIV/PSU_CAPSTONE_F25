#!/usr/bin/env python3
import requests
import json
import random
import time

# ==========================
# Configuration
# ==========================
GW_A = "192.168.0.100"
GW_B = "192.168.0.101"
DEVICE_NAME = "ESP32"
CONTAINER = "temperature"

# ==========================
# oneM2M Helper Functions
# ==========================
def create_ae(gw_ip, ae_name):
    """Register an AE on the given gateway."""
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
        "X-M2M-Origin": "CSeeed",
        "X-M2M-RI": f"reqAE_{random.randint(1000,9999)}",
        "X-M2M-RVI": "3",
        "X-M2M-TY": "2",
        "Content-Type": "application/json;ty=2",
        "Accept": "application/json"
    }

    try:
        r = requests.post(f"http://{gw_ip}:8080/cse-mn", headers=headers, json=data, timeout=5)
        print(f"📦 Created AE {ae_name} on {gw_ip} → {r.status_code}")
        print(r.text)
    except Exception as e:
        print(f"⚠️ Error creating AE on {gw_ip}: {e}")


def create_container(gw_ip, ae_name, container_name):
    """Create a container under the AE for sensor data."""
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
        print(f"📂 Created container {container_name} on {gw_ip} → {r.status_code}")
        print(r.text)
    except Exception as e:
        print(f"⚠️ Error creating container on {gw_ip}: {e}")


def delete_ae(gw_ip, ae_name):
    """Remove the AE from a gateway when switching connections."""
    headers = {
        "X-M2M-Origin": "CAdmin",
        "X-M2M-RI": f"reqDEL_{random.randint(1000,9999)}",
        "X-M2M-RVI": "3",
        "Accept": "application/json"
    }
    try:
        r = requests.delete(f"http://{gw_ip}:8080/cse-mn/{ae_name}", headers=headers, timeout=5)
        print(f"🗑️ Deleted AE {ae_name} from {gw_ip} → {r.status_code}")
    except Exception as e:
        print(f"⚠️ Error deleting AE on {gw_ip}: {e}")


def post_temperature(gw_ip, ae_name, tempC):
    """Post a new temperature reading as a CIN."""
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
        print(f"🌡️ Temp {tempC:.1f}°C sent via {gw_ip} → {r.status_code}")
        print(r.text)
    except Exception as e:
        print(f"⚠️ Error posting CIN to {gw_ip}: {e}")


# ==========================
# RSSI Simulation + Handover
# ==========================
def simulate_rssi():
    """Generate random RSSI values for Gateway A and B."""
    rssi_a = random.randint(-80, -45)
    rssi_b = random.randint(-80, -45)
    return rssi_a, rssi_b


def handover_if_needed(current_gw, rssi_a, rssi_b):
    """Switch gateways if one signal is significantly stronger."""
    if current_gw == GW_A and rssi_b - rssi_a > 5:
        print("🔁 Handover → B (stronger signal)")
        delete_ae(GW_A, DEVICE_NAME)
        setup_device(GW_B)
        return GW_B
    elif current_gw == GW_B and rssi_a - rssi_b > 5:
        print("🔁 Handover → A (stronger signal)")
        delete_ae(GW_B, DEVICE_NAME)
        setup_device(GW_A)
        return GW_A
    return current_gw


def setup_device(gw_ip):
    """Initialize the AE and its data container on a gateway."""
    create_ae(gw_ip, DEVICE_NAME)
    time.sleep(1)
    create_container(gw_ip, DEVICE_NAME, CONTAINER)
    print(f"✅ Device ready on {gw_ip}\n")


# ==========================
# Main Simulation Loop
# ==========================
def main():
    print("🚀 Starting RSSI + Handover simulation")
    current_gateway = GW_A
    setup_device(current_gateway)

    while True:
        rssi_a, rssi_b = simulate_rssi()
        print(f"📡 RSSI_A: {rssi_a}, RSSI_B: {rssi_b}")

        # Handle possible handover
        current_gateway = handover_if_needed(current_gateway, rssi_a, rssi_b)

        # Post a fake temperature value
        tempC = random.uniform(20.0, 26.0)
        post_temperature(current_gateway, DEVICE_NAME, tempC)

        # Wait 10 seconds before sending again
        time.sleep(30)


if __name__ == "__main__":
    main()
