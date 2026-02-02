"""Signals FLOTTE — création du profil utilisateur à l'inscription."""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import ProfilUtilisateur


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profil_utilisateur(sender, instance, created, **kwargs):
    """Crée un ProfilUtilisateur pour tout nouvel utilisateur."""
    if created and not hasattr(instance, 'profil_flotte'):
        ProfilUtilisateur.objects.get_or_create(
            user=instance,
            defaults={'role': 'admin' if instance.is_superuser else 'user'}
        )
