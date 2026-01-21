from django.apps import AppConfig


class VsoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "vso"

    def ready(self):
        import vso.signals  # noqa: F401
