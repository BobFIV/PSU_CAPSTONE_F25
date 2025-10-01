# DemoApp Web Application

## Overview
This repository contains the **web application** component of our Capstone project.  
Right now there is a functioning front end however the backend is connected to a script that acts as a device connected to the backend. We plan on integrating the backend with the proper ACME-CSE server soon.
## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/YourOrg/PSU_CAPSTONE_F25.git
cd PSU_CAPSTONE_F25
```

### 2. Option A: Use the Setup Script (Mac / WSL)
```bash
chmod +x setup.sh
./setup.sh
```

### 2. Option B: Use Makefile (Mac / WSL)
If you have `make` installed, you can simplify the setup:
```bash
make setup
```

### 3. Activate the Virtual Environment
```bash
source demoApp/venv/bin/activate
```

### 4. Run the Web App
```bash
python demoApp/manage.py runserver
```
Or, if using the Makefile:
```bash
make run
```
Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

## 📂 Project Structure
```
PSU_CAPSTONE_F25/
│
├── demoApp/          # Main web application
│   ├── manage.py     # Django management script
│   ├── demoApp/      # Django project settings
│   └── app/          # Example application code
│
├── setup.sh          # Auto-setup script (Mac/WSL)
├── Makefile          # Shortcuts for setup, run, and clean
└── .github/          # GitHub-specific configuration and README
```

## Notes
- Keep your `venv/` folder **out of version control** (already covered in `.gitignore`).
- Use the `.github/README.md` as the main project documentation.
- For now, this repo only covers the **web app** — other components will be added later.

---

