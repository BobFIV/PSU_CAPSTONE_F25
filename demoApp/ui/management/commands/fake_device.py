from django.core.management.base import BaseCommand
from ui.models import Device, Event
import random, time

class Command(BaseCommand):
    help = "Simulate IoT device updates realistically"

    def handle(self, *args, **kwargs):
        device, _ = Device.objects.get_or_create(
            name="esp32-01",
            device_type="ESP32",
        )

        # Start with some base values
        if device.battery == 0:
            device.battery = 100
            device.signal_strength = "Good"
            device.temperature = 25
            device.status = "Online"
            device.current_network = "WiFi"
            device.save()

        self.stdout.write(self.style.SUCCESS("Fake device started. Updating every 10 seconds..."))

        while True:
            old_status = device.status
            old_network = device.current_network
            old_battery = device.battery

            # Small chance of going offline temporarily
            if random.random() < 0.05:
                device.status = "Offline"
            else:
                device.status = "Online"

            if device.status == "Offline":
                # If offline, wipe other values
                device.signal_strength = "N/A"
                device.current_network = "None"
                device.temperature = None
            else:
                # Battery drains slowly
                if device.battery > 0 and random.random() < 0.3:
                    device.battery -= 1

                # Temperature drifts slightly
                device.temperature += random.choice([-0.2, 0, 0.2])

                # Small chance of network handover
                if random.random() < 0.05:
                    device.current_network = random.choice(["WiFi", "LTE", "BLE"])

                # Signal strength depends on network
                if device.current_network == "WiFi":
                    device.signal_strength = random.choice(["Good", "Excellent", "Fair"])
                elif device.current_network == "LTE":
                    device.signal_strength = random.choice(["Fair", "Good"])
                elif device.current_network == "BLE":
                    device.signal_strength = random.choice(["Weak", "Fair"])
                else:
                    device.signal_strength = "Unknown"

            device.save()

            # 🔹 Log Events if something important changed
            if device.status != old_status:
                Event.objects.create(device=device, message=f"Device went {device.status}")

            if device.current_network != old_network:
                Event.objects.create(device=device, message=f"Switched to {device.current_network}")

            if device.battery in [20, 10, 5] and device.battery != old_battery:
                Event.objects.create(device=device, message=f"Battery low at {device.battery}%")

            self.stdout.write(
                f"Updated {device.name}: "
                f"Battery={device.battery}%, "
                f"Signal={device.signal_strength}, "
                f"Temp={device.temperature:.1f}°C, "
                f"Status={device.status}, "
                f"Net={device.current_network}"
            )

            time.sleep(10)

