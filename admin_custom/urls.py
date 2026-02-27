from django.urls import path
from . import views

app_name = 'admin_custom'

urlpatterns = [
    path('api/chart-data/', views.chart_data, name='chart_data'),
    path('api/grid-data/', views.grid_data, name='grid_data'),
    path('api/stats/', views.stats_data, name='stats_data'),
    path('api/model-fields/', views.model_fields, name='model_fields'),
    path('api/grid-model-fields/', views.grid_model_fields, name='grid_model_fields'),
    path('api/dashboard-models/', views.dashboard_models, name='dashboard_models'),
    path('api/dashboard-metrics/', views.dashboard_metrics, name='dashboard_metrics'),
    path('api/dashboard-config/', views.dashboard_config_get, name='dashboard_config_get'),
    path('api/dashboard-config/save/', views.dashboard_config_save, name='dashboard_config_save'),
    path('api/dashboard-charts/', views.dashboard_charts_get, name='dashboard_charts_get'),
    path('api/dashboard-chart/save/', views.dashboard_chart_save, name='dashboard_chart_save'),
    path('api/dashboard-chart/delete/', views.dashboard_chart_delete, name='dashboard_chart_delete'),
]
