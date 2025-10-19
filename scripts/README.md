# oneM2M Automation Scripts (ACME-CSE)

This folder contains automation scripts for managing Application Entities (AEs) in the ACME oneM2M IN-CSE.  
They are designed to work together for a seamless workflow: creating, updating, and registering AEs into the Django dashboard automatically.

---

## Overview of Scripts

| Script | Purpose |
|--------|----------|
| `create_ae.sh` | Creates a new AE, adds containers, uploads values, and automatically updates Django views. |
| `append_ae_values.sh` | Appends new sensor readings or data values to existing AEs. |
| `update_views.sh` | Updates Django’s `views.py` to include new AE endpoints. |
| `setup_ae.sh` *(optional)* | Master script that runs all three steps in sequence (create → update → append). |

---

## 1. `create_ae.sh`

**Purpose:**  
Creates a new Application Entity (AE) on the IN-CSE, automatically adds containers (`temperature`, `humidity`, `battery`, `signal`), and uploads one user-defined value to each.

**Automation:**  
Now includes a built-in option to automatically update Django views immediately after AE creation.

**Usage:**
```bash
chmod +x create_ae.sh
./create_ae.sh
```

**Example Flow:**
```
Enter AE name (e.g., Device_2): Device_2
Enter Originator (e.g., CDevice2): CDevice2
temperature: 28.4
humidity: 61
battery: 84
signal: -70

Would you like to add this AE to Django views.py? (y/n): y
views.py updated successfully.
```

---

## 2. `append_ae_values.sh`

**Purpose:**  
Appends new readings to existing AEs and containers.

**Usage:**
```bash
chmod +x append_ae_values.sh
./append_ae_values.sh
```

**Example Flow:**
```
Enter existing AE name (e.g., Device_1): Device_2
Enter Originator (e.g., CDevice2): CDevice2
temperature: 29.0
humidity: 63
battery: 81
signal: -69
```

---

## 3. `update_views.sh`

**Purpose:**  
Updates Django’s `ui/views.py` to include the new AE in the `AE_ENDPOINTS` dictionary.  
Automatically adds entries like:
```python
"Device_2": f"{BASE_URL}/CDevice2",
```

**Usage (standalone):**
```bash
chmod +x update_views.sh
./update_views.sh
```

---

## 4. `setup_ae.sh` (Optional Master Script)

**Purpose:**  
Runs the full process automatically — AE creation, Django update, and optional data append.

**Usage:**
```bash
chmod +x setup_ae.sh
./setup_ae.sh
```

**Example Flow:**
```
[1] Create new AE → done
[2] Update Django views.py → done
[3] Append data values (optional) → done
AE setup and Django update complete.
```

---

## Recommended Workflow

| Step | Action | Script |
|------|--------|--------|
| 1 | Create new AE and containers | `create_ae.sh` |
| 2 | (Automatic) Update Django views | Auto-triggered inside create script |
| 3 | Append more data readings | `append_ae_values.sh` (optional) |
| 4 | Verify AE in dashboard | `/devices_list/` view in Django |

---

## Notes

- Run scripts from the `scripts/` folder.  
- Ensure `VIEWS_PATH` in `update_views.sh` points correctly to your Django `views.py` (e.g. `../demoApp/ui/views.py`).  
- The ACME-CSE instance must be running and accessible (`http://54.164.106.20:8080`).  
- All scripts are interactive and safe to rerun.  

---

© 2025 — Automation by Khairol Eimannajwan
