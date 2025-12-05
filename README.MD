# IoT Handover Framework

## 🌐 Overview

This repository contains the **IoT Handover Framework** developed for the Penn State Fall 2025 Senior Capstone Project.  
The system implements a **local, multi-gateway IoT mobility architecture** using the **oneM2M ACME platform** and a **custom Django dashboard** (CloudAppAE).

All components run **entirely inside a local Wi-Fi network**, enabling a telco-style handover simulation without requiring external routing, port-forwarding, or cloud services.

### 🧠 Core Concepts

- Multiple **gateways** (Raspberry Pis)
- One **IN-CSE coordinator** (laptop/server)
- Devices (ESP32 / Seeed XIAO) send sensor + RSSI data
- IN-CSE orchestrator makes **handover decisions**
- CloudAppAE shows **live device movement, RSSI graphs, and events**

---

# 🏗️ System Architecture

```
Device (ESP32 / Seeed XIAO)
        ↓
MN-CSE Gateway (Raspberry Pi)
        ↓
IN-CSE Orchestrator (Laptop)
        ↓
CloudAppAE (Django Dashboard)
```

---

# 📁 Repository Structure

```
PSU_CAPSTONE_F25/
│
├── ble/                            # BLE sensing system with RSSI handover
├── demoApp/                        # CloudAppAE Django Frontend
├── oneM2M/                         # IN-CSE + MN-CSE setup + handover simulation
├── setup.sh                        # Environment bootstrapper
├── requirements.txt                # Python dependencies
└── README.md                       # (This file)
```

---

# ⚙️ Getting Started (High-Level)

The system consists of **three components**:

1. **CloudAppAE WebApp** (`demoApp/`)
2. **IN-CSE Central Coordinator** (`oneM2M/`)
3. **Gateways** (Raspberry Pis)

Each has its own README with full instructions.

---

# 1️⃣ CloudAppAE WebApp (Django)

- Runs the device dashboard  
- Receives oneM2M notifications via `/notify/`  
- Stores & visualizes sensor data + mobility events  

See full guide:  
👉 `demoApp/README.md`

---

# 2️⃣ oneM2M IN-CSE (Laptop / Server)

- Hosts the ACME **Infrastructure Node CSE**
- Registers AEs from all MN-CSEs
- Receives CINs + forwards notifications to Django
- Runs orchestrator logic for handover simulation

Setup instructions:  
👉 `oneM2M/README.md`

---

# 3️⃣ Raspberry Pi MN-CSE Gateways

- Each Pi hosts ACME **Middle Node CSE**
- Receives UART sensor packets
- Sends CINs upward to IN-CSE
- Emits RSSI/MAC for mobility decisions

Guide also in:  
👉 `oneM2M/README.md`

---

# 🧪 Simulation Tools

Inside `oneM2M/`:

- `handover.py` — Single-device handover simulation  
- `handover_multi.py` — Multi-device, multi-threaded mobility simulator  

Used for validating handover logic before embedded RSSI integration.

---

# 📊 Current System Status

| Component | Status | Notes |
|----------|--------|-------|
| CloudAppAE Dashboard | ✔️ Stable | Live RSSI, devices, handovers |
| IN-CSE Orchestrator | 🟡 Partial | Basic algorithm; full MAC/RSSI integration pending |
| Gateways | 🟡 Working | Posting CINs, reporting RSSI |
| Sensor Nodes | 🟡 Working | UART → Gateway pipeline being finalized |

---

# 👥 Contributors

- Cole Nelson  
- Eric Shin  
- Donald Jeter Boswell  
- Khairol Eimannajwan  
- David Johnson  
- Ethan Liu  
- Steven Bowman  

---

# 📜 License

Developed under the  
**Penn State College of Engineering Senior Capstone Program (Fall 2025)**.  
All rights reserved.
