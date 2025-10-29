from django.urls import path
from . import views

urlpatterns = [
    path('api/pzem/', views.pzem_post_view),                          # POST from ESP32
    path('api/pzem/latest/<str:nodeid>/', views.latest_reading_view), # polling fallback
    path('api/pzem/control/<str:nodeid>/', views.control_view),       # control GET/POST
    path('api/pzem/stream/', views.sse_stream),
    path('api/pzem/', views.pzem_post, name='pzem_post'),
    path('pzem/dashboard/', views.dashboard, name='pzem_dashboard'),
]
