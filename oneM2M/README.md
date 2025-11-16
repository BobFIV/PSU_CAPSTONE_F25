# 🌐 oneM2M Local Network Setup (IN-CSE, MN-CSE, and Django Frontend)

This guide walks you through setting up a **local oneM2M environment** consisting of:

* An **IN-CSE** (central coordinator, usually your laptop)
* One or more **MN-CSEs** (e.g., Raspberry Pis acting as gateways)
* **Devices / AEs** (e.g., ESP32, Seeed Studio XIAO)
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

### Basic setup

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

Default port: **8080**  
Example IN-CSE URL: `http://192.168.0.102:8080`

Verify:

```bash
curl -X GET http://192.168.0.102:8080/cse-in \
  -H "X-M2M-Origin: CAdmin" \
  -H "X-M2M-RI: reqTest" \
  -H "Accept: application/json"
```

---

## 3️⃣ Start the MN-CSE (on Raspberry Pi)

Edit `acme.ini`:

```ini
[cse]
registrar = http://192.168.0.102:8080
id = id-mn
```

Launch:

```bash
python3 -m acme
```

Verify:

```bash
curl -X GET http://192.168.0.102:8080/cse-in?rcn=6 \
  -H "X-M2M-Origin: CAdmin" \
  -H "X-M2M-RI: reqCheckMN" \
  -H "Accept: application/json"
```

Look for `cbA_id-mn_XXXX`.

---

## 4️⃣ Create an AE (Application Entity)

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

---

## 6️⃣ Post a Content Instance (Sensor Data)

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

# 🆕 MAC Address & RSSI Support

Our setup supports:

- **MAC address** → unique device identity  
- **RSSI** → signal strength used for handover logic  

### Example CIN with MAC + RSSI:

```json
{
  "tempC": 24.4,
  "mac": "AA:BB:CC:DD:EE:FF",
  "rssi": -67
}
```

### Mock generator:

```bash
cd python
python3 uart.py
```

It posts:

- Temperature  
- Pressure  
- Humidity  
- **MAC**  
- **RSSI**  

every 5 seconds.

---

## 7️⃣ Create a Subscription → Django

```bash
curl -X POST \
  http://192.168.0.102:8080/cse-in/cbA_id-mn_WeFgxO8cud/aeA_5t9jDiTzH9/cntA_IZNkcs47HG \
  -H "X-M2M-Origin: CAdmin" \
  -H "X-M2M-RI: 12345" \
  -H "X-M2M-RVI: 5" \
  -H "Content-Type: application/json;ty=23" \
  -d '{
    "m2m:sub": {
      "rn": "sub_esp32_temp",
      "nu": ["http://192.168.0.102:8000/notify/"],
      "nct": 1,
      "enc": { "net": [3] }
    }
  }'
```

---

## 8️⃣ Run Django Frontend

```bash
make setup
make run
```

Open:

```
http://127.0.0.1:8000
```

---

## 9️⃣ Verify Data Flow

Django output example:

```
🌡️ tempC: 24.4
MAC: AA:BB:CC:DD:EE:FF
RSSI: -67
```

---

## 🔟 Adding More Devices

Repeat AE → CNT → SUB steps.  
Dashboard updates automatically.

---

# 🔧 Important: Adjusting URLs for Your Network & oneM2M Resources

Because oneM2M runs on your **local Wi-Fi network**, all URLs in this guide must be updated to match:

- Your **actual device IP addresses**
- Your **actual announced AE / CNT paths**
- Your **Django server IP**
- Your **IN-CSE IP**

Copy/pasting the examples without adjusting these values will result in failed registrations, broken subscriptions, or missing notifications.

---

## 🟦 1. Update the IP Address Based on Your Machine

### IN-CSE (ACME) runs on your laptop  
Find your laptop’s LAN IP:

```bash
hostname -I
```

Use this IP instead of `127.0.0.1` in **ALL ACME API calls**, e.g.:

```
http://192.168.x.x:8080/cse-in
```

### Django Frontend also runs on the laptop

Your subscription **nu** MUST be:

```
http://192.168.x.x:8000/notify/
```

**Never use `127.0.0.1` unless you are running curl from the same laptop running Django.**

---

## 🟦 2. Update AE / CNT Resource Paths Based on What ACME Creates

ACME assigns **dynamic** names when MN-CSEs register to the IN-CSE.  
Your actual resource tree may look like:

```
cbA_id-mn_abcd1234       → remoteCSE (MN-CSE announcement)
  └── aeA_XYZ123         → Announced AE
        └── cntA_hello99 → Announced container
```

To view the current names:

```bash
curl -X GET http://<IN-IP>:8080/cse-in?rcn=6 -H "X-M2M-Origin: CAdmin"
```

Then scroll until you find:

- `m2m:cb`  → remoteCSE  
- `m2m:aeAnnc` → announced AE  
- `m2m:cntAnnc` → announced container  

Use **these exact values** in your subscription URL:

```
http://<IN-IP>:8080/cse-in/<cbA_id-mn_xxx>/<aeA_xxx>/<cntA_xxx>
```

---

## 🟦 3. Update Which Container You Are Posting To

If your AE has multiple containers, e.g.:

- `temperature`
- `pressure`
- `humidity`

Then your CIN POST URL must match the container you want to update:

**Example:**

Temperature:
```
/cse-mn/SeeedStudioXIAO/temperature
```

Humidity:
```
/cse-mn/SeeedStudioXIAO/humidity
```

Pressure:
```
/cse-mn/SeeedStudioXIAO/pressure
```

---

## 🟦 4. Update Subscription Targets per Container

If you want Django to receive notifications for *pressure* instead of *temperature*, then:

Replace:

```
cntA_IZNkcs47HG
```

with the correct **announced “pressure” container**.

---

## 🟦 5. Summary of What You Must Always Update Manually

Before running any curl command, confirm:

| Item | Where to Get It |
|------|-----------------|
| IN-CSE IP | `hostname -I` on laptop |
| Django IP | Same as IN-CSE |
| MN-CSE IP | `hostname -I` on Raspberry Pi |
| AE Name | From AE creation |
| CNT Name | From your CNT creation |
| Announced paths | From `cse-in?rcn=6` |
| Notification URL | Must match Django IP |

If ANY of these differ, your CIN posts or subscriptions will not work.

---

## 🟦 Example of a Fully Updated Subscription (Template)

```bash
curl -X POST   http://<IN-IP>:8080/cse-in/<remoteCSE>/<AEAnnc>/<CNTAnnc>   -H "X-M2M-Origin: CAdmin"   -H "X-M2M-RI: sub001"   -H "X-M2M-RVI: 5"   -H "Content-Type: application/json;ty=23"   -d '{
    "m2m:sub": {
      "rn": "my_subscription",
      "nu": ["http://<DASHBOARD-IP>:8000/notify/"],
      "nct": 1,
      "enc": { "net": [3] }
    }
  }'
```

Replace only the parts inside brackets `<>`.



✔️ Once you understand this section, you can work with ANY oneM2M deployment.


## ⚙️ Troubleshooting

| Issue | Fix |
|------|-----|
| `No route to host` | Ensure devices are on same network |
| Subscription not firing | Must use `/notify/` with trailing slash |
| ACME state corrupted | Delete ACME `data/` directory |
| Debug CSE | `python3 -m acme -d` |

---

## 🧠 Tips

- Use `hostname -I` for Pi IP  
- Keep `acme.ini` backups  
- Restart ACME after config changes  

---

## 📡 Common WiFi Commands

```
sudo nmcli dev wifi list
sudo nmcli --ask dev wifi connect "oneM2M_Local" password "Coleisthebest" name "home2"
```

