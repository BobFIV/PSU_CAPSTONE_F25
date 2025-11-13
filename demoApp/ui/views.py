import requests
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import SensorReading
from django.db.models import Avg, Max, Min
from django.utils.timezone import now, timedelta
import uuid


BASE_URL = "http://127.0.0.1:8080/~/id-in/cse-in"
HEADERS = {
    "X-M2M-Origin": "CAdmin",
    "X-M2M-RVI": "3",
    "Accept": "application/json",
}


def login_view(request):
    return render(request, "ui/login.html")

def logout_view(request):
    return render(request, "ui/login.html")

def home(request):
    return render(request, "ui/home.html")


def device_list(request):
    """
    Discover all AEs (devices) directly under IN-CSE and display them.
    """
    devices = []
    try:
        params = {"fu": "1", "ty": "2"}
        headers = {**HEADERS, "X-M2M-RI": f"req-{uuid.uuid4()}"}
        resp = requests.get(
            "http://127.0.0.1:8080/~/id-in/cse-in",
            headers=headers,
            params=params,
            timeout=5
        )

        print("[DEBUG] Raw ACME response:", resp.text)

        if resp.status_code == 200:
            uris = resp.json().get("m2m:uril", [])
            for uri in uris:
                rn = uri.split("/")[-1]
                if rn in ["CAdmin", "CloudAppAE"]:
                    continue

                ae_url = f"http://127.0.0.1:8080/~/id-in/{uri}"
                ae_headers = {**HEADERS, "X-M2M-RI": f"req-{uuid.uuid4()}"}
                ae_resp = requests.get(ae_url, headers=ae_headers, timeout=3)

                if ae_resp.status_code == 200:
                    ae = ae_resp.json().get("m2m:ae", {})
                    
                    labels = [l for l in ae.get("lbl", [rn]) if l.lower() != "device"]
                    label = ", ".join(labels) if labels else rn

                    devices.append({
                        "name": rn,
                        "label": label,
                        "gateway": ae.get("api", "Unknown"),
                        "path": f"/id-in/{uri}",
                    })
    except Exception as e:
        print(f"[ERROR] device_list: {e}")

    return render(request, "ui/device_list.html", {"devices": devices})


def device_detail(request, device_name):
    """
    Renders the device detail page with the most recent temperature.
    """
    latest_temp = (
        SensorReading.objects
        .filter(device_name=device_name, sensor_type="temperature")
        .order_by('-timestamp')
        .first()
    )

    container_data = []
    if latest_temp:
        container_data.append(("temperature", latest_temp.value))

    return render(request, "ui/device_detail.html", {
        "device_name": device_name,
        "container_data": container_data
    })


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


def sensor_logs(request, device_name, sensor_type):
    """
    Return the 50 most recent readings stored in DB (/notify inserts them).
    """
    readings = SensorReading.objects.filter(
        device_name=device_name,
        sensor_type=sensor_type
    ).order_by("-timestamp")[:50]

    logs_data = [
        {"value": r.value, "timestamp": r.timestamp.isoformat()}
        for r in readings
    ]
    return JsonResponse({"logs": logs_data})


@csrf_exempt
def notify(request):
    """
    Receives notifications from ACME when new CINs are created.
    Extracts tempC and stores in DB under correct device.
    """
    if request.method == "GET":
        return JsonResponse({"status": "ok"})

    if request.method == "POST":
        try:
            body = json.loads(request.body.decode("utf-8"))
            print("\n📥 Notification received:\n", json.dumps(body, indent=2))

            cin = body.get("m2m:sgn", {}).get("nev", {}).get("rep", {}).get("m2m:cin", {})
            value_str = cin.get("con", "{}")
            pi = cin.get("pi", "")

            container_to_device = {
                "cntaGsbqEvg9o": "SeeedStudioXIAO",
                "cntRqbXHkN2ee": "ESP32-Gateway",
            }

            device_name = container_to_device.get(pi, "Unknown")

            payload = json.loads(value_str)
            tempC = payload.get("tempC")

            if tempC is not None and device_name != "Unknown":
                SensorReading.objects.create(
                    device_name=device_name,
                    sensor_type="temperature",
                    value=float(tempC)
                )
                print(f"🌡️ Saved temp {tempC} for {device_name}")
            else:
                print(f"⚠️ Unknown device or invalid payload: {pi}")

        except Exception as e:
            print(f"[ERROR] notify: {e}")

    return JsonResponse({"status": "received"})


def gateway_list(request):
    """
    Fetch all announced gateways (CSEAnncs) under IN-CSE.
    Will show only self-announcement if no MN-CSE connected.
    """
    gateways = []
    try:
        params = {"fu": "1", "ty": "16"}
        headers = {**HEADERS, "X-M2M-RI": f"req-{uuid.uuid4()}"}
        resp = requests.get(
            "http://127.0.0.1:8080/~/id-in",
            headers=headers,
            params=params,
            timeout=5
        )

        if resp.status_code == 200:
            data = resp.json()
            uris = data.get("m2m:uril", [])
            
            for uri in uris:
                rn = uri.split("/")[-1]
                
                resource_url = f"http://127.0.0.1:8080/~/id-in/{uri}"
                resource_headers = {**HEADERS, "X-M2M-RI": f"req-{uuid.uuid4()}"}
                resource_resp = requests.get(resource_url, headers=resource_headers, timeout=3)
                
                if resource_resp.status_code == 200:
                    resource = resource_resp.json()
                    
                    if "m2m:csr" in resource:
                        gateways.append({
                            "name": rn,
                            "path": f"/id-in/{uri}",
                            "type": "MN-CSE (remoteCSE)"
                        })
                    elif "m2m:cb" in resource:
                        continue
                        
    except Exception as e:
        print(f"[ERROR] gateway_list: {e}")

    return render(request, "ui/gateway_list.html", {"gateways": gateways})


def analytics_page(request):
    all_devices = SensorReading.objects.values_list('device_name', flat=True).distinct()
    devices = sorted(set(all_devices))
    
    devices_json = json.dumps(list(devices))
    
    return render(request, "ui/analytics.html", {"devices": devices_json})