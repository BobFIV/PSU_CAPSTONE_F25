import requests
import json
import uuid
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from orchestrator.mappings import SUR_MAP
from orchestrator.save_handlers import save_rssi, save_temperature
from .models import HandoverState, SensorReading

MAC_DEVICE_MAP = {
    "SEEED_XIAO": "D2:29:B2:D0:66:FC",
    "ESP32": "7C:DF:A1:FB:72:7D"
}

BASE_URL = "http://127.0.0.1:8080/~/id-in/cse-in"

HEADERS = {
    "X-M2M-Origin": "CAdmin",
    "X-M2M-RVI": "3",
    "Accept": "application/json",
}



# =============================================================================
# BASIC UI ROUTES
# =============================================================================

def login_view(request):
    return render(request, "ui/login.html")

def logout_view(request):
    return render(request, "ui/login.html")

def home(request):
    return render(request, "ui/home.html")


# =============================================================================
# DEVICE LIST
# =============================================================================

def device_list(request):
    devices = []
    try:
        params = {"fu": "1", "ty": "2"}  # Discover AEs
        headers = {**HEADERS, "X-M2M-RI": f"req-{uuid.uuid4()}"}

        resp = requests.get(
            f"{BASE_URL}",
            headers=headers,
            params=params,
            timeout=5
        )

        print("[DEBUG] Raw ACME response:", resp.text)

        if resp.status_code == 200:
            uris = resp.json().get("m2m:uril", [])
            for uri in uris:
                rn = uri.split("/")[-1]

                # Skip non-device AEs
                if rn.lower().startswith("gw-") or rn.lower() in ["orchestrator", "cadmin", "cloudappae"]:
                    continue

                ae_url = f"http://127.0.0.1:8080/~/id-in/{uri}"
                ae_resp = requests.get(
                    ae_url,
                    headers={**HEADERS, "X-M2M-RI": f"req-{uuid.uuid4()}"},
                    timeout=3
                )

                if ae_resp.status_code == 200:
                    ae = ae_resp.json().get("m2m:ae", {})

                    labels = [
                        l for l in ae.get("lbl", [rn])
                    ]

                    devices.append({
                        "name": rn,
                        "label": ", ".join(labels) if labels else rn,
                        "gateway": ae.get("api", "Unknown"),
                        "path": f"/id-in/{uri}",
                    })

    except Exception as e:
        print(f"[ERROR] device_list: {e}")

    return render(request, "ui/device_list.html", {"devices": devices})


# =============================================================================
# DEVICE DETAIL PAGE
# =============================================================================

def device_detail(request, device_name):
    mac = MAC_DEVICE_MAP.get(device_name, "None")
    latest_temp = (
        SensorReading.objects
        .filter(device_name=device_name, sensor_type="temperature")
        .order_by('-timestamp')
        .first()
    )

    # 🔍 Lookup HandoverState
    try:
        state = HandoverState.objects.get(mac=mac)
        current_gateway = f"Connected via {state.current_gateway}"
    except HandoverState.DoesNotExist:
        current_gateway = "No Gateway Status"

    container_data = []
    if latest_temp:
        container_data.append(("temperature", latest_temp.value))

    return render(request, "ui/device_detail.html", {
        "device_name": device_name,
        "container_data": container_data,
        "current_gateway": current_gateway,
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
            "device_name": latest.device_name,
            "sensor_type": latest.sensor_type,
            "value": latest.value,
            "timestamp": latest.timestamp.isoformat()
        })
    else:
        return JsonResponse({"error": "No data found"}, status=404)


def sensor_logs(request, device_name, sensor_type):
    logs = SensorReading.objects.filter(
        device_name=device_name,
        sensor_type=sensor_type
    ).order_by("-timestamp")[:50]

    return JsonResponse({
        "logs": [
            {"value": r.value, "timestamp": r.timestamp.isoformat()}
            for r in logs
        ]
    })

@csrf_exempt
def notify(request):
    try:
        body = json.loads(request.body.decode("utf-8"))

        sgn = body.get("m2m:sgn", {})
        sur = sgn.get("sur", "")
        sub_name = sur.split("/")[-1]

        mapping = SUR_MAP.get(sub_name)
        if not mapping:
            print(f"⚠ Unknown SUR: {sub_name}")
            return JsonResponse({}, status=200)

        cin = sgn.get("nev", {}).get("rep", {}).get("m2m:cin", {})
        con = json.loads(cin.get("con", "{}"))

        if mapping["type"] == "temperature":
            save_temperature(mapping["device"], con.get("tempC"))

        elif mapping["type"] == "rssi":
            save_rssi(
                gateway=mapping["gateway"],
                mac=con.get("mac"),
                rssi=con.get("rssi"),
                connected=con.get("connected", False)
            )

        return JsonResponse({}, status=200)

    except Exception as e:
        print("[ERROR] notify:", e)
        return JsonResponse({}, status=500)


# =============================================================================
# GATEWAY LIST
# =============================================================================

def current_gateway_api(request, device_name):
    mac = MAC_DEVICE_MAP.get(device_name, "None")
    try:
        from ui.models import HandoverState
        state = HandoverState.objects.get(mac=mac)
        return JsonResponse({"gateway": state.current_gateway})
    except HandoverState.DoesNotExist:
        return JsonResponse({"gateway": None})


def gateway_list(request):
    gateways = []
    try:
        params = {"fu": "1", "ty": "2"}  # Discover AEs
        headers = {**HEADERS, "X-M2M-RI": f"req-{uuid.uuid4()}"}

        resp = requests.get(
            f"{BASE_URL}",
            headers=headers,
            params=params,
            timeout=5
        )

        print("[DEBUG] Raw ACME response:", resp.text)

        if resp.status_code == 200:
            uris = resp.json().get("m2m:uril", [])
            for uri in uris:
                rn = uri.split("/")[-1]
                
                if rn.lower().startswith("gw-"):

                    ae_url = f"http://127.0.0.1:8080/~/id-in/{uri}"
                    ae_resp = requests.get(
                        ae_url,
                        headers={**HEADERS, "X-M2M-RI": f"req-{uuid.uuid4()}"},
                        timeout=3
                    )

                    if ae_resp.status_code == 200:
                        ae = ae_resp.json().get("m2m:ae", {})

                        labels = [
                            l for l in ae.get("lbl", [rn])
                            if l.lower() not in ["device"]
                        ]

                        gateways.append({
                            "name": rn,
                            "label": ", ".join(labels) if labels else rn,
                            "gateway": ae.get("api", "Unknown"),
                            "path": f"/id-in/{uri}",
                        })

    except Exception as e:
        print(f"[ERROR] device_list: {e}")

    return render(request, "ui/gateway_list.html", {"gateways": gateways})


# =============================================================================
# ANALYTICS
# =============================================================================

def analytics_page(request):
    devices = sorted(set(
        SensorReading.objects.values_list("device_name", flat=True)
    ))
    return render(
        request,
        "ui/analytics.html",
        {"devices": devices, "devices_json": json.dumps(list(devices))}
    )
