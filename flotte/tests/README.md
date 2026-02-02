# Tests FLOTTE

Structure des tests : **unitaires**, **intégration**, **fonctionnels (Selenium + Chrome)**.

## Structure

```
flotte/tests/
├── __init__.py          # Point d'entrée (découverte Django)
├── config.py            # Credentials et URL (variables d'environnement)
├── README.md            # Ce fichier
├── unit/                # Tests unitaires (modèles)
│   ├── test_models.py
│   └── ...
├── integration/         # Tests d'intégration (vues, permissions)
│   ├── test_views_permissions.py
│   └── ...
└── functional/          # Tests fonctionnels Selenium (parcours utilisateur Chrome)
    ├── test_selenium_journey.py
    └── ...
```

## Exécution

### Tests seuls

- **Tous les tests** :  
  `python manage.py test flotte`

- **Uniquement unitaires** :  
  `python manage.py test flotte.tests.unit`

- **Uniquement intégration** :  
  `python manage.py test flotte.tests.integration`

- **Uniquement fonctionnels (Selenium)** :  
  `python manage.py test flotte.tests.functional`

### Tests avec couverture (coverage)

- **Rapport console** :  
  `coverage run --source=flotte,flotte_project -m django test flotte`  
  `coverage report`

- **Rapport HTML** (dossier `htmlcov/`) :  
  `coverage run --source=flotte,flotte_project -m django test flotte`  
  `coverage html`  
  Puis ouvrir `htmlcov/index.html`.

- **Scripts à la racine** :  
  - PowerShell : `.\run_tests.ps1` (tous les tests + coverage, Chrome visible)  
  - PowerShell : `.\run_tests.ps1 -Html` (idem + ouverture du rapport HTML)  
  - CMD : `run_tests.bat` ou `run_tests.bat html`

Par défaut, **Chrome s'ouvre visiblement** pendant les tests Selenium. Pour headless : `FLOTTE_TEST_HEADLESS=1`.

## Prérequis pour les tests fonctionnels (Selenium)

1. **Chrome** installé sur la machine.
2. **Dépendances** :  
   `pip install selenium webdriver-manager`  
   (ou via `requirements-django.txt`.)

Les tests fonctionnels utilisent **LiveServerTestCase** : un serveur de test est lancé automatiquement, les utilisateurs (user, gestion, admin) sont créés en base de test, puis le parcours est simulé avec **Chrome visible** par défaut.

## Couverture de code

- Fichier de config : **`.coveragerc`** à la racine du projet.
- Branches prises en compte (`branch = true`).
- Exclusions : `migrations/`, `tests/`, `__pycache__/`, `venv/`.

## Credentials (tests fonctionnels)

Configurables par **variables d'environnement** (voir `flotte/tests/config.py`) :

| Rôle        | Variable username              | Variable password               | Défaut (username / password) |
|------------|---------------------------------|----------------------------------|-------------------------------|
| User       | `FLOTTE_TEST_USER_USERNAME`     | `FLOTTE_TEST_USER_PASSWORD`     | `user` / `52751040Ky`         |
| Manager    | `FLOTTE_TEST_MANAGER_USERNAME`  | `FLOTTE_TEST_MANAGER_PASSWORD`  | `gestion` / `52751040Ky`       |
| Admin      | `FLOTTE_TEST_ADMIN_USERNAME`    | `FLOTTE_TEST_ADMIN_PASSWORD`    | `yvan` / `5275`               |

- **URL de base** (optionnel, pour site live) : `FLOTTE_TEST_BASE_URL`
- **Chrome visible** : `FLOTTE_TEST_HEADLESS=0` (défaut) ; `1` pour headless (sans fenêtre).
- **Délai d’attente (s)** : `FLOTTE_TEST_IMPLICIT_WAIT=10`
- **Pause sur chaque page (s)** : `FLOTTE_TEST_PAUSE_SECONDS=2` (défaut) — pour voir le déroulement quand Chrome est visible

## Parcours couverts (Selenium)

- **User (consultation)** : dashboard, parc, réparations, documents, maintenance, carburant, conducteurs ; refus (403) sur import, ventes, CA, location, paramétrage.
- **Manager (gestion)** : tout le parcours opérationnel (y compris import, ventes, CA, location) ; refus sur paramétrage.
- **Admin** : accès à tout, y compris paramétrage (marques, modèles, etc.).
