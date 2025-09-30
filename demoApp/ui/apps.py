from django.apps import AppConfig

class UiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ui'

    def ready(self):
        import ui.dash_apps.simple_chart
        import ui.dash_apps.bar_chart
