from django.apps import AppConfig


class ProjdjangoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'projdjango'

    def ready(self):
        from projdjango.mobile_access import log_startup_network_info
        log_startup_network_info()
