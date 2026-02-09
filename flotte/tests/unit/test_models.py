"""
Tests unitaires FLOTTE — modèles (véhicules, châssis unique, marques, dépenses, etc.).
"""
from decimal import Decimal
from datetime import date
from django.test import TestCase

from flotte.models import (
    Marque,
    Modele,
    Vehicule,
    Depense,
    Maintenance,
    ReleveCarburant,
    Conducteur,
    Vente,
)


class VehiculeModelTests(TestCase):
    """Tests sur le modèle Véhicule (unicité châssis)."""

    def setUp(self):
        self.marque = Marque.objects.create(nom='Toyota')
        self.modele = Modele.objects.create(
            marque=self.marque, nom='Corolla', version='Berline', annee_min=2020
        )

    def test_creation_vehicule_ok(self):
        v = Vehicule.objects.create(
            numero_chassis='CHASSIS001',
            marque=self.marque,
            modele=self.modele,
            statut='parc',
        )
        self.assertEqual(v.numero_chassis, 'CHASSIS001')
        self.assertEqual(v.marque.nom, 'Toyota')

    def test_unicite_chassis(self):
        Vehicule.objects.create(
            numero_chassis='CHASSIS002',
            marque=self.marque,
            modele=self.modele,
            statut='parc',
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Vehicule.objects.create(
                numero_chassis='CHASSIS002',
                marque=self.marque,
                modele=self.modele,
                statut='parc',
            )


class MarqueModelTests(TestCase):
    """Tests sur le modèle Marque (unicité nom)."""

    def test_creation_marque_ok(self):
        m = Marque.objects.create(nom='Mercedes')
        self.assertEqual(m.nom, 'Mercedes')

    def test_unicite_nom_marque(self):
        Marque.objects.create(nom='BMW')
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Marque.objects.create(nom='BMW')


class DepenseModelTests(TestCase):
    """Tests sur le modèle Dépense (rattachement véhicule)."""

    def setUp(self):
        self.marque = Marque.objects.create(nom='Peugeot')
        self.modele = Modele.objects.create(
            marque=self.marque, nom='308', version='Berline', annee_min=2019
        )
        self.vehicule = Vehicule.objects.create(
            numero_chassis='CHASSIS003',
            marque=self.marque,
            modele=self.modele,
            statut='parc',
        )

    def test_creation_depense_ok(self):
        d = Depense.objects.create(
            vehicule=self.vehicule,
            type_depense='carburant',
            libelle='Plein',
            montant=Decimal('50000'),
        )
        self.assertEqual(d.vehicule.numero_chassis, 'CHASSIS003')
        self.assertEqual(d.type_depense, 'carburant')


class RapportJournalierMaintenanceConducteurTests(TestCase):
    """Tests sur les modèles Maintenance, ReleveCarburant, Conducteur."""

    def setUp(self):
        self.marque = Marque.objects.create(nom='Renault')
        self.modele = Modele.objects.create(
            marque=self.marque, nom='Clio', version='Berline', annee_min=2020
        )
        self.vehicule = Vehicule.objects.create(
            numero_chassis='CHASSIS004',
            marque=self.marque,
            modele=self.modele,
            statut='parc',
        )

    def test_creation_conducteur_ok(self):
        c = Conducteur.objects.create(nom='Dupont', prenom='Jean', actif=True)
        self.assertEqual(c.nom, 'Dupont')
        self.assertTrue(c.actif)

    def test_creation_maintenance_ok(self):
        m = Maintenance.objects.create(
            vehicule=self.vehicule,
            type_maintenance='vidange',
            statut='a_faire',
            date_prevue=date(2026, 3, 1),
        )
        self.assertEqual(m.vehicule.numero_chassis, 'CHASSIS004')
        self.assertEqual(m.get_type_maintenance_display(), 'Vidange')

    def test_creation_releve_carburant_ok(self):
        r = ReleveCarburant.objects.create(
            vehicule=self.vehicule,
            date_releve=date(2026, 2, 1),
            kilometrage=50000,
            montant_fcfa=Decimal('45000'),
        )
        self.assertEqual(r.vehicule.numero_chassis, 'CHASSIS004')


class VenteModelTests(TestCase):
    """Tests sur le modèle Vente (CA, graphiques évolution)."""

    def setUp(self):
        self.marque = Marque.objects.create(nom='VenteTest')
        self.modele = Modele.objects.create(
            marque=self.marque, nom='M1', version='V1', annee_min=2020
        )
        self.vehicule = Vehicule.objects.create(
            numero_chassis='CH_VENTE_001',
            marque=self.marque,
            modele=self.modele,
            statut='vendu',
        )

    def test_creation_vente_ok(self):
        v = Vente.objects.create(
            vehicule=self.vehicule,
            date_vente=date(2025, 1, 15),
            prix_vente=Decimal('2500000'),
        )
        self.assertEqual(v.vehicule.numero_chassis, 'CH_VENTE_001')
        self.assertEqual(v.date_vente.year, 2025)
        self.assertEqual(v.prix_vente, Decimal('2500000'))

    def test_vente_sans_prix_autorise(self):
        """Vente avec prix_vente null (pour évolution CA, exclue du CA)."""
        v = Vente.objects.create(
            vehicule=self.vehicule,
            date_vente=date(2025, 2, 1),
        )
        self.assertIsNone(v.prix_vente)
