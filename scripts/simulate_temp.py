import requests
import json
import random
import time
import uuid

# ---------------- CONFIG ----------------
BASE_URL = "http://127.0.0.1:8080/~/id-in/cse-in"
HEADERS = {
    "X-M2M-Origin": "CAdmin",
    "X-M2M-RVI": "3",
    "Content-Type": "application/json;ty=4",  # ty=4 = ContentInstance
    "Accept": "application/json",
}

# Your AE resource names (from device list)
DEVICES = ["SeeedStudioXIAO", "ESP32-Gateway"]

def push_random_temp(ae_name):
    """Send a random temperature CIN to AE’s /temperature container."""
    # Random realistic temperature (20–35°C)
    temp = round(random.uniform(20.0, 35.0), 1)

    # Make sure the container path exists
    container_url = f"{BASE_URL}/{ae_name}/temperature"
    cin_url = f"{container_url}"
    data = {
        "m2m:cin": {
            "con": json.dumps({"tempC": temp})
        }
    }

    try:
        resp = requests.post(
            cin_url,
            headers={**HEADERS, "X-M2M-RI": f"req-{uuid.uuid4()}"},
            data=json.dumps(data),
            timeout=3
        )
        if resp.status_code in [200, 201]:
            print(f"✅ Pushed {temp}°C to {ae_name}/temperature")
        else:
            print(f"⚠️ Failed for {ae_name}: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"❌ Error pushing to {ae_name}: {e}")


if __name__ == "__main__":
    print("🌡️  Starting random temperature simulator...")
    while True:
        for device in DEVICES:
            push_random_temp(device)
        time.sleep(5)  # every 5 seconds
