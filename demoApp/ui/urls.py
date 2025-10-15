# ui/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name ='login'),
    path('home/', views.home, name='home'),  # Home page
    path('devices/', views.devices_list, name='devices_list'),  # Correct path for device list
    path('logout/', views.logout_view, name ='logout'),
   path('device-detail/<str:device_name>/', views.device_detail, name='device_detail'),
]