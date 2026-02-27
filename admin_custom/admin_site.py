"""
CustomAdminSite - Site d'administration Django personnalisé et réutilisable

Ce module définit un AdminSite personnalisé qui peut être utilisé
comme package réutilisable dans d'autres projets Django.
Supporte deux interfaces : Classique (AdminLTE) et Moderne (Design 1).
"""
from django.contrib import admin
from django.contrib.admin import actions as admin_actions
from django.contrib.auth import logout as auth_logout
from django.urls import path, include, reverse
from django.shortcuts import render, redirect

from . import admin_views as custom_views
from . import auth_views
from . import modern_views
from .auth_views import SESSION_INTERFACE_KEY, INTERFACE_MODERN


def _delete_selected_modern_aware(modeladmin, request, queryset):
    """delete_selected qui utilise le template moderne si l'interface est en mode moderne."""
    from .modern_model_admin import _use_modern_templates
    orig = getattr(modeladmin, 'delete_selected_confirmation_template', None)
    if _use_modern_templates(request) and hasattr(modeladmin, 'modern_delete_selected_confirmation_template'):
        modeladmin.delete_selected_confirmation_template = modeladmin.modern_delete_selected_confirmation_template
    try:
        return admin_actions.delete_selected(modeladmin, request, queryset)
    finally:
        modeladmin.delete_selected_confirmation_template = orig


class CustomAdminSite(admin.AdminSite):
    """
    Site d'administration personnalisé avec fonctionnalités avancées :
    - Graphiques dynamiques
    - Grilles de données configurables
    - Dashboard personnalisé
    - Design moderne avec thèmes
    """
    site_header = "Administration Django Personnalisée"
    site_title = "Admin Personnalisé"
    index_title = "Tableau de bord"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._actions = {**self._actions, "delete_selected": _delete_selected_modern_aware}
    
    # Templates personnalisés - Utiliser nos templates namespacés
    index_template = 'admin_custom/index.html'
    app_index_template = 'admin/index.html'
    login_template = 'admin_custom/auth/login_with_interface.html'
    change_list_template = 'admin_custom/change_list.html'
    change_form_template = 'admin_custom/change_form.html'
    logout_template = None  # Redirection directe vers la page de connexion (voir logout ci-dessous)
    password_change_template = 'admin/password_change_form.html'
    password_change_done_template = 'admin/password_change_done.html'
    
    def _force_custom_templates(self, request=None):
        """
        Force l'utilisation des templates personnalisés pour tous les ModelAdmin enregistrés.
        
        Cette méthode centralise la logique de forçage des templates et garantit
        que tous les ModelAdmin utilisent les bons templates selon l'interface active.
        
        Args:
            request: Objet HttpRequest optionnel pour détecter l'interface active.
                    Si None, utilise l'interface classique par défaut.
        """
        # Détecter l'interface active si request est fourni
        if request:
            use_modern = request.session.get(SESSION_INTERFACE_KEY) == INTERFACE_MODERN
        else:
            use_modern = False
        
        # Déterminer les templates à utiliser
        if use_modern:
            change_list_template = 'admin_custom/modern/change_list.html'
            change_form_template = 'admin_custom/modern/change_form.html'
        else:
            change_list_template = 'admin_custom/change_list.html'
            change_form_template = 'admin_custom/change_form.html'
        
        # Forcer sur toutes les instances et classes ModelAdmin enregistrées
        for model, admin_instance in self._registry.items():
            # Forcer sur l'instance
            admin_instance.change_list_template = change_list_template
            admin_instance.change_form_template = change_form_template
            
            # Forcer sur la classe
            admin_class = admin_instance.__class__
            admin_class.change_list_template = change_list_template
            admin_class.change_form_template = change_form_template
            
            # Forcer sur toutes les classes parentes dans le MRO
            for cls in admin_class.__mro__:
                if (issubclass(cls, admin.ModelAdmin) and 
                    cls != admin.ModelAdmin and 
                    hasattr(cls, 'change_list_template')):
                    cls.change_list_template = change_list_template
                    cls.change_form_template = change_form_template
    
    def each_context(self, request):
        """
        Ajoute le contexte pour tous les templates.
        En mode moderne : admin_interface et app_list pour la sidebar.
        Force également les templates personnalisés pour tous les ModelAdmin.
        """
        # Forcer les templates personnalisés avant de générer le contexte
        self._force_custom_templates(request)
        
        context = super().each_context(request)
        admin_interface = request.session.get(SESSION_INTERFACE_KEY, 'classic')
        context['admin_interface'] = admin_interface
        if admin_interface == INTERFACE_MODERN:
            context['app_list'] = self.get_app_list(request)
            context['user_display'] = request.user.get_short_name() or request.user.get_username() if request.user.is_authenticated else ''
            context['user_initial'] = (context['user_display'][0] if context['user_display'] else 'A').upper()
            context['admin_base_template'] = 'admin_custom/modern/admin_base.html'
        else:
            context['admin_base_template'] = 'admin_custom/base.html'
        return context
    
    def logout(self, request, extra_context=None):
        """Déconnexion puis redirection vers la page de connexion admin (évite le template manquant)."""
        auth_logout(request)
        request.current_app = self.name
        return redirect(reverse('admin:login', current_app=self.name))
    
    def get_urls(self):
        """
        Ajoute les URLs personnalisées (charts, grids, dashboard, login, switch interface)
        aux URLs standard de l'admin Django
        """
        urls = super().get_urls()
        
        # URLs personnalisées - en premier pour override le login
        custom_urls = [
            path('login/', auth_views.select_interface_login, name='login'),
            path('switch-interface/', auth_views.switch_interface, name='switch_interface'),
            path('modern/', include([
                path('', self.admin_view(modern_views.modern_dashboard), name='modern_dashboard'),
                path('charts/', self.admin_view(modern_views.modern_charts), name='modern_charts'),
                path('grids/', self.admin_view(modern_views.modern_grids), name='modern_grids'),
                path('settings/', self.admin_view(modern_views.modern_settings), name='modern_settings'),
            ])),
            path('charts/', self.admin_view(custom_views.charts_view), name='admin_charts'),
            path('grids/', self.admin_view(custom_views.grids_view), name='admin_grids'),
            path('dashboard/', self.admin_view(custom_views.dashboard_view), name='admin_dashboard'),
            path('dashboard-customize/', self.admin_view(custom_views.dashboard_customize_page), name='dashboard_customize'),
            path('settings/', self.admin_view(custom_views.classic_settings), name='classic_settings'),
        ]
        
        return custom_urls + urls
    
    def get_app_list(self, request, app_label=None):
        """
        Retourne la liste des applications, en excluant admin_custom
        et en ajoutant les icônes pour l'interface moderne.
        """
        app_list = super().get_app_list(request, app_label)
        
        model_icons = {
            'userprofile': 'fa-user',
            'group': 'fa-users',
            'permission': 'fa-key',
            'user': 'fa-user',
            'category': 'fa-folder',
            'product': 'fa-box',
            'orderitem': 'fa-shopping-cart',
            'order': 'fa-file-lines',
            'invoice': 'fa-file-invoice',
            'payment': 'fa-credit-card',
        }

        filtered_app_list = []
        for app in app_list:
            if app.get('app_label') == 'admin_custom':
                continue
            app_copy = dict(app)
            app_copy['models'] = [
                dict(m, icon=model_icons.get(m.get('object_name', '').lower(), 'fa-cube'))
                for m in app_copy.get('models', [])
            ]
            filtered_app_list.append(app_copy)

        return filtered_app_list


# Instance globale par défaut
# Dans un package, cette instance sera remplacée par autodiscover
custom_admin_site = CustomAdminSite()
