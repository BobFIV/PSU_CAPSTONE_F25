#!/usr/bin/env python3
"""
Mock Sensor Data Generator → oneM2M MN-CSE
Simulates Seeed → nRF7002 → Raspberry Pi data flow.
"""

import requests
import json
import random
import time
from datetime import datetime

# ----------------------------------------
# oneM2M MN-CSE Configuration
# ----------------------------------------
MN_CSE = "http://10.0.0.37:8080/cse-mn/AnnouncedAE/infared-temperature"
AE_NAME = "AnnouncedAE"
CNT_NAME = "infrared-temperature"

HEADERS = {
	"X-M2M-Origin": "ColeAdmin",
	"X-M2M-RI": "reqCIN1",
	"X-M2M-RVI":"3",
	"X-M2M-TY":"4",
	"Content-Type":"application/json;ty=4",
	"Accept":"application/json"
}

# ----------------------------------------
# Generate random mock sensor data
# ----------------------------------------
def generate_mock_data():
    """Simulate one sensor reading."""
    return {
        "device_addr": "SEEED_NODE_1",
        "tempC": round(random.uniform(20.0, 30.0), 2),
        "pressurePa": random.randint(100000, 102000),
        "humidityPct": round(random.uniform(40.0, 60.0), 1),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


# ----------------------------------------
# Post contentInstance to MN-CSE
# ----------------------------------------
def post_to_cse(data):
    payload = {
        "m2m:cin": {
            "con": json.dumps(data),
	    "at": ["/id-in"],
	    "aa": ["con"]
        }
    }

    try:
        r = requests.post(f"{MN_CSE}", headers=HEADERS, json=payload, timeout=2)
        if r.status_code in (200, 201):
            print(f"✅ Sent mock data → MN-CSE: {data}")
        else:
            print(f"⚠️ Failed ({r.status_code}): {r.text}")
    except Exception as e:
        print(f"❌ Error posting to CSE: {e}")


# ----------------------------------------
# Main loop
# ----------------------------------------
def main():
    print("🌡️  Mock sensor generator started — sending to MN-CSE every 5 seconds...\n")

    while True:
        data = generate_mock_data()
        post_to_cse(data)
        time.sleep(5)   # send every 5 seconds


if __name__ == "__main__":
    main()
