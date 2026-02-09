"""
Sérialiseurs Django REST Framework pour l'API FLOTTE.
"""
from rest_framework import serializers
from .models import (
    Marque, Modele, TypeCarburant, TypeTransmission, TypeVehicule,
    Vehicule, Vente, Location, Conducteur,
)


class MarqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = ['id', 'nom', 'archive', 'created_at']


class ModeleSerializer(serializers.ModelSerializer):
    marque_nom = serializers.CharField(source='marque.nom', read_only=True)

    class Meta:
        model = Modele
        fields = ['id', 'marque', 'marque_nom', 'nom', 'version', 'annee_min', 'annee_max', 'archive', 'created_at']


class TypeCarburantSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeCarburant
        fields = ['id', 'libelle', 'created_at']


class TypeTransmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeTransmission
        fields = ['id', 'libelle', 'created_at']


class TypeVehiculeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeVehicule
        fields = ['id', 'libelle', 'created_at']


class VehiculeListSerializer(serializers.ModelSerializer):
    marque_nom = serializers.CharField(source='marque.nom', read_only=True)
    modele_nom = serializers.CharField(source='modele.nom', read_only=True)
    libelle_court = serializers.ReadOnlyField()

    class Meta:
        model = Vehicule
        fields = [
            'id', 'numero_chassis', 'libelle_court', 'marque', 'marque_nom', 'modele', 'modele_nom',
            'annee', 'statut', 'numero_immatriculation', 'date_entree_parc',
            'kilometrage_actuel', 'prix_achat', 'created_at',
        ]


class VehiculeDetailSerializer(serializers.ModelSerializer):
    marque_nom = serializers.CharField(source='marque.nom', read_only=True)
    modele_nom = serializers.CharField(source='modele.nom', read_only=True)
    type_vehicule_libelle = serializers.CharField(source='type_vehicule.libelle', read_only=True)
    type_carburant_libelle = serializers.CharField(source='type_carburant.libelle', read_only=True)
    type_transmission_libelle = serializers.CharField(source='type_transmission.libelle', read_only=True)
    libelle_court = serializers.ReadOnlyField()

    class Meta:
        model = Vehicule
        fields = [
            'id', 'numero_chassis', 'libelle_court',
            'marque', 'marque_nom', 'modele', 'modele_nom', 'annee',
            'type_vehicule', 'type_vehicule_libelle',
            'type_carburant', 'type_carburant_libelle',
            'type_transmission', 'type_transmission_libelle',
            'couleur_exterieure', 'couleur_interieure',
            'date_entree_parc', 'km_entree', 'kilometrage_actuel', 'prix_achat',
            'origine_pays', 'etat_entree', 'statut',
            'numero_immatriculation', 'date_premiere_immat',
            'consommation_moyenne', 'rejet_co2', 'puissance_fiscale', 'km_prochaine_vidange',
            'created_at', 'updated_at',
        ]


class VenteListSerializer(serializers.ModelSerializer):
    vehicule_libelle = serializers.CharField(source='vehicule.libelle_court', read_only=True)

    class Meta:
        model = Vente
        fields = [
            'id', 'vehicule', 'vehicule_libelle', 'date_vente', 'acquereur',
            'prix_vente', 'km_vente', 'garantie_duree', 'etat_livraison', 'created_at',
        ]


class VenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vente
        fields = [
            'id', 'vehicule', 'date_vente', 'acquereur', 'prix_vente',
            'km_vente', 'garantie_duree', 'etat_livraison', 'created_at',
        ]


class LocationListSerializer(serializers.ModelSerializer):
    vehicule_libelle = serializers.CharField(source='vehicule.libelle_court', read_only=True)

    class Meta:
        model = Location
        fields = [
            'id', 'vehicule', 'vehicule_libelle', 'locataire', 'type_location',
            'date_debut', 'date_fin', 'statut', 'loyer_mensuel',
            'date_expiration_ct', 'date_expiration_assurance', 'created_at',
        ]


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            'id', 'vehicule', 'locataire', 'type_location', 'date_debut', 'date_fin',
            'loyer_mensuel', 'km_inclus_mois', 'prix_km_supplementaire',
            'date_expiration_ct', 'date_expiration_assurance', 'km_prochaine_vidange',
            'remarques', 'statut', 'created_at', 'updated_at',
        ]


class ConducteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conducteur
        fields = [
            'id', 'nom', 'prenom', 'email', 'telephone',
            'permis_numero', 'permis_date_expiration', 'actif', 'remarque',
            'created_at', 'updated_at',
        ]
