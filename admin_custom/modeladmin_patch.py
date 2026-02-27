"""
Monkey-patch global de ModelAdmin pour forcer les templates personnalisés.

Ce module garantit que TOUS les ModelAdmin utilisent les templates personnalisés
selon l'interface active (classique ou moderne), même ceux qui n'héritent pas
de ModernTemplateMixin ou qui sont enregistrés par des packages tiers.
"""
from django.contrib import admin
from django.template.response import TemplateResponse
from django.http import HttpResponse

from .auth_views import SESSION_INTERFACE_KEY, INTERFACE_MODERN


def _use_modern_templates(request):
    """Détecte si l'interface moderne est active."""
    return request.session.get(SESSION_INTERFACE_KEY) == INTERFACE_MODERN


def _force_template_on_instance_and_class(admin_instance, template_name, request):
    """
    Force un template sur une instance ModelAdmin et sa classe, ainsi que
    toutes les classes parentes dans le MRO (Method Resolution Order).
    """
    # Forcer sur l'instance
    admin_instance.change_list_template = template_name
    admin_instance.change_form_template = template_name
    
    # Forcer sur la classe
    admin_class = admin_instance.__class__
    admin_class.change_list_template = template_name
    admin_class.change_form_template = template_name
    
    # Forcer sur toutes les classes parentes dans le MRO
    for cls in admin_class.__mro__:
        if issubclass(cls, admin.ModelAdmin) and cls != admin.ModelAdmin:
            cls.change_list_template = template_name
            cls.change_form_template = template_name


def patched_changelist_view(self, request, extra_context=None):
    """
    Version patchée de changelist_view qui force les templates personnalisés.
    """
    use_modern = _use_modern_templates(request)
    
    # Déterminer le template à utiliser
    if use_modern:
        template_name = 'admin_custom/modern/change_list.html'
        admin_base_template = 'admin_custom/modern/admin_base.html'
    else:
        template_name = 'admin_custom/change_list.html'
        admin_base_template = 'admin_custom/base.html'
    
    # Forcer le template sur l'instance, la classe et toutes les classes parentes
    _force_template_on_instance_and_class(self, template_name, request)
    
    # Ajouter admin_base_template au contexte
    if extra_context is None:
        extra_context = {}
    extra_context['admin_base_template'] = admin_base_template
    
    # Appeler la méthode originale (qui peut être celle de ModernTemplateMixin)
    try:
        response = self._original_changelist_view(request, extra_context)
        
        # Intercepter TemplateResponse : forcer le template personnalisé en mode classique ET moderne
        # (en mode classique, sans ça, la réponse peut encore utiliser admin/change_list.html → cadre Django)
        if isinstance(response, TemplateResponse):
            resp_name = str(response.template_name)
            if 'admin/change_list.html' in resp_name and 'admin_custom' not in resp_name:
                response.template_name = template_name
                if 'admin_base_template' not in response.context_data:
                    response.context_data['admin_base_template'] = admin_base_template
        
        return response
    except Exception:
        # En cas d'erreur, essayer d'appeler directement la méthode parente
        return admin.ModelAdmin.changelist_view(self, request, extra_context)


def patched_changeform_view(self, request, object_id=None, form_url='', extra_context=None):
    """
    Version patchée de changeform_view qui force les templates personnalisés.
    """
    use_modern = _use_modern_templates(request)
    
    # Déterminer le template à utiliser
    if use_modern:
        template_name = 'admin_custom/modern/change_form.html'
        admin_base_template = 'admin_custom/modern/admin_base.html'
    else:
        template_name = 'admin_custom/change_form.html'
        admin_base_template = 'admin_custom/base.html'
    
    # Forcer le template sur l'instance, la classe et toutes les classes parentes
    _force_template_on_instance_and_class(self, template_name, request)
    
    # Ajouter admin_base_template au contexte
    if extra_context is None:
        extra_context = {}
    extra_context['admin_base_template'] = admin_base_template
    
    # Appeler la méthode originale (qui peut être celle de ModernTemplateMixin)
    try:
        response = self._original_changeform_view(request, object_id, form_url, extra_context)
        
        # Intercepter TemplateResponse : forcer le template personnalisé en mode classique ET moderne
        if isinstance(response, TemplateResponse):
            resp_name = str(response.template_name)
            if 'admin/change_form.html' in resp_name and 'admin_custom' not in resp_name:
                response.template_name = template_name
                if 'admin_base_template' not in response.context_data:
                    response.context_data['admin_base_template'] = admin_base_template
        
        return response
    except Exception:
        # En cas d'erreur, essayer d'appeler directement la méthode parente
        return admin.ModelAdmin.changeform_view(self, request, object_id, form_url, extra_context)


def patch_modeladmin():
    """
    Monkey-patch global de ModelAdmin pour forcer les templates personnalisés.
    
    Cette fonction doit être appelée très tôt dans le processus de démarrage,
    idéalement dans admin_custom/apps.py avant l'enregistrement des modèles.
    """
    # Sauvegarder les méthodes originales si elles n'ont pas déjà été sauvegardées
    if not hasattr(admin.ModelAdmin, '_original_changelist_view'):
        admin.ModelAdmin._original_changelist_view = admin.ModelAdmin.changelist_view
    if not hasattr(admin.ModelAdmin, '_original_changeform_view'):
        admin.ModelAdmin._original_changeform_view = admin.ModelAdmin.changeform_view
    
    # Remplacer par les versions patchées
    admin.ModelAdmin.changelist_view = patched_changelist_view
    admin.ModelAdmin.changeform_view = patched_changeform_view
