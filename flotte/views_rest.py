"""
Vues Django REST Framework — ViewSets pour l'API FLOTTE (api/v1/).
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum, Avg
from django.utils import timezone

from .models import Marque, Modele, Vehicule, Vente, Location, Conducteur
from .serializers import (
    MarqueSerializer, ModeleSerializer,
    VehiculeListSerializer, VehiculeDetailSerializer,
    VenteListSerializer, VenteSerializer,
    LocationListSerializer, LocationSerializer,
    ConducteurSerializer,
)
from .permissions import IsManagerOrAdmin
from .views import _ca_evolution_queryset


class MarqueViewSet(viewsets.ReadOnlyModelViewSet):
    """Marques — liste et détail (lecture seule)."""
    queryset = Marque.objects.all().order_by('nom')
    serializer_class = MarqueSerializer


class ModeleViewSet(viewsets.ReadOnlyModelViewSet):
    """Modèles — liste et détail (lecture seule)."""
    queryset = Modele.objects.select_related('marque').all().order_by('marque__nom', 'nom')
    serializer_class = ModeleSerializer


class VehiculeViewSet(viewsets.ReadOnlyModelViewSet):
    """Véhicules — liste et détail (lecture seule). Query: ?q=, ?statut=parc|import|vendu."""
    queryset = Vehicule.objects.select_related(
        'marque', 'modele', 'type_vehicule', 'type_carburant', 'type_transmission'
    ).order_by('-date_entree_parc', '-id')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return VehiculeDetailSerializer
        return VehiculeListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get('q', '').strip()
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(numero_chassis__icontains=q) |
                Q(numero_immatriculation__icontains=q) |
                Q(marque__nom__icontains=q) |
                Q(modele__nom__icontains=q)
            )
        statut = self.request.query_params.get('statut', '').strip()
        if statut in ('parc', 'import', 'vendu'):
            qs = qs.filter(statut=statut)
        return qs


class VenteViewSet(viewsets.ReadOnlyModelViewSet):
    """Ventes — liste et détail (manager/admin, lecture seule)."""
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]
    queryset = Vente.objects.select_related('vehicule').order_by('-date_vente')
    serializer_class = VenteListSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return VenteSerializer
        return VenteListSerializer


class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    """Locations — liste et détail (lecture seule)."""
    queryset = Location.objects.select_related('vehicule').order_by('-date_debut')
    serializer_class = LocationListSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LocationSerializer
        return LocationListSerializer


class ConducteurViewSet(viewsets.ReadOnlyModelViewSet):
    """Conducteurs — liste et détail (lecture seule)."""
    queryset = Conducteur.objects.all().order_by('nom', 'prenom')
    serializer_class = ConducteurSerializer


class CAViewSet(viewsets.ViewSet):
    """Chiffre d'affaires — synthèse et évolution (manager/admin)."""
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def list(self, request):
        """GET /api/v1/ca/ — Synthèse CA (total, nb_ventes, moyenne)."""
        agg = Vente.objects.aggregate(
            total_ca=Sum('prix_vente'),
            nb_ventes=Count('id'),
            moyenne_vente=Avg('prix_vente'),
        )
        return Response({
            'total_ca': float(agg['total_ca'] or 0),
            'nb_ventes': agg['nb_ventes'] or 0,
            'moyenne_vente': float(agg['moyenne_vente'] or 0),
        })

    @action(detail=False, methods=['get'], url_path='evolution')
    def evolution(self, request):
        """GET /api/v1/ca/evolution/?granularite=mois&annee=2025"""
        granularite = request.query_params.get('granularite', 'mois')
        if granularite not in ('jour', 'mois', 'annee'):
            granularite = 'mois'
        try:
            annee = int(request.query_params.get('annee', timezone.now().year))
        except (TypeError, ValueError):
            annee = timezone.now().year
        mois = request.query_params.get('mois')
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
        return Response({'labels': labels, 'data': data, 'nb_ventes': nb_ventes})


class DashboardViewSet(viewsets.ViewSet):
    """Tableau de bord — KPIs (lecture seule)."""

    def list(self, request):
        """GET /api/v1/dashboard/ — KPIs (parc, import, vendus, total)."""
        qs = Vehicule.objects.all()
        parc = qs.filter(statut='parc').count()
        import_ = qs.filter(statut='import').count()
        vendus = qs.filter(statut='vendu').count()
        total = qs.count()
        return Response({
            'parc': parc,
            'import': import_,
            'vendus': vendus,
            'total': total,
        })
