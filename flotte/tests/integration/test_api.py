"""
Tests d'intégration FLOTTE — API (index, évolution CA, marques, etc.).
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from flotte.models import (
    ProfilUtilisateur,
    Marque,
    Modele,
    Vehicule,
    Vente,
)

User = get_user_model()


class ApiIndexTests(TestCase):
    """Tests pour GET /api/ (redirection HTML vs JSON)."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='apiuser', password='testpass123', is_staff=False
        )
        ProfilUtilisateur.objects.get_or_create(
            user=self.user, defaults={'role': 'user'}
        )

    def test_api_index_anonymous_redirects_to_login(self):
        """Sans authentification, /api/ redirige vers la page de connexion."""
        response = self.client.get(reverse('flotte:api_index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('flotte:login'), response.url)

    def test_api_index_accept_html_redirects_to_api_root(self):
        """Authentifié + Accept: text/html → redirection vers l'API root DRF."""
        self.client.login(username='apiuser', password='testpass123')
        response = self.client.get(
            reverse('flotte:api_index'),
            HTTP_ACCEPT='text/html, application/xhtml+xml',
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('flotte:api-root'))

    def test_api_index_accept_json_returns_index(self):
        """Authentifié + Accept: application/json → JSON avec endpoints."""
        self.client.login(username='apiuser', password='testpass123')
        response = self.client.get(
            reverse('flotte:api_index'),
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('message', data)
        self.assertIn('endpoints', data)
        self.assertIn('api_legere', data['endpoints'])
        self.assertIn('marques', data['endpoints']['api_legere'])
        self.assertIn('api_rest_framework_v1', data['endpoints'])
        self.assertIn('ca_evolution', data['endpoints'])


class CaApiEvolutionTests(TestCase):
    """Tests pour GET /ca/api/evolution/ (données graphiques CA)."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='causer', password='testpass123', is_staff=False
        )
        ProfilUtilisateur.objects.get_or_create(
            user=self.user, defaults={'role': 'user'}
        )
        self.marque = Marque.objects.create(nom='TestMarque')
        self.modele = Modele.objects.create(
            marque=self.marque, nom='TestModele', version='V1', annee_min=2020
        )
        self.vehicule = Vehicule.objects.create(
            numero_chassis='CHASSIS_CA_001',
            marque=self.marque,
            modele=self.modele,
            statut='vendu',
        )

    def test_ca_api_evolution_anonymous_redirects(self):
        """Sans authentification → redirection vers login."""
        response = self.client.get(reverse('flotte:ca_api_evolution'))
        self.assertEqual(response.status_code, 302)

    def test_ca_api_evolution_logged_in_returns_json(self):
        """Utilisateur connecté → 200 et JSON avec labels, data, nb_ventes."""
        self.client.login(username='causer', password='testpass123')
        response = self.client.get(
            reverse('flotte:ca_api_evolution'),
            {'granularite': 'mois', 'annee': '2025'},
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('labels', data)
        self.assertIn('data', data)
        self.assertIn('nb_ventes', data)
        self.assertIsInstance(data['labels'], list)
        self.assertIsInstance(data['data'], list)
        self.assertIsInstance(data['nb_ventes'], list)

    def test_ca_api_evolution_empty_data(self):
        """Sans ventes pour l'année → listes vides."""
        self.client.login(username='causer', password='testpass123')
        response = self.client.get(
            reverse('flotte:ca_api_evolution'),
            {'granularite': 'mois', 'annee': '2099'},
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['labels'], [])
        self.assertEqual(data['data'], [])
        self.assertEqual(data['nb_ventes'], [])

    def test_ca_api_evolution_with_vente_returns_data(self):
        """Avec une vente pour l'année → labels, data et nb_ventes cohérents."""
        Vente.objects.create(
            vehicule=self.vehicule,
            date_vente=date(2025, 3, 15),
            prix_vente=Decimal('1000000'),
        )
        self.client.login(username='causer', password='testpass123')
        response = self.client.get(
            reverse('flotte:ca_api_evolution'),
            {'granularite': 'mois', 'annee': '2025'},
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['labels']), 1)
        self.assertIn('Mar', data['labels'][0])
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0], 1000000.0)
        self.assertEqual(data['nb_ventes'], [1])

    def test_ca_api_evolution_granularite_annee(self):
        """Paramètre granularite=annee retourne des labels année."""
        Vente.objects.create(
            vehicule=self.vehicule,
            date_vente=date(2024, 6, 1),
            prix_vente=Decimal('500000'),
        )
        self.client.login(username='causer', password='testpass123')
        response = self.client.get(
            reverse('flotte:ca_api_evolution'),
            {'granularite': 'annee', 'annee': '2024'},
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['labels']), 1)
        self.assertEqual(data['labels'][0], '2024')
        self.assertEqual(data['data'][0], 500000.0)


class ApiMarquesTests(TestCase):
    """Tests pour GET /api/marques/."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='marquesuser', password='testpass123', is_staff=False
        )
        ProfilUtilisateur.objects.get_or_create(
            user=self.user, defaults={'role': 'user'}
        )
        Marque.objects.create(nom='MarqueA')
        Marque.objects.create(nom='MarqueB')

    def test_api_marques_anonymous_redirects(self):
        response = self.client.get(reverse('flotte:api_marques_list'))
        self.assertEqual(response.status_code, 302)

    def test_api_marques_returns_list(self):
        self.client.login(username='marquesuser', password='testpass123')
        response = self.client.get(
            reverse('flotte:api_marques_list'),
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('marques', data)
        self.assertGreaterEqual(len(data['marques']), 2)
        noms = [m['nom'] for m in data['marques']]
        self.assertIn('MarqueA', noms)
        self.assertIn('MarqueB', noms)


class ApiCaSyntheseTests(TestCase):
    """Tests pour GET /api/ca/synthese/ (réservé manager/admin)."""

    def setUp(self):
        self.client = Client()
        self.manager = User.objects.create_user(
            username='synthesemgr', password='testpass123', is_staff=False
        )
        ProfilUtilisateur.objects.get_or_create(
            user=self.manager, defaults={'role': 'manager'}
        )
        p = ProfilUtilisateur.objects.get(user=self.manager)
        p.role = 'manager'
        p.save()

    def test_api_ca_synthese_anonymous_redirects(self):
        response = self.client.get(reverse('flotte:api_ca_synthese'))
        self.assertEqual(response.status_code, 302)

    def test_api_ca_synthese_manager_returns_total_nb_moyenne(self):
        self.client.login(username='synthesemgr', password='testpass123')
        response = self.client.get(
            reverse('flotte:api_ca_synthese'),
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total_ca', data)
        self.assertIn('nb_ventes', data)
        self.assertIn('moyenne_vente', data)


class ApiRootDrfTests(TestCase):
    """Tests pour l'API root DRF /api/v1/."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='drfuser', password='testpass123', is_staff=False
        )
        ProfilUtilisateur.objects.get_or_create(
            user=self.user, defaults={'role': 'user'}
        )

    def test_api_v1_root_anonymous_redirects_or_403(self):
        """Sans auth, api/v1/ peut rediriger ou 403 selon config DRF."""
        response = self.client.get(reverse('flotte:api-root'))
        self.assertIn(response.status_code, (302, 403))

    def test_api_v1_root_authenticated_returns_200(self):
        """Authentifié → 200 et liens vers les ressources."""
        self.client.login(username='drfuser', password='testpass123')
        response = self.client.get(reverse('flotte:api-root'))
        self.assertEqual(response.status_code, 200)
