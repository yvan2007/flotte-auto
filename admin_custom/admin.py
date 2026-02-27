from django.contrib import admin
from .models import DashboardGrid, DashboardChart, UserDashboardConfig
from .modern_model_admin import ModernTemplateMixin


class DashboardGridAdmin(ModernTemplateMixin, admin.ModelAdmin):
    """
    Admin pour DashboardGrid.
    Note: Le modèle doit être enregistré manuellement avec custom_admin_site
    dans le fichier urls.py du projet, pas via @admin.register.
    """
    list_display = ['name', 'model_name', 'created_at']
    search_fields = ['name', 'description', 'model_name']
    list_filter = ['created_at']


class DashboardChartAdmin(ModernTemplateMixin, admin.ModelAdmin):
    """
    Admin pour DashboardChart.
    Note: Le modèle doit être enregistré manuellement avec custom_admin_site
    dans le fichier urls.py du projet, pas via @admin.register.
    """
    list_display = ['name', 'chart_type', 'model_name', 'field_name', 'frequency', 'created_at']
    search_fields = ['name', 'model_name', 'field_name']
    list_filter = ['chart_type', 'frequency', 'created_at']


class UserDashboardConfigAdmin(admin.ModelAdmin):
    """Admin en lecture pour la config tableau de bord par utilisateur."""
    list_display = ['user', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['user__username']
    readonly_fields = ['user', 'metrics_config', 'updated_at']

    def has_add_permission(self, request):
        return False
