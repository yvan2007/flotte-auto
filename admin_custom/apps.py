from django.apps import AppConfig
from django.contrib import admin


def _reregister_inline_admins(custom_admin_site):
    """
    Ré-enregistre chaque modèle dont le ModelAdmin définit des inlines,
    pour garantir que les inlines (ex. OrderItem, Invoice sous Order) s'affichent.
    """
    for model, admin_instance in list(custom_admin_site._registry.items()):
        if not getattr(admin_instance, 'inlines', None):
            continue
        admin_cls = admin_instance.__class__
        try:
            custom_admin_site.unregister(model)
            custom_admin_site.register(model, admin_cls)
        except Exception:
            pass


class AdminCustomConfig(AppConfig):
    """
    Configuration de l'application admin_custom.
    
    Au chargement, remplace le site admin Django par défaut (admin.site)
    par notre CustomAdminSite. Ainsi, tout projet qui utilise
    path('admin/', admin.site.urls) affiche automatiquement le panel personnalisé
    sur toutes les pages (dashboard, listes, formulaires, grilles).
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_custom'
    verbose_name = 'Django Admin Custom'
    
    def ready(self):
        self._install_custom_admin_site()
    
    def _install_custom_admin_site(self):
        """
        Remplace admin.site par notre CustomAdminSite et enregistre tous les
        modèles du projet dessus. À appeler une seule fois au démarrage.
        """
        import django.contrib.admin
        from django.conf import settings
        
        from .admin_site import custom_admin_site
        
        # ÉTAPE 0 : Appliquer le monkey-patch global TRÈS TÔT
        # Cela garantit que même les ModelAdmin de packages tiers utilisent les templates personnalisés
        try:
            from .modeladmin_patch import patch_modeladmin
            patch_modeladmin()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                "admin_custom: erreur patch_modeladmin: %s", e
            )
        
        # 1) Charger tous les admin.py AVANT de remplacer admin.site
        #    Cela permet à autodiscover_models de récupérer les classes ModelAdmin originales
        #    depuis un site admin temporaire, puis de les enregistrer correctement sur custom_admin_site
        try:
            from .autodiscover import autodiscover_models
            autodiscover_models(custom_admin_site, exclude_apps=['admin_custom'])
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                "admin_custom: erreur autodiscover_models: %s", e
            )
        
        # 2) Remplacer le site admin par défaut APRÈS l'auto-découverte
        #    Tout code qui utilise admin.site (y compris path('admin/', admin.site.urls)) utilisera
        #    notre panel personnalisé. Les modèles sont déjà enregistrés sur custom_admin_site.
        django.contrib.admin.site = custom_admin_site
        
        # 2b) Ré-enregistrer les ModelAdmin qui ont des inlines pour garantir l'affichage
        _reregister_inline_admins(custom_admin_site)
        
        # 2c) Forcer l'enregistrement explicite des ModelAdmin pour garantir que list_display est correct
        # Cela garantit que tous les modèles utilisent leurs vraies classes ModelAdmin avec tous les attributs
        try:
            from django.apps import apps as django_apps
            
            # Catalog app
            if django_apps.is_installed('catalog'):
                try:
                    from catalog.models import Category, Product
                    from catalog.admin import CategoryAdmin, ProductAdmin
                    for model, admin_cls in [(Category, CategoryAdmin), (Product, ProductAdmin)]:
                        if model in custom_admin_site._registry:
                            custom_admin_site.unregister(model)
                        custom_admin_site.register(model, admin_cls)
                except ImportError:
                    pass
            
            # Sales app
            if django_apps.is_installed('sales'):
                try:
                    from sales.models import Order, OrderItem, Invoice, Payment
                    from sales.admin import OrderAdmin, OrderItemAdmin, InvoiceAdmin, PaymentAdmin
                    for model, admin_cls in [
                        (Order, OrderAdmin), 
                        (OrderItem, OrderItemAdmin), 
                        (Invoice, InvoiceAdmin),
                        (Payment, PaymentAdmin)
                    ]:
                        if model in custom_admin_site._registry:
                            custom_admin_site.unregister(model)
                        custom_admin_site.register(model, admin_cls)
                except ImportError:
                    pass
        except Exception:
            pass
        
        # 3) Remplacer User, Group, Permission par nos classes d'admin
        from django.contrib.auth.models import User, Group, Permission
        from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin, GroupAdmin
        from .user_admin import CustomUserAdmin
        from .modern_model_admin import ModernTemplateMixin
        
        # User : ne remplacer que si l'admin actuel est exactement celui de Django (conserver l'admin métier du projet)
        if User in custom_admin_site._registry:
            current_user_admin_instance = custom_admin_site._registry[User]
            if type(current_user_admin_instance) is DjangoUserAdmin:
                custom_admin_site.unregister(User)
                custom_admin_site.register(User, CustomUserAdmin)
        
        for model in (Group, Permission):
            if model in custom_admin_site._registry:
                custom_admin_site.unregister(model)
        
        custom_admin_site.register(Group, GroupAdmin)
        custom_admin_site.register(Permission, type(
            'PermissionAdmin', (ModernTemplateMixin, admin.ModelAdmin), {
                'list_display': ['name', 'content_type', 'codename'],
                'list_filter': ['content_type'],
                'search_fields': ['name', 'codename'],
            }
        ))
        
        # 4) Enregistrer les modèles admin_custom (grilles, graphiques, config dashboard)
        from .models import DashboardGrid, DashboardChart, UserDashboardConfig
        from .admin import DashboardGridAdmin, DashboardChartAdmin, UserDashboardConfigAdmin
        
        for model, admin_class in (
            (DashboardGrid, DashboardGridAdmin),
            (DashboardChart, DashboardChartAdmin),
            (UserDashboardConfig, UserDashboardConfigAdmin),
        ):
            if model in custom_admin_site._registry:
                custom_admin_site.unregister(model)
            custom_admin_site.register(model, admin_class)
        
        # 5) S'assurer que TOUS les ModelAdmin héritent de ModernTemplateMixin
        # Cela garantit que le basculement entre interfaces fonctionne pour tous les modèles
        from .modern_model_admin import ModernTemplateMixin
        
        for model, admin_instance in list(custom_admin_site._registry.items()):
            admin_class = admin_instance.__class__
            
            # Si le ModelAdmin n'hérite pas déjà du mixin, le créer avec le mixin
            if not issubclass(admin_class, ModernTemplateMixin):
                try:
                    # Créer une nouvelle classe avec le mixin en premier (MRO important)
                    class_name = f"{admin_class.__name__}WithModernMixin"
                    
                    # Préserver tous les attributs existants
                    admin_attrs = {
                        '__module__': admin_class.__module__,
                    }
                    
                    # Copier les attributs de classe importants
                    for attr_name in ['list_display', 'list_filter', 'search_fields', 'inlines', 
                                     'readonly_fields', 'prepopulated_fields', 'list_editable',
                                     'list_per_page', 'list_max_show_all', 'date_hierarchy',
                                     'ordering', 'save_as', 'save_on_top']:
                        if hasattr(admin_class, attr_name):
                            admin_attrs[attr_name] = getattr(admin_class, attr_name)
                    
                    # Créer la nouvelle classe avec le mixin en premier (MRO)
                    new_admin_class = type(class_name, (ModernTemplateMixin, admin_class), admin_attrs)
                    
                    # Ré-enregistrer avec la nouvelle classe
                    custom_admin_site.unregister(model)
                    custom_admin_site.register(model, new_admin_class)
                except Exception:
                    # En cas d'erreur, ignorer silencieusement pour ne pas bloquer le démarrage
                    pass
        
        # 6) Forcer les templates personnalisés au démarrage
        custom_admin_site._force_custom_templates()
