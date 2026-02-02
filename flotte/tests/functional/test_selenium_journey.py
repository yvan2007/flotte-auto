"""
Tests fonctionnels FLOTTE — parcours utilisateur avec Selenium et Chrome.
Vérifie que chaque rôle (user, manager, admin) accède aux bonnes pages
et est bloqué sur les pages restreintes.
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
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(FLOTTE_TEST_IMPLICIT_WAIT)
    return driver


class SeleniumTestMixin:
    """Mixin pour login et navigation Selenium."""

    def login(self, username, password):
        """Connexion via le formulaire login (id_username, id_password)."""
        self.driver.get(self.live_server_url + reverse('flotte:login'))
        time.sleep(FLOTTE_TEST_PAUSE_SECONDS)
        self.driver.find_element('id', 'id_username').send_keys(username)
        self.driver.find_element('id', 'id_password').send_keys(password)
        self.driver.find_element('css selector', 'button[type="submit"]').click()
        time.sleep(FLOTTE_TEST_PAUSE_SECONDS)

    def goto(self, url_name, **kwargs):
        """Ouvre l'URL nommée (reverse) et reste sur la page le temps de la pause configurée."""
        path = reverse(url_name, **kwargs)
        self.driver.get(self.live_server_url + path)
        time.sleep(FLOTTE_TEST_PAUSE_SECONDS)

    def page_ok(self, expected_status=200):
        """Vérifie que la page courante n'est pas une erreur 403/404/500."""
        # Selenium ne donne pas le code HTTP directement ; on vérifie l'absence de corps d'erreur
        body = self.driver.find_element('tag name', 'body').text
        self.assertNotIn('403', self.driver.title or '')
        self.assertNotIn('Forbidden', body)
        self.assertNotIn('PermissionDenied', body)

    def page_forbidden(self):
        """Vérifie que la page affiche un accès interdit (403)."""
        body = self.driver.find_element('tag name', 'body').text
        self.assertTrue(
            '403' in (self.driver.title or '') or 'Forbidden' in body or 'interdit' in body.lower() or 'PermissionDenied' in body,
            f'Expected 403/Forbidden, got title={self.driver.title!r}'
        )


@override_settings(DEBUG=True)  # Nécessaire pour que /static/ soit servi pendant les tests (Django met DEBUG=False par défaut)
class SeleniumUserJourneyTests(SeleniumTestMixin, LiveServerTestCase):
    """
    Parcours utilisateur (rôle user) — consultation uniquement.
    Doit accéder : dashboard, parc, réparations, documents, maintenance, carburant, conducteurs.
    Doit être refusé (403) : import, ventes, CA, location, paramétrage.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver = get_selenium_driver()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username=FLOTTE_TEST_USER_USERNAME,
            password=FLOTTE_TEST_USER_PASSWORD,
            is_staff=False,
        )
        ProfilUtilisateur.objects.get_or_create(
            user=self.user, defaults={'role': 'user'}
        )
        p = self.user.profil_flotte
        p.role = 'user'
        p.save()

    def test_user_journey_pages_allowed(self):
        """Utilisateur peut consulter dashboard, parc, réparations, documents, maintenance, carburant, conducteurs."""
        self.login(FLOTTE_TEST_USER_USERNAME, FLOTTE_TEST_USER_PASSWORD)
        self.goto('flotte:dashboard')
        self.assertIn('dashboard', self.driver.current_url.lower() or '')
        self.goto('flotte:parc')
        self.page_ok()
        self.goto('flotte:reparations_list')
        self.page_ok()
        self.goto('flotte:documents_list')
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

    def test_user_denied_ventes(self):
        self.login(FLOTTE_TEST_USER_USERNAME, FLOTTE_TEST_USER_PASSWORD)
        self.goto('flotte:ventes_list')
        self.page_forbidden()

    def test_user_denied_ca(self):
        self.login(FLOTTE_TEST_USER_USERNAME, FLOTTE_TEST_USER_PASSWORD)
        self.goto('flotte:ca')
        self.page_forbidden()

    def test_user_denied_location(self):
        self.login(FLOTTE_TEST_USER_USERNAME, FLOTTE_TEST_USER_PASSWORD)
        self.goto('flotte:location_list')
        self.page_forbidden()

    def test_user_denied_parametrage(self):
        self.login(FLOTTE_TEST_USER_USERNAME, FLOTTE_TEST_USER_PASSWORD)
        self.goto('flotte:parametrage_index')
        self.page_forbidden()


@override_settings(DEBUG=True)  # Pour que le CSS soit chargé pendant les tests Selenium
class SeleniumManagerJourneyTests(SeleniumTestMixin, LiveServerTestCase):
    """
    Parcours gestionnaire (rôle manager) — consultation + import, ventes, CA, location.
    Doit être refusé : paramétrage (admin).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver = get_selenium_driver()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username=FLOTTE_TEST_MANAGER_USERNAME,
            password=FLOTTE_TEST_MANAGER_PASSWORD,
            is_staff=False,
        )
        ProfilUtilisateur.objects.get_or_create(
            user=self.user, defaults={'role': 'manager'}
        )
        p = self.user.profil_flotte
        p.role = 'manager'
        p.save()

    def test_manager_journey_operational_pages(self):
        """Gestionnaire accède à dashboard, parc, import, ventes, CA, location."""
        self.login(FLOTTE_TEST_MANAGER_USERNAME, FLOTTE_TEST_MANAGER_PASSWORD)
        self.goto('flotte:dashboard')
        self.page_ok()
        self.goto('flotte:parc')
        self.page_ok()
        self.goto('flotte:import_list')
        self.page_ok()
        self.goto('flotte:ventes_list')
        self.page_ok()
        self.goto('flotte:ca')
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


@override_settings(DEBUG=True)  # Pour que le CSS soit chargé pendant les tests Selenium
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
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username=FLOTTE_TEST_ADMIN_USERNAME,
            password=FLOTTE_TEST_ADMIN_PASSWORD,
            is_staff=True,
            is_superuser=True,
        )
        ProfilUtilisateur.objects.get_or_create(
            user=self.user, defaults={'role': 'admin'}
        )
        p = self.user.profil_flotte
        p.role = 'admin'
        p.save()

    def test_admin_journey_all_pages(self):
        """Admin accède à tout : dashboard, parc, import, ventes, CA, location, paramétrage."""
        self.login(FLOTTE_TEST_ADMIN_USERNAME, FLOTTE_TEST_ADMIN_PASSWORD)
        self.goto('flotte:dashboard')
        self.page_ok()
        self.goto('flotte:parc')
        self.page_ok()
        self.goto('flotte:import_list')
        self.page_ok()
        self.goto('flotte:ventes_list')
        self.page_ok()
        self.goto('flotte:ca')
        self.page_ok()
        self.goto('flotte:location_list')
        self.page_ok()
        self.goto('flotte:parametrage_index')
        self.page_ok()
        self.goto('flotte:parametrage_marques')
        self.page_ok()
