"""
Tests fonctionnels FLOTTE — parcours utilisateur avec Selenium et Chrome.
Vérifie que chaque rôle (user, manager, admin) accède aux bonnes pages
et est bloqué sur les pages restreintes. Utilise des attentes explicites
pour éviter les échecs intermittents.
"""
import time
from django.test import LiveServerTestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from flotte.models import ProfilUtilisateur
from flotte.tests.config import (
    FLOTTE_TEST_USER_USERNAME,
    FLOTTE_TEST_USER_PASSWORD,
    FLOTTE_TEST_MANAGER_USERNAME,
    FLOTTE_TEST_MANAGER_PASSWORD,
    FLOTTE_TEST_ADMIN_USERNAME,
    FLOTTE_TEST_ADMIN_PASSWORD,
    FLOTTE_TEST_HEADLESS,
    FLOTTE_TEST_IMPLICIT_WAIT,
    FLOTTE_TEST_PAUSE_SECONDS,
)

User = get_user_model()

# Délai max pour les attentes explicites (secondes)
WAIT_TIMEOUT = 15


def get_selenium_driver():
    """Crée un WebDriver Chrome (headless ou non)."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError:
        raise ImportError(
            'Pour les tests Selenium, installez : pip install selenium webdriver-manager'
        )
    options = Options()
    if FLOTTE_TEST_HEADLESS:
        options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280,900')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(FLOTTE_TEST_IMPLICIT_WAIT)
    return driver


def get_wait(driver, timeout=WAIT_TIMEOUT):
    """Retourne un WebDriverWait pour le driver."""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    return WebDriverWait(driver, timeout)


class SeleniumTestMixin:
    """Mixin pour login et navigation Selenium avec attentes explicites."""

    def wait_for_element(self, by, value, timeout=WAIT_TIMEOUT):
        """Attend qu'un élément soit présent et visible."""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((by, value))
        )

    def wait_for_url_contains(self, fragment, timeout=WAIT_TIMEOUT):
        """Attend que l'URL courante contienne fragment."""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        return WebDriverWait(self.driver, timeout).until(
            EC.url_contains(fragment)
        )

    def login(self, username, password):
        """Connexion via le formulaire login ; attend le succès (redirection ou contenu principal)."""
        self.driver.get(self.live_server_url + reverse('flotte:login'))
        self.wait_for_element('id', 'id_username', timeout=WAIT_TIMEOUT)
        self.wait_for_element('id', 'id_password', timeout=WAIT_TIMEOUT)
        self.driver.find_element('id', 'id_username').clear()
        self.driver.find_element('id', 'id_username').send_keys(username)
        self.driver.find_element('id', 'id_password').clear()
        self.driver.find_element('id', 'id_password').send_keys(password)
        self.driver.find_element('css selector', 'button[type="submit"]').click()
        # Attendre soit la redirection vers dashboard, soit l'affichage du contenu principal (sidebar ou main)
        try:
            self.wait_for_element('css selector', 'main.main, .sidebar', timeout=WAIT_TIMEOUT)
        except Exception:
            # Si on est resté sur la page login (erreur), le body existe quand même
            pass
        time.sleep(FLOTTE_TEST_PAUSE_SECONDS)

    def goto(self, url_name, **kwargs):
        """Ouvre l'URL nommée et attend que la page soit chargée (main ou body visible)."""
        path = reverse(url_name, **kwargs)
        self.driver.get(self.live_server_url + path)
        # Attendre que le corps de la page soit chargé (évite lectures trop tôt)
        self.wait_for_element('tag name', 'body', timeout=WAIT_TIMEOUT)
        time.sleep(FLOTTE_TEST_PAUSE_SECONDS)

    def page_ok(self):
        """Vérifie que la page courante n'est pas une erreur 403/404/500."""
        self.wait_for_element('tag name', 'body', timeout=WAIT_TIMEOUT)
        time.sleep(0.5)  # Laisser le temps au rendu éventuel d'erreur
        body = self.driver.find_element('tag name', 'body').text
        title = (self.driver.title or '')
        self.assertNotIn('403', title, msg=f'Page attendue OK mais titre contient 403: {title!r}')
        self.assertNotIn('Forbidden', body, msg=f'Page attendue OK mais body contient Forbidden')
        self.assertNotIn('PermissionDenied', body, msg=f'Page attendue OK mais body contient PermissionDenied')
        self.assertNotIn('interdit', body.lower(), msg=f'Page attendue OK mais body contient "interdit"')

    def page_forbidden(self):
        """Vérifie que la page affiche un accès interdit (403)."""
        self.wait_for_element('tag name', 'body', timeout=WAIT_TIMEOUT)
        time.sleep(0.8)  # Laisser le temps au rendu de la page 403
        body = self.driver.find_element('tag name', 'body').text
        title = (self.driver.title or '')
        ok = (
            '403' in title
            or 'Forbidden' in body
            or 'interdit' in body.lower()
            or 'PermissionDenied' in body
            or 'Accès réservé' in body
        )
        self.assertTrue(
            ok,
            f'Attendu 403/Forbidden/interdit, titre={title!r}, body (200 premiers car)={body[:200]!r}'
        )


def _ensure_user_with_role(username, password, role, is_staff=False, is_superuser=False):
    """Crée ou récupère un utilisateur avec le rôle donné (user, manager, admin)."""
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={'is_staff': is_staff, 'is_superuser': is_superuser}
    )
    user.set_password(password)
    user.is_staff = is_staff
    user.is_superuser = is_superuser
    user.save()
    profil, _ = ProfilUtilisateur.objects.get_or_create(
        user=user,
        defaults={'role': role}
    )
    profil.role = role
    profil.save()
    return user


@override_settings(DEBUG=True)
class SeleniumUserJourneyTests(SeleniumTestMixin, LiveServerTestCase):
    """
    Parcours utilisateur (rôle user) — consultation uniquement.
    Accès : dashboard, recherche, échéances, parc, réparations, documents, ventes, maintenance, carburant, conducteurs.
    Refusé (403) : import, parties importées, CA, TCO, location, paramétrage.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver = get_selenium_driver()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.driver.quit()
        except Exception:
            pass
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        _ensure_user_with_role(
            FLOTTE_TEST_USER_USERNAME,
            FLOTTE_TEST_USER_PASSWORD,
            'user',
            is_staff=False,
            is_superuser=False,
        )

    def test_user_journey_pages_allowed(self):
        """Utilisateur peut consulter toutes les pages autorisées : dashboard, recherche, échéances, parc, réparations, documents, ventes, maintenance, carburant, conducteurs."""
        self.login(FLOTTE_TEST_USER_USERNAME, FLOTTE_TEST_USER_PASSWORD)
        # Dashboard
        self.goto('flotte:dashboard')
        self.assertIn('dashboard', self.driver.current_url.lower())
        self.page_ok()
        # Recherche
        self.goto('flotte:recherche')
        self.page_ok()
        # Échéances
        self.goto('flotte:echeances')
        self.page_ok()
        # Parc
        self.goto('flotte:parc')
        self.page_ok()
        # Réparations, documents, ventes, maintenance, carburant, conducteurs
        self.goto('flotte:reparations_list')
        self.page_ok()
        self.goto('flotte:documents_list')
        self.page_ok()
        self.goto('flotte:ventes_list')
        self.page_ok()
        self.goto('flotte:maintenance_list')
        self.page_ok()
        self.goto('flotte:carburant_list')
        self.page_ok()
        self.goto('flotte:conducteurs_list')
        self.page_ok()

    def test_user_denied_import(self):
        self.login(FLOTTE_TEST_USER_USERNAME, FLOTTE_TEST_USER_PASSWORD)
        self.goto('flotte:import_list')
        self.page_forbidden()

    def test_user_denied_parties_importees(self):
        self.login(FLOTTE_TEST_USER_USERNAME, FLOTTE_TEST_USER_PASSWORD)
        self.goto('flotte:parties_importees_list')
        self.page_forbidden()

    def test_user_denied_ca(self):
        self.login(FLOTTE_TEST_USER_USERNAME, FLOTTE_TEST_USER_PASSWORD)
        self.goto('flotte:ca')
        self.page_forbidden()

    def test_user_denied_tco(self):
        self.login(FLOTTE_TEST_USER_USERNAME, FLOTTE_TEST_USER_PASSWORD)
        self.goto('flotte:tco')
        self.page_forbidden()

    def test_user_denied_location(self):
        self.login(FLOTTE_TEST_USER_USERNAME, FLOTTE_TEST_USER_PASSWORD)
        self.goto('flotte:location_list')
        self.page_forbidden()

    def test_user_denied_parametrage(self):
        self.login(FLOTTE_TEST_USER_USERNAME, FLOTTE_TEST_USER_PASSWORD)
        self.goto('flotte:parametrage_index')
        self.page_forbidden()


@override_settings(DEBUG=True)
class SeleniumManagerJourneyTests(SeleniumTestMixin, LiveServerTestCase):
    """
    Parcours gestionnaire (rôle manager) — tout sauf paramétrage.
    Accès : dashboard, recherche, échéances, parc, import, parties importées, réparations, documents, ventes, CA, TCO, location, maintenance, carburant, conducteurs.
    Refusé (403) : paramétrage.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver = get_selenium_driver()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.driver.quit()
        except Exception:
            pass
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        _ensure_user_with_role(
            FLOTTE_TEST_MANAGER_USERNAME,
            FLOTTE_TEST_MANAGER_PASSWORD,
            'manager',
            is_staff=False,
            is_superuser=False,
        )

    def test_manager_journey_all_operational_pages(self):
        """Gestionnaire accède à toutes les pages opérationnelles (dashboard, recherche, échéances, parc, import, parties importées, ventes, CA, TCO, location, maintenance, carburant, conducteurs)."""
        self.login(FLOTTE_TEST_MANAGER_USERNAME, FLOTTE_TEST_MANAGER_PASSWORD)
        self.goto('flotte:dashboard')
        self.page_ok()
        self.goto('flotte:recherche')
        self.page_ok()
        self.goto('flotte:echeances')
        self.page_ok()
        self.goto('flotte:parc')
        self.page_ok()
        self.goto('flotte:import_list')
        self.page_ok()
        self.goto('flotte:parties_importees_list')
        self.page_ok()
        self.goto('flotte:reparations_list')
        self.page_ok()
        self.goto('flotte:documents_list')
        self.page_ok()
        self.goto('flotte:ventes_list')
        self.page_ok()
        self.goto('flotte:ca')
        self.page_ok()
        self.goto('flotte:tco')
        self.page_ok()
        self.goto('flotte:location_list')
        self.page_ok()
        self.goto('flotte:maintenance_list')
        self.page_ok()
        self.goto('flotte:carburant_list')
        self.page_ok()
        self.goto('flotte:conducteurs_list')
        self.page_ok()

    def test_manager_denied_parametrage(self):
        self.login(FLOTTE_TEST_MANAGER_USERNAME, FLOTTE_TEST_MANAGER_PASSWORD)
        self.goto('flotte:parametrage_index')
        self.page_forbidden()

    def test_manager_denied_parametrage_marques(self):
        self.login(FLOTTE_TEST_MANAGER_USERNAME, FLOTTE_TEST_MANAGER_PASSWORD)
        self.goto('flotte:parametrage_marques')
        self.page_forbidden()


@override_settings(DEBUG=True)
class SeleniumAdminJourneyTests(SeleniumTestMixin, LiveServerTestCase):
    """
    Parcours administrateur — accès à tout, y compris paramétrage.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver = get_selenium_driver()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.driver.quit()
        except Exception:
            pass
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        _ensure_user_with_role(
            FLOTTE_TEST_ADMIN_USERNAME,
            FLOTTE_TEST_ADMIN_PASSWORD,
            'admin',
            is_staff=True,
            is_superuser=True,
        )

    def test_admin_journey_all_pages(self):
        """Admin accède à tout : dashboard, recherche, échéances, parc, import, parties importées, ventes, CA, TCO, location, maintenance, carburant, conducteurs, paramétrage (index + marques + modèles)."""
        self.login(FLOTTE_TEST_ADMIN_USERNAME, FLOTTE_TEST_ADMIN_PASSWORD)
        self.goto('flotte:dashboard')
        self.page_ok()
        self.goto('flotte:recherche')
        self.page_ok()
        self.goto('flotte:echeances')
        self.page_ok()
        self.goto('flotte:parc')
        self.page_ok()
        self.goto('flotte:import_list')
        self.page_ok()
        self.goto('flotte:parties_importees_list')
        self.page_ok()
        self.goto('flotte:ventes_list')
        self.page_ok()
        self.goto('flotte:ca')
        self.page_ok()
        self.goto('flotte:tco')
        self.page_ok()
        self.goto('flotte:location_list')
        self.page_ok()
        self.goto('flotte:maintenance_list')
        self.page_ok()
        self.goto('flotte:carburant_list')
        self.page_ok()
        self.goto('flotte:conducteurs_list')
        self.page_ok()
        # Paramétrage
        self.goto('flotte:parametrage_index')
        self.page_ok()
        self.goto('flotte:parametrage_marques')
        self.page_ok()
        self.goto('flotte:parametrage_modeles')
        self.page_ok()
        self.goto('flotte:parametrage_utilisateurs')
        self.page_ok()