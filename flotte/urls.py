"""URLs FLOTTE — routes de l'application de gestion de flotte."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views
from .views_rest import (
    MarqueViewSet, ModeleViewSet, VehiculeViewSet,
    VenteViewSet, LocationViewSet, ConducteurViewSet,
    CAViewSet, DashboardViewSet,
)

app_name = 'flotte'

# Router Django REST Framework (api/v1/)
router = DefaultRouter()
router.register(r'marques', MarqueViewSet, basename='api-marque')
router.register(r'modeles', ModeleViewSet, basename='api-modele')
router.register(r'vehicules', VehiculeViewSet, basename='api-vehicule')
router.register(r'ventes', VenteViewSet, basename='api-vente')
router.register(r'locations', LocationViewSet, basename='api-location')
router.register(r'conducteurs', ConducteurViewSet, basename='api-conducteur')
router.register(r'ca', CAViewSet, basename='api-ca')
router.register(r'dashboard', DashboardViewSet, basename='api-dashboard')

urlpatterns = [
    path('', views.FlotteLoginView.as_view(), name='login'),
    path('logout/', views.FlotteLogoutView.as_view(), name='logout'),
    path('mot-de-passe-oublie/', views.FlottePasswordResetView.as_view(), name='password_reset'),
    path('mot-de-passe-oublie/envoye/', views.FlottePasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reinitialiser/<uidb64>/<token>/', views.FlottePasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reinitialiser/termine/', views.FlottePasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('recherche/', views.recherche, name='recherche'),
    path('recherche/api/', views.recherche_api, name='recherche_api'),
    path('echeances/', views.echeances, name='echeances'),
    # Parc / Véhicules
    path('parc/', views.ParcListView.as_view(), name='parc'),
    path('parc/ajout/', views.VehiculeCreateView.as_view(), name='vehicule_create'),
    path('parc/<int:pk>/', views.vehicule_detail, name='vehicule_detail'),
    path('parc/<int:pk>/modifier/', views.VehiculeUpdateView.as_view(), name='vehicule_update'),
    path('parc/<int:vehicule_pk>/documents/ajout/', views.DocumentVehiculeCreateView.as_view(), name='document_create'),
    path('parc/<int:vehicule_pk>/photos/ajout/', views.PhotoVehiculeCreateView.as_view(), name='photo_vehicule_create'),
    path('photos/<int:pk>/modifier/', views.PhotoVehiculeUpdateView.as_view(), name='photo_vehicule_update'),
    path('photos/<int:pk>/supprimer/', views.PhotoVehiculeDeleteView.as_view(), name='photo_vehicule_delete'),
    path('parc/<int:vehicule_pk>/reparations/ajout/', views.ReparationCreateView.as_view(), name='reparation_create'),
    path('parc/<int:vehicule_pk>/depenses/ajout/', views.DepenseCreateView.as_view(), name='depense_create'),
    path('parc/<int:vehicule_pk>/factures/ajout/', views.FactureCreateView.as_view(), name='facture_create'),
    path('parc/<int:vehicule_pk>/import-demarches/ajout/', views.ImportDemarcheCreateView.as_view(), name='import_demarche_create'),
    path('parc/<int:vehicule_pk>/charges-import/ajout/', views.ChargeImportCreateView.as_view(), name='charge_import_create'),
    path('charges-import/<int:pk>/modifier/', views.ChargeImportUpdateView.as_view(), name='charge_import_update'),
    path('parc/<int:vehicule_pk>/parties-importees/ajout/', views.PartieImporteeCreateView.as_view(), name='partie_importee_create'),
    path('parties-importees/', views.PartieImporteeListView.as_view(), name='parties_importees_list'),
    path('parties-importees/ajout/', views.PartieImporteeCreateView.as_view(), name='partie_importee_create_standalone'),
    path('parties-importees/<int:pk>/modifier/', views.PartieImporteeUpdateView.as_view(), name='partie_importee_update'),
    path('parc/<int:vehicule_pk>/ventes/ajout/', views.VenteCreateView.as_view(), name='vente_create'),
    path('import-demarches/<int:pk>/modifier/', views.ImportDemarcheUpdateView.as_view(), name='import_demarche_update'),
    path('ventes/<int:pk>/modifier/', views.VenteUpdateView.as_view(), name='vente_update'),
    path('documents/<int:pk>/modifier/', views.DocumentVehiculeUpdateView.as_view(), name='document_update'),
    path('reparations/<int:pk>/modifier/', views.ReparationUpdateView.as_view(), name='reparation_update'),
    path('depenses/<int:pk>/modifier/', views.DepenseUpdateView.as_view(), name='depense_update'),
    path('factures/<int:pk>/modifier/', views.FactureUpdateView.as_view(), name='facture_update'),
    path('factures/<int:facture_pk>/penalites/ajout/', views.PenaliteFactureCreateView.as_view(), name='penalite_facture_create'),
    path('penalites-facture/<int:pk>/modifier/', views.PenaliteFactureUpdateView.as_view(), name='penalite_facture_update'),
    path('penalites-facture/<int:pk>/supprimer/', views.PenaliteFactureDeleteView.as_view(), name='penalite_facture_delete'),
    # Location
    path('location/', views.LocationListView.as_view(), name='location_list'),
    path('location/ajout/', views.LocationCreateView.as_view(), name='location_create'),
    path('location/<int:pk>/', views.location_detail, name='location_detail'),
    path('location/<int:pk>/modifier/', views.LocationUpdateView.as_view(), name='location_update'),
    path('contraventions/', views.contraventions_list, name='contraventions_list'),
    path('location/<int:location_pk>/contraventions/ajout/', views.ContraventionCreateView.as_view(), name='contravention_create'),
    path('contraventions/<int:pk>/modifier/', views.ContraventionUpdateView.as_view(), name='contravention_update'),
    # Autres sections
    path('import/', views.import_list, name='import_list'),
    path('reparations/', views.reparations_list, name='reparations_list'),
    path('documents/', views.documents_list, name='documents_list'),
    path('ventes/', views.ventes_list, name='ventes_list'),
    path('ca/', views.ca_view, name='ca'),
    path('tco/', views.tco_view, name='tco'),
    path('export-reglementaire/', views.export_reglementaire, name='export_reglementaire'),
    path('export-charges-import/', views.export_charges_import, name='export_charges_import'),
    path('export-locations/', views.export_locations, name='export_locations'),
    path('ca/api/evolution/', views.ca_api_evolution, name='ca_api_evolution'),
    path('ca/api/check-code/', views.ca_check_code, name='ca_check_code'),
    path('ca/rapport/<int:pk>/', views.rapport_download, name='rapport_download'),
    path('ca/rapport/<int:pk>/modifier/', views.RapportJournalierUpdateView.as_view(), name='rapport_update'),
    path('maintenance/', views.maintenance_list, name='maintenance_list'),
    path('maintenance/ajout/', views.MaintenanceCreateView.as_view(), name='maintenance_create'),
    path('maintenance/<int:pk>/modifier/', views.MaintenanceUpdateView.as_view(), name='maintenance_update'),
    path('carburant/', views.carburant_list, name='carburant_list'),
    path('carburant/ajout/', views.ReleveCarburantCreateView.as_view(), name='carburant_create'),
    path('carburant/<int:pk>/modifier/', views.ReleveCarburantUpdateView.as_view(), name='carburant_update'),
    path('conducteurs/', views.conducteurs_list, name='conducteurs_list'),
    path('conducteurs/ajout/', views.ConducteurCreateView.as_view(), name='conducteur_create'),
    path('conducteurs/<int:pk>/modifier/', views.ConducteurUpdateView.as_view(), name='conducteur_update'),
    # Paramétrage (admin)
    path('parametrage/', views.parametrage_index, name='parametrage_index'),
    path('parametrage/marques/', views.ParametrageMarqueListView.as_view(), name='parametrage_marques'),
    path('parametrage/marques/ajout/', views.MarqueCreateView.as_view(), name='marque_create'),
    path('parametrage/marques/<int:pk>/modifier/', views.MarqueUpdateView.as_view(), name='marque_update'),
    path('parametrage/modeles/', views.ParametrageModeleListView.as_view(), name='parametrage_modeles'),
    path('parametrage/modeles/ajout/', views.ModeleCreateView.as_view(), name='modele_create'),
    path('parametrage/modeles/<int:pk>/modifier/', views.ModeleUpdateView.as_view(), name='modele_update'),
    path('parametrage/carburant/', views.ParametrageCarburantListView.as_view(), name='parametrage_carburant'),
    path('parametrage/carburant/ajout/', views.TypeCarburantCreateView.as_view(), name='type_carburant_create'),
    path('parametrage/carburant/<int:pk>/modifier/', views.TypeCarburantUpdateView.as_view(), name='type_carburant_update'),
    path('parametrage/transmission/', views.ParametrageTransmissionListView.as_view(), name='parametrage_transmission'),
    path('parametrage/transmission/ajout/', views.TypeTransmissionCreateView.as_view(), name='type_transmission_create'),
    path('parametrage/transmission/<int:pk>/modifier/', views.TypeTransmissionUpdateView.as_view(), name='type_transmission_update'),
    path('parametrage/type-vehicule/', views.ParametrageTypeVehiculeListView.as_view(), name='parametrage_type_vehicule'),
    path('parametrage/type-vehicule/ajout/', views.TypeVehiculeCreateView.as_view(), name='type_vehicule_create'),
    path('parametrage/type-vehicule/<int:pk>/modifier/', views.TypeVehiculeUpdateView.as_view(), name='type_vehicule_update'),
    path('parametrage/type-document/', views.ParametrageTypeDocumentListView.as_view(), name='parametrage_type_document'),
    path('parametrage/type-document/ajout/', views.TypeDocumentCreateView.as_view(), name='type_document_create'),
    path('parametrage/type-document/<int:pk>/modifier/', views.TypeDocumentUpdateView.as_view(), name='type_document_update'),
    path('parametrage/utilisateurs/', views.parametrage_utilisateurs, name='parametrage_utilisateurs'),
    path('parametrage/utilisateurs/ajout/', views.UserCreateView.as_view(), name='utilisateur_create'),
    path('parametrage/utilisateurs/<int:pk>/modifier/', views.UserUpdateView.as_view(), name='utilisateur_update'),
    path('parametrage/ca-code/', views.parametrage_ca_code, name='parametrage_ca_code'),
    path('parametrage/audit/', views.audit_list, name='audit_list'),
    # API — index et endpoints JSON
    path('api/', api_views.api_index, name='api_index'),
    path('api/modeles-par-marque/', views.api_modeles_par_marque, name='api_modeles_par_marque'),
    path('api/marques/', api_views.api_marques_list, name='api_marques_list'),
    path('api/vehicules/', api_views.api_vehicules_list, name='api_vehicules_list'),
    path('api/vehicules/<int:pk>/', api_views.api_vehicule_detail, name='api_vehicule_detail'),
    path('api/ventes/', api_views.api_ventes_list, name='api_ventes_list'),
    path('api/ca/synthese/', api_views.api_ca_synthese, name='api_ca_synthese'),
    path('api/dashboard/kpis/', api_views.api_dashboard_kpis, name='api_dashboard_kpis'),
    path('api/conducteurs/', api_views.api_conducteurs_list, name='api_conducteurs_list'),
    path('api/locations/', api_views.api_locations_list, name='api_locations_list'),
    # API REST Framework (api/v1/) — browsable API, pagination, filtres
    path('api/v1/', include(router.urls)),
]
