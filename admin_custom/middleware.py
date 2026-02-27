"""
Middleware pour la redirection selon l'interface admin choisie et le forçage des templates.

Ce middleware :
1. Redirige vers l'interface moderne si nécessaire
2. Force les templates personnalisés sur tous les ModelAdmin à chaque requête admin
3. Intercepte les TemplateResponse pour garantir que les bons templates sont utilisés
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.template.response import TemplateResponse
from django.contrib import admin

from .auth_views import SESSION_INTERFACE_KEY, INTERFACE_MODERN


class AdminInterfaceRedirectMiddleware:
    """
    Redirige les utilisateurs connectés vers l'interface choisie (moderne ou classique)
    et force les templates personnalisés pour toutes les requêtes admin.
    
    Fonctionnalités :
    - Redirection vers l'interface moderne si nécessaire
    - Forçage des templates sur toutes les instances et classes ModelAdmin
    - Interception des TemplateResponse pour garantir les bons templates
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path.rstrip('/')
        
        # 1. Redirection vers l'interface moderne si nécessaire
        if (request.user.is_authenticated and 
            request.user.is_staff and
            path == '/admin' and
            request.session.get(SESSION_INTERFACE_KEY) == INTERFACE_MODERN):
            return redirect(reverse('admin:modern_dashboard'))
        
        # 2. Forcer les templates personnalisés pour toutes les requêtes admin
        if path.startswith('/admin'):
            try:
                from .admin_site import custom_admin_site
                # Forcer les templates sur tous les ModelAdmin enregistrés
                custom_admin_site._force_custom_templates(request)
                
                # Forcer également sur les instances et classes directement
                use_modern = request.session.get(SESSION_INTERFACE_KEY) == INTERFACE_MODERN
                if use_modern:
                    change_list_template = 'admin_custom/modern/change_list.html'
                    change_form_template = 'admin_custom/modern/change_form.html'
                    admin_base_template = 'admin_custom/modern/admin_base.html'
                else:
                    change_list_template = 'admin_custom/change_list.html'
                    change_form_template = 'admin_custom/change_form.html'
                    admin_base_template = 'admin_custom/base.html'
                
                # Forcer sur toutes les instances et classes ModelAdmin
                for model, admin_instance in custom_admin_site._registry.items():
                    admin_instance.change_list_template = change_list_template
                    admin_instance.change_form_template = change_form_template
                    admin_class = admin_instance.__class__
                    admin_class.change_list_template = change_list_template
                    admin_class.change_form_template = change_form_template
                    
                    # Forcer sur toutes les classes parentes dans le MRO
                    for cls in admin_class.__mro__:
                        if (hasattr(cls, 'change_list_template') and 
                            issubclass(cls, admin.ModelAdmin) and 
                            cls != admin.ModelAdmin):
                            cls.change_list_template = change_list_template
                            cls.change_form_template = change_form_template
            except Exception:
                # Ignorer les erreurs silencieusement pour ne pas bloquer les requêtes
                pass
        
        # 3. Obtenir la réponse
        response = self.get_response(request)
        
        # 4. Intercepter les TemplateResponse pour forcer les templates modernes si nécessaire
        if isinstance(response, TemplateResponse) and path.startswith('/admin'):
            use_modern = request.session.get(SESSION_INTERFACE_KEY) == INTERFACE_MODERN
            current_template = str(response.template_name)
            
            if use_modern:
                # Forcer les templates modernes si un template Django de base est détecté
                if 'admin/change_list.html' in current_template:
                    response.template_name = 'admin_custom/modern/change_list.html'
                    if 'admin_base_template' not in response.context_data:
                        response.context_data['admin_base_template'] = 'admin_custom/modern/admin_base.html'
                elif 'admin/change_form.html' in current_template:
                    response.template_name = 'admin_custom/modern/change_form.html'
                    if 'admin_base_template' not in response.context_data:
                        response.context_data['admin_base_template'] = 'admin_custom/modern/admin_base.html'
            else:
                # Forcer les templates classiques si nécessaire
                if 'admin/change_list.html' in current_template and 'admin_custom' not in current_template:
                    response.template_name = 'admin_custom/change_list.html'
                    if 'admin_base_template' not in response.context_data:
                        response.context_data['admin_base_template'] = 'admin_custom/base.html'
                elif 'admin/change_form.html' in current_template and 'admin_custom' not in current_template:
                    response.template_name = 'admin_custom/change_form.html'
                    if 'admin_base_template' not in response.context_data:
                        response.context_data['admin_base_template'] = 'admin_custom/base.html'
        
        return response
