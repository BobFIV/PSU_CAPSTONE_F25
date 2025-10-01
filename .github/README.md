## Overview
This repository contains the **web application** component of our Capstone project as for now.  

Right now the front end works with a fake script that acts as a device connected to the back-end. We plan on integrating the back-end with a the ACME-CSE server soon.

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/YourOrg/PSU_CAPSTONE_F25.git
cd PSU_CAPSTONE_F25
```

### 2. Run the Setup Script (Mac / WSL)
A setup script is provided to create and configure the virtual environment automatically.

```bash
chmod +x setup.sh
./setup.sh
```

### 3. Activate the Virtual Environment
```bash
source demoApp/venv/bin/activate
```

### 4. Run the Web App
```bash
python demoApp/manage.py runserver
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
└── .github/          # GitHub-specific configuration and README
```

## Notes
- Keep your `venv/` folder **out of version control** (add it to `.gitignore`).
- Use the `.github/README.md` as the main project documentation.
- For now, this repo only covers the **web app** — other components will be added later.

---
🚀 You’re ready to develop and run the web app!
