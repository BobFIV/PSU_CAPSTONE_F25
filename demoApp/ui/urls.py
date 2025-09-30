from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='home'),       # root ("/") now shows dashboard
    path('latest/', views.latest_data, name='latest_data'),
    path("dashboard/", views.dashboard, name="dashboard"),
]
