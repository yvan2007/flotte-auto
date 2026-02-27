"""
Système de hooks pour étendre les fonctionnalités d'admin_custom

Permet aux projets utilisant le package d'ajouter des fonctionnalités
sans modifier le code source du package.
"""
from typing import Callable, List, Dict, Any


class HookRegistry:
    """
    Registre centralisé pour les hooks d'extension
    """
    def __init__(self):
        self._hooks: Dict[str, List[Callable]] = {}
    
    def register(self, hook_name: str, callback: Callable):
        """
        Enregistre un callback pour un hook spécifique
        
        Args:
            hook_name: Nom du hook (ex: 'before_model_register')
            callback: Fonction à appeler
        """
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)
    
    def call(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Appelle tous les callbacks enregistrés pour un hook
        
        Args:
            hook_name: Nom du hook
            *args, **kwargs: Arguments à passer aux callbacks
        
        Returns:
            Liste des valeurs de retour des callbacks
        """
        results = []
        if hook_name in self._hooks:
            for callback in self._hooks[hook_name]:
                try:
                    result = callback(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    # Logger l'erreur mais continuer
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Erreur dans le hook {hook_name}: {e}")
        return results
    
    def has_hooks(self, hook_name: str) -> bool:
        """Vérifie si un hook a des callbacks enregistrés"""
        return hook_name in self._hooks and len(self._hooks[hook_name]) > 0


# Instance globale du registre de hooks
hooks = HookRegistry()


# Définition des hooks disponibles
HOOK_NAMES = {
    'BEFORE_MODEL_REGISTER': 'before_model_register',
    'AFTER_MODEL_REGISTER': 'after_model_register',
    'CUSTOM_CHART_MODELS': 'custom_chart_models',
    'CUSTOM_GRID_MODELS': 'custom_grid_models',
    'BEFORE_CHART_GENERATE': 'before_chart_generate',
    'AFTER_CHART_GENERATE': 'after_chart_generate',
    'BEFORE_GRID_GENERATE': 'before_grid_generate',
    'AFTER_GRID_GENERATE': 'after_grid_generate',
    'CUSTOM_THEMES': 'custom_themes',
}


# Fonctions utilitaires pour les développeurs
def register_hook(hook_name: str, callback: Callable):
    """
    Fonction helper pour enregistrer un hook
    
    Exemple:
        from admin_custom.hooks import register_hook, HOOK_NAMES
        
        def my_custom_chart_models():
            return [{'name': 'MyModel', 'label': 'Mon Modèle'}]
        
        register_hook(HOOK_NAMES['CUSTOM_CHART_MODELS'], my_custom_chart_models)
    """
    hooks.register(hook_name, callback)


def call_hook(hook_name: str, *args, **kwargs):
    """
    Fonction helper pour appeler un hook
    
    Exemple:
        from admin_custom.hooks import call_hook, HOOK_NAMES
        
        results = call_hook(HOOK_NAMES['BEFORE_MODEL_REGISTER'], model)
    """
    return hooks.call(hook_name, *args, **kwargs)
