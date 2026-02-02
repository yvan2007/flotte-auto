"""
Vues FLOTTE — Dashboard, parc (châssis), location (CT, assurance, vidange),
import, paramétrage (marques, modèles, types, utilisateurs).
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
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
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from django.utils import timezone
from decimal import Decimal
from django.utils.decorators import method_decorator

from .models import (
    Marque, Modele, TypeCarburant, TypeTransmission, TypeVehicule,
    Vehicule, Location, ImportDemarche, Depense, DocumentVehicule,
    Reparation, Vente, ProfilUtilisateur, Facture,
    RapportJournalier, Maintenance, ReleveCarburant, Conducteur,
)
from .forms import (
    LoginForm, UserCreateForm, UserUpdateForm, MarqueForm, ModeleForm,
    TypeCarburantForm, TypeTransmissionForm, TypeVehiculeForm,
    VehiculeForm, LocationForm, DepenseForm, DocumentVehiculeForm,
    ReparationForm, FactureForm, ImportDemarcheForm, VenteForm,
    RapportJournalierForm, MaintenanceForm, ReleveCarburantForm, ConducteurForm,
)
from .mixins import (
    AdminRequiredMixin, ManagerRequiredMixin,
    user_role, is_admin, is_manager_or_admin,
    manager_or_admin_required,
)
from django.contrib.auth import get_user_model

User = get_user_model()


def get_sidebar_context(request):
    """Contexte commun : rôle, is_admin, is_manager_or_admin pour la sidebar et les boutons."""
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
    parc = qs.filter(statut='parc').count()
    import_ = qs.filter(statut='import').count()
    vendus = qs.filter(statut='vendu').count()
    total = qs.count()
    by_marque = list(
        qs.values('marque__nom').annotate(n=Count('id')).order_by('-n')
    )
    # Alertes : locations dont CT ou assurance expire dans les 30 jours
    now = timezone.now().date()
    fin_alerte = now + timedelta(days=30)
    alertes_ct = list(
        Location.objects.filter(
            date_expiration_ct__isnull=False,
            date_expiration_ct__gte=now,
            date_expiration_ct__lte=fin_alerte,
            statut='en_cours',
        ).select_related('vehicule').order_by('date_expiration_ct')[:10]
    )
    alertes_assurance = list(
        Location.objects.filter(
            date_expiration_assurance__isnull=False,
            date_expiration_assurance__gte=now,
            date_expiration_assurance__lte=fin_alerte,
            statut='en_cours',
        ).select_related('vehicule').order_by('date_expiration_assurance')[:10]
    )
    vehicules_import = list(
        Vehicule.objects.filter(statut='import').select_related('marque', 'modele').order_by('-date_entree_parc')[:5]
    )
    context = {
        'parc': parc,
        'import': import_,
        'vendus': vendus,
        'total': total,
        'by_marque': by_marque,
        'alertes_ct': alertes_ct,
        'alertes_assurance': alertes_assurance,
        'vehicules_import': vehicules_import,
        **get_sidebar_context(request),
    }
    return render(request, 'flotte/dashboard.html', context)


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
    vehicule = get_object_or_404(
        Vehicule.objects.select_related(
            'marque', 'modele', 'type_vehicule', 'type_carburant', 'type_transmission'
        ).prefetch_related(
            'import_demarches', 'depenses', 'documents', 'reparations', 'locations', 'ventes', 'factures'
        ),
        pk=pk
    )
    total_depenses = vehicule.depenses.aggregate(s=Sum('montant'))['s'] or 0
    total_reparations = vehicule.reparations.aggregate(s=Sum('cout'))['s'] or 0
    cout_total = (vehicule.prix_achat or 0) + total_depenses + total_reparations
    derniere_vente = vehicule.ventes.order_by('-date_vente').first()
    marge = None
    if derniere_vente and derniere_vente.prix_vente:
        marge = derniere_vente.prix_vente - cout_total
    context = {
        'vehicule': vehicule,
        'total_depenses': total_depenses,
        'total_reparations': total_reparations,
        'cout_total': cout_total,
        'derniere_vente': derniere_vente,
        'marge': marge,
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
        return Location.objects.select_related('vehicule__marque', 'vehicule__modele').order_by('-date_debut')

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
    """Fiche location."""
    loc = get_object_or_404(Location.objects.select_related('vehicule'), pk=pk)
    context = {'location': loc, **get_sidebar_context(request)}
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
@method_decorator(login_required, name='dispatch')
class FactureCreateView(ManagerRequiredMixin, CreateView):
    model = Facture
    form_class = FactureForm
    template_name = 'flotte/facture_form.html'
    context_object_name = 'facture'

    def form_valid(self, form):
        form.instance.vehicule_id = self.kwargs['vehicule_pk']
        messages.success(self.request, 'Facture enregistrée.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('flotte:vehicule_detail', args=[self.kwargs['vehicule_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicule'] = get_object_or_404(Vehicule, pk=self.kwargs['vehicule_pk'])
        context['title'] = 'Ajouter une facture'
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


# ——— Ventes (CRUD depuis l'app) ———
@method_decorator(login_required, name='dispatch')
class VenteCreateView(ManagerRequiredMixin, CreateView):
    model = Vente
    form_class = VenteForm
    template_name = 'flotte/vente_form.html'
    context_object_name = 'vente'

    def form_valid(self, form):
        form.instance.vehicule_id = self.kwargs['vehicule_pk']
        messages.success(self.request, 'Vente enregistrée.')
        result = super().form_valid(form)
        # Marquer le véhicule comme vendu
        vehicule = get_object_or_404(Vehicule, pk=self.kwargs['vehicule_pk'])
        vehicule.statut = 'vendu'
        vehicule.save(update_fields=['statut'])
        return result

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
        messages.success(self.request, 'Vente mise à jour.')
        return super().form_valid(form)


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


# ——— Réparations, Documents, Ventes, CA, Maintenance, Carburant, Conducteurs ———
@login_required
def reparations_list(request):
    """Liste des réparations."""
    reps = Reparation.objects.select_related('vehicule').order_by('-date_reparation', '-id')[:200]
    context = {'reparations': reps, **get_sidebar_context(request)}
    return render(request, 'flotte/reparations_list.html', context)


@login_required
def documents_list(request):
    """Documents par véhicule."""
    vehicules = Vehicule.objects.prefetch_related('documents').order_by('marque__nom', 'modele__nom')[:100]
    context = {'vehicules': vehicules, **get_sidebar_context(request)}
    return render(request, 'flotte/documents_list.html', context)


@manager_or_admin_required
def ventes_list(request):
    """Liste des ventes."""
    ventes = Vente.objects.select_related('vehicule').order_by('-date_vente')[:100]
    context = {'ventes': ventes, **get_sidebar_context(request)}
    return render(request, 'flotte/ventes_list.html', context)


def _ca_evolution_queryset(granularite, annee, mois=None):
    """Retourne les valeurs annotées (date/mois/année, total) pour l'évolution du CA."""
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


@manager_or_admin_required
def ca_api_evolution(request):
    """API JSON : évolution du CA par jour / mois / année pour les graphiques."""
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
    nb_ventes = [r['nb'] for r in rows]
    return JsonResponse({'labels': labels, 'data': data, 'nb_ventes': nb_ventes})


@manager_or_admin_required
def ca_view(request):
    """Chiffre d'affaires : KPIs, synthèse des ventes et données pour graphiques."""
    now = timezone.now()
    agg = Vente.objects.aggregate(
        total_ca=Sum('prix_vente'),
        nb_ventes=Count('id'),
        moyenne_vente=Avg('prix_vente'),
    )
    annees = list(range(now.year - 2, now.year + 3))
    context = {
        'total_ca': agg['total_ca'] or Decimal('0'),
        'nb_ventes': agg['nb_ventes'] or 0,
        'moyenne_vente': agg['moyenne_vente'] or Decimal('0'),
        'annee_courante': now.year,
        'mois_courant': now.month,
        'annees': annees,
        **get_sidebar_context(request),
    }
    return render(request, 'flotte/ca.html', context)


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
    """Liste des maintenances préventives."""
    maintenances = Maintenance.objects.select_related('vehicule').order_by('-date_prevue', '-id')[:200]
    context = {
        'maintenances': maintenances,
        **get_sidebar_context(request),
    }
    return render(request, 'flotte/maintenance_list.html', context)


@login_required
def carburant_list(request):
    """Liste des relevés carburant."""
    releves = ReleveCarburant.objects.select_related('vehicule').order_by('-date_releve', '-id')[:200]
    context = {
        'releves': releves,
        **get_sidebar_context(request),
    }
    return render(request, 'flotte/carburant_list.html', context)


@login_required
def conducteurs_list(request):
    """Liste des conducteurs."""
    conducteurs = Conducteur.objects.all().order_by('nom', 'prenom')
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
