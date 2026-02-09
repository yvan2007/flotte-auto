"""
API JSON FLOTTE — endpoints pour parc, ventes, CA, dashboard, paramétrage.
Tous les endpoints nécessitent une authentification (session).
"""
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Count, Sum, Avg, Q

from .models import (
    Marque, Modele, Vehicule, Vente, Conducteur,
    Location, ReleveCarburant, Maintenance,
)
from .mixins import manager_or_admin_required


@login_required
def api_index(request):
    """GET /api/ — En navigateur : redirection vers api/v1/ (browsable API DRF). En JSON : index des endpoints."""
    # Navigateur (Accept: text/html) → rediriger vers l'interface REST Framework
    accept = request.META.get('HTTP_ACCEPT', '')
    if 'text/html' in accept and 'application/json' not in accept:
        return redirect('flotte:api-root')
    # Sinon (client API, ?format=json, etc.) → renvoyer l'index JSON
    base = request.build_absolute_uri('/').rstrip('/')
    return JsonResponse({
        'message': 'API FLOTTE — authentification requise (session).',
        'endpoints': {
            'api_legere': {
                'marques': f'{base}/api/marques/',
                'modeles_par_marque': f'{base}/api/modeles-par-marque/?marque_id=<id>',
                'vehicules': f'{base}/api/vehicules/',
                'vehicules_detail': f'{base}/api/vehicules/<id>/',
                'ventes': f'{base}/api/ventes/',
                'ca_synthese': f'{base}/api/ca/synthese/',
                'dashboard_kpis': f'{base}/api/dashboard/kpis/',
                'conducteurs': f'{base}/api/conducteurs/',
                'locations': f'{base}/api/locations/',
            },
            'api_rest_framework_v1': f'{base}/api/v1/',
            'ca_evolution': f'{base}/ca/api/evolution/?granularite=mois&annee=2025',
        },
    })


def _serialize_vehicule(v):
    """Convertit un véhicule en dict JSON-serializable."""
    return {
        'id': v.id,
        'numero_chassis': v.numero_chassis,
        'libelle_court': v.libelle_court,
        'marque': v.marque.nom if v.marque else None,
        'modele': v.modele.nom if v.modele else None,
        'annee': v.annee,
        'statut': v.statut,
        'numero_immatriculation': v.numero_immatriculation or '',
        'date_entree_parc': v.date_entree_parc.isoformat() if v.date_entree_parc else None,
        'kilometrage_actuel': v.kilometrage_actuel,
        'prix_achat': float(v.prix_achat) if v.prix_achat else None,
    }


@login_required
def api_marques_list(request):
    """GET /api/marques/ — Liste des marques (id, nom) pour formulaires."""
    marques = list(Marque.objects.filter(archive=False).order_by('nom').values('id', 'nom'))
    return JsonResponse({'marques': marques})


@login_required
def api_vehicules_list(request):
    """GET /api/vehicules/ — Liste des véhicules (résumé). Query: statut, q, limit."""
    qs = Vehicule.objects.select_related('marque', 'modele').order_by('-date_entree_parc', '-id')
    statut = request.GET.get('statut', '').strip()
    if statut and statut in ('parc', 'import', 'vendu'):
        qs = qs.filter(statut=statut)
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(numero_chassis__icontains=q) |
            Q(numero_immatriculation__icontains=q) |
            Q(marque__nom__icontains=q) |
            Q(modele__nom__icontains=q)
        )
    try:
        limit = min(int(request.GET.get('limit', 50)), 200)
    except (TypeError, ValueError):
        limit = 50
    qs = qs[:limit]
    data = [_serialize_vehicule(v) for v in qs]
    return JsonResponse({'vehicules': data, 'count': len(data)})


@login_required
def api_vehicule_detail(request, pk):
    """GET /api/vehicules/<id>/ — Détail d'un véhicule."""
    v = get_object_or_404(Vehicule.objects.select_related(
        'marque', 'modele', 'type_vehicule', 'type_carburant', 'type_transmission'
    ), pk=pk)
    data = _serialize_vehicule(v)
    data.update({
        'couleur_exterieure': v.couleur_exterieure or '',
        'couleur_interieure': v.couleur_interieure or '',
        'km_entree': v.km_entree,
        'origine_pays': v.origine_pays or '',
        'etat_entree': v.etat_entree or '',
        'date_premiere_immat': v.date_premiere_immat.isoformat() if v.date_premiere_immat else None,
        'nb_documents': v.documents.count(),
        'nb_reparations': v.reparations.count(),
        'nb_ventes': v.ventes.count(),
    })
    return JsonResponse(data)


@manager_or_admin_required
def api_ventes_list(request):
    """GET /api/ventes/ — Liste des ventes (manager/admin). Query: limit."""
    qs = Vente.objects.select_related('vehicule').order_by('-date_vente')
    try:
        limit = min(int(request.GET.get('limit', 50)), 200)
    except (TypeError, ValueError):
        limit = 50
    qs = qs[:limit]
    data = [
        {
            'id': v.id,
            'vehicule_id': v.vehicule_id,
            'vehicule': v.vehicule.libelle_court,
            'date_vente': v.date_vente.isoformat(),
            'acquereur': v.acquereur or '',
            'prix_vente': float(v.prix_vente) if v.prix_vente else None,
            'km_vente': v.km_vente,
        }
        for v in qs
    ]
    return JsonResponse({'ventes': data, 'count': len(data)})


@manager_or_admin_required
def api_ca_synthese(request):
    """GET /api/ca/synthese/ — Synthèse CA : total, nb_ventes, moyenne."""
    agg = Vente.objects.aggregate(
        total_ca=Sum('prix_vente'),
        nb_ventes=Count('id'),
        moyenne_vente=Avg('prix_vente'),
    )
    return JsonResponse({
        'total_ca': float(agg['total_ca'] or 0),
        'nb_ventes': agg['nb_ventes'] or 0,
        'moyenne_vente': float(agg['moyenne_vente'] or 0),
    })


@login_required
def api_dashboard_kpis(request):
    """GET /api/dashboard/kpis/ — KPIs tableau de bord (parc, import, vendus, total)."""
    qs = Vehicule.objects.all()
    parc = qs.filter(statut='parc').count()
    import_ = qs.filter(statut='import').count()
    vendus = qs.filter(statut='vendu').count()
    total = qs.count()
    return JsonResponse({
        'parc': parc,
        'import': import_,
        'vendus': vendus,
        'total': total,
    })


@login_required
def api_conducteurs_list(request):
    """GET /api/conducteurs/ — Liste des conducteurs (id, nom, prenom, email, actif)."""
    qs = Conducteur.objects.all().order_by('nom', 'prenom')
    data = [
        {
            'id': c.id,
            'nom': c.nom,
            'prenom': c.prenom,
            'email': c.email or '',
            'telephone': c.telephone or '',
            'actif': c.actif,
        }
        for c in qs
    ]
    return JsonResponse({'conducteurs': data, 'count': len(data)})


@login_required
def api_locations_list(request):
    """GET /api/locations/ — Liste des locations (résumé). Query: statut, limit."""
    qs = Location.objects.select_related('vehicule').order_by('-date_debut')
    statut = request.GET.get('statut', '').strip()
    if statut and statut in ('en_cours', 'a_venir', 'termine'):
        qs = qs.filter(statut=statut)
    try:
        limit = min(int(request.GET.get('limit', 50)), 200)
    except (TypeError, ValueError):
        limit = 50
    qs = qs[:limit]
    data = [
        {
            'id': loc.id,
            'vehicule_id': loc.vehicule_id,
            'vehicule': loc.vehicule.libelle_court,
            'locataire': loc.locataire,
            'type_location': loc.type_location,
            'date_debut': loc.date_debut.isoformat(),
            'date_fin': loc.date_fin.isoformat(),
            'statut': loc.statut,
            'loyer_mensuel': float(loc.loyer_mensuel) if loc.loyer_mensuel else None,
        }
        for loc in qs
    ]
    return JsonResponse({'locations': data, 'count': len(data)})
