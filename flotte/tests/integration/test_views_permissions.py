"""
Tests d'intégration FLOTTE — accès aux vues selon le rôle (user, manager, admin).
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from flotte.models import ProfilUtilisateur, Marque, Modele, Vehicule, Vente

User = get_user_model()


class PermissionsViewsTests(TestCase):
    """Tests d'accès aux vues selon le rôle (manager vs user vs admin)."""

    def setUp(self):
        self.client = Client()
        # Manager
        self.user_manager = User.objects.create_user(
            username='manager1', password='testpass123', is_staff=False
        )
        p, _ = ProfilUtilisateur.objects.get_or_create(
            user=self.user_manager, defaults={'role': 'manager'}
        )
        p.role = 'manager'
        p.save()
        # User (consultation)
        self.user_normal = User.objects.create_user(
            username='user1', password='testpass123', is_staff=False
        )
        p2, _ = ProfilUtilisateur.objects.get_or_create(
            user=self.user_normal, defaults={'role': 'user'}
        )
        p2.role = 'user'
        p2.save()
        # Admin
        self.user_admin = User.objects.create_user(
            username='admin1', password='testpass123', is_staff=True, is_superuser=True
        )
        p3, _ = ProfilUtilisateur.objects.get_or_create(
            user=self.user_admin, defaults={'role': 'admin'}
        )
        p3.role = 'admin'
        p3.save()

    def test_login_required_dashboard(self):
        response = self.client.get(reverse('flotte:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.client.login(username='manager1', password='testpass123')
        response = self.client.get(reverse('flotte:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_manager_can_access_parc(self):
        self.client.login(username='manager1', password='testpass123')
        response = self.client.get(reverse('flotte:parc'))
        self.assertEqual(response.status_code, 200)

    def test_user_can_access_parc(self):
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(reverse('flotte:parc'))
        self.assertEqual(response.status_code, 200)

    def test_user_denied_import_list(self):
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(reverse('flotte:import_list'))
        self.assertEqual(response.status_code, 403)

    def test_manager_can_access_import_list(self):
        self.client.login(username='manager1', password='testpass123')
        response = self.client.get(reverse('flotte:import_list'))
        self.assertEqual(response.status_code, 200)

    def test_user_denied_ca(self):
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(reverse('flotte:ca'))
        self.assertEqual(response.status_code, 403)

    def test_manager_can_access_ca(self):
        self.client.login(username='manager1', password='testpass123')
        response = self.client.get(reverse('flotte:ca'))
        self.assertEqual(response.status_code, 200)

    def test_user_can_access_ventes_list(self):
        """Liste ventes : accessible à tout utilisateur connecté (filtrée par acquereur pour rôle user)."""
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(reverse('flotte:ventes_list'))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_parametrage(self):
        self.client.login(username='admin1', password='testpass123')
        response = self.client.get(reverse('flotte:parametrage_index'))
        self.assertEqual(response.status_code, 200)

    def test_manager_denied_parametrage_marques(self):
        self.client.login(username='manager1', password='testpass123')
        response = self.client.get(reverse('flotte:parametrage_marques'))
        self.assertEqual(response.status_code, 403)

    def test_user_can_access_maintenance_list(self):
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(reverse('flotte:maintenance_list'))
        self.assertEqual(response.status_code, 200)

    def test_user_can_access_carburant_list(self):
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(reverse('flotte:carburant_list'))
        self.assertEqual(response.status_code, 200)

    def test_user_can_access_conducteurs_list(self):
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(reverse('flotte:conducteurs_list'))
        self.assertEqual(response.status_code, 200)

    def test_login_redirect_with_next_api(self):
        """Après connexion avec ?next=/api/, redirection vers /api/."""
        login_url = reverse('flotte:login')
        next_url = '/api/'
        response = self.client.post(
            login_url,
            {'username': 'manager1', 'password': 'testpass123', 'next': next_url},
            follow=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, next_url)

    def test_ca_view_annee_courante_when_ventes_exist(self):
        """Page CA : annee_courante = dernière année ayant une vente."""
        marque = Marque.objects.create(nom='CA Test')
        modele = Modele.objects.create(
            marque=marque, nom='M1', version='V1', annee_min=2020
        )
        vehicule = Vehicule.objects.create(
            numero_chassis='CH_CA_TEST',
            marque=marque,
            modele=modele,
            statut='vendu',
        )
        Vente.objects.create(
            vehicule=vehicule,
            date_vente=date(2023, 5, 10),
            prix_vente=Decimal('500000'),
        )
        self.client.login(username='manager1', password='testpass123')
        response = self.client.get(reverse('flotte:ca'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['annee_courante'], 2023)
        self.assertIn(2023, response.context['annees'])
