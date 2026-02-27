"""
Django Admin Custom - Package d'administration Django personnalisé

Un package réutilisable pour personnaliser l'interface d'administration Django
avec des graphiques dynamiques, des grilles de données et un design moderne.
"""

__version__ = '0.1.0'
__author__ = 'Agile Custom Admin'

# Note: Les imports sont faits directement depuis les modules pour éviter les imports circulaires
# Utilisez: from admin_custom.admin_site import CustomAdminSite, custom_admin_site
#          from admin_custom.autodiscover import autodiscover_models
#          etc.

__all__ = [
    'CustomAdminSite',
    'custom_admin_site',
    'autodiscover_models',
    'get_all_models_for_charts',
    'get_all_models_for_grids',
    'hooks',
    'register_hook',
    'call_hook',
    'HOOK_NAMES',
]
