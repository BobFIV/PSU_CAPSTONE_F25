import requests
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import SensorReading

# ---------------- CONFIG ----------------
BASE_URL = "http://192.168.0.102:8080"
HEADERS = {
    "X-M2M-Origin": "CAdmin",
    "X-M2M-RVI": "3",
    "Accept": "application/json",
}

# ---------------- BASIC UI VIEWS ----------------
def login_view(request):
    return render(request, "ui/login.html")

def logout_view(request):
    return render(request, "ui/login.html")

def home(request):
    return render(request, "ui/home.html")


# ---------------- DEVICE LIST ----------------
def device_list(request):
    """
    Dynamically fetch all AEAnncs (devices) registered under any gateway,
    and display their human-readable labels (lbl) when available.
    """
    try:
        headers = {**HEADERS, "X-M2M-RI": "reqDeviceList"}
        response = requests.get(f"{BASE_URL}/cse-in?rcn=6", headers=headers, timeout=5)
        data = response.json()

        refs = data.get("m2m:rrl", {}).get("rrf", [])
        devices = []

        for item in refs:
            if item.get("typ") == 10002:  # AEAnnc
                path = item.get("val", "")
                ae_name = item.get("nm")

                # Extract gateway name from the path (e.g., cbA_id-mn_WeFgxO8cud)
                path_parts = path.split("/")
                gateway_name = path_parts[5] if len(path_parts) > 5 else "Unknown"

                # Clean up path to make a valid REST URL (drop /id-in prefix)
                clean_path = path.replace("/id-in", "")

                label = ae_name  # fallback
                try:
                    ae_response = requests.get(
                        f"{BASE_URL}{clean_path}",
                        headers={**HEADERS, "X-M2M-RI": f"reqFetchAE_{ae_name}"},
                        timeout=3,
                    )
                    ae_data = ae_response.json()
                    print(ae_data)  # debug to verify structure

                    lbls = (
                        ae_data.get("m2m:aeA", {}).get("lbl")
                        or ae_data.get("m2m:aeAnnc", {}).get("lbl")
                        or []
                    )
                    if lbls:
                        label = ", ".join(lbls)

                except Exception as e:
                    print(f"⚠️ Could not fetch labels for {ae_name}: {e}")

                devices.append({
                    "name": ae_name,
                    "label": label,
                    "path": path,
                    "gateway": gateway_name,
                })


        return render(request, "ui/device_list.html", {"devices": devices})

    except Exception as e:
        print(f"[ERROR] Could not fetch device list: {e}")
        return render(request, "ui/device_list.html", {"devices": []})





# ---------------- DEVICE DETAIL ----------------
def device_detail(request, device_name):
    """
    Display the most recent reading stored in the Django DB
    (populated via /notify).
    """
    # Get most recent temperature reading
    latest_temp = (
        SensorReading.objects
        .filter(device_name="cbA_id-mn_WeFgxO8cud", sensor_type="temperature")
        .order_by("-timestamp")
        .first()
    )

    container_data = []
    if latest_temp:
        container_data.append(("temperature", latest_temp.value))

    return render(
        request,
        "ui/device_detail.html",
        {
            "device_name": "cbA_id-mn_WeFgxO8cud",
            "container_data": container_data,
        },
    )
    
def latest_value(request, device_name, sensor_type):
    latest = (
        SensorReading.objects
        .filter(device_name=device_name, sensor_type=sensor_type)
        .order_by('-timestamp')
        .first()
    )

    if latest:
        return JsonResponse({
            'device_name': latest.device_name,
            'sensor_type': latest.sensor_type,
            'value': latest.value,
            'timestamp': latest.timestamp.isoformat()
        })
    else:
        return JsonResponse({'error': 'No data found'}, status=404)



# ---------------- HISTORICAL LOGS ----------------
def sensor_logs(request, device_name, sensor_type):
    """
    Returns the last 50 readings stored in your Django DB.
    These are populated by the /notify subscription endpoint.
    """
    readings = SensorReading.objects.filter(
        device_name=device_name,
        sensor_type=sensor_type
    ).order_by("-timestamp")[:50]

    logs_data = [
        {"value": reading.value, "timestamp": reading.timestamp.isoformat()}
        for reading in readings
    ]
    return JsonResponse({"logs": logs_data})


# ---------------- NOTIFY (Subscription Callback) ----------------
@csrf_exempt
def notify(request):
    """
    Subscription endpoint that ACME calls when new CINs are created.
    It parses the incoming body and stores the reading in your database.
    """
    if request.method == 'GET':
        return JsonResponse({'status': 'verification-ok'})
    if request.method == 'POST':
        raw_body = request.body.decode("utf-8", errors="ignore")
        print("\n====================")
        print("📥 RAW BODY RECEIVED:")
        print("--------------------")
        print(raw_body)
        print("====================\n")

        try:
            body = json.loads(raw_body)
            cin = body.get("m2m:sgn", {}).get("nev", {}).get("rep", {}).get("m2m:cinA", {})
            value = cin.get("con")
            if value is not None:
                try:
                    payload = json.loads(value)
                    tempC = payload.get("tempC")

                    print(f"🌡️ tempC: {tempC}")

                    if tempC is not None:
                        SensorReading.objects.create(
                            device_name="cbA_id-mn_WeFgxO8cud",
                            sensor_type="temperature",
                            value=float(tempC)
                        )

                except json.JSONDecodeError:
                    print(f"⚠️ con was not valid JSON: {value}")
        except Exception as e:
            print(f"[ERROR] Could not parse or save CIN: {e}")

    return JsonResponse({"status": "received"})


def gateway_list(request):
    """
    Dynamically fetch all announced gateways (CSEAnncs) from the IN-CSE.
    """
    try:
        headers = {
            **HEADERS,
            "X-M2M-RI": "reqGatewayList"
        }

        response = requests.get(f"{BASE_URL}/cse-in?rcn=6", headers=headers, timeout=5)
        data = response.json()

        gateways = []
        refs = data.get("m2m:rrl", {}).get("rrf", [])

        for item in refs:
            if item.get("typ") == 10005:  # 10005 = CSEAnnc
                gateways.append({
                    "name": item.get("nm"),
                    "path": item.get("val"),
                    "type": "CSEAnnc"
                })

        return render(request, "ui/gateway_list.html", {"gateways": gateways})

    except Exception as e:
        print(f"[ERROR] Could not fetch gateway list: {e}")
        return render(request, "ui/gateway_list.html", {"gateways": []})
