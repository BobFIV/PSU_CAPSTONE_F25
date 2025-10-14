from django.urls import path
from . import views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('get_sensor_data/', views.get_sensor_data, name='get_sensor_data'),
]
