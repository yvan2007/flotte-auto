from django.db import models
from django.contrib.auth.models import User


def default_dashboard_metrics_config():
    """
    Configuration par défaut des indicateurs du tableau de bord.
    Liste vide pour rester indépendant du type de projet (e-commerce, blog, etc.).
    L'utilisateur choisit ses indicateurs via « Personnaliser l'affichage ».
    """
    return []


class UserDashboardConfig(models.Model):
    """Configuration des indicateurs du tableau de bord par utilisateur (sauvegardée en base)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dashboard_config')
    metrics_config = models.JSONField(default=default_dashboard_metrics_config)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuration tableau de bord"
        verbose_name_plural = "Configurations tableau de bord"

    def __str__(self):
        return f"Config dashboard — {self.user.get_username()}"


class DashboardGrid(models.Model):
    """Grille de données configurable pour le dashboard"""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    model_name = models.CharField(max_length=200)  # Nom du modèle Django
    columns = models.JSONField(default=list)  # Liste des colonnes à afficher
    filters = models.JSONField(default=dict, blank=True)  # Filtres à appliquer
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Grille de données"
        verbose_name_plural = "Grilles de données"


class DashboardChart(models.Model):
    """Configuration de graphique pour le dashboard"""
    CHART_TYPES = [
        ('line', 'Courbe'),
        ('bar', 'Histogramme'),
        ('pie', 'Camembert'),
        ('doughnut', 'Donut'),
        ('area', 'Aire'),
    ]
    
    FREQUENCY_CHOICES = [
        ('day', 'Jour'),
        ('week', 'Semaine'),
        ('month', 'Mois'),
        ('quarter', 'Trimestre'),
        ('year', 'Année'),
    ]

    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_charts', null=True, blank=True)
    chart_type = models.CharField(max_length=20, choices=CHART_TYPES, default='line')
    model_name = models.CharField(max_length=200)  # Nom du modèle principal
    field_name = models.CharField(max_length=200)  # Champ à analyser
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='month')
    operation = models.CharField(max_length=20, default='sum', blank=True)  # sum, avg, count, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_chart_type_display()})"

    class Meta:
        verbose_name = "Graphique"
        verbose_name_plural = "Graphiques"
        unique_together = [['name', 'user']]  # Un nom unique par utilisateur
