# 🌐 oneM2M Local Network Setup (IN-CSE, MN-CSE, and Django Frontend)

This guide walks you through setting up a **local oneM2M environment** consisting of:

* An **IN-CSE** (central coordinator, usually your laptop)
* One or more **MN-CSEs** (e.g., Raspberry Pis acting as gateways)
* **Devices / AEs** (e.g., ESP32, Seeed Studio XIAO, etc.)
* A **Django frontend** that receives sensor notifications and displays live data

---

## 🧩 System Overview

```
[ESP32 / Seeed XIAO] → [MN-CSE (Raspberry Pi)] → [IN-CSE (Laptop)] → [Django Frontend]
```

All components run on the same **local Wi-Fi network**.
Data flows upward automatically via the oneM2M protocol.

---

## 🧰 Prerequisites

### Hardware

* Laptop (acts as IN-CSE + Django frontend)
* One or more Raspberry Pis (MN-CSEs / gateways)
* Optional sensors (ESP32, Seeed Studio XIAO)

### Software

* Python ≥ 3.10
* Git
* Open ports `8080` (for ACME) and `8000` (for Django)

### Basic setup commands

```bash
sudo apt install python3-full python3-venv git
```

---

## 1️⃣ Clone the ACME oneM2M CSE

Run on both **IN-CSE** (laptop) and **MN-CSE** (Pi):

```bash
git clone https://github.com/ankraft/ACME-oneM2M-CSE.git
cd ACME-oneM2M-CSE
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 2️⃣ Start the IN-CSE (on Laptop)

```bash
python3 -m acme
```

By default, it runs on port `8080`.
Example IN-CSE URL: `http://192.168.0.102:8080`

Verify it’s up:

```bash
curl -X GET http://192.168.0.102:8080/cse-in \
  -H "X-M2M-Origin: CAdmin" \
  -H "X-M2M-RI: reqTest" \
  -H "Accept: application/json"
```

---

## 3️⃣ Start the MN-CSE (on Raspberry Pi)

Edit `acme.ini` to point the Pi to your IN-CSE:

```ini
[cse]
registrar = http://192.168.0.102:8080
id = id-mn
```

Then launch it:

```bash
python3 -m acme
```

Check that it registered with the IN-CSE:

```bash
curl -X GET http://192.168.0.102:8080/cse-in?rcn=6 \
  -H "X-M2M-Origin: CAdmin" \
  -H "X-M2M-RI: reqCheckMN" \
  -H "Accept: application/json"
```

You should see an entry like `cbA_id-mn_XXXX` under `rrf`.

---

## 4️⃣ Create an AE (Application Entity)

Each physical device (ESP32, Seeed, etc.) becomes an AE in the MN-CSE.

```bash
curl -X POST \
  http://192.168.0.101:8080/cse-mn \
  -H "X-M2M-Origin: CSeeed" \
  -H "X-M2M-RI: reqAE1" \
  -H "X-M2M-RVI: 3" \
  -H "Content-Type: application/json;ty=2" \
  -d '{
    "m2m:ae": {
      "rn": "SeeedStudioXIAO",
      "api": "N.seeed",
      "rr": true,
      "srv": ["3"],
      "lbl": ["Seeed Studio XIAO"],
      "at": ["/id-in"],
      "aa": ["lbl", "rn", "api"]
    }
  }'
```

---

## 5️⃣ Create a Container for Sensor Data

Each AE holds one or more containers for its sensor types (e.g., temperature).

```bash
curl -X POST \
  http://192.168.0.101:8080/cse-mn/SeeedStudioXIAO \
  -H "X-M2M-Origin: CAdmin" \
  -H "X-M2M-RI: reqCNT1" \
  -H "X-M2M-RVI: 3" \
  -H "Content-Type: application/json;ty=3" \
  -d '{
    "m2m:cnt": {
      "rn": "temperature",
      "at": ["/id-in"],
      "lbl": ["data:temperature", "type:sensor"],
      "aa": ["lbl", "rn"]
    }
  }'
```

---

## 6️⃣ Post a Content Instance (Example Sensor Data)

```bash
curl -X POST \
  http://192.168.0.101:8080/cse-mn/SeeedStudioXIAO/temperature \
  -H "X-M2M-Origin: CAdmin" \
  -H "X-M2M-RI: reqCIN1" \
  -H "X-M2M-RVI: 3" \
  -H "X-M2M-TY: 4" \
  -H "Content-Type: application/json;ty=4" \
  -H "Accept: application/json" \
  -d '{
    "m2m:cin": {
      "con": "{\"tempC\":24.4}",
      "at": ["/id-in"],
      "aa": ["con"]
    }
  }'
```

---

## 7️⃣ Create a Subscription (Notify Django Frontend)

This subscription pushes new CINs automatically to your Django app’s `/notify` endpoint.

```bash
curl -X POST \
  http://192.168.0.101:8080/cse-mn/SeeedStudioXIAO/temperature \
  -H "X-M2M-Origin: CAdmin" \
  -H "X-M2M-RI: 12345" \
  -H "X-M2M-RVI: 5" \
  -H "Content-Type: application/json;ty=23" \
  -d '{
    "m2m:sub": {
      "rn": "sub_seeed_temp",
      "nu": ["http://127.0.0.1:8000/notify/"],
      "nct": 1,
      "enc": { "net": [3] }
    }
  }'
```

---

## 8️⃣ Run the Django Frontend

Run locally on your laptop to visualize live sensor data. From root of project, run:

```bash
make setup
make run
```

Access via browser:

```
http://127.0.0.1:8000
```

---

## 9️⃣ Verify Data Flow

1. MN-CSE sends a new CIN (sensor reading)
2. Subscription triggers POST → `http://127.0.0.1:8000/notify/`
3. Django logs show:

   ```
   🌡️ tempC: 24.4
   ```
4. Web UI automatically updates live with the new temperature value

---

## 🔟 Adding More Devices

To add another sensor:

1. Create a new AE for that device
2. Add containers for each sensor type
3. Create a subscription pointing to `/notify`

Data from all devices appears automatically in your UI.

---

## ⚙️ Troubleshooting

| Issue                         | Solution                                    |
| ----------------------------- | ------------------------------------------- |
| `No route to host`            | Ensure both devices are on the same network |
| `Verification request failed` | Add a trailing slash in `/notify/`          |
| Missing dependencies          | Run `pip install -r requirements.txt`       |
| Clear ACME state              | Delete local `data/` directory in ACME repo |
| Debug ACME                    | Run with `python3 -m acme -d`               |

---

## 🧠 Tips

* Use `hostname -I` on your Pi to find its IP
* Keep `acme.ini` backups for consistent configuration
* For quick resets, restart both CSEs (`CTRL+C` → rerun)
* To simulate sensors, just repeat the `CIN` POST command with new values

---

## ✅ Summary

After setup, you’ll have a working **end-to-end local oneM2M system**:

```
Device (ESP32 / Seeed)
     ↓
MN-CSE on Pi
     ↓
IN-CSE on Laptop
     ↓
Django Frontend (Live Dashboard)
```


# Helpful commands

For setting WiFi network on Pi:
```
sudo nmcli dev wifi list

sudo nmcli --ask dev wifi connect "ssid" password "psswrd" name "home"
```
