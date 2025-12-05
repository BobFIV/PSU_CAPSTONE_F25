# 📡 CloudAppAE — Django Frontend & Notification Handler

## 🌐 Overview

The **CloudAppAE** is the web-facing component of the IoT Handover Framework.  
It serves as the system’s **Application Entity (AE)** and provides:

- Real-time device dashboard  
- Live RSSI visualization  
- Handover event logging  
- OneM2M `/notify` endpoint  
- Device + gateway association insights  

This is the interface that brings the entire mobility system to life.

---

# 🏗️ Architecture

```
IN-CSE (Laptop)
        ↓  oneM2M Notification
CloudAppAE (/notify)
        ↓
Django Models → Database
        ↓
Dashboard UI (Devices, RSSI, CINs, Events)
```

---

# 📁 Project Structure

```
demoApp/
│
├── orchestrator/               # Manage handover process 
|
|
├── ui/                         
│   ├── templates/              # HTML pages for dashboard
│   ├── dash_apps/              # Optional analytics (Plotly/Dash)
│   ├── migrations/             # DB migrations
│   ├── models.py               # Device + SensorReading storage
│   ├── views.py                # Core logic + /notify endpoint
│   ├── urls.py                 # Routing
│   └── apps.py
└── manage.py                   # Django app launcher
```

---

# ⚙️ Setup Instructions

## 1️⃣ Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate       # Windows
```

## 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```
---

# ▶️ Running the Server

## Development Mode

```bash
python manage.py runserver
```

Visit:

```
http://127.0.0.1:8000
```

## Production Mode (Gunicorn + Nginx)

```bash
gunicorn ui.wsgi:application --bind 0.0.0.0:8000
```

---

# 📬 oneM2M Notification Endpoint (`/notify/`)

This is where IN-CSE sends CIN updates.

### Example Payload

```json
{
  "m2m:sgn": {
    "nev": {
      "rep": {
        "m2m:cin": {
          "con": "27.5"
        }
      }
    },
    "net": 3
  }
}
```

### Processing Flow

1. IN-CSE detects new CIN  
2. POST → `/notify/`  
3. Django parses the signal  
4. Device + reading stored  
5. Dashboard updates  

---

# 🗄️ Database Commands

Apply migrations:

```bash
python manage.py migrate
```

Create admin user:

```bash
python manage.py createsuperuser
```

---

# 🛠️ Utility Scripts

### Create AE Automatically

```bash
python scripts/create_ae.py
```

### Test Notification Handling

```bash
python scripts/test_notify.py
```

---

# 📊 UI Pages

| URL | Description |
|-----|-------------|
| `/` | Dashboard home |
| `/devices` | Device list + details |
| `/analytics` | RSSI + sensor plots |
| `/logs` | Handover + orchestrator events |

---

# 🐞 Troubleshooting

### ❌ Not receiving notifications  
- Ensure PoA ends with `/notify/`  
- Confirm IN-CSE ↔ Django connectivity  
- Verify `net=3` in subscription

### ❌ CSRF issues  
Add `@csrf_exempt` to `/notify/`.

### ❌ CIN not appearing  
Check container path + mirrored resources.

---

