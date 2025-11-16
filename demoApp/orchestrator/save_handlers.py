from orchestrator.mappings import MAC_DEVICE_MAP
from orchestrator.rssi_logic import evaluate_handover
from ui.models import HandoverState, SensorReading, RSSIReading
from django.utils.timezone import now

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

        #print(f"🌡 DB: Saved temperature {tempC} for {device_name}")

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

