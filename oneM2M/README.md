# oneM2M Local IN‑CSE Architecture (Gateways + Devices + Django Dashboard)

This README explains  IN‑CSE resource tree and how it matches gateway code, Django orchestrator logic, and BLE device data flow.

---

# 📡 System Architecture

```
                    ┌─────────────────────────────┐
                    │        Django Orchestrator   │
                    │  (notify → save handlers)    │
                    └──────────────┬──────────────┘
                                   │ subscriptions
                                   ▼
                        ┌─────────────────────┐
                        │      IN‑CSE (ACME)  │
                        │   http://<IP>:8080  │
                        └───────────┬─────────┘
                                    │
                  ┌─────────────────┼──────────────────┐
                  │                 │                  │
                  ▼                 ▼                  ▼
          ┌────────────┐   ┌────────────┐     ┌────────────┐
          │   ESP32     │   │   gw‑A      │     │   gw‑B      │
          │(Sensor AE)  │   │(Gateway AE)│     │(Gateway AE)│
          └─────┬───────┘   └─────┬──────┘     └─────┬──────┘
                │                 │                  │
       CNT: temperature     CNT: scan          CNT: scan
                          CNT: inbox          CNT: inbox
```

This matches exactly what your CSE tree shows:

```
CSE:
  AE: ESP32
      CNT: temperature
  AE: gw‑A
      CNT: inbox
      CNT: scan
  AE: gw‑B
      CNT: scan
      CNT: inbox
  AE: SEEED_XIAO
```

---

# 🎯 High‑Level Summary

### ✔ IN‑CSE only  
You run **one** ACME instance (IN‑CSE) on your laptop.  
Gateways do **not** run MN‑CSEs. Gateways are simply **AEs**.

### ✔ Gateways register themselves  
`gw-A` and `gw-B` create:

- `scan` container → where RSSI scan results are posted  
- `inbox` container → where the orchestrator posts WL_ADD, WL_DEL, DC commands  

### ✔ Devices send CINs to their temperature container  
ESP32 and XIAO write CINs into:

```
/cse-in/ESP32/temperature
/cse-in/SEEED_XIAO/temperature
```

### ✔ Django subscribes to these  
IN‑CSE sends notifications to:

```
http://<Django-IP>:8000/notify/
```

### ✔ Django evaluates RSSI, performs handover  
Django:

- saves RSSI readings  
- checks if a handover is needed  
- writes commands into gateway inboxes  
- updates HandoverState  
- logs HandoverEvent  

---

# 🔧 ACME Resource Breakdown (Your Actual Layout)

## 🟦 1. Sensor AEs

### ESP32
```
/cse-in/ESP32
/cse-in/ESP32/temperature
```

Content instances here carry JSON:

```json
{
  "device": "ESP32",
  "tempC": 21.3
}
```

### SEEED_XIAO
```
/cse-in/SEEED_XIAO/temperature
```

---

## 🟦 2. Gateway AEs

### gw‑A
```
/cse-in/gw-A
  /scan
  /inbox
```

### gw‑B
```
/cse-in/gw-B
  /scan
  /inbox
```

### POSTs into `/scan`
Gateways publish RSSI telemetry:

```json
{
  "mac": "D2:29:B2:D0:66:FC",
  "rssi": -57,
  "connected": false
}
```

### POSTs into `/inbox`
Orchestrator writes:

```json
{
  "cmd": "WL_ADD",
  "mac": "D2:29:B2:D0:66:FC"
}
```

Gateways receive them via Flask `/notify` and execute UART commands.

---

# 🔔 Django Subscription Model

You create subscriptions pointing to:

```
AE/temperature → Django notify
AE/scan        → Django notify
```

Example:

```bash
curl -X POST http://<IN-IP>:8080/cse-in/ESP32/temperature   -H "X-M2M-Origin: CAdmin"   -H "Content-Type: application/json;ty=23"   -d '{
    "m2m:sub": {
      "rn": "sub_temp_esp32",
      "nu": ["http://<Django-IP>:8000/notify/"],
      "nct": 1,
      "enc": { "net": [3] }
    }
  }'
```

---

# 🧠 Data Flow: End‑to‑End

### ➤ Sensor → Gateway → IN‑CSE → Django → Handover → Gateway

1. **XIAO / ESP32 sends sensor packet**
2. **Gateway extracts temp/RSSI**
3. **Gateway posts CIN**
4. **ACME stores CIN**
5. **ACME notifies Django**
6. **Django save handlers update DB**
7. **Django evaluates handover**
8. **If needed → writes commands to gw-A/gw-B inbox**
9. **Gateway receives inbox CIN and executes UART commands**
10. **Device reconnects → new RSSI → loop continues**

---

# 🛰 Handover Rules (Recap)

Django logic:

```python
if current_rssi > best_rssi - margin:
    do nothing

if current_rssi > bad_threshold:
    do nothing

if best_gateway == current_gateway:
    do nothing

trigger_handover(...)
```

---

# 🎨 UI Integration

Device detail page displays:

- latest temperature  
- converted Fahrenheit value  
- status badge (Optimal / Cool / Warm / Cold / Hot)  
- **current gateway from HandoverState**  

Template displays:

```html
<strong>{{ current_gateway }}</strong>
```

And can be auto‑refreshed similarly to temperature.

---

# 🛠 Gateway Flask/Serial Interface

Gateways expose:

```
POST /notify
```

Receives:

```json
{ "cmd": "WL_ADD", "mac": "XX:XX..." }
```

Executes UART:

```
WL_ADD <mac>
WL_DEL <mac>
DC <mac>
```

---

# 📦 Install & Run Instructions

## 1. Start ACME
```
python3 -m acme
```

## 2. Start Django
```
make run
```

## 3. Start each gateway
```
python3 gateway.py
```

## 4. Verify CSE Tree  
Open web UI:

```
http://<IN-IP>:8080
```

---

# 🧪 Testing

### Send fake temp CIN:

```bash
curl -X POST http://<IN-IP>:8080/cse-in/ESP32/temperature   -H "Content-Type: application/json;ty=4"   -H "X-M2M-Origin: CAdmin"   -d '{"m2m:cin":{"con":"{"tempC":24.4}"}}'
```

### Send fake RSSI CIN:

```bash
curl -X POST http://<IN-IP>:8080/cse-in/gw-A/scan   -H "Content-Type: application/json;ty=4"   -d '{"m2m:cin":{"con":"{"mac":"AA:BB","rssi":-90}"}}'
```

Django should print:

```
📡 DB: Saved RSSI -90 for AA:BB via gw-A
```

---

# 🐛 Troubleshooting

| Problem | Cause | Fix |
|--------|-------|-----|
| No /notify callbacks | Wrong Django IP | Use LAN IP, not 127.0.0.1 |
| Gateways not receiving WL_ADD | Wrong inbox URL | Must be `/cse-in/gw-A/inbox` |
| Duplicate AEs | Didn't purge ACME state | Delete ACME `data/` folder |
| Handover oscillation | RSSI margin too small | Increase `RSSI_HANDOVER_MARGIN` |

---