# project/urls.py
from django.contrib import admin
from django.urls import path, include  # include your app URLs here

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('ui.urls')),  # Include ui app URLs and handle the root URL
]