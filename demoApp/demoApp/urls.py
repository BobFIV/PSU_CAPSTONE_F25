from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # 👇 add this line so django-plotly-dash registers its namespace
    path('django_plotly_dash/', include('django_plotly_dash.urls')),

    # your UI app
    path('', include('ui.urls')),
]
