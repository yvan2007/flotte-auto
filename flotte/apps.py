from django.apps import AppConfig


class FlotteConfig(AppConfig):
    """Configuration de l'application FLOTTE."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'flotte'
    verbose_name = 'FLOTTE — Gestion parc véhicules'

    def ready(self):
        from . import signals  # noqa: F401
