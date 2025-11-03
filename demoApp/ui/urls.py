# ui/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('home/', views.home, name='home'),
    path('devices/', views.device_list, name='device_list'),
    path('logout/', views.logout_view, name='logout'),
    path('devices/<str:device_name>/', views.device_detail, name='device_detail'),
    path('notify', views.notify, name='notify'),
    path('gateways/', views.gateway_list, name='gateway_list'),
    path('api/latest/<str:device_name>/<str:sensor_type>/', views.latest_value, name='latest_value'),
    path('api/logs/<str:device_name>/<str:sensor_type>/', views.sensor_logs, name='sensor_logs'),
]