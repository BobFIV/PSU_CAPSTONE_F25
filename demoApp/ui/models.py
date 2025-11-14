from django.db import models
from django.utils import timezone

class Device(models.Model):
    name = models.CharField(max_length=100)   # e.g. esp32-01
    device_type = models.CharField(max_length=50)  # e.g. ESP32, Thingy:91
    battery = models.IntegerField(null=True, blank=True)
    signal_strength = models.CharField(max_length=50, null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)
    current_network = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=20, default="Offline")  # Online/Offline
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.device_type})"

class Event(models.Model):
    device = models.ForeignKey("Device", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    message = models.TextField()

    def __str__(self):
        return f"[{self.timestamp}] {self.device.name}: {self.message}"

class SensorReading(models.Model):
    """
    Store historical sensor readings for logging/charting.
    Each time we fetch data from CSE, we save it here.
    """
    device_name = models.CharField(max_length=100, db_index=True)  # AE name
    sensor_type = models.CharField(max_length=50, db_index=True)  # battery, temperature, signal, humiditymac = models.CharField(max_length=32, blank=True, null=True)  # ✅ new
    mac = models.CharField(max_length=32, blank=True, null=True)  # ✅ new
    value = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']  # Newest first
        indexes = [
            models.Index(fields=['device_name', 'sensor_type', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.device_name} - {self.sensor_type}: {self.value} at {self.timestamp} from {self.mac}"