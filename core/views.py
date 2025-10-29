from django.shortcuts import render

# Create your views here.
import json
import os
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .models import PzemReading
from django.shortcuts import render

# configure this env var on PythonAnywhere web UI or settings.py
API_KEY = "Chutiya@123"

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

# app/views.py
import json
import time
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import PzemReading, RelayState
from django.conf import settings

# NOTE: store this in settings.py in production
API_SECRET = getattr(settings, "PZEM_API_SECRET", "Chutiya@123")
API_KEY_META = 'HTTP_X_API_KEY'  # header 'X-API-KEY' accessible via request.META

def check_api_key(request):
    return request.META.get(API_KEY_META) == API_SECRET

@csrf_exempt
def pzem_post_view(request):
    """
    POST /api/pzem/  -- expects JSON from ESP32 with fields:
       nodeid, voltage, current, power, energy, pf, frequency, relay, timestamp_ist
    Header: X-API-KEY required
    """
    if request.method != "POST":
        return JsonResponse({"detail":"Method not allowed"}, status=405)

    if not check_api_key(request):
        return JsonResponse({"detail":"Unauthorized"}, status=401)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return JsonResponse({"detail":"Invalid JSON", "error": str(e)}, status=400)

    # Required minimal field
    nodeid = data.get("nodeid")
    if not nodeid:
        return JsonResponse({"detail":"Missing nodeid"}, status=400)

    # Create reading - using `.get()` with default None for numeric fields
    try:
        reading = PzemReading.objects.create(
            nodeid = nodeid,
            voltage = try_parse_float(data.get("voltage")),
            current = try_parse_float(data.get("current")),
            power = try_parse_float(data.get("power")),
            energy = try_parse_float(data.get("energy")),
            pf = try_parse_float(data.get("pf")),
            frequency = try_parse_float(data.get("frequency")),
            relay = str(data.get("relay","")).upper(),
            timestamp_ist = str(data.get("timestamp_ist",""))
        )
    except Exception as e:
        return JsonResponse({"detail":"Failed to save", "error": str(e)}, status=500)

    # Ensure RelayState exists so control endpoint works
    RelayState.objects.get_or_create(nodeid=nodeid)

    return JsonResponse({"detail":"Saved", "id": reading.id}, status=201)

def try_parse_float(v):
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None

def latest_reading_view(request, nodeid):
    """
    GET /api/pzem/latest/<nodeid>/
    Returns latest reading as JSON (fields listed by the user)
    """
    latest = PzemReading.objects.filter(nodeid=nodeid).order_by('-created').first()
    if not latest:
        return JsonResponse({"detail":"No data"}, status=404)
    return JsonResponse(latest.as_dict())

@csrf_exempt
def control_view(request, nodeid):
    """
    GET -> current desired relay state
    POST -> set desired relay state (requires X-API-KEY)
    """
    if request.method == 'GET':
        obj, _ = RelayState.objects.get_or_create(nodeid=nodeid)
        return JsonResponse({'nodeid': nodeid, 'relay': obj.relay, 'updated': obj.updated.isoformat()})
    elif request.method == 'POST':
        if not check_api_key(request):
            return JsonResponse({'detail': 'Unauthorized'}, status=401)
        try:
            payload = json.loads(request.body.decode('utf-8'))
            r = str(payload.get('relay','')).upper()
            if r not in ('ON','OFF'):
                return JsonResponse({'detail':'Invalid relay value'}, status=400)
            obj, _ = RelayState.objects.get_or_create(nodeid=nodeid)
            obj.relay = r
            obj.save()
            return JsonResponse({'nodeid': nodeid, 'relay': obj.relay, 'updated': obj.updated.isoformat()})
        except Exception as e:
            return JsonResponse({'detail': str(e)}, status=400)
    else:
        return JsonResponse({'detail':'Method not allowed'}, status=405)


# SSE stream generator - yields new readings as they appear.
# WARNING: PythonAnywhere free tier may not permit long-lived connections, but this works if allowed.
def sse_stream(request):
    response = StreamingHttpResponse(event_stream_generator(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    return response

def event_stream_generator(poll_interval=1.0):
    """
    Poll DB for newest reading and yield when it changes.
    Yields full reading JSON.
    """
    last_id = None
    while True:
        latest = PzemReading.objects.order_by('-created').first()
        if latest and latest.id != last_id:
            last_id = latest.id
            payload = json.dumps(latest.as_dict())
            yield f"data: {payload}\n\n"
        time.sleep(poll_interval)


def dashboard(request):
    # show last 100 readings (or filtered)
    readings = PzemReading.objects.all()[:100]
    return render(request, "dashboard.html", {"readings": readings})
