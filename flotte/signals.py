"""Signals FLOTTE — profil utilisateur à l'inscription, journal d'audit (traçabilité)."""
import threading
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from .models import (
    ProfilUtilisateur, AuditLog, Vehicule, Location, DocumentVehicule,
    Vente, Depense, Facture, Conducteur, Marque, Modele,
)

_thread_locals = threading.local()


def get_current_user():
    """Retourne l'utilisateur courant (défini par le middleware d'audit)."""
    return getattr(_thread_locals, 'user', None)


class AuditMiddleware:
    """Enregistre l'utilisateur courant pour le journal d'audit."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, 'user', None) if request else None
        try:
            return self.get_response(request)
        finally:
            _thread_locals.user = None


def _log_audit(instance, action, object_repr_max=200):
    """Crée une entrée AuditLog (sans faire remonter les erreurs)."""
    try:
        model_name = instance._meta.label
        object_id = str(instance.pk) if instance.pk else ''
        object_repr = str(instance)[:object_repr_max] if instance else ''
        AuditLog.objects.create(
            user=get_current_user(),
            action=action,
            model_name=model_name,
            object_id=object_id,
            object_repr=object_repr,
        )
    except Exception:
        pass


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profil_utilisateur(sender, instance, created, **kwargs):
    """Crée un ProfilUtilisateur pour tout nouvel utilisateur."""
    if created and not hasattr(instance, 'profil_flotte'):
        ProfilUtilisateur.objects.get_or_create(
            user=instance,
            defaults={'role': 'admin' if instance.is_superuser else 'user'}
        )


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def send_welcome_email_on_signup(sender, instance, created, **kwargs):
    """Envoie l'email de bienvenue à tout nouvel utilisateur ayant une adresse email."""
    if created:
        from .emails import send_welcome_email
        send_welcome_email(instance)


@receiver(post_save, sender=Vehicule)
def audit_vehicule_save(sender, instance, created, **kwargs):
    if sender is Vehicule:
        _log_audit(instance, 'create' if created else 'update')


@receiver(post_delete, sender=Vehicule)
def audit_vehicule_delete(sender, instance, **kwargs):
    _log_audit(instance, 'delete')


@receiver(post_save, sender=Location)
def audit_location_save(sender, instance, created, **kwargs):
    if sender is Location:
        _log_audit(instance, 'create' if created else 'update')


@receiver(post_delete, sender=Location)
def audit_location_delete(sender, instance, **kwargs):
    _log_audit(instance, 'delete')


@receiver(post_save, sender=DocumentVehicule)
def audit_document_save(sender, instance, created, **kwargs):
    if sender is DocumentVehicule:
        _log_audit(instance, 'create' if created else 'update')


@receiver(post_delete, sender=DocumentVehicule)
def audit_document_delete(sender, instance, **kwargs):
    _log_audit(instance, 'delete')


# ——— Audit étendu : Vente, Depense, Facture, Conducteur, Utilisateurs, Paramétrage ———

@receiver(post_save, sender=Vente)
def audit_vente_save(sender, instance, created, **kwargs):
    _log_audit(instance, 'create' if created else 'update')


@receiver(post_delete, sender=Vente)
def audit_vente_delete(sender, instance, **kwargs):
    _log_audit(instance, 'delete')


@receiver(post_save, sender=Depense)
def audit_depense_save(sender, instance, created, **kwargs):
    _log_audit(instance, 'create' if created else 'update')


@receiver(post_delete, sender=Depense)
def audit_depense_delete(sender, instance, **kwargs):
    _log_audit(instance, 'delete')


@receiver(post_save, sender=Facture)
def audit_facture_save(sender, instance, created, **kwargs):
    _log_audit(instance, 'create' if created else 'update')


@receiver(post_delete, sender=Facture)
def audit_facture_delete(sender, instance, **kwargs):
    _log_audit(instance, 'delete')


@receiver(post_save, sender=Conducteur)
def audit_conducteur_save(sender, instance, created, **kwargs):
    _log_audit(instance, 'create' if created else 'update')


@receiver(post_delete, sender=Conducteur)
def audit_conducteur_delete(sender, instance, **kwargs):
    _log_audit(instance, 'delete')


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def audit_user_save(sender, instance, created, **kwargs):
    if created:
        _log_audit(instance, 'create')


@receiver(post_delete, sender=settings.AUTH_USER_MODEL)
def audit_user_delete(sender, instance, **kwargs):
    _log_audit(instance, 'delete')


@receiver(post_save, sender=Marque)
def audit_marque_save(sender, instance, created, **kwargs):
    _log_audit(instance, 'create' if created else 'update')


@receiver(post_delete, sender=Marque)
def audit_marque_delete(sender, instance, **kwargs):
    _log_audit(instance, 'delete')


@receiver(post_save, sender=Modele)
def audit_modele_save(sender, instance, created, **kwargs):
    _log_audit(instance, 'create' if created else 'update')


@receiver(post_delete, sender=Modele)
def audit_modele_delete(sender, instance, **kwargs):
    _log_audit(instance, 'delete')
