# DemoApp Web Application (IoT Dashboard)

## Overview

This repository contains the **web application** component of our Capstone project — the **IoT Handover Framework**.  
The web application is built using **Django** and serves as the central **IoT dashboard** for monitoring Application Entities (AEs), their sensors, and real-time data integrated through the **ACME oneM2M IN-CSE** server hosted on AWS.

Previously, a fake device simulator (`fake_device.py`) was used to populate data when the ACME-CSE connection was unavailable.  
**Now, the backend is fully connected to ACME-CSE**, and we use **automation scripts** to register AEs, create containers, and push sensor data directly.

For now, **this script-based setup** will serve as the primary way to generate and manage new AEs, until the MN-CSE nodes are connected and synchronized with the IN-CSE.

---

## Features

- Django web dashboard for IoT devices and analytics  
- Real-time retrieval of AE and container data from ACME-CSE  
- Automated AE creation and registration through shell scripts  
- Built-in data append functionality for updating sensor readings  
- Dashboard auto-updates to recognize new AEs dynamically  
- Future support for MN-CSE → IN-CSE integration  

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/BobFIV/PSU_CAPSTONE_F25.git
cd PSU_CAPSTONE_F25

```

---

### 2. Environment Setup
If you have `make` installed:
```bash
make setup
```

#### Option B: Manual Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### 3. Run the Web Application
```bash
make run
```
Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

### 4. Adding New Application Entities (AEs)

Since the MN-CSE is not yet connected to the IN-CSE, we are currently using **automation scripts** to create and manage AEs directly through the IN-CSE.  

These scripts can be found in the `scripts/` directory and include:

| Script | Description |
|--------|--------------|
| `create_ae.sh` | Creates a new AE on the IN-CSE, adds containers, posts initial values, and updates Django `views.py` automatically. |
| `append_ae_values.sh` | Appends new data values to existing AEs. |
| `update_views.sh` | Updates `ui/views.py` with new AE endpoints for dashboard recognition. |
| `setup_ae.sh` | Master script that runs all three steps in sequence (create → update → append). |

Example usage:
```bash
cd scripts
./create_ae.sh
```
You will be prompted to enter the AE name, Originator ID, and sensor values for containers (`temperature`, `humidity`, `battery`, `signal`).  
The script will automatically update Django so the new AE appears in the device list.

---

### 5. Cleaning up
```bash
make clean
```

## Project Structure
```
PSU_CAPSTONE_F25/
│
├── demoApp/                      # Main Django web app
│   ├── manage.py                 # Django management script
│   ├── demoApp/                  # Django project settings
│   ├── ui/                       # Frontend templates and views
│   └── ui/management/commands/   # (Previously contained fake_device.py)
│
├── scripts/                      # oneM2M automation scripts
│   ├── create_ae.sh              # Create new AEs and containers
│   ├── append_ae_values.sh       # Append new readings
│   ├── update_views.sh           # Auto-update Django views
│   └── setup_ae.sh               # Master orchestrator
│
├── Makefile                      # Shortcuts for setup, run, and clean
├── setup.sh                      # Auto environment setup (optional)
└── .github/                      # GitHub documentation and workflow files
```

---

## Notes

- Keep your `venv/` folder **out of version control** (`.gitignore` already covers it).  
- The system integrates with the hosted ACME-CSE instance at:  
  `http://54.164.106.20:8080`  
- All automation scripts in `scripts/` are interactive and reusable.  
- Once MN-CSE integration is complete, AE creation will occur automatically during device registration.  

---

## Contributors

- Capstone Project Team, Penn State University  

---

© 2025 — Penn State Capstone F25, IoT Handover Framework