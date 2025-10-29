# app/models.py
from django.db import models

class PzemReading(models.Model):
    nodeid = models.CharField(max_length=100, db_index=True)
    voltage = models.FloatField(null=True, blank=True)
    current = models.FloatField(null=True, blank=True)
    power = models.FloatField(null=True, blank=True)
    energy = models.FloatField(null=True, blank=True)
    pf = models.FloatField(null=True, blank=True)
    frequency = models.FloatField(null=True, blank=True)
    relay = models.CharField(max_length=10, blank=True, default="")
    timestamp_ist = models.CharField(max_length=64, blank=True, default="")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def as_dict(self):
        return {
            "nodeid": self.nodeid,
            "voltage": self.voltage,
            "current": self.current,
            "power": self.power,
            "energy": self.energy,
            "pf": self.pf,
            "frequency": self.frequency,
            "relay": self.relay,
            "timestamp_ist": self.timestamp_ist,
            "created": self.created.isoformat()
        }

    def __str__(self):
        return f"{self.nodeid} @ {self.created.isoformat()}"

class RelayState(models.Model):
    nodeid = models.CharField(max_length=100, unique=True)
    relay = models.CharField(max_length=3, choices=(('ON','ON'),('OFF','OFF')), default='ON')
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nodeid} -> {self.relay}"
