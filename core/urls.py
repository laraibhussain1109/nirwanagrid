from django.urls import path
from . import views

urlpatterns = [
    path('api/pzem/', views.pzem_post, name='pzem_post'),
    path('pzem/dashboard/', views.dashboard, name='pzem_dashboard'),
]
