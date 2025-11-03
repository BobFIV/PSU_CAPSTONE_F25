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

# Adjust this to your actual CSEAnnc name (gateway)
GATEWAY_NAME = "cbA_id-mn_WeFgxO8cud"

# Adjust this to your container name inside AEAnnc
CONTAINER_NAME = "cntA_3e3M97AjNG"


# ---------------- BASIC UI VIEWS ----------------
def login_view(request):
    return render(request, "ui/login.html")

def logout_view(request):
    return render(request, "ui/login.html")

def home(request):
    return render(request, "ui/home.html")


# ---------------- DEVICE LIST ----------------
def devices_list(request):
    """
    For now: show a single device corresponding to one gateway (CSEAnnc).
    Later you can expand to dynamically list all gateways under /cse-in.
    """
    devices = [{"name": GATEWAY_NAME, "status": "online"}]
    return render(request, "ui/devices_list.html", {"devices": devices})



# ---------------- DEVICE DETAIL ----------------
def device_detail(request, device_name):
    """
    Display the most recent reading stored in the Django DB
    (populated via /notify).
    """
    # Get most recent temperature reading
    latest_temp = (
        SensorReading.objects
        .filter(device_name=device_name, sensor_type="temperature")
        .order_by("-timestamp")
        .first()
    )

    # Get most recent humidity (optional)
    latest_humidity = (
        SensorReading.objects
        .filter(device_name=device_name, sensor_type="humidity")
        .order_by("-timestamp")
        .first()
    )

    container_data = []
    if latest_temp:
        container_data.append(("temperature", latest_temp.value))
    if latest_humidity:
        container_data.append(("humidity", latest_humidity.value))

    return render(
        request,
        "ui/device_detail.html",
        {
            "device_name": device_name,
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
                    # Parse JSON string into Python dict
                    payload = json.loads(value)

                    # Extract fields
                    tempC = payload.get("tempC")
                    humidityPct = payload.get("humidityPct")

                    print(f"🌡️ tempC: {tempC}, 💧 humidityPct: {humidityPct}")

                    # Save to database if available
                    if tempC is not None:
                        SensorReading.objects.create(
                            device_name=GATEWAY_NAME,
                            sensor_type="temperature",
                            value=float(tempC)
                        )

                    if humidityPct is not None:
                        SensorReading.objects.create(
                            device_name=GATEWAY_NAME,
                            sensor_type="humidity",
                            value=float(humidityPct)
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
