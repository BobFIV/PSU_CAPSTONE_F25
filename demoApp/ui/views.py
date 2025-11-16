import time
import requests
import json
import uuid
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import HandoverEvent, HandoverState, SensorReading, RSSIReading
from django.utils.timezone import now

# ---------------------------------------
# OneM2M base config
# ---------------------------------------

BASE_URL = "http://127.0.0.1:8080/~/id-in/cse-in"

HEADERS = {
    "X-M2M-Origin": "CAdmin",
    "X-M2M-RVI": "3",
    "Accept": "application/json",
}

# ---------------------------------------
# MAC → Device name mapping
# ---------------------------------------
MAC_DEVICE_MAP = {
    "D2:29:B2:D0:66:FC": "SEEED_XIAO",
    # Add ESP32 here later
}

# ---------------------------------------
# Subscription → processing mapping
# ---------------------------------------
SUR_MAP = {
    "subLv4fd0fZH5": {    # Example: temp subscription
        "type": "temperature",
        "device": "SEEED_XIAO",
    },
    "subIGPRVOogVb": {    # Example: RSSI from gw-B
        "type": "rssi",
        "gateway": "gw-B",
    },
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
                        if l.lower() not in ["device", "gateway", "orchestrator"]
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


# =============================================================================
# SAVE HELPERS
# =============================================================================

def save_temperature(device_name, tempC):
    try:
        if tempC is None:
            print("⚠ save_temperature: Missing tempC")
            return

        SensorReading.objects.create(
            device_name=device_name,
            sensor_type="temperature",
            value=float(tempC),
            timestamp=now()
        )

        print(f"🌡 DB: Saved temperature {tempC} for {device_name}")

    except Exception as e:
        print(f"[ERROR] save_temperature: {e}")


def save_rssi(gateway, mac, rssi, connected):
    try:
        device_name = MAC_DEVICE_MAP.get(mac)
        if not device_name:
            print(f"⚠ Unknown MAC {mac}, ignoring")
            return
        
        # Store RSSI in the RSSIReading model
        RSSIReading.objects.create(
            mac=mac,
            gateway=gateway,
            rssi=float(rssi),
            connected=connected,
            timestamp=now()
        )

        print(f"📡 DB: Saved RSSI {rssi} dBm for {mac} via {gateway}")

        # If connected=True → update orchestrator current gateway
        if connected:
            HandoverState.objects.update_or_create(
                mac=mac,
                defaults={"current_gateway": gateway}
            )

        # Run the orchestrator logic
        evaluate_handover(mac)

    except Exception as e:
        print(f"[ERROR] save_rssi: {e}")



# =============================================================================
# GATEWAY TRACKING
# =============================================================================

# RSSI thresholds
RSSI_BAD_THRESHOLD = -80   # below this is considered poor connection
RSSI_HANDOVER_MARGIN = 12  # new GW must be stronger by this amount

def latest_rssi(mac, gateway):
    last = RSSIReading.objects.filter(mac=mac, gateway=gateway).order_by('-timestamp').first()
    return last.rssi if last else -200

def evaluate_handover(mac):
    try:
        state = HandoverState.objects.get(mac=mac)
    except HandoverState.DoesNotExist:
        print(f"⚠ No handover state for {mac}")
        return

    current_gw = state.current_gateway

    # Get the latest scan reports
    scans = RSSIReading.objects.filter(mac=mac).order_by('-timestamp')[:4]
    if not scans:
        return
    
    # Determine the best gateway based on highest RSSI
    best_gateway = None
    best_rssi = -200

    for s in scans:
        if s.rssi > best_rssi:
            best_rssi = s.rssi
            best_gateway = s.gateway

    if best_gateway is None:
        return

    current_rssi = latest_rssi(mac, current_gw)

    # 1. If the current gateway is still clearly dominant → do nothing
    if current_rssi > best_rssi - RSSI_HANDOVER_MARGIN:
        return

    # 2. Only switch when current gateway is truly bad
    if current_rssi > RSSI_BAD_THRESHOLD:
        return

    # 3. Perform handover
    trigger_handover(mac, current_gw, best_gateway)


def trigger_handover(mac, old_gw, new_gw):
    print(f"\n🔀 Handover required for {mac}: {old_gw} → {new_gw}\n")

    # Remove from every gateway's whitelist
    gateways = ["gw-A", "gw-B", "gw-C"]   # adjust to your config
    for gw in gateways:
        post_inbox_command(gw, f"WL_DEL {mac}")

    time.sleep(0.2)

    # Add to new gateway
    post_inbox_command(new_gw, f"WL_ADD {mac}")

    # Disconnect from old gateway
    post_inbox_command(old_gw, f"DC {mac}")

    # Update state
    HandoverState.objects.update_or_create(mac=mac, defaults={"current_gateway": new_gw})

    # Log event
    HandoverEvent.objects.create(mac=mac, from_gw=old_gw, to_gw=new_gw)

    print(f"✅ Handover complete {mac}: {old_gw} → {new_gw}")

def post_inbox_command(gateway, command):
    try:
        url = f"http://127.0.0.1:8080/cse-in/{gateway}/inbox"
        headers = {
            "X-M2M-Origin": "CAdmin",
            "X-M2M-RI": f"req-{uuid.uuid4()}",
            "X-M2M-RVI": "3",
            "Content-Type": "application/json;ty=4",
        }
        payload = {
            "m2m:cin": {
                "con": command
            }
        }

        r = requests.post(url, headers=headers, json=payload)
        if r.status_code in (200, 201):
            print(f"📤 Sent command to {gateway}: {command}")
        else:
            print(f"⚠ Inbox command failed: {r.status_code} {r.text}")

    except Exception as e:
        print(f"[ERROR] post_inbox_command: {e}")


def update_current_gateway(mac, gateway):
    """
    Stores which gateway the device is CURRENTLY attached to.
    """
    print(f"🔗 Device {mac} → connected to {gateway}")

    # TODO: requires creating HandoverState model
    # HandoverState.objects.update_or_create(
    #     mac=mac,
    #     defaults={"current_gateway": gateway}
    # )


# =============================================================================
# NOTIFICATION (main entry point)
# =============================================================================

@csrf_exempt
def notify(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
        print("\n📥 Notification received:\n")

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

def gateway_list(request):
    gateways = []
    try:
        params = {"fu": "1", "ty": "16"}  # Discover CSEAnncs
        resp = requests.get(
            "http://127.0.0.1:8080/~/id-in",
            headers={**HEADERS, "X-M2M-RI": f"req-{uuid.uuid4()}"},
            params=params,
            timeout=5
        )

        if resp.status_code == 200:
            for uri in resp.json().get("m2m:uril", []):
                url = f"http://127.0.0.1:8080/~/id-in/{uri}"
                r = requests.get(url, headers=HEADERS, timeout=3)
                if "m2m:csr" in r.json():
                    gateways.append({
                        "name": uri.split("/")[-1],
                        "path": f"/id-in/{uri}",
                        "type": "MN-CSE"
                    })

    except Exception as e:
        print(f"[ERROR] gateway_list: {e}")

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
