"""
UserAdmin personnalisé avec interface améliorée
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .modern_model_admin import ModernTemplateMixin


class CustomUserAdmin(ModernTemplateMixin, BaseUserAdmin):
    """
    UserAdmin personnalisé avec une meilleure disposition des champs
    et une interface améliorée pour les permissions.
    """
    # Template personnalisé pour l'ajout (classique) / moderne via modern_add_form_template
    add_form_template = "admin_custom/auth/user/add_form.html"
    modern_add_form_template = "admin_custom/modern/auth/user/add_form.html"
    
    # Fieldsets améliorés pour l'édition
    fieldsets = (
        (_("Informations de connexion"), {
            "fields": ("username", "password"),
            "classes": ("wide", "collapse"),
            "description": "Identifiants de connexion de l'utilisateur"
        }),
        (_("Informations personnelles"), {
            "fields": ("first_name", "last_name", "email"),
            "classes": ("wide",),
            "description": "Informations de base sur l'utilisateur"
        }),
        (_("Permissions et statut"), {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
            ),
            "classes": ("wide",),
            "description": "Contrôle l'accès et les permissions de l'utilisateur"
        }),
        (_("Groupes et permissions"), {
            "fields": ("groups", "user_permissions"),
            "classes": ("wide", "collapse"),
            "description": "Gestion des groupes et permissions spécifiques"
        }),
        (_("Dates importantes"), {
            "fields": ("last_login", "date_joined"),
            "classes": ("collapse",),
            "description": "Informations sur les dates de connexion et d'inscription"
        }),
    )
    
    # Fieldsets améliorés pour l'ajout
    add_fieldsets = (
        (_("Informations de connexion"), {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2"),
            "description": "Créez les identifiants de connexion pour le nouvel utilisateur"
        }),
        (_("Informations personnelles"), {
            "classes": ("wide",),
            "fields": ("first_name", "last_name", "email"),
            "description": "Informations de base (optionnelles)"
        }),
        (_("Permissions initiales"), {
            "classes": ("wide",),
            "fields": ("is_active", "is_staff", "is_superuser"),
            "description": "Définissez les permissions initiales de l'utilisateur"
        }),
    )
    
    # Affichage dans la liste
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active", "is_superuser", "date_joined")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups", "date_joined")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("-date_joined",)
    
    # Filtres horizontaux pour les groupes et permissions
    filter_horizontal = ("groups", "user_permissions")
    
    # Amélioration de l'affichage des champs
    readonly_fields = ("last_login", "date_joined")
    
    def get_fieldsets(self, request, obj=None):
        """Retourne les fieldsets appropriés selon le contexte (ajout ou édition)"""
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)
    
    def get_form(self, request, obj=None, **kwargs):
        """Utilise le formulaire spécial lors de la création d'utilisateur"""
        defaults = {}
        if obj is None:
            defaults["form"] = self.add_form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)
