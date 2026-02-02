"""Charge les données initiales de paramétrage FLOTTE (marques, modèles, types)."""
from django.core.management.base import BaseCommand
from flotte.models import Marque, Modele, TypeCarburant, TypeTransmission, TypeVehicule


class Command(BaseCommand):
    help = 'Charge marques, modèles, types carburant, transmission, véhicule.'

    def handle(self, *args, **options):
        if TypeCarburant.objects.exists():
            self.stdout.write('Paramétrage déjà chargé.')
            return

        carburants = ['Essence', 'Diesel', 'Gasoil', 'Électrique', 'Hybride', 'GPL', 'GNV']
        for lib in carburants:
            TypeCarburant.objects.get_or_create(libelle=lib)
        self.stdout.write(f'  {len(carburants)} types carburant.')

        transmissions = ['Manuelle', 'Automatique', 'Semi-automatique', 'Robotisée']
        for lib in transmissions:
            TypeTransmission.objects.get_or_create(libelle=lib)
        self.stdout.write(f'  {len(transmissions)} types transmission.')

        types_veh = ['Voiture', 'SUV', 'Fourgon', 'Utilitaire', 'Camion', 'Bus', 'Engin de chantier']
        for lib in types_veh:
            TypeVehicule.objects.get_or_create(libelle=lib)
        self.stdout.write(f'  {len(types_veh)} types véhicule.')

        marques_nom = [
            'Mercedes', 'BMW', 'Toyota', 'Renault', 'Audi', 'VW', 'Honda',
            'Nissan', 'Peugeot', 'Ford', 'Citroën', 'Opel', 'Hyundai',
        ]
        for nom in marques_nom:
            Marque.objects.get_or_create(nom=nom)
        self.stdout.write(f'  {len(marques_nom)} marques.')

        marques = {m.nom: m for m in Marque.objects.all()}
        modeles_data = [
            ('Mercedes', 'Classe C'), ('Mercedes', 'Classe E'), ('BMW', '320d'),
            ('BMW', '320i'), ('Toyota', 'Corolla'), ('Toyota', 'Yaris'),
            ('Renault', 'Mégane'), ('Renault', 'Kangoo'), ('Renault', 'Clio'),
            ('Audi', 'A4'), ('VW', 'Golf'), ('VW', 'Passat'), ('Honda', 'Civic'),
            ('Nissan', 'Qashqai'), ('Peugeot', '3008'), ('Peugeot', '308'),
            ('Ford', 'Focus'), ('Citroën', 'C3'),
        ]
        for marque_nom, modele_nom in modeles_data:
            marque = marques.get(marque_nom)
            if marque:
                Modele.objects.get_or_create(marque=marque, nom=modele_nom)
        self.stdout.write(f'  {len(modeles_data)} modèles.')
        self.stdout.write(self.style.SUCCESS('Paramétrage initial chargé.'))
