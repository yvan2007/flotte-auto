"""
Tests fonctionnels FLOTTE — parcours utilisateur avec Selenium et Chrome.
Vérifie que chaque rôle (user, manager, admin) accède aux bonnes pages
et est bloqué sur les pages restreintes. Utilise des attentes explicites
pour éviter les échecs intermittents.
"""
import time
import tempfile
from datetime import date
from pathlib import Path
from django.test import LiveServerTestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from flotte.models import (
    ProfilUtilisateur,
    Marque,
    Modele,
    TypeVehicule,
    TypeCarburant,
    TypeTransmission,
    TypeDocument,
    Vehicule,
    Location,
    Vente,
    Depense,
    Reparation,
    ImportDemarche,
    ChargeImport,
    PartieImportee,
    DocumentVehicule,
    Maintenance,
    ReleveCarburant,
    Conducteur,
    Contravention,
    PhotoVehicule,
)
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


def _ensure_catalog_basics():
    """
    Crée un minimum de données de paramétrage nécessaires aux formulaires
    (marque/modèle/types) pour les tests E2E.
    """
    type_vehicule, _ = TypeVehicule.objects.get_or_create(libelle='Berline')
    type_carburant, _ = TypeCarburant.objects.get_or_create(libelle='Essence')
    type_transmission, _ = TypeTransmission.objects.get_or_create(libelle='Automatique')
    type_document, _ = TypeDocument.objects.get_or_create(libelle='Carte grise', defaults={'ordre': 1})
    marque, _ = Marque.objects.get_or_create(nom='TestMarqueE2E', defaults={'archive': False})
    if marque.archive:
        marque.archive = False
        marque.save(update_fields=['archive'])
    modele, _ = Modele.objects.get_or_create(
        marque=marque,
        nom='TestModeleE2E',
        version='V1',
        defaults={'annee_min': 2020, 'annee_max': None, 'archive': False},
    )
    if modele.archive:
        modele.archive = False
        modele.save(update_fields=['archive'])
    return {
        'type_vehicule': type_vehicule,
        'type_carburant': type_carburant,
        'type_transmission': type_transmission,
        'type_document': type_document,
        'marque': marque,
        'modele': modele,
    }


def _write_temp_png():
    """
    Écrit un PNG minimal sur disque (nécessaire pour <input type=file> Selenium).
    Retourne le chemin.
    """
    # PNG 1x1 transparent
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0cIDAT\x08\xd7c"
        b"\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\xa6\x8c\xb7\x00\x00\x00\x00IEND"
        b"\xaeB`\x82"
    )
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    tmp.write(png_bytes)
    tmp.flush()
    tmp.close()
    return Path(tmp.name)


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

    def _wait_select_has_non_empty_option(self, select_id, timeout=WAIT_TIMEOUT):
        """Attend qu'un <select> ait au moins une option avec value non vide."""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support.ui import Select

        def _has_non_empty(_driver):
            el = _driver.find_element('id', select_id)
            sel = Select(el)
            for opt in sel.options:
                value = (opt.get_attribute('value') or '').strip()
                if value:
                    return True
            return False

        WebDriverWait(self.driver, timeout).until(_has_non_empty)

    def _select_first_non_empty(self, select_id):
        from selenium.webdriver.support.ui import Select
        el = self.wait_for_element('id', select_id, timeout=WAIT_TIMEOUT)
        sel = Select(el)
        # Choisir le 1er choix non vide si possible
        for opt in sel.options:
            value = (opt.get_attribute('value') or '').strip()
            if value:
                sel.select_by_value(value)
                return value
        return None

    def _set_input_value(self, input_id, value):
        el = self.wait_for_element('id', input_id, timeout=WAIT_TIMEOUT)
        el.clear()
        el.send_keys(value)

    def _submit(self):
        self.wait_for_element('css selector', 'button[type="submit"]', timeout=WAIT_TIMEOUT).click()

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

    def test_user_denied_vehicule_create(self):
        self.login(FLOTTE_TEST_USER_USERNAME, FLOTTE_TEST_USER_PASSWORD)
        self.goto('flotte:vehicule_create')
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

    def test_manager_full_workflow_create_everywhere_smoke(self):
        """
        Smoke E2E: création véhicule puis création dans la plupart des modules liés.
        Objectif: vérifier que "ça rentre partout" (formulaires + redirections + permissions).
        """
        basics = _ensure_catalog_basics()
        self.login(FLOTTE_TEST_MANAGER_USERNAME, FLOTTE_TEST_MANAGER_PASSWORD)

        # 1) Créer un véhicule (UI)
        chassis = f"E2E-{int(time.time())}"
        self.goto('flotte:vehicule_create')
        self._set_input_value('id_numero_chassis', chassis)
        self._select_first_non_empty('id_marque')
        # Dépend de la marque: la liste des modèles est mise à jour via fetch().
        self._wait_select_has_non_empty_option('id_modele', timeout=WAIT_TIMEOUT)
        self._select_first_non_empty('id_modele')
        self._set_input_value('id_annee', '2025')
        self._select_first_non_empty('id_statut')
        self._select_first_non_empty('id_type_vehicule')
        self._select_first_non_empty('id_type_carburant')
        self._select_first_non_empty('id_type_transmission')
        self._submit()
        self.wait_for_url_contains('/parc/', timeout=WAIT_TIMEOUT)
        self.page_ok()
        vehicule = Vehicule.objects.get(numero_chassis=chassis)

        # 2) Ajouter une dépense
        self.goto('flotte:depense_create', vehicule_pk=vehicule.pk)
        self._select_first_non_empty('id_type_depense')
        self._set_input_value('id_libelle', 'Plein test E2E')
        self._set_input_value('id_phase', 'Import')
        self._set_input_value('id_montant', '10000')
        self._set_input_value('id_date_depense', '2026-02-01')
        self._submit()
        self.page_ok()
        self.assertTrue(Depense.objects.filter(vehicule=vehicule).exists())

        # 3) Ajouter une réparation
        self.goto('flotte:reparation_create', vehicule_pk=vehicule.pk)
        self._set_input_value('id_date_reparation', '2026-02-02')
        self._set_input_value('id_kilometrage', '50000')
        self._set_input_value('id_type_rep', 'Mécanique')
        self._set_input_value('id_description', 'Réparation test E2E')
        self._set_input_value('id_cout', '25000')
        self._set_input_value('id_prestataire', 'Garage E2E')
        self._submit()
        self.page_ok()
        self.assertTrue(Reparation.objects.filter(vehicule=vehicule).exists())

        # 4) Ajouter une démarche d'import
        self.goto('flotte:import_demarche_create', vehicule_pk=vehicule.pk)
        self._set_input_value('id_etape', 'Dédouanement')
        self._set_input_value('id_date_etape', '2026-02-03')
        self._set_input_value('id_statut_etape', 'En cours')
        self._set_input_value('id_remarque', 'Démarche test E2E')
        self._submit()
        self.page_ok()
        self.assertTrue(ImportDemarche.objects.filter(vehicule=vehicule).exists())

        # 5) Ajouter des charges d'import
        self.goto('flotte:charge_import_create', vehicule_pk=vehicule.pk)
        self._set_input_value('id_fret', '100000')
        self._set_input_value('id_frais_dedouanement', '20000')
        self._set_input_value('id_frais_transitaire', '15000')
        self._set_input_value('id_cout_total', '135000')
        self._submit()
        self.page_ok()
        self.assertTrue(ChargeImport.objects.filter(vehicule=vehicule).exists())

        # 6) Ajouter une partie importée
        self.goto('flotte:partie_importee_create', vehicule_pk=vehicule.pk)
        # vehicule est pré-rempli (initial), mais on s'assure qu'il est sélectionné si select existe
        self._set_input_value('id_designation', 'Pare-choc')
        self._set_input_value('id_quantite', '1')
        self._set_input_value('id_cout_unitaire', '50000')
        self._submit()
        self.page_ok()
        self.assertTrue(PartieImportee.objects.filter(vehicule=vehicule).exists())

        # 7) Ajouter un document véhicule
        self.goto('flotte:document_create', vehicule_pk=vehicule.pk)
        # Prendre un type en liste, sinon saisir librement
        chosen = self._select_first_non_empty('id_type_document_fk')
        if not chosen:
            self._set_input_value('id_type_document', basics['type_document'].libelle)
        self._set_input_value('id_numero', 'DOC-001')
        self._set_input_value('id_date_emission', '2026-02-01')
        self._set_input_value('id_date_echeance', '2027-02-01')
        self._submit()
        self.page_ok()
        self.assertTrue(DocumentVehicule.objects.filter(vehicule=vehicule).exists())

        # 8) Ajouter une photo véhicule (upload)
        self.goto('flotte:photo_vehicule_create', vehicule_pk=vehicule.pk)
        img_path = _write_temp_png()
        self.wait_for_element('id', 'id_photo', timeout=WAIT_TIMEOUT).send_keys(str(img_path))
        self._select_first_non_empty('id_angle')
        self._set_input_value('id_description', 'Photo test E2E')
        self._submit()
        self.page_ok()
        self.assertTrue(PhotoVehicule.objects.filter(vehicule=vehicule).exists())

        # 9) Créer un conducteur
        self.goto('flotte:conducteur_create')
        self._set_input_value('id_nom', 'Dupont')
        self._set_input_value('id_prenom', 'Jean')
        self._set_input_value('id_telephone', '00000000')
        self._submit()
        self.page_ok()
        self.assertTrue(Conducteur.objects.filter(nom='Dupont', prenom='Jean').exists())

        # 10) Créer une location
        self.goto('flotte:location_create')
        self._select_first_non_empty('id_vehicule')
        self._set_input_value('id_locataire', 'Client E2E')
        self._select_first_non_empty('id_type_location')
        self._set_input_value('id_loyer_mensuel', '200000')
        self._set_input_value('id_date_debut', '2026-02-05')
        self._set_input_value('id_date_fin', '2026-03-05')
        self._set_input_value('id_km_inclus_mois', '1000')
        self._set_input_value('id_prix_km_supplementaire', '100')
        self._select_first_non_empty('id_statut')
        self._submit()
        self.page_ok()
        loc = Location.objects.order_by('-id').first()
        self.assertIsNotNone(loc)

        # 11) Ajouter une contravention sur la location
        self.goto('flotte:contravention_create', location_pk=loc.pk)
        self._set_input_value('id_date_contravention', '2026-02-06')
        self._set_input_value('id_motif', 'Stationnement interdit')
        self._set_input_value('id_reference', 'PV-001')
        self._set_input_value('id_montant', '25000')
        self._set_input_value('id_lieu', 'Centre-ville')
        self._submit()
        self.page_ok()
        self.assertTrue(Contravention.objects.filter(location=loc).exists())

        # 12) Maintenance (création)
        self.goto('flotte:maintenance_create')
        self._select_first_non_empty('id_vehicule')
        self._select_first_non_empty('id_type_maintenance')
        self._select_first_non_empty('id_statut')
        self._set_input_value('id_date_prevue', '2026-04-01')
        self._submit()
        self.page_ok()
        self.assertTrue(Maintenance.objects.exists())

        # 13) Carburant (relevé)
        self.goto('flotte:carburant_create')
        self._select_first_non_empty('id_vehicule')
        self._set_input_value('id_date_releve', '2026-02-10')
        self._set_input_value('id_kilometrage', '51000')
        self._set_input_value('id_litres', '40')
        self._set_input_value('id_montant_fcfa', '30000')
        self._set_input_value('id_prix_litre', '750')
        self._set_input_value('id_lieu', 'Station E2E')
        self._submit()
        self.page_ok()
        self.assertTrue(ReleveCarburant.objects.exists())

        # 14) Vente (création)
        self.goto('flotte:vente_create', vehicule_pk=vehicule.pk)
        self._set_input_value('id_date_vente', '2026-02-12')
        self._set_input_value('id_acquereur', 'Acheteur E2E')
        self._set_input_value('id_prix_vente', '1500000')
        self._set_input_value('id_km_vente', '52000')
        self._set_input_value('id_garantie_duree', '6 mois')
        self._set_input_value('id_etat_livraison', 'Bon état')
        self._submit()
        self.page_ok()
        self.assertTrue(Vente.objects.filter(vehicule=vehicule).exists())


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

    def test_admin_parametrage_create_marque_modele_type_document_smoke(self):
        """Smoke E2E (admin): création dans le paramétrage (marque, modèle, type document)."""
        self.login(FLOTTE_TEST_ADMIN_USERNAME, FLOTTE_TEST_ADMIN_PASSWORD)

        # Marque
        marque_nom = f"MarqueE2E-{int(time.time())}"
        self.goto('flotte:marque_create')
        self._set_input_value('id_nom', marque_nom)
        self._submit()
        self.wait_for_url_contains('/parametrage/marques/', timeout=WAIT_TIMEOUT)
        self.page_ok()
        self.assertTrue(Marque.objects.filter(nom=marque_nom).exists())

        # Modèle (lié à la marque)
        self.goto('flotte:modele_create')
        self._select_first_non_empty('id_marque')
        self._set_input_value('id_nom', 'ModeleE2E')
        self._set_input_value('id_version', 'V1')
        self._set_input_value('id_annee_min', '2020')
        self._submit()
        self.wait_for_url_contains('/parametrage/modeles/', timeout=WAIT_TIMEOUT)
        self.page_ok()
        self.assertTrue(Modele.objects.filter(nom='ModeleE2E').exists())

        # Type document
        self.goto('flotte:type_document_create')
        self._set_input_value('id_libelle', f"TypeDocE2E-{int(time.time())}")
        self._set_input_value('id_ordre', '10')
        self._submit()
        self.wait_for_url_contains('/parametrage/type-document/', timeout=WAIT_TIMEOUT)
        self.page_ok()