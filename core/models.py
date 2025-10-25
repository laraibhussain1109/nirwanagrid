from django.db import models

# Create your models here.


class PzemReading(models.Model):
    nodeid    = models.CharField(max_length=64)
    voltage   = models.FloatField(null=True, blank=True)
    current   = models.FloatField(null=True, blank=True)
    power     = models.FloatField(null=True, blank=True)
    energy    = models.FloatField(null=True, blank=True)
    pf        = models.FloatField(null=True, blank=True)
    frequency = models.FloatField(null=True, blank=True)
    relay     = models.CharField(max_length=8, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nodeid} @ {self.created_at}"
