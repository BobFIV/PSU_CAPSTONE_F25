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