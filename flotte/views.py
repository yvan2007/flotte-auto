"""
Vues FLOTTE — Dashboard, parc (châssis), location (CT, assurance, vidange),
import, paramétrage (marques, modèles, types, utilisateurs).
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.views import (
    LoginView, LogoutView,
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView,
)
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, FormView,
)
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_GET
from django.db.models import Avg, Case, Count, IntegerField, Prefetch, Q, Sum, Value, When
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from django.utils import timezone
from decimal import Decimal
from django.utils.decorators import method_decorator
from django.db import DatabaseError, IntegrityError

from .models import (
    Marque, Modele, TypeCarburant, TypeTransmission, TypeVehicule,
    Vehicule, Location, ImportDemarche, Depense, DocumentVehicule,
    Reparation, Vente, ProfilUtilisateur, Facture,
    RapportJournalier, Maintenance, ReleveCarburant, Conducteur,
    ChargeImport, PartieImportee, Contravention, TypeDocument,
    AuditLog, PhotoVehicule, PenaliteFacture,
)
from .forms import (
    LoginForm, UserCreateForm, UserUpdateForm, MarqueForm, ModeleForm,
    TypeCarburantForm, TypeTransmissionForm, TypeVehiculeForm,
    VehiculeForm, LocationForm, DepenseForm, DocumentVehiculeForm,
    ReparationForm, FactureForm, ImportDemarcheForm, VenteForm,
    RapportJournalierForm, MaintenanceForm, ReleveCarburantForm, ConducteurForm,
    ChargeImportForm, PartieImporteeForm, ContraventionForm, TypeDocumentForm,
    PhotoVehiculeForm, PenaliteFactureForm, CAAmountCodeForm,
)
from .mixins import (
    AdminRequiredMixin, ManagerRequiredMixin,
    user_role, is_admin, is_manager_or_admin,
    manager_or_admin_required,
)
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


def get_sidebar_context(request):
    """Contexte commun : rôle, is_admin, is_manager_or_admin pour la sidebar et les boutons.
    Utilisé par toutes les vues pour l'affichage du menu latéral."""
    return {
        'user_role': user_role(request) if request.user.is_authenticated else None,
        'is_admin': is_admin(request),
        'is_manager_or_admin': is_manager_or_admin(request),
    }


# ——— Auth ———
class FlotteLoginView(LoginView):
    """Connexion FLOTTE avec thème beige."""
    template_name = 'flotte/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        from django.utils.http import url_has_allowed_host_and_scheme
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        if next_url:
            # Chemin relatif (ex. /api/) : autoriser si pas d'URL externe
            if next_url.startswith('/') and '//' not in next_url:
                return next_url
            # URL absolue : vérifier hôte autorisé
            if url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={self.request.get_host()}, require_https=self.request.is_secure()
            ):
                return next_url
        return reverse_lazy('flotte:dashboard')


class FlotteLogoutView(LogoutView):
    """Déconnexion. Accepte GET et POST pour éviter HTTP 405 (lien direct ou actualisation)."""
    next_page = 'flotte:login'
    http_method_names = ['get', 'post', 'head', 'options']

    def get(self, request, *args, **kwargs):
        """Déconnecte aussi sur GET (évite 405 si l'utilisateur ouvre /logout/ en lien direct)."""
        from django.contrib.auth import logout as auth_logout
        auth_logout(request)
        return redirect(self.get_success_url())


# ——— Mot de passe oublié ———
class FlottePasswordResetView(PasswordResetView):
    """Demande de réinitialisation du mot de passe (email)."""
    template_name = 'flotte/password_reset_form.html'
    email_template_name = 'flotte/emails/password_reset_email.html'
    html_email_template_name = 'flotte/emails/password_reset_email_html.html'
    subject_template_name = 'flotte/emails/password_reset_subject.txt'
    success_url = reverse_lazy('flotte:password_reset_done')
    from_email = None  # utilise DEFAULT_FROM_EMAIL


class FlottePasswordResetDoneView(PasswordResetDoneView):
    """Confirmation : email envoyé."""
    template_name = 'flotte/password_reset_done.html'


class FlottePasswordResetConfirmView(PasswordResetConfirmView):
    """Formulaire nouveau mot de passe (lien reçu par email)."""
    template_name = 'flotte/password_reset_confirm.html'
    success_url = reverse_lazy('flotte:password_reset_complete')
    title = 'Nouveau mot de passe'


class FlottePasswordResetCompleteView(PasswordResetCompleteView):
    """Mot de passe réinitialisé, lien vers connexion."""
    template_name = 'flotte/password_reset_complete.html'


# ——— API légère (formulaire dynamique) ———
@login_required
def api_modeles_par_marque(request):
    """Retourne les modèles pour une marque (JSON) — pour mise à jour dynamique du formulaire véhicule."""
    marque_id = request.GET.get('marque_id')
    if not marque_id:
        return JsonResponse({'modeles': []})
    try:
        marque_id = int(marque_id)
    except (ValueError, TypeError):
        return JsonResponse({'modeles': []})
    modeles = list(
        Modele.objects.filter(marque_id=marque_id).order_by('nom').values('id', 'nom')
    )
    return JsonResponse({'modeles': modeles})


# ——— Dashboard ———
@login_required
def dashboard(request):
    """Tableau de bord avec KPIs, alertes (CT, assurance), véhicules en import."""
    from django.utils import timezone
    from datetime import timedelta
    qs = Vehicule.objects.all()
    if not is_manager_or_admin(request):
        qs = qs.filter(proprietaire=request.user)
    parc = qs.filter(statut='parc').count()
    import_ = qs.filter(statut='import').count()
    vendus = qs.filter(statut='vendu').count()
    total = qs.count()
    by_marque = list(
        qs.values('marque__nom').annotate(n=Count('id')).order_by('-n')
    )
    # Occupation de la flotte (véhicules en location vs total)
    vehicules_en_location_qs = Vehicule.objects.filter(
        locations__statut='en_cours'
    )
    if not is_manager_or_admin(request):
        vehicules_en_location_qs = vehicules_en_location_qs.filter(proprietaire=request.user)
    vehicules_en_location_qs = vehicules_en_location_qs.distinct()
    nb_vehicules_en_location = vehicules_en_location_qs.count()
    # Disponibles : véhicules au parc sans location en cours
    vehicules_disponibles_qs = qs.filter(statut='parc').exclude(
        locations__statut='en_cours'
    ).distinct()
    nb_vehicules_disponibles = vehicules_disponibles_qs.count()
    taux_occupation = 0
    if total:
        taux_occupation = round((nb_vehicules_en_location / total) * 100)
    # Alertes : locations dont CT ou assurance expire dans les 30 jours
    now = timezone.now().date()
    fin_alerte = now + timedelta(days=30)
    base_loc_alertes = Location.objects.filter(
        date_expiration_ct__isnull=False,
        date_expiration_ct__gte=now,
        date_expiration_ct__lte=fin_alerte,
        statut='en_cours',
    ).select_related('vehicule')
    if not is_manager_or_admin(request):
        base_loc_alertes = base_loc_alertes.filter(vehicule__proprietaire=request.user)
    alertes_ct = list(base_loc_alertes.order_by('date_expiration_ct')[:10])

    base_loc_assurance = Location.objects.filter(
            date_expiration_assurance__isnull=False,
            date_expiration_assurance__gte=now,
            date_expiration_assurance__lte=fin_alerte,
            statut='en_cours',
        ).select_related('vehicule')
    if not is_manager_or_admin(request):
        base_loc_assurance = base_loc_assurance.filter(vehicule__proprietaire=request.user)
    alertes_assurance = list(base_loc_assurance.order_by('date_expiration_assurance')[:10])

    # Alertes permis (conducteurs dont le permis expire dans les 30 jours)
    conducteurs_qs = Conducteur.objects.filter(
            actif=True,
            permis_date_expiration__isnull=False,
            permis_date_expiration__gte=now,
            permis_date_expiration__lte=fin_alerte,
        )
    if not is_manager_or_admin(request):
        conducteurs_qs = conducteurs_qs.filter(user=request.user)
    alertes_permis = list(conducteurs_qs.order_by('permis_date_expiration')[:10])
    # Alertes documents véhicule (échéance dans les 30 jours)
    docs_qs = DocumentVehicule.objects.filter(
            date_echeance__isnull=False,
            date_echeance__gte=now,
            date_echeance__lte=fin_alerte,
        ).select_related('vehicule')
    if not is_manager_or_admin(request):
        docs_qs = docs_qs.filter(vehicule__proprietaire=request.user)
    alertes_documents = list(docs_qs.order_by('date_echeance')[:10])

    # CT et assurance au niveau véhicule (au parc sans location en cours, 30 jours)
    vehicules_parc_sans_location = qs.filter(statut='parc').exclude(
        locations__statut='en_cours'
    ).distinct()
    alertes_ct_vehicule = list(
        vehicules_parc_sans_location.filter(
            date_expiration_ct__isnull=False,
            date_expiration_ct__gte=now,
            date_expiration_ct__lte=fin_alerte,
        ).select_related('marque', 'modele').order_by('date_expiration_ct')[:10]
    )
    alertes_assurance_vehicule = list(
        vehicules_parc_sans_location.filter(
            date_expiration_assurance__isnull=False,
            date_expiration_assurance__gte=now,
            date_expiration_assurance__lte=fin_alerte,
        ).select_related('marque', 'modele').order_by('date_expiration_assurance')[:10]
    )
    vehicules_import_qs = Vehicule.objects.filter(statut='import').select_related('marque', 'modele')
    if not is_manager_or_admin(request):
        vehicules_import_qs = vehicules_import_qs.filter(proprietaire=request.user)
    vehicules_import = list(vehicules_import_qs.order_by('-date_entree_parc')[:5])
    context = {
        'parc': parc,
        'import': import_,
        'vendus': vendus,
        'total': total,
        'by_marque': by_marque,
        'vehicules_en_location': nb_vehicules_en_location,
        'vehicules_disponibles': nb_vehicules_disponibles,
        'taux_occupation': taux_occupation,
        'alertes_ct': alertes_ct,
        'alertes_assurance': alertes_assurance,
        'alertes_permis': alertes_permis,
        'alertes_documents': alertes_documents,
        'alertes_ct_vehicule': alertes_ct_vehicule,
        'alertes_assurance_vehicule': alertes_assurance_vehicule,
        'vehicules_import': vehicules_import,
        **get_sidebar_context(request),
    }
    return render(request, 'flotte/dashboard.html', context)


# ——— Échéances (conformité flotte) ———
@login_required
def echeances(request):
    """Page consolidée des échéances : CT, assurance, documents, permis conducteurs, maintenance à faire."""
    from datetime import timedelta
    now = timezone.now().date()
    horizon = now + timedelta(days=90)
    # CT (locations en cours)
    loc_ct_qs = Location.objects.filter(
            date_expiration_ct__isnull=False,
            date_expiration_ct__gte=now,
            date_expiration_ct__lte=horizon,
            statut='en_cours',
        ).select_related('vehicule')
    if not is_manager_or_admin(request):
        loc_ct_qs = loc_ct_qs.filter(vehicule__proprietaire=request.user)
    echeances_ct = list(loc_ct_qs.order_by('date_expiration_ct'))

    # Assurance (locations en cours)
    loc_ass_qs = Location.objects.filter(
            date_expiration_assurance__isnull=False,
            date_expiration_assurance__gte=now,
            date_expiration_assurance__lte=horizon,
            statut='en_cours',
        ).select_related('vehicule')
    if not is_manager_or_admin(request):
        loc_ass_qs = loc_ass_qs.filter(vehicule__proprietaire=request.user)
    echeances_assurance = list(loc_ass_qs.order_by('date_expiration_assurance'))
    # CT et assurance au niveau véhicule (au parc sans location en cours)
    base_vehicules = Vehicule.objects.filter(statut='parc')
    if not is_manager_or_admin(request):
        base_vehicules = base_vehicules.filter(proprietaire=request.user)
    vehicules_parc_sans_location = base_vehicules.exclude(
        locations__statut='en_cours'
    ).distinct()
    echeances_ct_vehicule = list(
        vehicules_parc_sans_location.filter(
            date_expiration_ct__isnull=False,
            date_expiration_ct__gte=now,
            date_expiration_ct__lte=horizon,
        ).select_related('marque', 'modele').order_by('date_expiration_ct')
    )
    echeances_assurance_vehicule = list(
        vehicules_parc_sans_location.filter(
            date_expiration_assurance__isnull=False,
            date_expiration_assurance__gte=now,
            date_expiration_assurance__lte=horizon,
        ).select_related('marque', 'modele').order_by('date_expiration_assurance')
    )
    # Documents véhicule (date échéance)
    docs_qs = DocumentVehicule.objects.filter(
            date_echeance__isnull=False,
            date_echeance__gte=now,
            date_echeance__lte=horizon,
        ).select_related('vehicule')
    if not is_manager_or_admin(request):
        docs_qs = docs_qs.filter(vehicule__proprietaire=request.user)
    echeances_documents = list(docs_qs.order_by('date_echeance'))

    # Permis conducteurs
    cond_qs = Conducteur.objects.filter(
            actif=True,
            permis_date_expiration__isnull=False,
            permis_date_expiration__gte=now,
            permis_date_expiration__lte=horizon,
        )
    if not is_manager_or_admin(request):
        cond_qs = cond_qs.filter(user=request.user)
    echeances_permis = list(cond_qs.order_by('permis_date_expiration'))
    # Maintenance à faire (date prévue dans l'horizon ou sans date)
    echeances_maintenance = list(
        Maintenance.objects.filter(statut='a_faire').filter(
            Q(date_prevue__isnull=True) | Q(date_prevue__lte=horizon)
        ).select_related('vehicule').order_by('date_prevue')[:50]
    )
    # Vidange — km atteint ou dépassé (véhicule ou location)
    from django.db.models import F
    vehicules_vidange_qs = Vehicule.objects.filter(
        statut__in=['parc', 'import'],
        km_prochaine_vidange__isnull=False,
    )
    if not is_manager_or_admin(request):
        vehicules_vidange_qs = vehicules_vidange_qs.filter(proprietaire=request.user)
    alertes_vidange_vehicules = list(
        vehicules_vidange_qs.filter(kilometrage_actuel__gte=F('km_prochaine_vidange')).select_related('marque', 'modele')
    )
    locations_km_qs = Location.objects.filter(
        statut='en_cours',
        km_prochaine_vidange__isnull=False,
    ).select_related('vehicule')
    if not is_manager_or_admin(request):
        locations_km_qs = locations_km_qs.filter(vehicule__proprietaire=request.user)
    locations_km = list(locations_km_qs)
    alertes_vidange_locations = [
        loc for loc in locations_km
        if (loc.vehicule.kilometrage_actuel or 0) >= (loc.km_prochaine_vidange or 0)
    ]
    context = {
        'echeances_ct': echeances_ct,
        'echeances_assurance': echeances_assurance,
        'echeances_ct_vehicule': echeances_ct_vehicule,
        'echeances_assurance_vehicule': echeances_assurance_vehicule,
        'echeances_documents': echeances_documents,
        'echeances_permis': echeances_permis,
        'echeances_maintenance': echeances_maintenance,
        'alertes_vidange_vehicules': alertes_vidange_vehicules,
        'alertes_vidange_locations': alertes_vidange_locations,
        'date_debut': now,
        'date_fin': horizon,
        **get_sidebar_context(request),
    }
    return render(request, 'flotte/echeances.html', context)


# ——— TCO (coût total de possession) ———
@login_required
@manager_or_admin_required
def tco_view(request):
    """Rapport TCO par véhicule : acquisition + dépenses + carburant + maintenance − vente."""
    qs = Vehicule.objects.select_related('marque', 'modele').prefetch_related(
        'charges_import', 'depenses', 'maintenances', 'releves_carburant', 'ventes'
    ).order_by('marque__nom', 'modele__nom')
    rows = []
    for v in qs:
        acquisition = v.prix_achat or Decimal(0)
        acquisition += sum((c.cout_total or Decimal(0)) for c in v.charges_import.all())
        depenses = sum((d.montant or Decimal(0)) for d in v.depenses.all())
        maintenance = sum((m.cout or Decimal(0)) for m in v.maintenances.all())
        carburant = sum((r.montant_fcfa or Decimal(0)) for r in v.releves_carburant.all())
        ventes = list(v.ventes.all()[:1])
        vente_prix = ventes[0].prix_vente if ventes else None
        vente_prix = vente_prix or Decimal(0)
        tco = acquisition + depenses + maintenance + carburant - vente_prix
        rows.append({
            'vehicule': v,
            'acquisition': acquisition,
            'depenses': depenses,
            'maintenance': maintenance,
            'carburant': carburant,
            'vente_prix': vente_prix,
            'tco': tco,
        })
    context = {
        'rows': rows,
        **get_sidebar_context(request),
    }
    return render(request, 'flotte/tco.html', context)


# ——— Export réglementaire (CSV) ———
@login_required
@manager_or_admin_required
def export_reglementaire(request):
    """Export CSV : véhicules avec immat, CT, assurance, locataire (pour contrôle)."""
    import csv
    from io import StringIO
    qs = Vehicule.objects.select_related('marque', 'modele').prefetch_related(
        'locations'
    ).filter(statut__in=['parc', 'import']).order_by('numero_chassis')
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter=';')
    writer.writerow([
        'Châssis', 'Immat', 'Marque', 'Modèle', 'Km', 'CT (véhicule)', 'Assurance (véhicule)',
        'Location en cours', 'Locataire', 'CT (location)', 'Assurance (location)',
    ])
    for v in qs:
        loc_en_cours = v.locations.filter(statut='en_cours').first()
        writer.writerow([
            v.numero_chassis,
            v.numero_immatriculation or '',
            v.marque.nom if v.marque else '',
            v.modele.nom if v.modele else '',
            v.kilometrage_actuel or '',
            str(v.date_expiration_ct) if getattr(v, 'date_expiration_ct', None) else '',
            str(v.date_expiration_assurance) if getattr(v, 'date_expiration_assurance', None) else '',
            'Oui' if loc_en_cours else 'Non',
            loc_en_cours.locataire if loc_en_cours else '',
            str(loc_en_cours.date_expiration_ct) if loc_en_cours and loc_en_cours.date_expiration_ct else '',
            str(loc_en_cours.date_expiration_assurance) if loc_en_cours and loc_en_cours.date_expiration_assurance else '',
        ])
    content = '\ufeff' + buffer.getvalue()  # BOM UTF-8 pour Excel
    response = HttpResponse(content, content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="flotte_export_reglementaire.csv"'
    return response


@login_required
@manager_or_admin_required
def export_charges_import(request):
    """Export CSV : charges d'importation (fret, dédouanement, transitaire, coût total) par véhicule."""
    import csv
    from io import StringIO
    qs = ChargeImport.objects.select_related('vehicule').order_by('vehicule__numero_chassis', '-id')
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter=';')
    writer.writerow([
        'Châssis', 'Fret (FCFA)', 'Dédouanement (FCFA)', 'Transitaire (FCFA)',
        'Coût total (FCFA)', 'Remarque',
    ])
    for c in qs:
        writer.writerow([
            c.vehicule.numero_chassis if c.vehicule else '',
            c.fret or '',
            c.frais_dedouanement or '',
            c.frais_transitaire or '',
            c.cout_total or '',
            (c.remarque or '')[:200],
        ])
    content = '\ufeff' + buffer.getvalue()
    response = HttpResponse(content, content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="flotte_charges_import.csv"'
    return response


@login_required
@manager_or_admin_required
def export_locations(request):
    """Export CSV : locations avec coût total (loyer + frais annexes + contraventions)."""
    import csv
    from io import StringIO
    qs = Location.objects.select_related('vehicule__marque', 'vehicule__modele').prefetch_related(
        'contraventions'
    ).order_by('-date_debut')
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter=';')
    writer.writerow([
        'Véhicule', 'Châssis', 'Locataire', 'Type', 'Date début', 'Date fin',
        'Loyer (FCFA)', 'Frais annexes (FCFA)', 'Coût total (FCFA)', 'Statut',
    ])
    for loc in qs:
        total = loc.cout_total_location
        writer.writerow([
            loc.vehicule.libelle_court if loc.vehicule else '',
            loc.vehicule.numero_chassis if loc.vehicule else '',
            loc.locataire or '',
            loc.type_location or '',
            str(loc.date_debut) if loc.date_debut else '',
            str(loc.date_fin) if loc.date_fin else '',
            loc.loyer_mensuel or '',
            loc.frais_annexes or '',
            total if total is not None else '',
            loc.get_statut_display() if loc.statut else loc.statut or '',
        ])
    content = '\ufeff' + buffer.getvalue()
    response = HttpResponse(content, content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="flotte_locations.csv"'
    return response


# ——— Recherche globale ———
@login_required
def recherche(request):
    """Recherche globale : véhicules, locations, ventes, conducteurs, factures (selon ce qu'on tape)."""
    q = (request.GET.get('q') or '').strip()
    vehicules = []
    locations = []
    ventes = []
    conducteurs = []
    factures = []
    if q:
        # Véhicules : châssis, immat, marque, modèle, pays
        vehicules_qs = Vehicule.objects.filter(
            Q(numero_chassis__icontains=q) |
            Q(numero_immatriculation__icontains=q) |
            Q(marque__nom__icontains=q) |
            Q(modele__nom__icontains=q) |
            Q(origine_pays__icontains=q)
        ).select_related('marque', 'modele')
        if not is_manager_or_admin(request):
            vehicules_qs = vehicules_qs.filter(proprietaire=request.user)
        vehicules = vehicules_qs.order_by('-date_entree_parc')[:25]
        # Locations : locataire, type, véhicule
        if is_manager_or_admin(request):
            locations = Location.objects.filter(
                Q(locataire__icontains=q) |
                Q(type_location__icontains=q) |
                Q(vehicule__numero_chassis__icontains=q) |
                Q(vehicule__marque__nom__icontains=q) |
                Q(vehicule__modele__nom__icontains=q)
            ).select_related('vehicule__marque', 'vehicule__modele').order_by('-date_debut')[:25]
        # Ventes : acquéreur, véhicule (manager voit tout ; user voit ses ventes)
        ventes_qs = Vente.objects.select_related('vehicule__marque', 'vehicule__modele').order_by('-date_vente')
        if not is_manager_or_admin(request):
            ventes_qs = ventes_qs.filter(acquereur_compte=request.user)
        ventes = ventes_qs.filter(
            Q(acquereur__icontains=q) |
            Q(vehicule__numero_chassis__icontains=q) |
            Q(vehicule__marque__nom__icontains=q) |
            Q(vehicule__modele__nom__icontains=q)
        )[:25]
        # Conducteurs : nom, prénom, email, téléphone
        conducteurs = Conducteur.objects.filter(
            Q(nom__icontains=q) |
            Q(prenom__icontains=q) |
            Q(email__icontains=q) |
            Q(telephone__icontains=q)
        ).order_by('nom', 'prenom')[:25]
        # Factures : numéro, fournisseur, véhicule (manager/admin)
        if is_manager_or_admin(request):
            factures = Facture.objects.filter(
                Q(numero__icontains=q) |
                Q(fournisseur__icontains=q) |
                Q(vehicule__numero_chassis__icontains=q) |
                Q(vehicule__marque__nom__icontains=q) |
                Q(vehicule__modele__nom__icontains=q)
            ).select_related('vehicule__marque', 'vehicule__modele').order_by('-date_facture')[:25]

    context = {
        'q': q,
        'vehicules': vehicules,
        'locations': locations,
        'ventes': ventes,
        'conducteurs': conducteurs,
        'factures': factures,
        **get_sidebar_context(request),
    }
    return render(request, 'flotte/recherche.html', context)


@login_required
@require_GET
def recherche_api(request):
    """API JSON pour la recherche en direct : renvoie véhicules, locations, ventes, conducteurs, factures (labels + URLs)."""
    q = (request.GET.get('q') or '').strip()
    out = {'vehicules': [], 'locations': [], 'ventes': [], 'conducteurs': [], 'factures': []}
    if not q:
        return JsonResponse(out)

    # Véhicules
    vehicules_qs = Vehicule.objects.filter(
        Q(numero_chassis__icontains=q) |
        Q(numero_immatriculation__icontains=q) |
        Q(marque__nom__icontains=q) |
        Q(modele__nom__icontains=q) |
        Q(origine_pays__icontains=q)
    ).select_related('marque', 'modele')
    if not is_manager_or_admin(request):
        vehicules_qs = vehicules_qs.filter(proprietaire=request.user)
    for v in vehicules_qs.order_by('-date_entree_parc')[:15]:
        out['vehicules'].append({
            'id': v.pk,
            'label': '{} — {}'.format(v.libelle_court, v.numero_chassis) + (' · ' + v.numero_immatriculation if v.numero_immatriculation else ''),
            'url': reverse('flotte:vehicule_detail', args=[v.pk]),
        })

    if is_manager_or_admin(request):
        for loc in Location.objects.filter(
            Q(locataire__icontains=q) |
            Q(type_location__icontains=q) |
            Q(vehicule__numero_chassis__icontains=q) |
            Q(vehicule__marque__nom__icontains=q) |
            Q(vehicule__modele__nom__icontains=q)
        ).select_related('vehicule__marque', 'vehicule__modele').order_by('-date_debut')[:15]:
            out['locations'].append({
                'id': loc.pk,
                'label': '{} — {} · {}'.format(loc.locataire, loc.vehicule.libelle_court if loc.vehicule else loc.vehicule_id, loc.type_location),
                'url': reverse('flotte:location_detail', args=[loc.pk]),
            })

    ventes_qs = Vente.objects.select_related('vehicule__marque', 'vehicule__modele').order_by('-date_vente')
    if not is_manager_or_admin(request):
        ventes_qs = ventes_qs.filter(acquereur_compte=request.user)
    for v in ventes_qs.filter(
        Q(acquereur__icontains=q) |
        Q(vehicule__numero_chassis__icontains=q) |
        Q(vehicule__marque__nom__icontains=q) |
        Q(vehicule__modele__nom__icontains=q)
    )[:15]:
        out['ventes'].append({
            'id': v.pk,
            'label': '{} — {} · {}'.format(v.vehicule.libelle_court if v.vehicule else '', v.acquereur or '—', v.date_vente),
            'url': reverse('flotte:vehicule_detail', args=[v.vehicule_id]),
        })

    cond_search_qs = Conducteur.objects.filter(
        Q(nom__icontains=q) | Q(prenom__icontains=q) | Q(email__icontains=q) | Q(telephone__icontains=q)
    )
    if not is_manager_or_admin(request):
        cond_search_qs = cond_search_qs.filter(user=request.user)
    for c in cond_search_qs.order_by('nom', 'prenom')[:15]:
        out['conducteurs'].append({
            'id': c.pk,
            'label': '{} {}'.format(c.nom, c.prenom) + (' · ' + (c.email or c.telephone or '') if (c.email or c.telephone) else ''),
            'url': reverse('flotte:conducteur_update', args=[c.pk]),
        })

    if is_manager_or_admin(request):
        for f in Facture.objects.filter(
            Q(numero__icontains=q) |
            Q(fournisseur__icontains=q) |
            Q(vehicule__numero_chassis__icontains=q) |
            Q(vehicule__marque__nom__icontains=q) |
            Q(vehicule__modele__nom__icontains=q)
        ).select_related('vehicule__marque', 'vehicule__modele').order_by('-date_facture')[:15]:
            out['factures'].append({
                'id': f.pk,
                'label': '{} — {} · {}'.format(f.vehicule.libelle_court if f.vehicule else '', f.numero, f.fournisseur or ''),
                'url': reverse('flotte:vehicule_detail', args=[f.vehicule_id]),
            })

    return JsonResponse(out)


# ——— Parc / Véhicules ———
@method_decorator(login_required, name='dispatch')
class ParcListView(ListView):
    """Liste des véhicules (châssis = identifiant principal)."""
    model = Vehicule
    template_name = 'flotte/parc.html'
    context_object_name = 'vehicules'
    paginate_by = 50

    def get_queryset(self):
        qs = Vehicule.objects.select_related(
            'marque', 'modele', 'type_vehicule', 'type_carburant', 'type_transmission'
        ).order_by('-date_entree_parc', '-id')
        # Utilisateur simple : ne voir que ses véhicules
        if not is_manager_or_admin(self.request):
            qs = qs.filter(proprietaire=self.request.user)
        statut = self.request.GET.get('statut')
        if statut:
            qs = qs.filter(statut=statut)
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(numero_chassis__icontains=q) |
                Q(numero_immatriculation__icontains=q) |
                Q(marque__nom__icontains=q) |
                Q(modele__nom__icontains=q) |
                Q(origine_pays__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = Vehicule.objects.all()
        if not is_manager_or_admin(self.request):
            qs = qs.filter(proprietaire=self.request.user)
        context['total'] = qs.count()
        context['parc_count'] = qs.filter(statut='parc').count()
        context['import_count'] = qs.filter(statut='import').count()
        context['vendu_count'] = qs.filter(statut='vendu').count()
        context['by_marque'] = list(
            qs.values('marque__nom').annotate(n=Count('id')).order_by('-n')
        )
        context.update(get_sidebar_context(self.request))
        return context


@login_required
def vehicule_detail(request, pk):
    """Fiche véhicule (détail) — démarches, dépenses, documents, réparations, locations, vente, coûts."""
    qs = Vehicule.objects.select_related(
        'marque', 'modele', 'type_vehicule', 'type_carburant', 'type_transmission'
    ).prefetch_related(
        'import_demarches', 'depenses', 'documents', 'reparations', 'locations', 'ventes',
        'charges_import', 'parties_importees', 'photos',
        Prefetch('factures', queryset=Facture.objects.prefetch_related('penalites').order_by('-date_facture', '-id')),
    )
    # Utilisateur simple : ne peut consulter que ses propres véhicules
    if not is_manager_or_admin(request):
        qs = qs.filter(proprietaire=request.user)
    vehicule = get_object_or_404(qs, pk=pk)
    total_depenses = vehicule.depenses.aggregate(s=Sum('montant'))['s'] or 0
    total_reparations = vehicule.reparations.aggregate(s=Sum('cout'))['s'] or 0
    total_charges_import = vehicule.charges_import.aggregate(s=Sum('cout_total'))['s'] or 0
    cout_total = (vehicule.prix_achat or 0) + total_depenses + total_reparations + total_charges_import
    derniere_vente = vehicule.ventes.order_by('-date_vente').first()
    marge = None
    if derniere_vente and derniere_vente.prix_vente:
        marge = derniere_vente.prix_vente - cout_total
    photos = vehicule.photos.all()
    context = {
        'vehicule': vehicule,
        'total_depenses': total_depenses,
        'total_reparations': total_reparations,
        'total_charges_import': total_charges_import,
        'cout_total': cout_total,
        'derniere_vente': derniere_vente,
        'marge': marge,
        'photos': photos,
        **get_sidebar_context(request),
    }
    return render(request, 'flotte/vehicule_detail.html', context)


@method_decorator(login_required, name='dispatch')
class VehiculeCreateView(ManagerRequiredMixin, CreateView):
    """Nouveau véhicule — châssis obligatoire."""
    model = Vehicule
    form_class = VehiculeForm
    template_name = 'flotte/vehicule_form.html'
    success_url = reverse_lazy('flotte:parc')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nouveau véhicule — Import'
        context.update(get_sidebar_context(self.request))
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Véhicule enregistré.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class VehiculeUpdateView(ManagerRequiredMixin, UpdateView):
    """Modifier un véhicule."""
    model = Vehicule
    form_class = VehiculeForm
    template_name = 'flotte/vehicule_form.html'
    context_object_name = 'vehicule'
    success_url = reverse_lazy('flotte:parc')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifier le véhicule'
        context.update(get_sidebar_context(self.request))
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Véhicule mis à jour.')
        return super().form_valid(form)


# ——— Location ———
@method_decorator(login_required, name='dispatch')
class LocationListView(ManagerRequiredMixin, ListView):
    """Liste des locations (avec CT, assurance, km vidange)."""
    model = Location
    template_name = 'flotte/location_list.html'
    context_object_name = 'locations'
    paginate_by = 50

    def get_queryset(self):
        qs = Location.objects.select_related('vehicule__marque', 'vehicule__modele')
        qs = qs.annotate(
            statut_order=Case(
                When(statut='en_cours', then=Value(0)),
                When(statut='a_venir', then=Value(1)),
                When(statut='termine', then=Value(2)),
                default=Value(2),
                output_field=IntegerField(),
            )
        )
        return qs.order_by('statut_order', '-date_debut')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class LocationCreateView(ManagerRequiredMixin, CreateView):
    """Nouvelle location."""
    model = Location
    form_class = LocationForm
    template_name = 'flotte/location_form.html'
    success_url = reverse_lazy('flotte:location_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nouvelle location'
        context.update(get_sidebar_context(self.request))
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Location enregistrée.')
        return super().form_valid(form)


@manager_or_admin_required
def location_detail(request, pk):
    """Fiche location (avec contraventions et coût total)."""
    loc = get_object_or_404(
        Location.objects.select_related('vehicule').prefetch_related('contraventions'),
        pk=pk
    )
    total_contraventions = sum((c.montant or Decimal(0)) for c in loc.contraventions.all())
    context = {
        'location': loc,
        'total_contraventions': total_contraventions,
        **get_sidebar_context(request),
    }
    return render(request, 'flotte/location_detail.html', context)


@method_decorator(login_required, name='dispatch')
class LocationUpdateView(ManagerRequiredMixin, UpdateView):
    """Modifier une location."""
    model = Location
    form_class = LocationForm
    template_name = 'flotte/location_form.html'
    context_object_name = 'location'
    success_url = reverse_lazy('flotte:location_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifier la location'
        context.update(get_sidebar_context(self.request))
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Location mise à jour.')
        return super().form_valid(form)


# ——— Documents véhicule (CRUD depuis l'app) ———
@method_decorator(login_required, name='dispatch')
class DocumentVehiculeCreateView(ManagerRequiredMixin, CreateView):
    model = DocumentVehicule
    form_class = DocumentVehiculeForm
    template_name = 'flotte/document_form.html'
    context_object_name = 'document'

    def get_initial(self):
        return {'vehicule': get_object_or_404(Vehicule, pk=self.kwargs['vehicule_pk'])}

    def form_valid(self, form):
        form.instance.vehicule_id = self.kwargs['vehicule_pk']
        messages.success(self.request, 'Document enregistré.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.kwargs['vehicule_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicule'] = get_object_or_404(Vehicule, pk=self.kwargs['vehicule_pk'])
        context['title'] = 'Ajouter un document'
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class DocumentVehiculeUpdateView(ManagerRequiredMixin, UpdateView):
    model = DocumentVehicule
    form_class = DocumentVehiculeForm
    template_name = 'flotte/document_form.html'
    context_object_name = 'document'

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.object.vehicule_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicule'] = self.object.vehicule
        context['title'] = 'Modifier le document'
        context.update(get_sidebar_context(self.request))
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Document mis à jour.')
        return super().form_valid(form)


# ——— Photos véhicule (CRUD) ———
@method_decorator(login_required, name='dispatch')
class PhotoVehiculeCreateView(ManagerRequiredMixin, CreateView):
    """Ajouter une photo à un véhicule."""
    model = PhotoVehicule
    form_class = PhotoVehiculeForm
    template_name = 'flotte/photo_vehicule_form.html'
    context_object_name = 'photo'

    def get_initial(self):
        return {'vehicule': get_object_or_404(Vehicule, pk=self.kwargs['vehicule_pk'])}

    def form_valid(self, form):
        form.instance.vehicule_id = self.kwargs['vehicule_pk']
        # Si c'est la photo principale, désactiver les autres
        if form.instance.est_principale:
            PhotoVehicule.objects.filter(vehicule_id=self.kwargs['vehicule_pk']).exclude(pk=form.instance.pk).update(est_principale=False)
        messages.success(self.request, 'Photo ajoutée avec succès.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.kwargs['vehicule_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicule'] = get_object_or_404(Vehicule, pk=self.kwargs['vehicule_pk'])
        context['title'] = 'Ajouter une photo'
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class PhotoVehiculeUpdateView(ManagerRequiredMixin, UpdateView):
    """Modifier une photo de véhicule."""
    model = PhotoVehicule
    form_class = PhotoVehiculeForm
    template_name = 'flotte/photo_vehicule_form.html'
    context_object_name = 'photo'

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.object.vehicule_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicule'] = self.object.vehicule
        context['title'] = 'Modifier la photo'
        context.update(get_sidebar_context(self.request))
        return context

    def form_valid(self, form):
        # Si c'est la photo principale, désactiver les autres
        if form.instance.est_principale:
            PhotoVehicule.objects.filter(vehicule_id=form.instance.vehicule_id).exclude(pk=form.instance.pk).update(est_principale=False)
        messages.success(self.request, 'Photo mise à jour.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class PhotoVehiculeDeleteView(ManagerRequiredMixin, DeleteView):
    """Supprimer une photo de véhicule."""
    model = PhotoVehicule
    template_name = 'flotte/photo_vehicule_confirm_delete.html'
    context_object_name = 'photo'

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.object.vehicule_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicule'] = self.object.vehicule
        context.update(get_sidebar_context(self.request))
        return context

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Photo supprimée.')
        return super().delete(request, *args, **kwargs)


# ——— Réparations (CRUD depuis l'app) ———
@method_decorator(login_required, name='dispatch')
class ReparationCreateView(ManagerRequiredMixin, CreateView):
    model = Reparation
    form_class = ReparationForm
    template_name = 'flotte/reparation_form.html'
    context_object_name = 'reparation'

    def form_valid(self, form):
        form.instance.vehicule_id = self.kwargs['vehicule_pk']
        messages.success(self.request, 'Réparation enregistrée.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.kwargs['vehicule_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicule'] = get_object_or_404(Vehicule, pk=self.kwargs['vehicule_pk'])
        context['title'] = 'Ajouter une réparation'
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class ReparationUpdateView(ManagerRequiredMixin, UpdateView):
    model = Reparation
    form_class = ReparationForm
    template_name = 'flotte/reparation_form.html'
    context_object_name = 'reparation'

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.object.vehicule_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicule'] = self.object.vehicule
        context['title'] = 'Modifier la réparation'
        context.update(get_sidebar_context(self.request))
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Réparation mise à jour.')
        return super().form_valid(form)


# ——— Dépenses (CRUD depuis l'app) ———
@method_decorator(login_required, name='dispatch')
class DepenseCreateView(ManagerRequiredMixin, CreateView):
    model = Depense
    form_class = DepenseForm
    template_name = 'flotte/depense_form.html'
    context_object_name = 'depense'

    def form_valid(self, form):
        form.instance.vehicule_id = self.kwargs['vehicule_pk']
        messages.success(self.request, 'Dépense enregistrée.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.kwargs['vehicule_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicule'] = get_object_or_404(Vehicule, pk=self.kwargs['vehicule_pk'])
        context['title'] = 'Ajouter une dépense'
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class DepenseUpdateView(ManagerRequiredMixin, UpdateView):
    model = Depense
    form_class = DepenseForm
    template_name = 'flotte/depense_form.html'
    context_object_name = 'depense'

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.object.vehicule_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicule'] = self.object.vehicule
        context['title'] = 'Modifier la dépense'
        context.update(get_sidebar_context(self.request))
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Dépense mise à jour.')
        return super().form_valid(form)


# ——— Factures (CRUD depuis l'app) ———
def get_next_numero_facture():
    """Génère le prochain numéro de facture au format FAC-AAAA-NNNNN (ex. FAC-2026-00001)."""
    year = timezone.now().year
    prefix = f'FAC-{year}-'
    # Nombre de factures existantes avec ce préfixe (numéro auto ou manuel commençant par FAC-AAAA-)
    count = Facture.objects.filter(numero__startswith=prefix).count()
    next_n = count + 1
    return f'{prefix}{next_n:05d}'


@method_decorator(login_required, name='dispatch')
class FactureCreateView(ManagerRequiredMixin, CreateView):
    model = Facture
    form_class = FactureForm
    template_name = 'flotte/facture_form.html'
    context_object_name = 'facture'

    def get_initial(self):
        initial = super().get_initial()
        initial['numero'] = get_next_numero_facture()
        return initial

    def form_valid(self, form):
        form.instance.vehicule_id = self.kwargs['vehicule_pk']
        messages.success(self.request, 'Facture enregistrée.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.kwargs['vehicule_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vehicule = get_object_or_404(
            Vehicule.objects.prefetch_related('charges_import', 'depenses', 'reparations'),
            pk=self.kwargs['vehicule_pk']
        )
        from django.db.models import Sum
        total_charges = vehicule.charges_import.aggregate(s=Sum('cout_total'))['s'] or 0
        total_dep = vehicule.depenses.aggregate(s=Sum('montant'))['s'] or 0
        total_rep = vehicule.reparations.aggregate(s=Sum('cout'))['s'] or 0
        context['vehicule'] = vehicule
        context['title'] = 'Ajouter une facture'
        context['cout_total_vehicule'] = (vehicule.prix_achat or 0) + total_charges + total_dep + total_rep
        context['numero_suggere'] = get_next_numero_facture()
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class FactureUpdateView(ManagerRequiredMixin, UpdateView):
    model = Facture
    form_class = FactureForm
    template_name = 'flotte/facture_form.html'
    context_object_name = 'facture'

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.object.vehicule_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicule'] = self.object.vehicule
        context['title'] = 'Modifier la facture'
        context.update(get_sidebar_context(self.request))
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Facture mise à jour.')
        return super().form_valid(form)


# ——— Pénalités facture (CRUD) ———
@method_decorator(login_required, name='dispatch')
class PenaliteFactureCreateView(ManagerRequiredMixin, CreateView):
    """Ajouter une pénalité à une facture."""
    model = PenaliteFacture
    form_class = PenaliteFactureForm
    template_name = 'flotte/penalite_facture_form.html'
    context_object_name = 'penalite'

    def form_valid(self, form):
        form.instance.facture_id = self.kwargs['facture_pk']
        messages.success(self.request, 'Pénalité enregistrée.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.object.facture.vehicule_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        facture = get_object_or_404(Facture, pk=self.kwargs['facture_pk'])
        context['facture'] = facture
        context['vehicule'] = facture.vehicule
        context['title'] = 'Ajouter une pénalité'
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class PenaliteFactureUpdateView(ManagerRequiredMixin, UpdateView):
    """Modifier une pénalité de facture."""
    model = PenaliteFacture
    form_class = PenaliteFactureForm
    template_name = 'flotte/penalite_facture_form.html'
    context_object_name = 'penalite'

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.object.facture.vehicule_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['facture'] = self.object.facture
        context['vehicule'] = self.object.facture.vehicule
        context['title'] = 'Modifier la pénalité'
        context.update(get_sidebar_context(self.request))
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Pénalité mise à jour.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class PenaliteFactureDeleteView(ManagerRequiredMixin, DeleteView):
    """Supprimer une pénalité de facture."""
    model = PenaliteFacture
    template_name = 'flotte/penalite_facture_confirm_delete.html'
    context_object_name = 'penalite'

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.object.facture.vehicule_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['facture'] = self.object.facture
        context['vehicule'] = self.object.facture.vehicule
        context.update(get_sidebar_context(self.request))
        return context

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Pénalité supprimée.')
        return super().delete(request, *args, **kwargs)


# ——— Démarches import (CRUD depuis l'app) ———
@method_decorator(login_required, name='dispatch')
class ImportDemarcheCreateView(ManagerRequiredMixin, CreateView):
    model = ImportDemarche
    form_class = ImportDemarcheForm
    template_name = 'flotte/import_demarche_form.html'
    context_object_name = 'import_demarche'

    def form_valid(self, form):
        form.instance.vehicule_id = self.kwargs['vehicule_pk']
        messages.success(self.request, 'Démarche enregistrée.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.kwargs['vehicule_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicule'] = get_object_or_404(Vehicule, pk=self.kwargs['vehicule_pk'])
        context['title'] = 'Ajouter une démarche import'
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class ImportDemarcheUpdateView(ManagerRequiredMixin, UpdateView):
    model = ImportDemarche
    form_class = ImportDemarcheForm
    template_name = 'flotte/import_demarche_form.html'
    context_object_name = 'import_demarche'

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.object.vehicule_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicule'] = self.object.vehicule
        context['title'] = 'Modifier la démarche import'
        context.update(get_sidebar_context(self.request))
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Démarche mise à jour.')
        return super().form_valid(form)


# ——— Charges d'importation (par véhicule) ———
@method_decorator(login_required, name='dispatch')
class ChargeImportCreateView(ManagerRequiredMixin, CreateView):
    model = ChargeImport
    form_class = ChargeImportForm
    template_name = 'flotte/charge_import_form.html'
    context_object_name = 'charge_import'

    def form_valid(self, form):
        form.instance.vehicule_id = self.kwargs['vehicule_pk']
        messages.success(self.request, 'Charges d\'importation enregistrées.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.kwargs['vehicule_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicule'] = get_object_or_404(Vehicule, pk=self.kwargs['vehicule_pk'])
        context['title'] = 'Ajouter charges d\'importation'
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class ChargeImportUpdateView(ManagerRequiredMixin, UpdateView):
    model = ChargeImport
    form_class = ChargeImportForm
    template_name = 'flotte/charge_import_form.html'
    context_object_name = 'charge_import'

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.object.vehicule_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicule'] = self.object.vehicule
        context['title'] = 'Modifier charges d\'importation'
        context.update(get_sidebar_context(self.request))
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Charges d\'importation mises à jour.')
        return super().form_valid(form)


# ——— Pièces importées ———
@method_decorator(login_required, name='dispatch')
class PartieImporteeListView(ManagerRequiredMixin, ListView):
    model = PartieImportee
    template_name = 'flotte/parties_importees_list.html'
    context_object_name = 'parties'
    paginate_by = 30

    def get_queryset(self):
        qs = PartieImportee.objects.select_related('vehicule').order_by('-id')
        vehicule_id = self.request.GET.get('vehicule')
        if vehicule_id:
            qs = qs.filter(vehicule_id=vehicule_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicules'] = Vehicule.objects.all().order_by('marque__nom', 'modele__nom')[:200]
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class PartieImporteeCreateView(ManagerRequiredMixin, CreateView):
    model = PartieImportee
    form_class = PartieImporteeForm
    template_name = 'flotte/partie_importee_form.html'
    context_object_name = 'partie'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['vehicule_filtre'] = self.kwargs.get('vehicule_pk')
        return kwargs

    def form_valid(self, form):
        if self.kwargs.get('vehicule_pk'):
            form.instance.vehicule_id = self.kwargs['vehicule_pk']
        messages.success(self.request, 'Partie importée enregistrée.')
        return super().form_valid(form)

    def get_success_url(self):
        if self.kwargs.get('vehicule_pk'):
            return reverse('flotte:vehicule_detail', args=[self.kwargs['vehicule_pk']])
        return reverse('flotte:parties_importees_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.kwargs.get('vehicule_pk'):
            context['vehicule'] = get_object_or_404(Vehicule, pk=self.kwargs['vehicule_pk'])
        context['title'] = 'Ajouter une pièce / partie importée'
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class PartieImporteeUpdateView(ManagerRequiredMixin, UpdateView):
    model = PartieImportee
    form_class = PartieImporteeForm
    template_name = 'flotte/partie_importee_form.html'
    context_object_name = 'partie'

    def get_success_url(self):
        if self.object.vehicule_id:
            return reverse('flotte:vehicule_detail', args=[self.object.vehicule_id])
        return reverse('flotte:parties_importees_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.vehicule_id:
            context['vehicule'] = self.object.vehicule
        context['title'] = 'Modifier la pièce / partie importée'
        context.update(get_sidebar_context(self.request))
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Partie importée mise à jour.')
        return super().form_valid(form)


# ——— Contraventions (par location) ———
@method_decorator(login_required, name='dispatch')
class ContraventionCreateView(ManagerRequiredMixin, CreateView):
    model = Contravention
    form_class = ContraventionForm
    template_name = 'flotte/contravention_form.html'
    context_object_name = 'contravention'

    def form_valid(self, form):
        form.instance.location_id = self.kwargs['location_pk']
        messages.success(self.request, 'Contravention enregistrée.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('flotte:location_detail', args=[self.kwargs['location_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['location'] = get_object_or_404(Location, pk=self.kwargs['location_pk'])
        context['title'] = 'Ajouter une contravention'
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class ContraventionUpdateView(ManagerRequiredMixin, UpdateView):
    model = Contravention
    form_class = ContraventionForm
    template_name = 'flotte/contravention_form.html'
    context_object_name = 'contravention'

    def get_success_url(self):
        return reverse('flotte:location_detail', args=[self.object.location_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['location'] = self.object.location
        context['title'] = 'Modifier la contravention'
        context.update(get_sidebar_context(self.request))
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Contravention mise à jour.')
        return super().form_valid(form)


# ——— Ventes (CRUD depuis l'app) ———
@method_decorator(login_required, name='dispatch')
class VenteCreateView(ManagerRequiredMixin, CreateView):
    model = Vente
    form_class = VenteForm
    template_name = 'flotte/vente_form.html'
    context_object_name = 'vente'

    def form_valid(self, form):
        form.instance.vehicule_id = self.kwargs['vehicule_pk']
        try:
            result = super().form_valid(form)
            vehicule = get_object_or_404(Vehicule, pk=self.kwargs['vehicule_pk'])
            vehicule.statut = 'vendu'
            vehicule.save(update_fields=['statut'])
            messages.success(self.request, 'Vente enregistrée.')
            return result
        except (DatabaseError, IntegrityError) as e:
            logger.exception('VenteCreateView: erreur enregistrement vente: %s', e)
            messages.error(
                self.request,
                'L\'enregistrement de la vente a échoué. Veuillez vérifier les données ou réessayer.',
            )
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.kwargs['vehicule_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicule'] = get_object_or_404(Vehicule, pk=self.kwargs['vehicule_pk'])
        context['title'] = 'Enregistrer une vente'
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class VenteUpdateView(ManagerRequiredMixin, UpdateView):
    model = Vente
    form_class = VenteForm
    template_name = 'flotte/vente_form.html'
    context_object_name = 'vente'

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.object.vehicule_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicule'] = self.object.vehicule
        context['title'] = 'Modifier la vente'
        context.update(get_sidebar_context(self.request))
        return context

    def form_valid(self, form):
        try:
            result = super().form_valid(form)
            messages.success(self.request, 'Vente mise à jour.')
            return result
        except (DatabaseError, IntegrityError) as e:
            logger.exception('VenteUpdateView: erreur mise à jour vente: %s', e)
            messages.error(
                self.request,
                'La mise à jour de la vente a échoué. Veuillez vérifier les données ou réessayer.',
            )
            return self.form_invalid(form)


# ——— Import (réservé manager / admin) ———
@manager_or_admin_required
def import_list(request):
    """Véhicules en import & démarches."""
    vehicules = Vehicule.objects.filter(statut='import').select_related(
        'marque', 'modele'
    ).prefetch_related('import_demarches').order_by('-date_entree_parc')
    context = {
        'vehicules': vehicules,
        **get_sidebar_context(request),
    }
    return render(request, 'flotte/import_list.html', context)


# ——— Réparations, Documents, Ventes, CA, Maintenance, Carburant, Conducteurs, Contraventions ———
@login_required
def reparations_list(request):
    """Liste des réparations."""
    reps_qs = Reparation.objects.select_related('vehicule')
    if not is_manager_or_admin(request):
        reps_qs = reps_qs.filter(vehicule__proprietaire=request.user)
    reps = reps_qs.order_by('-date_reparation', '-id')[:200]
    context = {'reparations': reps, **get_sidebar_context(request)}
    return render(request, 'flotte/reparations_list.html', context)


@manager_or_admin_required
def contraventions_list(request):
    """Liste de toutes les contraventions (véhicules loués)."""
    contraventions = Contravention.objects.select_related(
        'location', 'location__vehicule__marque', 'location__vehicule__modele'
    ).order_by('-date_contravention', '-id')[:500]
    total_montant = sum((c.montant or Decimal(0)) for c in contraventions)
    context = {
        'contraventions': contraventions,
        'total_montant': total_montant,
        **get_sidebar_context(request),
    }
    return render(request, 'flotte/contraventions_list.html', context)


@login_required
def documents_list(request):
    """Documents par véhicule."""
    vehicules_qs = Vehicule.objects.prefetch_related('documents')
    if not is_manager_or_admin(request):
        vehicules_qs = vehicules_qs.filter(proprietaire=request.user)
    vehicules = vehicules_qs.order_by('marque__nom', 'modele__nom')[:100]
    context = {'vehicules': vehicules, **get_sidebar_context(request)}
    return render(request, 'flotte/documents_list.html', context)


@login_required
def ventes_list(request):
    """Liste des ventes. Manager/Admin : toutes. Utilisateur (client) : uniquement ses ventes (acquereur_compte)."""
    from .mixins import is_manager_or_admin
    context_base = get_sidebar_context(request)
    try:
        qs = Vente.objects.select_related('vehicule', 'acquereur_compte').order_by('-date_vente')
        if not is_manager_or_admin(request):
            qs = qs.filter(acquereur_compte=request.user)
        ventes = list(qs[:100])
    except (DatabaseError, Exception) as e:
        logger.exception('ventes_list: erreur lors du chargement des ventes: %s', e)
        ventes = []
        messages.error(
            request,
            'Impossible de charger la liste des ventes. Veuillez réessayer plus tard.',
        )
    context = {'ventes': ventes, **context_base}
    return render(request, 'flotte/ventes_list.html', context)


def _ca_evolution_queryset(granularite, annee, mois=None):
    """Retourne les valeurs annotées (date/mois/année, total) pour l'évolution du CA.
    Utilisé par l'API ca_api_evolution pour les graphiques."""
    qs = Vente.objects.exclude(prix_vente__isnull=True).exclude(prix_vente=0)
    if annee:
        qs = qs.filter(date_vente__year=annee)
    if mois is not None:
        qs = qs.filter(date_vente__month=mois)
    if granularite == 'jour':
        qs = qs.annotate(periode=TruncDate('date_vente')).values('periode').annotate(
            total=Sum('prix_vente'), nb=Count('id')
        ).order_by('periode')
    elif granularite == 'mois':
        qs = qs.annotate(periode=TruncMonth('date_vente')).values('periode').annotate(
            total=Sum('prix_vente'), nb=Count('id')
        ).order_by('periode')
    else:  # annee
        qs = qs.annotate(periode=TruncYear('date_vente')).values('periode').annotate(
            total=Sum('prix_vente'), nb=Count('id')
        ).order_by('periode')
    return qs


@login_required
def ca_api_evolution(request):
    """API JSON : évolution du CA par jour / mois / année pour les graphiques.
    Accessible à tout utilisateur connecté (cohérent avec la page CA)."""
    granularite = request.GET.get('granularite', 'mois')
    if granularite not in ('jour', 'mois', 'annee'):
        granularite = 'mois'
    try:
        annee = int(request.GET.get('annee', timezone.now().year))
    except (TypeError, ValueError):
        annee = timezone.now().year
    mois = request.GET.get('mois')
    if mois is not None:
        try:
            mois = int(mois)
        except (TypeError, ValueError):
            mois = None
    rows = list(_ca_evolution_queryset(granularite, annee, mois))
    if granularite == 'jour':
        labels = [r['periode'].strftime('%d/%m') if r['periode'] else '' for r in rows]
    elif granularite == 'mois':
        mois_noms = ('', 'Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc')
        labels = [
            f"{mois_noms[r['periode'].month]} {r['periode'].year}" if r['periode'] else ''
            for r in rows
        ]
    else:
        labels = [str(r['periode'].year) if r['periode'] else '' for r in rows]
    data = [float(r['total'] or 0) for r in rows]
    nb_ventes = [int(r['nb']) for r in rows]
    return JsonResponse({'labels': labels, 'data': data, 'nb_ventes': nb_ventes})


@manager_or_admin_required
def ca_view(request):
    """Chiffre d'affaires : KPIs sur toutes les ventes avec prix (cohérent avec graphiques)."""
    now = timezone.now()
    # Même base que les graphiques : ventes avec prix renseigné et > 0
    qs_ventes_ca = Vente.objects.exclude(prix_vente__isnull=True).exclude(prix_vente=0)
    agg = qs_ventes_ca.aggregate(
        total_ca=Sum('prix_vente'),
        nb_ventes=Count('id'),
        moyenne_vente=Avg('prix_vente'),
    )
    annees = list(range(now.year - 2, now.year + 3))
    # Année par défaut : dernière année ayant au moins une vente, sinon année courante
    derniere_annee_avec_vente = (
        Vente.objects.exclude(date_vente__isnull=True)
        .values_list('date_vente__year', flat=True)
        .order_by('-date_vente__year')
        .first()
    )
    annee_defaut = derniere_annee_avec_vente if derniere_annee_avec_vente else now.year
    if annee_defaut not in annees:
        annees = sorted(set(annees) | {annee_defaut})

    # CA par année (année par défaut vs année précédente) pour indicateur de tendance
    from decimal import Decimal as _Decimal
    ca_annee = qs_ventes_ca.filter(date_vente__year=annee_defaut).aggregate(
        total=Sum('prix_vente')
    )['total'] or _Decimal('0')
    ca_annee_prec = qs_ventes_ca.filter(date_vente__year=annee_defaut - 1).aggregate(
        total=Sum('prix_vente')
    )['total'] or _Decimal('0')
    diff_abs = ca_annee - ca_annee_prec
    diff_pct = _Decimal('0')
    if ca_annee_prec:
        diff_pct = (diff_abs / ca_annee_prec) * _Decimal('100')

    # Top 5 véhicules par CA (toutes périodes)
    top_vehicules = list(
        qs_ventes_ca.values(
            'vehicule_id',
            'vehicule__marque__nom',
            'vehicule__modele__nom',
            'vehicule__numero_chassis',
        )
        .annotate(total_ca=Sum('prix_vente'), nb_ventes=Count('id'))
        .order_by('-total_ca')[:5]
    )

    context = {
        'total_ca': agg['total_ca'] or Decimal('0'),
        'nb_ventes': agg['nb_ventes'] or 0,
        'moyenne_vente': agg['moyenne_vente'] or Decimal('0'),
        'annee_courante': annee_defaut,
        'mois_courant': now.month,
        'annees': annees,
        'ca_annee': ca_annee,
        'ca_annee_prec': ca_annee_prec,
        'ca_diff_abs': diff_abs,
        'ca_diff_pct': diff_pct,
        'top_vehicules': top_vehicules,
        **get_sidebar_context(request),
    }
    return render(request, 'flotte/ca.html', context)


@login_required
def ca_check_code(request):
    """API JSON : vérifie le code d'affichage des montants de CA pour l'utilisateur courant."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'Méthode non autorisée.'}, status=405)
    profil = getattr(request.user, 'profil_flotte', None)
    if not profil:
        return JsonResponse({'ok': False, 'message': 'Profil utilisateur introuvable.'}, status=400)
    try:
        import json

        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except (TypeError, ValueError):
        payload = {}
    code = (payload.get('code') or '').strip()
    # Si aucun code n'est défini côté profil, on considère que tout est autorisé
    if not profil.code_ca_hash:
        return JsonResponse({'ok': True, 'message': 'Aucun code défini (accès autorisé).'})
    if profil.check_code_ca(code):
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False, 'message': 'Code incorrect.'}, status=400)


@manager_or_admin_required
def parametrage_ca_code(request):
    """Page de réglage du code d'affichage des montants CA pour l'utilisateur courant."""
    profil = getattr(request.user, 'profil_flotte', None)
    if not profil:
        messages.error(request, "Profil utilisateur introuvable.")
        return redirect('flotte:parametrage_index')
    if request.method == 'POST':
        form = CAAmountCodeForm(request.POST, user=request.user)
        if form.is_valid():
            new_code = form.cleaned_data.get('new_code') or ''
            profil.set_code_ca(new_code)
            profil.save(update_fields=['code_ca_hash'])
            if new_code:
                messages.success(request, "Code d'affichage des montants mis à jour.")
            else:
                messages.success(request, "Code supprimé : l'affichage des montants n'est plus protégé.")
            return redirect('flotte:parametrage_index')
    else:
        form = CAAmountCodeForm(user=request.user)
    context = {
        'form': form,
        'title': "Code d'affichage des montants (CA)",
        'back_url': reverse_lazy('flotte:parametrage_index'),
        **get_sidebar_context(request),
    }
    return render(request, 'flotte/parametrage_form.html', context)


@manager_or_admin_required
def rapport_download(request, pk):
    """Téléchargement d'un rapport journalier (PDF)."""
    rapport = get_object_or_404(RapportJournalier, pk=pk)
    if not rapport.fichier:
        messages.error(request, 'Aucun fichier associé.')
        return redirect('flotte:ca')
    from django.http import FileResponse
    import os
    return FileResponse(
        rapport.fichier.open('rb'),
        as_attachment=True,
        filename=os.path.basename(rapport.fichier.name),
    )


@login_required
def maintenance_list(request):
    """Liste des maintenances préventives (à faire / en cours en haut, effectuées en bas)."""
    qs = Maintenance.objects.select_related('vehicule').annotate(
        statut_order=Case(
            When(statut='a_faire', then=Value(0)),
            When(statut='en_cours', then=Value(1)),
            When(statut='effectue', then=Value(2)),
            default=Value(2),
            output_field=IntegerField(),
        )
    )
    if not is_manager_or_admin(request):
        qs = qs.filter(vehicule__proprietaire=request.user)
    qs = qs.order_by('statut_order', '-date_prevue', '-id')[:200]
    maintenances = qs
    context = {
        'maintenances': maintenances,
        **get_sidebar_context(request),
    }
    return render(request, 'flotte/maintenance_list.html', context)


@login_required
def carburant_list(request):
    """Liste des relevés carburant."""
    releves_qs = ReleveCarburant.objects.select_related('vehicule')
    if not is_manager_or_admin(request):
        releves_qs = releves_qs.filter(vehicule__proprietaire=request.user)
    releves = releves_qs.order_by('-date_releve', '-id')[:200]
    context = {
        'releves': releves,
        **get_sidebar_context(request),
    }
    return render(request, 'flotte/carburant_list.html', context)


@login_required
def conducteurs_list(request):
    """Liste des conducteurs."""
    conducteurs_qs = Conducteur.objects.all()
    if not is_manager_or_admin(request):
        conducteurs_qs = conducteurs_qs.filter(user=request.user)
    conducteurs = conducteurs_qs.order_by('nom', 'prenom')
    context = {
        'conducteurs': conducteurs,
        **get_sidebar_context(request),
    }
    return render(request, 'flotte/conducteurs_list.html', context)


# ——— Maintenance (CRUD) ———
@method_decorator(login_required, name='dispatch')
class MaintenanceCreateView(ManagerRequiredMixin, CreateView):
    model = Maintenance
    form_class = MaintenanceForm
    template_name = 'flotte/maintenance_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nouvelle maintenance'
        context.update(get_sidebar_context(self.request))
        return context

    def get_success_url(self):
        return reverse_lazy('flotte:maintenance_list')


@method_decorator(login_required, name='dispatch')
class MaintenanceUpdateView(ManagerRequiredMixin, UpdateView):
    model = Maintenance
    form_class = MaintenanceForm
    template_name = 'flotte/maintenance_form.html'
    context_object_name = 'maintenance'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifier la maintenance'
        context.update(get_sidebar_context(self.request))
        return context

    def get_success_url(self):
        return reverse_lazy('flotte:maintenance_list')


# ——— Relevés carburant (CRUD) ———
@method_decorator(login_required, name='dispatch')
class ReleveCarburantCreateView(ManagerRequiredMixin, CreateView):
    model = ReleveCarburant
    form_class = ReleveCarburantForm
    template_name = 'flotte/carburant_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nouveau relevé carburant'
        context.update(get_sidebar_context(self.request))
        return context

    def get_success_url(self):
        return reverse_lazy('flotte:carburant_list')


@method_decorator(login_required, name='dispatch')
class ReleveCarburantUpdateView(ManagerRequiredMixin, UpdateView):
    model = ReleveCarburant
    form_class = ReleveCarburantForm
    template_name = 'flotte/carburant_form.html'
    context_object_name = 'releve'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifier le relevé carburant'
        context.update(get_sidebar_context(self.request))
        return context

    def get_success_url(self):
        return reverse_lazy('flotte:carburant_list')


# ——— Conducteurs (CRUD) ———
@method_decorator(login_required, name='dispatch')
class ConducteurCreateView(ManagerRequiredMixin, CreateView):
    model = Conducteur
    form_class = ConducteurForm
    template_name = 'flotte/conducteur_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nouveau conducteur'
        context.update(get_sidebar_context(self.request))
        return context

    def get_success_url(self):
        return reverse_lazy('flotte:conducteurs_list')


@method_decorator(login_required, name='dispatch')
class ConducteurUpdateView(ManagerRequiredMixin, UpdateView):
    model = Conducteur
    form_class = ConducteurForm
    template_name = 'flotte/conducteur_form.html'
    context_object_name = 'conducteur'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifier le conducteur'
        context.update(get_sidebar_context(self.request))
        return context

    def get_success_url(self):
        return reverse_lazy('flotte:conducteurs_list')


# ——— Rapports journaliers (modifier / supprimer) ———
@method_decorator(login_required, name='dispatch')
class RapportJournalierUpdateView(ManagerRequiredMixin, UpdateView):
    model = RapportJournalier
    form_class = RapportJournalierForm
    template_name = 'flotte/rapport_form.html'
    context_object_name = 'rapport'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifier le rapport'
        context.update(get_sidebar_context(self.request))
        return context

    def get_success_url(self):
        return reverse_lazy('flotte:ca')


# ——— Paramétrage (Admin) ———
@login_required
def parametrage_index(request):
    """Page d'accueil Paramétrage : 5 volets (véhicules, caractéristiques, marques/modèles, utilisateurs, financier)."""
    if not is_admin(request):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    context = {**get_sidebar_context(request)}
    return render(request, 'flotte/parametrage.html', context)


@login_required
def audit_list(request):
    """Consultation et export du journal d'audit (réservé admin). Filtres : date, utilisateur, modèle."""
    if not is_admin(request):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    qs = AuditLog.objects.select_related('user').order_by('-timestamp')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    user_id = request.GET.get('user')
    model_name = request.GET.get('model', '').strip()
    if date_from:
        qs = qs.filter(timestamp__date__gte=date_from)
    if date_to:
        qs = qs.filter(timestamp__date__lte=date_to)
    if user_id:
        qs = qs.filter(user_id=user_id)
    if model_name:
        qs = qs.filter(model_name__icontains=model_name)
    qs = qs[:500]
    if request.GET.get('export') == 'csv':
        import csv
        from django.utils import timezone
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="audit_flotte_{}.csv"'.format(
            timezone.now().strftime('%Y%m%d_%H%M')
        )
        response.write('\ufeff')
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Date', 'Utilisateur', 'Action', 'Modèle', 'ID objet', 'Représentation'])
        for log in qs:
            writer.writerow([
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else '',
                log.user.username if log.user else '',
                log.get_action_display() if log.action else log.action,
                log.model_name or '',
                log.object_id or '',
                (log.object_repr or '')[:200],
            ])
        return response
    context = {
        'audit_logs': qs,
        'date_from': date_from,
        'date_to': date_to,
        'user_id': user_id,
        'model_name': model_name,
        **get_sidebar_context(request),
    }
    return render(request, 'flotte/audit_list.html', context)


@method_decorator(login_required, name='dispatch')
class ParametrageMarqueListView(AdminRequiredMixin, ListView):
    model = Marque
    template_name = 'flotte/parametrage_marques.html'
    context_object_name = 'marques'
    paginate_by = 50

    def get_queryset(self):
        return Marque.objects.order_by('nom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class MarqueCreateView(AdminRequiredMixin, CreateView):
    model = Marque
    form_class = MarqueForm
    template_name = 'flotte/parametrage_form.html'
    success_url = reverse_lazy('flotte:parametrage_marques')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Ajouter une marque'
        context['back_url'] = reverse_lazy('flotte:parametrage_marques')
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class MarqueUpdateView(AdminRequiredMixin, UpdateView):
    model = Marque
    form_class = MarqueForm
    template_name = 'flotte/parametrage_form.html'
    context_object_name = 'object'
    success_url = reverse_lazy('flotte:parametrage_marques')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifier la marque'
        context['back_url'] = reverse_lazy('flotte:parametrage_marques')
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class ParametrageModeleListView(AdminRequiredMixin, ListView):
    model = Modele
    template_name = 'flotte/parametrage_modeles.html'
    context_object_name = 'modeles'
    paginate_by = 50

    def get_queryset(self):
        qs = Modele.objects.select_related('marque').filter(marque__archive=False).order_by('marque__nom', 'nom')
        marque_id = self.request.GET.get('marque_id')
        if marque_id:
            qs = qs.filter(marque_id=marque_id)
        # Filtrer modèles archivés si demandé (par défaut on affiche tous)
        if self.request.GET.get('archives') != '1':
            qs = qs.filter(archive=False)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['marques'] = Marque.objects.filter(archive=False).order_by('nom')
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class ModeleCreateView(AdminRequiredMixin, CreateView):
    model = Modele
    form_class = ModeleForm
    template_name = 'flotte/parametrage_form.html'
    success_url = reverse_lazy('flotte:parametrage_modeles')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Ajouter un modèle'
        context['back_url'] = reverse_lazy('flotte:parametrage_modeles')
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class ModeleUpdateView(AdminRequiredMixin, UpdateView):
    model = Modele
    form_class = ModeleForm
    template_name = 'flotte/parametrage_form.html'
    context_object_name = 'object'
    success_url = reverse_lazy('flotte:parametrage_modeles')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifier le modèle'
        context['back_url'] = reverse_lazy('flotte:parametrage_modeles')
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class ParametrageCarburantListView(AdminRequiredMixin, ListView):
    model = TypeCarburant
    template_name = 'flotte/parametrage_carburant.html'
    context_object_name = 'types'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class TypeCarburantCreateView(AdminRequiredMixin, CreateView):
    model = TypeCarburant
    form_class = TypeCarburantForm
    template_name = 'flotte/parametrage_form.html'
    success_url = reverse_lazy('flotte:parametrage_carburant')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Ajouter un type de carburant'
        context['back_url'] = reverse_lazy('flotte:parametrage_carburant')
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class TypeCarburantUpdateView(AdminRequiredMixin, UpdateView):
    model = TypeCarburant
    form_class = TypeCarburantForm
    template_name = 'flotte/parametrage_form.html'
    context_object_name = 'object'
    success_url = reverse_lazy('flotte:parametrage_carburant')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifier le type de carburant'
        context['back_url'] = reverse_lazy('flotte:parametrage_carburant')
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class ParametrageTransmissionListView(AdminRequiredMixin, ListView):
    model = TypeTransmission
    template_name = 'flotte/parametrage_transmission.html'
    context_object_name = 'types'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class TypeTransmissionCreateView(AdminRequiredMixin, CreateView):
    model = TypeTransmission
    form_class = TypeTransmissionForm
    template_name = 'flotte/parametrage_form.html'
    success_url = reverse_lazy('flotte:parametrage_transmission')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Ajouter un type de transmission'
        context['back_url'] = reverse_lazy('flotte:parametrage_transmission')
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class TypeTransmissionUpdateView(AdminRequiredMixin, UpdateView):
    model = TypeTransmission
    form_class = TypeTransmissionForm
    template_name = 'flotte/parametrage_form.html'
    context_object_name = 'object'
    success_url = reverse_lazy('flotte:parametrage_transmission')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifier le type de transmission'
        context['back_url'] = reverse_lazy('flotte:parametrage_transmission')
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class ParametrageTypeVehiculeListView(AdminRequiredMixin, ListView):
    model = TypeVehicule
    template_name = 'flotte/parametrage_type_vehicule.html'
    context_object_name = 'types'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class TypeVehiculeCreateView(AdminRequiredMixin, CreateView):
    model = TypeVehicule
    form_class = TypeVehiculeForm
    template_name = 'flotte/parametrage_form.html'
    success_url = reverse_lazy('flotte:parametrage_type_vehicule')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Ajouter un type de véhicule'
        context['back_url'] = reverse_lazy('flotte:parametrage_type_vehicule')
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class TypeVehiculeUpdateView(AdminRequiredMixin, UpdateView):
    model = TypeVehicule
    form_class = TypeVehiculeForm
    template_name = 'flotte/parametrage_form.html'
    context_object_name = 'object'
    success_url = reverse_lazy('flotte:parametrage_type_vehicule')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifier le type de véhicule'
        context['back_url'] = reverse_lazy('flotte:parametrage_type_vehicule')
        context.update(get_sidebar_context(self.request))
        return context


# ——— Paramétrage Types de document ———
@method_decorator(login_required, name='dispatch')
class ParametrageTypeDocumentListView(AdminRequiredMixin, ListView):
    model = TypeDocument
    template_name = 'flotte/parametrage_type_document.html'
    context_object_name = 'types'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class TypeDocumentCreateView(AdminRequiredMixin, CreateView):
    model = TypeDocument
    form_class = TypeDocumentForm
    template_name = 'flotte/parametrage_form.html'
    success_url = reverse_lazy('flotte:parametrage_type_document')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Ajouter un type de document'
        context['back_url'] = reverse_lazy('flotte:parametrage_type_document')
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class TypeDocumentUpdateView(AdminRequiredMixin, UpdateView):
    model = TypeDocument
    form_class = TypeDocumentForm
    template_name = 'flotte/parametrage_form.html'
    context_object_name = 'object'
    success_url = reverse_lazy('flotte:parametrage_type_document')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifier le type de document'
        context['back_url'] = reverse_lazy('flotte:parametrage_type_document')
        context.update(get_sidebar_context(self.request))
        return context


@login_required
def parametrage_utilisateurs(request):
    """Liste des utilisateurs (admin)."""
    if not is_admin(request):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    users = User.objects.all().order_by('username')
    for u in users:
        try:
            u.role_display = u.profil_flotte.get_role_display()
        except ProfilUtilisateur.DoesNotExist:
            u.role_display = '—'
    context = {'users': users, **get_sidebar_context(request)}
    return render(request, 'flotte/parametrage_utilisateurs.html', context)


@method_decorator(login_required, name='dispatch')
class UserCreateView(AdminRequiredMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = 'flotte/parametrage_form.html'
    success_url = reverse_lazy('flotte:parametrage_utilisateurs')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Créer un utilisateur'
        context['back_url'] = reverse_lazy('flotte:parametrage_utilisateurs')
        context.update(get_sidebar_context(self.request))
        return context


@method_decorator(login_required, name='dispatch')
class UserUpdateView(AdminRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'flotte/user_update.html'
    context_object_name = 'utilisateur'
    success_url = reverse_lazy('flotte:parametrage_utilisateurs')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifier l\'utilisateur'
        context['back_url'] = reverse_lazy('flotte:parametrage_utilisateurs')
        context.update(get_sidebar_context(self.request))
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Utilisateur mis à jour.')
        return super().form_valid(form)
