from django.shortcuts import render, redirect
from .models import Device, Event
from django.http import JsonResponse
from datetime import timedelta
from django.utils import timezone
import pytz
from zoneinfo import ZoneInfo
from django.http import JsonResponse
import requests

BASE_URL = "http://54.164.106.20:8080/cse-in/DummyData"
HEADERS = {
    "X-M2M-Origin": "CAdmin",
    "X-M2M-RVI": "3",
    "X-M2M-RI": "tempReq2",
    "Accept": "application/json"
}

def dashboard(request):
    device = Device.objects.order_by("-last_updated").first()
    events = Event.objects.order_by("-timestamp")[:10]  # last 10 events
    
    return render(request, "ui/dashboard.html", {"device": device, "events": events})


def home(request):
    return render(request, "ui/dashboard.html")

def get_sensor_data(request):
    containers = ["temperature", "humidity", "battery", "signal"]  # add more as available
    data = {}

    for c in containers:
        try:
            url = f"{BASE_URL}/{c}/la"
            response = requests.get(url, headers=HEADERS, timeout=3)
            if response.status_code == 200:
                value = response.json().get("m2m:cin", {}).get("con", "N/A")
            else:
                value = "N/A"
        except Exception as e:
            print(f"Error fetching {c}: {e}")
            value = "N/A"
        data[c] = value

    return JsonResponse(data)


def latest_data(request):
    device = Device.objects.order_by("-last_updated").first()
    events = Event.objects.order_by("-timestamp")[:5]
    eastern = ZoneInfo("America/New_York")

    if device:
        # check if device is stale (>60s since last update)
        stale = device.last_updated < timezone.now() - timedelta(seconds=15)

        if stale:
            new_status = "offline"
        else:
            # keep whatever status device_manager.py wrote (Online/Offline)
            new_status = device.status or "online"

        # log status change
        if device.status != new_status:
            Event.objects.create(
                device=device,
                message=f"Device went {new_status.capitalize()}"
            )
            device.status = new_status
            device.save(update_fields=["status"])

        # hide metrics if offline
        if new_status == "offline":
            battery = None
            signal = None
            temperature = None
            network = None
        else:
            battery = device.battery
            signal = device.signal_strength
            temperature = device.temperature
            network = device.current_network

        device_data = {
            "name": device.name,
            "battery": battery,
            "signal": signal,
            "temperature": temperature,
            "status": new_status,
            "network": network,
        }
    else:
        device_data = None

    data = {
        "device": device_data,
        "events": [
            {
                "timestamp": e.timestamp.astimezone(eastern).strftime("%Y-%m-%d %H:%M:%S"),
                "device": e.device.name,
                "message": e.message,
            }
            for e in events
        ],
    }
    return JsonResponse(data)
