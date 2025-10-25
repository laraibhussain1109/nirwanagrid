from django.shortcuts import render

# Create your views here.
import json
import os
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .models import PzemReading
from django.shortcuts import render

# configure this env var on PythonAnywhere web UI or settings.py
API_KEY = os.environ.get("PZEM_API_KEY", "changeme_replace_with_env")

@csrf_exempt
def pzem_post(request):
    # Simple API key header: X-API-KEY
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST allowed")

    key = request.headers.get('X-API-KEY') or request.META.get('HTTP_X_API_KEY')
    if key != API_KEY:
        return HttpResponseForbidden("Forbidden")

    try:
        data = json.loads(request.body)
    except Exception as e:
        return HttpResponseBadRequest("Invalid JSON")

    # basic validation (tolerant)
    nodeid = data.get("nodeid") or data.get("id") or "NODE"
    reading = PzemReading.objects.create(
        nodeid=nodeid,
        voltage=data.get("voltage"),
        current=data.get("current"),
        power=data.get("power"),
        energy=data.get("energy"),
        pf=data.get("pf"),
        frequency=data.get("frequency"),
        relay=data.get("relay", "")
    )
    return JsonResponse({"status": "ok", "id": reading.id})

def dashboard(request):
    # show last 100 readings (or filtered)
    readings = PzemReading.objects.all()[:100]
    return render(request, "dashboard.html", {"readings": readings})
