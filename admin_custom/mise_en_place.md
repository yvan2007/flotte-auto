# Django Admin Custom - Guide de mise en place

Guide complet pour intégrer le panel admin personnalisé dans un projet Django. **Toute l'administration** (tableau de bord, grilles, graphiques, listes et formulaires) utilise le thème personnalisé.

---

## Installation rapide (6 étapes)

1. **Copier** le dossier `admin_custom/` à la racine du projet (même niveau que `manage.py`)
2. **Ajouter** `'admin_custom'` en **dernier** dans `INSTALLED_APPS`
3. **Ajouter** `'admin_custom.middleware.AdminInterfaceRedirectMiddleware'` à la **fin** de `MIDDLEWARE`
4. **Configurer** `urls.py` avec `path('admin/', custom_admin_site.urls)`
5. **Exécuter** `python manage.py migrate`
6. **Redémarrer** le serveur Django

**C'est tout !** L'auto-découverte détecte automatiquement tous vos modèles et leurs configurations.

---

## Configuration détaillée

### 1. Copier le dossier `admin_custom/`

Copiez **tout le dossier** `admin_custom/` à la racine de votre projet :

```
mon_projet/
├── manage.py
├── mon_projet/
│   ├── settings.py
│   └── urls.py
├── mon_app/
│   └── admin.py  # Vos ModelAdmin existants fonctionnent sans modification
└── admin_custom/  # ← COLLER ICI (tout le dossier)
    ├── apps.py
    ├── admin_site.py
    ├── templates/
    ├── static/
    └── migrations/
```

### 2. Configurer `settings.py`

#### INSTALLED_APPS

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    # ... autres apps Django ...
    
    # Vos apps métier
    'mon_app',
    
    # Admin personnalisé (EN DERNIER - IMPORTANT)
    'admin_custom',
]
```

**Pourquoi en dernier ?** L'auto-découverte doit s'exécuter après toutes les autres apps pour détecter tous les fichiers `admin.py`.

#### MIDDLEWARE

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # ... autres middlewares ...
    'django.contrib.messages.middleware.MessageMiddleware',
    
    # Middleware admin custom (À LA FIN - IMPORTANT)
    'admin_custom.middleware.AdminInterfaceRedirectMiddleware',
]
```

#### TEMPLATES

Vérifiez que `APP_DIRS = True` et que `django.template.context_processors.request` est présent. **Pour que l’interface classique (AdminLTE) s’affiche sur les listes et formulaires** (et non l’admin standard Django), ajoutez `DIRS` et créez la surcharge suivante :

```python
# settings.py - BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],   # ← requis pour l’interface classique
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]
```

Créez le dossier `templates/admin/` à la racine du projet et le fichier **`templates/admin/base_site.html`** avec le contenu suivant (une seule ligne) :

```django
{% extends "admin_custom/base_site.html" %}
```

Ainsi, toutes les pages admin (listes, formulaires) qui s’appuient sur `admin/base_site.html` utilisent le cadre AdminLTE de admin_custom en mode classique. Un exemple est fourni dans `admin_custom/project_override_example/admin_base_site.html` (à copier dans `templates/admin/base_site.html`).

### 3. Configurer `urls.py`

**Important :** Utilisez explicitement `custom_admin_site.urls` pour garantir que toutes les colonnes (`list_display`) et inlines s'affichent correctement.

```python
from django.urls import path, include
from admin_custom.admin_site import custom_admin_site

urlpatterns = [
    # Tout l'admin : listes avec toutes les colonnes, formulaires avec inlines
    path('admin/', custom_admin_site.urls),
    # API REST (graphiques, grilles, config dashboard)
    path('admin_custom/', include('admin_custom.urls')),
]
```

**⚠️ Ne pas utiliser** `path('admin/', admin.site.urls)` - cela empêcherait l'affichage correct des colonnes et inlines.

### 4. Migrations

```bash
python manage.py migrate
```

Les migrations sont déjà incluses dans `admin_custom/migrations/`. Si vous obtenez un message indiquant qu'il n'y a pas de changements, c'est normal.

### 5. Fichiers statiques (production)

```bash
python manage.py collectstatic
```

### 6. Redémarrer le serveur

**Toujours redémarrer** après modification de `settings.py` ou `urls.py` :

```bash
python manage.py runserver
```

---

## Fonctionnalités

| Fonctionnalité | Description |
|----------------|-------------|
| **Double interface** | Classique (AdminLTE) et moderne (Bootstrap 5) avec basculement automatique |
| **Thèmes** | 7 thèmes classiques, 4 thèmes modernes (changement en temps réel) |
| **Dashboard** | Tableau de bord personnalisable avec statistiques dynamiques |
| **Grilles** | Affichent **automatiquement tous les champs concrets** du modèle |
| **Graphiques** | Générateur de graphiques (ligne, barre, camembert, etc.) |
| **Auto-découverte** | Détecte automatiquement tous les modèles et leurs `ModelAdmin` |
| **Inlines en onglets** | Parent et enfants affichés en onglets au même niveau |
| **Liens bidirectionnels** | Navigation parent ↔ enfants |
| **Responsive** | Adapté mobile, tablette et desktop |

---

## Enregistrement des modèles

### Utilisation standard (recommandée)

Vos fichiers `admin.py` existants fonctionnent **sans modification** :

```python
# mon_app/admin.py
from django.contrib import admin
from admin_custom.modern_model_admin import ModernTemplateMixin
from .models import MonModele

@admin.register(MonModele)
class MonModeleAdmin(ModernTemplateMixin, admin.ModelAdmin):
    list_display = ['nom', 'date_creation', 'statut']
    list_filter = ['statut']
    search_fields = ['nom']
    inlines = [MonEnfantInline]  # S'affichent automatiquement en onglets
```

L'auto-découverte détecte automatiquement cette classe et l'enregistre sur `custom_admin_site` avec tous ses attributs (`list_display`, `inlines`, etc.).

**Note :** Le `ModernTemplateMixin` est appliqué automatiquement à tous les ModelAdmin, même si vous ne l'incluez pas explicitement.

---

## Vérification

Après installation, vérifiez que :

- ✅ `/admin/` affiche le thème personnalisé (pas le vert Django par défaut)
- ✅ Les listes affichent **toutes les colonnes** définies dans `list_display`
- ✅ Les formulaires affichent les inlines en onglets
- ✅ Les grilles affichent tous les champs concrets du modèle

---

## Dépannage

| Problème | Solution |
|----------|----------|
| **Tableau de bord OK mais autres pages → admin Django par défaut** | Utilisez `path('admin/', custom_admin_site.urls)` au lieu de `path('admin/', admin.site.urls)`. Redémarrez le serveur. |
| **Les listes n'affichent qu'une seule colonne** | Vérifiez que votre `ModelAdmin` définit bien `list_display` avec toutes les colonnes. Redémarrez le serveur. |
| **Les modèles n'apparaissent pas** | Vérifiez que vos apps sont dans `INSTALLED_APPS` et que vos fichiers `admin.py` enregistrent les modèles. Redémarrez le serveur. |
| **Les styles ne s'affichent pas** | `python manage.py collectstatic` puis Ctrl+Shift+R (hard refresh) |
| **Erreur "No module named admin_custom"** | Vérifiez que le dossier `admin_custom/` est à la racine du projet et dans `INSTALLED_APPS` (en dernier) |
| **Les inlines ne s'affichent pas** | Utilisez `path('admin/', custom_admin_site.urls)`. Vérifiez que vos `ModelAdmin` définissent bien `inlines`. Redémarrez le serveur. |
| **Interface classique : listes/formulaires affichent l’admin Django (bleu/noir)** | Ajoutez `DIRS`: `[BASE_DIR / 'templates']` dans `TEMPLATES` et créez `templates/admin/base_site.html` avec : `{% extends "admin_custom/base_site.html" %}`. Redémarrez le serveur. |

---

## Personnalisation

### Logo

Remplacez `admin_custom/static/admin_custom/image.png` par votre logo.

### Hooks (optionnel)

Pour étendre le comportement sans modifier le code source :

```python
# mon_app/apps.py
from django.apps import AppConfig

class MonAppConfig(AppConfig):
    name = 'mon_app'
    
    def ready(self):
        from admin_custom.hooks import register_hook
        
        def mon_hook_dashboard(context):
            context['extra_stats'] = {'clients_actifs': 42}
            return context
        
        register_hook('dashboard_context', mon_hook_dashboard)
```

---

## Points clés

✅ **Aucune modification nécessaire** : Vos fichiers `admin.py` existants fonctionnent tels quels  
✅ **Auto-découverte automatique** : Tous les modèles sont détectés et enregistrés automatiquement  
✅ **Préservation des configurations** : `list_display`, `inlines`, `list_filter`, etc. sont préservés  
✅ **Tous types de projets** : E-commerce, blog, CRM, etc. - s'adapte automatiquement  
✅ **Architecture multi-couches** : Garantit que les templates personnalisés sont toujours utilisés

---

## Checklist finale

- [ ] Dossier `admin_custom/` copié à la racine du projet
- [ ] `'admin_custom'` ajouté en dernier dans `INSTALLED_APPS`
- [ ] Middleware ajouté à la fin de `MIDDLEWARE`
- [ ] `path('admin/', custom_admin_site.urls)` dans `urls.py`
- [ ] `DIRS`: `[BASE_DIR / 'templates']` dans `TEMPLATES` et fichier `templates/admin/base_site.html` créé (pour l’interface classique)
- [ ] Migrations appliquées (`python manage.py migrate`)
- [ ] Serveur Django redémarré
- [ ] Vérification : `/admin/` affiche le thème personnalisé
- [ ] Vérification : Les listes (interface classique) restent en AdminLTE, pas en admin Django
- [ ] Vérification : Les formulaires affichent les inlines en onglets

---

**C'est tout !** Votre admin personnalisé est maintenant complètement fonctionnel. 🎉
