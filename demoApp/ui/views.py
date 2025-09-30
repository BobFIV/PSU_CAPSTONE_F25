from django.shortcuts import render, redirect
from .models import Device, Event
from django.http import JsonResponse
from datetime import timedelta
from django.utils import timezone
import pytz
from zoneinfo import ZoneInfo


def dashboard(request):
    device = Device.objects.order_by("-last_updated").first()
    events = Event.objects.order_by("-timestamp")[:10]  # last 10 events
    
    return render(request, "ui/dashboard.html", {"device": device, "events": events})


def home(request):
    return render(request, "ui/dashboard.html")

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
