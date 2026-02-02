"""
Package de tests FLOTTE — unitaires, intégration, fonctionnels (Selenium).
Django découvre les tests via les sous-modules.
Exécution : python manage.py test flotte
- Unitaires seuls : python manage.py test flotte.tests.unit
- Intégration seuls : python manage.py test flotte.tests.integration
- Fonctionnels Selenium (Chrome) : python manage.py test flotte.tests.functional
"""
from .unit.test_models import (
    VehiculeModelTests,
    MarqueModelTests,
    DepenseModelTests,
    RapportJournalierMaintenanceConducteurTests,
)
from .integration.test_views_permissions import PermissionsViewsTests

__all__ = [
    'VehiculeModelTests',
    'MarqueModelTests',
    'DepenseModelTests',
    'RapportJournalierMaintenanceConducteurTests',
    'PermissionsViewsTests',
]

# Tests fonctionnels Selenium (optionnels si selenium + webdriver-manager installés)
try:
    from .functional.test_selenium_journey import (
        SeleniumUserJourneyTests,
        SeleniumManagerJourneyTests,
        SeleniumAdminJourneyTests,
    )
    __all__ += [
        'SeleniumUserJourneyTests',
        'SeleniumManagerJourneyTests',
        'SeleniumAdminJourneyTests',
    ]
except ImportError:
    pass
