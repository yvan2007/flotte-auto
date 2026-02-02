"""Admin Django pour FLOTTE — interface d'administration des modèles."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import (
    Marque, Modele, TypeCarburant, TypeTransmission, TypeVehicule,
    Vehicule, ImportDemarche, Depense, DocumentVehicule, Reparation,
    Location, Vente, ProfilUtilisateur, Facture,
    RapportJournalier, Maintenance, ReleveCarburant, Conducteur,
)

User = get_user_model()


@admin.register(Marque)
class MarqueAdmin(admin.ModelAdmin):
    list_display = ('nom', 'archive', 'created_at')
    list_filter = ('archive',)
    search_fields = ('nom',)


@admin.register(Modele)
class ModeleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'marque', 'version', 'annee_min', 'annee_max', 'archive')
    list_filter = ('marque', 'archive')
    search_fields = ('nom', 'marque__nom')


@admin.register(TypeCarburant)
class TypeCarburantAdmin(admin.ModelAdmin):
    list_display = ('libelle',)


@admin.register(TypeTransmission)
class TypeTransmissionAdmin(admin.ModelAdmin):
    list_display = ('libelle',)


@admin.register(TypeVehicule)
class TypeVehiculeAdmin(admin.ModelAdmin):
    list_display = ('libelle',)


class ImportDemarcheInline(admin.TabularInline):
    model = ImportDemarche
    extra = 0


class DepenseInline(admin.TabularInline):
    model = Depense
    extra = 0


class DocumentVehiculeInline(admin.TabularInline):
    model = DocumentVehicule
    extra = 0


class ReparationInline(admin.TabularInline):
    model = Reparation
    extra = 0


class FactureInline(admin.TabularInline):
    model = Facture
    extra = 0


@admin.register(Vehicule)
class VehiculeAdmin(admin.ModelAdmin):
    list_display = (
        'numero_chassis', 'marque', 'modele', 'annee', 'statut',
        'kilometrage_actuel', 'date_entree_parc', 'prix_achat'
    )
    list_filter = ('statut', 'marque', 'type_carburant')
    search_fields = ('numero_chassis', 'numero_immatriculation', 'marque__nom', 'modele__nom')
    inlines = [ImportDemarcheInline, DepenseInline, DocumentVehiculeInline, ReparationInline, FactureInline]
    date_hierarchy = 'date_entree_parc'


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        'vehicule', 'locataire', 'type_location', 'date_debut', 'date_fin',
        'loyer_mensuel', 'date_expiration_ct', 'date_expiration_assurance', 'statut'
    )
    list_filter = ('statut', 'type_location')


@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ('numero', 'vehicule', 'fournisseur', 'date_facture', 'montant', 'type_facture')
    list_filter = ('type_facture',)
    search_fields = ('numero', 'fournisseur', 'vehicule__numero_chassis')


@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    list_display = ('vehicule', 'date_vente', 'acquereur', 'prix_vente', 'km_vente')


class ProfilUtilisateurInline(admin.StackedInline):
    model = ProfilUtilisateur
    can_delete = False


class UserAdmin(BaseUserAdmin):
    inlines = (ProfilUtilisateurInline,)


@admin.register(RapportJournalier)
class RapportJournalierAdmin(admin.ModelAdmin):
    list_display = ('date_rapport', 'titre', 'type_rapport', 'created_at')
    list_filter = ('type_rapport',)
    search_fields = ('titre',)
    date_hierarchy = 'date_rapport'


@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ('vehicule', 'type_maintenance', 'date_prevue', 'statut', 'cout', 'prestataire')
    list_filter = ('type_maintenance', 'statut')
    search_fields = ('vehicule__numero_chassis',)
    date_hierarchy = 'date_prevue'


@admin.register(ReleveCarburant)
class ReleveCarburantAdmin(admin.ModelAdmin):
    list_display = ('vehicule', 'date_releve', 'kilometrage', 'litres', 'montant_fcfa', 'lieu')
    list_filter = ('vehicule',)
    search_fields = ('vehicule__numero_chassis',)
    date_hierarchy = 'date_releve'


@admin.register(Conducteur)
class ConducteurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'email', 'telephone', 'permis_numero', 'permis_date_expiration', 'actif')
    list_filter = ('actif',)
    search_fields = ('nom', 'prenom', 'email')


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(ProfilUtilisateur)
