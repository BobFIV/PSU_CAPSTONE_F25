# ui/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('home/', views.home, name='home'),
    path('devices/', views.devices_list, name='devices_list'),
    path('logout/', views.logout_view, name='logout'),
    path('device-detail/<str:device_name>/', views.device_detail, name='device_detail'),
    path('notify', views.notify, name='notify'),
    
    # New API endpoint for sensor logs
    path('api/logs/<str:device_name>/<str:sensor_type>/', views.sensor_logs, name='sensor_logs'),
]