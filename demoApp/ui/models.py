from django.db import models
from django.utils import timezone


# =============================================================================
# DEVICE + EVENT MODELS (your existing ones)
# =============================================================================

class Device(models.Model):
    name = models.CharField(max_length=100)           # Example: esp32-01
    device_type = models.CharField(max_length=50)     # Example: ESP32, Thingy:91
    battery = models.IntegerField(null=True, blank=True)
    signal_strength = models.CharField(max_length=50, null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)
    current_network = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=20, default="Offline")  # Online / Offline
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.device_type})"


class Event(models.Model):
    device = models.ForeignKey("Device", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    message = models.TextField()

    def __str__(self):
        return f"[{self.timestamp}] {self.device.name}: {self.message}"


# =============================================================================
# SENSOR READING (existing)
# =============================================================================

class SensorReading(models.Model):
    """
    Generic container for any type of sensor reading.
    Temperature, battery, RSSI (combined), and misc.
    """
    device_name = models.CharField(max_length=100, db_index=True)
    sensor_type = models.CharField(max_length=50, db_index=True)
    mac = models.CharField(max_length=32, blank=True, null=True)

    # - temperature → Celsius
    # - rssi_x → RSSI values
    # - More types stored as float
    value = models.FloatField()

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["device_name", "sensor_type", "-timestamp"]),
        ]

    def __str__(self):
        return (
            f"{self.device_name} - {self.sensor_type}: "
            f"{self.value} at {self.timestamp} (mac={self.mac})"
        )


# =============================================================================
# RSSI READINGS (per gateway) — needed for handover decision logic
# =============================================================================

class RSSIReading(models.Model):
    """
    Every RSSI scan report from any gateway.
    The orchestrator will choose best gateway from this table.
    """
    mac = models.CharField(max_length=32, db_index=True)
    gateway = models.CharField(max_length=64, db_index=True)   # gw-A, gw-B, etc.
    rssi = models.IntegerField()
    connected = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["mac", "timestamp"]),
            models.Index(fields=["mac", "gateway", "-timestamp"]),
        ]

    def __str__(self):
        return (
            f"MAC={self.mac} via {self.gateway}: RSSI={self.rssi} "
            f"connected={self.connected} at {self.timestamp}"
        )


# =============================================================================
# CURRENT GATEWAY STATE — Orchestrator's truth for each device
# =============================================================================

class HandoverState(models.Model):
    """
    Stores which gateway the device is CURRENTLY attached to.
    Updated whenever 'connected=True' shows up in scan reports.
    """
    mac = models.CharField(max_length=32, unique=True)
    current_gateway = models.CharField(max_length=64)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.mac} → {self.current_gateway} (last seen {self.last_seen})"


# =============================================================================
# HANDOVER HISTORY — Optional but extremely useful for debugging
# =============================================================================

class HandoverEvent(models.Model):
    """
    Whenever the orchestrator triggers a handover, we save:
    - which device
    - from → to gateway
    - RSSI reason
    """
    mac = models.CharField(max_length=32)
    from_gateway = models.CharField(max_length=64)
    to_gateway = models.CharField(max_length=64)
    old_rssi = models.IntegerField()
    new_rssi = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"Handover {self.mac}: {self.from_gateway} → {self.to_gateway} "
            f"(RSSI {self.old_rssi} → {self.new_rssi}) at {self.timestamp}"
        )
