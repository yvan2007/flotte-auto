"""
Actions personnalisées pour l'interface admin moderne
Ces actions peuvent être utilisées dans les ModelAdmin pour ajouter des fonctionnalités supplémentaires
"""
from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.admin.utils import model_ngettext
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _


def export_selected_csv(modeladmin, request, queryset):
    """
    Action pour exporter les éléments sélectionnés en CSV
    """
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{modeladmin.model.__name__}_export.csv"'
    
    writer = csv.writer(response)
    
    # Écrire les en-têtes
    if queryset.exists():
        first_obj = queryset.first()
        headers = [field.name for field in first_obj._meta.fields]
        writer.writerow(headers)
        
        # Écrire les données
        for obj in queryset:
            row = [getattr(obj, field.name, '') for field in obj._meta.fields]
            writer.writerow(row)
    
    return response
export_selected_csv.short_description = _("Exporter les éléments sélectionnés en CSV")


def mark_as_active(modeladmin, request, queryset):
    """
    Action pour marquer les éléments comme actifs (si le modèle a un champ 'active' ou 'is_active')
    """
    updated = 0
    for obj in queryset:
        if hasattr(obj, 'active'):
            obj.active = True
            obj.save(update_fields=['active'])
            updated += 1
        elif hasattr(obj, 'is_active'):
            obj.is_active = True
            obj.save(update_fields=['is_active'])
            updated += 1
    
    modeladmin.message_user(
        request,
        _("{} éléments marqués comme actifs.").format(updated),
    )
mark_as_active.short_description = _("Marquer comme actif")


def mark_as_inactive(modeladmin, request, queryset):
    """
    Action pour marquer les éléments comme inactifs
    """
    updated = 0
    for obj in queryset:
        if hasattr(obj, 'active'):
            obj.active = False
            obj.save(update_fields=['active'])
            updated += 1
        elif hasattr(obj, 'is_active'):
            obj.is_active = False
            obj.save(update_fields=['is_active'])
            updated += 1
    
    modeladmin.message_user(
        request,
        _("{} éléments marqués comme inactifs.").format(updated),
    )
mark_as_inactive.short_description = _("Marquer comme inactif")


def duplicate_selected(modeladmin, request, queryset):
    """
    Action pour dupliquer les éléments sélectionnés
    """
    duplicated = 0
    for obj in queryset:
        # Créer une copie de l'objet
        obj.pk = None
        # Si le modèle a un champ 'name' ou 'title', ajouter " (Copie)"
        if hasattr(obj, 'name'):
            obj.name = f"{obj.name} (Copie)"
        elif hasattr(obj, 'title'):
            obj.title = f"{obj.title} (Copie)"
        obj.save()
        duplicated += 1
    
    modeladmin.message_user(
        request,
        _("{} éléments dupliqués avec succès.").format(duplicated),
    )
duplicate_selected.short_description = _("Dupliquer les éléments sélectionnés")


def archive_selected(modeladmin, request, queryset):
    """
    Action pour archiver les éléments sélectionnés (si le modèle a un champ 'archived' ou 'is_archived')
    """
    archived = 0
    for obj in queryset:
        if hasattr(obj, 'archived'):
            obj.archived = True
            obj.save(update_fields=['archived'])
            archived += 1
        elif hasattr(obj, 'is_archived'):
            obj.is_archived = True
            obj.save(update_fields=['is_archived'])
            archived += 1
    
    modeladmin.message_user(
        request,
        _("{} éléments archivés avec succès.").format(archived),
    )
archive_selected.short_description = _("Archiver les éléments sélectionnés")
