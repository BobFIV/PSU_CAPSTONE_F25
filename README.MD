# PSU_CAPSTONE_F25 — IoT Handover Framework

## Overview
This repository contains the **complete IoT Handover Framework** developed as part of our Penn State Capstone project (Fall 2025).  
The system aims to establish a **seamless handover architecture** between multiple gateways (MN-CSEs) and a centralized IN-CSE using the **oneM2M ACME** framework.

Currently, the **web dashboard (DemoApp)** is the main working component, serving as the user interface for visualizing devices, sensors, and ACME resource data.  
Future components (e.g., `handover/`, `sensor/`, `gateway/`) are in progress and will be integrated once MN-CSE ↔ IN-CSE communication is fully established.

---

## Repository Structure

```
PSU_CAPSTONE_F25/
│
├── demoApp/                # Django web dashboard for IoT data visualization
│   ├── ui/                 # Frontend HTML templates and views
│   ├── scripts/            # Bash automation for AE/container creation and management
│   └── manage.py
│
├── gateway/                # (Planned) Gateway management module for MN-CSE integration
├── handover/               # (Planned) Handover management logic (hardware ↔ network)
├── sensor/                 # (Planned) Sensor data collection and communication module
├── oneM2M/                 # (Planned) oneM2M ACME-based management utilities
├── docker/                 # (Future) Dockerization for local and remote deployments
├── docs/                   # Documentation and setup guides
├── tests/                  # Test scripts and validation framework
│
├── scripts/                # Standalone helper scripts (AE creation, updates, etc.)
│   ├── create_ae.sh        # Creates a new AE and associated containers
│   ├── append_ae_values.sh # Adds new sensor readings to existing AEs
│   ├── update_views.sh     # Updates Django views.py to include new AEs automatically
│   └── README.md           # Documentation for using scripts
│
├── Makefile                # Shortcuts for setup, running Django, and cleaning
├── setup.sh                # Environment setup for first-time runs
├── init_cse_data.sh        # Initializes sample CSE data for testing
├── registerAE.py           # Python script for programmatic AE registration
└── .github/                # GitHub metadata and documentation
```

---

## Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/BobFIV/PSU_CAPSTONE_F25.git
cd PSU_CAPSTONE_F25
```

### 2. Set Up the Environment
Use the setup script to create the virtual environment and install dependencies:
```bash
bash setup.sh
```

Or use the Makefile shortcut:
```bash
make setup
```

### 3. Run the Web Dashboard
```bash
make run
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

### 4. Create a New AE (Optional for Now)
Until the **MN-CSE → IN-CSE** link is fully established, AEs and containers are managed through scripts.

To create a new AE and its containers:
```bash
cd scripts
./create_ae.sh
```
You will be prompted to enter the AE name, Originator ID, and sensor values for containers (`temperature`, `humidity`, `battery`, `signal`).  
The script will automatically update Django so the new AE appears in the device list.


---

## Current Status
- The **web app** (`demoApp/`) is fully functional for visualizing ACME data, however backend must be updated manually.
- The **ACME IN-CSE** is connected and supports AE creation via REST API.
- The **MN-CSE integration** (Raspberry Pi gateways) is **in progress** and will soon handle automatic AE registration and real-time sensor updates.

---

## Contributors

### oneM2M Team
- **Cole Nelson** 
- **Eric Shin**
- **Donald Jeter Boswell**
- **Khairol Eimannajwan**

### Embedded Systems Team
- **David Johnson**
- **Ethan Liu**
- **Steven Bowman**

---

## License
This project is developed for educational purposes under Penn State University’s Capstone Program (Fall 2025).  
All rights reserved to the project team and supervising faculty.
