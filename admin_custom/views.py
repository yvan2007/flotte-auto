from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Sum, Avg, Count
from django.apps import apps
from datetime import timedelta, datetime
from decimal import Decimal
import json


def get_model_class(model_name):
    """
    Retourne la classe du modèle à partir de son nom.
    Utilise l'auto-découverte Django pour trouver le modèle.
    """
    # Parcourir toutes les apps pour trouver le modèle
    for app_config in apps.get_app_configs():
        try:
            model = app_config.get_model(model_name)
            if model:
                return model
        except LookupError:
            # Le modèle n'existe pas dans cette app, continuer
            continue
    
    # Si le modèle n'est pas trouvé, essayer avec le nom complet app.ModelName
    if '.' in model_name:
        try:
            app_label, model_name_only = model_name.split('.', 1)
            app_config = apps.get_app_config(app_label)
            return app_config.get_model(model_name_only)
        except (LookupError, ValueError):
            pass
    
    return None


@require_http_methods(["GET"])
def chart_data(request):
    """API pour récupérer les données de graphique"""
    model_name = request.GET.get('model')
    field_name = request.GET.get('field')
    chart_type = request.GET.get('type', 'line')
    frequency = request.GET.get('frequency', 'month')
    operation = request.GET.get('operation', 'sum')
    
    if not model_name or not field_name:
        return JsonResponse({'error': 'Model and field are required'}, status=400)
    
    model_class = get_model_class(model_name)
    if not model_class:
        return JsonResponse({'error': 'Invalid model'}, status=400)
    
    # Vérifier que le champ existe
    try:
        # Créer une instance pour vérifier les champs
        instance = model_class()
        if not hasattr(instance, field_name):
            # Liste des champs disponibles
            available_fields = [f.name for f in model_class._meta.get_fields() if hasattr(f, 'name')]
            numeric_fields = []
            for field in model_class._meta.get_fields():
                if hasattr(field, 'name'):
                    field_obj = model_class._meta.get_field(field.name)
                    if hasattr(field_obj, 'get_internal_type'):
                        field_type = field_obj.get_internal_type()
                        if field_type in ['DecimalField', 'FloatField', 'IntegerField', 'PositiveIntegerField', 'BigIntegerField']:
                            numeric_fields.append(field.name)
            
            return JsonResponse({
                'error': f'Le champ "{field_name}" n\'existe pas sur le modèle {model_name}',
                'available_fields': numeric_fields,
                'suggestion': numeric_fields[0] if numeric_fields else None
            }, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Erreur lors de la vérification du champ: {str(e)}'}, status=400)
    
    # Calculer la période selon la fréquence
    now = timezone.now()
    periods_map = {
        'day': 30,
        'week': 12,
        'month': 12,
        'quarter': 8,
        'year': 5,
    }
    periods = periods_map.get(frequency, 12)
    
    # Récupérer les données
    data = []
    labels = []
    
    for i in range(periods - 1, -1, -1):
        if frequency == 'day':
            start = now - timedelta(days=i+1)
            end = now - timedelta(days=i)
            label = start.strftime('%d/%m')
        elif frequency == 'week':
            start = now - timedelta(weeks=i+1)
            end = now - timedelta(weeks=i)
            label = f"Sem {start.isocalendar()[1]}"
        elif frequency == 'month':
            # Calculer le début du mois
            month_start = now.month - i - 1
            year = now.year
            while month_start < 1:
                month_start += 12
                year -= 1
            start = timezone.make_aware(datetime(year, month_start, 1))
            month_end = now.month - i
            year_end = now.year
            while month_end < 1:
                month_end += 12
                year_end -= 1
            end = timezone.make_aware(datetime(year_end, month_end, 1))
            label = start.strftime('%m/%Y')
        elif frequency == 'quarter':
            quarter = ((now.month - 1) // 3) - i
            year = now.year
            while quarter < 0:
                quarter += 4
                year -= 1
            month_start = (quarter * 3) + 1
            start = timezone.make_aware(datetime(year, month_start, 1))
            label = f"T{quarter + 1} {year}"
            end = start + timedelta(days=90)
        else:  # year
            year = now.year - i
            start = timezone.make_aware(datetime(year, 1, 1))
            end = timezone.make_aware(datetime(year + 1, 1, 1))
            label = str(year)
        
        # Filtrer les données pour cette période
        queryset = model_class.objects.filter(created_at__gte=start, created_at__lt=end)
        
        # Appliquer l'opération
        if operation == 'sum':
            try:
                from django.db.models import Sum
                result = queryset.aggregate(sum=Sum(field_name))
                value = float(result['sum'] or 0)
            except:
                value = 0
        elif operation == 'avg':
            try:
                from django.db.models import Avg
                result = queryset.aggregate(avg=Avg(field_name))
                value = float(result['avg'] or 0)
            except:
                value = 0
        elif operation == 'count':
            value = queryset.count()
        else:
            value = queryset.count()
        
        data.append(value)
        labels.append(label)
    
    return JsonResponse({
        'labels': labels,
        'data': data,
        'chart_type': chart_type
    })


def _get_grid_columns_for_model(model_class):
    """Retourne tous les champs concrets du modèle (id, nom, slug, description, catégorie, prix, stock, etc.).
    Utilise concrete_fields directement comme pour Order/Invoice qui fonctionnent bien."""
    return [f.name for f in model_class._meta.concrete_fields]


@require_http_methods(["GET"])
def grid_data(request):
    """API pour récupérer les données de grille. Utilise toujours tous les champs concrets du modèle pour garantir l'affichage complet."""
    grid_id = request.GET.get('grid_id')
    model_name = request.GET.get('model')
    requested_columns = request.GET.getlist('columns')
    
    if not model_name:
        return JsonResponse({'error': 'Model is required'}, status=400)
    
    model_class = get_model_class(model_name)
    if not model_class:
        return JsonResponse({'error': 'Invalid model'}, status=400)
    
    # TOUJOURS utiliser tous les champs concrets du modèle pour garantir l'affichage complet
    # (comme Order/Invoice qui fonctionnent bien)
    columns = _get_grid_columns_for_model(model_class)
    if not columns:
        columns = ['pk']
    
    # Récupérer les données
    queryset = model_class.objects.all()
    
    # Construire les données
    data = []
    for obj in queryset[:100]:  # Limiter à 100 résultats
        row = {}
        for col in columns:
            if hasattr(obj, col):
                value = getattr(obj, col)
                # Convertir les objets en string (FK, dates, etc.)
                if hasattr(value, '__str__') and not isinstance(value, (int, float, type(None), bool)):
                    row[col] = str(value)
                else:
                    row[col] = value
            else:
                row[col] = '-'
        data.append(row)
    
    return JsonResponse({
        'data': data,
        'columns': columns
    })


@require_http_methods(["GET"])
def stats_data(request):
    """API pour récupérer les statistiques rapides - utilise l'auto-découverte"""
    from django.db.models import Sum
    from django.apps import apps
    
    stats = {}
    total_revenue = 0
    
    # Parcourir tous les modèles pour détecter automatiquement ceux avec des données
    for app_config in apps.get_app_configs():
        # Ignorer les apps Django internes
        if app_config.name.startswith('django.contrib'):
            continue
        
        for model in app_config.get_models():
            if model._meta.abstract or model._meta.proxy:
                continue
            
            model_name = model.__name__.lower()
            
            # Chercher des champs de montant pour calculer les revenus
            if hasattr(model, 'total_amount'):
                count = model.objects.count()
                revenue = float(model.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0)
                stats[model_name] = count
                total_revenue += revenue
            elif hasattr(model, 'amount'):
                count = model.objects.count()
                revenue = float(model.objects.aggregate(Sum('amount'))['amount__sum'] or 0)
                stats[model_name] = count
                total_revenue += revenue
            else:
                # Compter simplement le nombre d'objets
                count = model.objects.count()
                if count > 0:
                    stats[model_name] = count
    
    # Ajouter le revenu total
    stats['revenue'] = total_revenue
    
    # Garder la compatibilité avec l'ancien format pour l'index.html
    # On essaie de trouver les modèles courants
    order_model = get_model_class('Order')
    invoice_model = get_model_class('Invoice')
    payment_model = get_model_class('Payment')
    product_model = get_model_class('Product')
    
    result = {
        'orders': order_model.objects.count() if order_model else 0,
        'invoices': invoice_model.objects.count() if invoice_model else 0,
        'payments': payment_model.objects.count() if payment_model else 0,
        'products': product_model.objects.count() if product_model else 0,
        'revenue': total_revenue,
    }
    
    return JsonResponse(result)


@require_http_methods(["GET"])
def model_fields(request):
    """API pour récupérer les champs numériques d'un modèle (graphiques)."""
    model_name = request.GET.get('model')
    
    if not model_name:
        return JsonResponse({'error': 'Model name is required'}, status=400)
    
    model_class = get_model_class(model_name)
    if not model_class:
        return JsonResponse({'error': f'Model "{model_name}" not found'}, status=404)
    
    # Détecter les champs numériques
    numeric_fields = []
    for field in model_class._meta.get_fields():
        if hasattr(field, 'name'):
            try:
                field_obj = model_class._meta.get_field(field.name)
                if hasattr(field_obj, 'get_internal_type'):
                    field_type = field_obj.get_internal_type()
                    if field_type in ['DecimalField', 'FloatField', 'IntegerField', 
                                     'PositiveIntegerField', 'BigIntegerField', 'SmallIntegerField']:
                        numeric_fields.append(field.name)
            except Exception:
                continue
    
    return JsonResponse({
        'model': model_name,
        'fields': numeric_fields,
    })


@require_http_methods(["GET"])
def grid_model_fields(request):
    """API pour récupérer tous les champs d'un modèle (grilles)."""
    model_name = request.GET.get('model')
    if not model_name:
        return JsonResponse({'error': 'Model name is required'}, status=400)
    model_class = get_model_class(model_name)
    if not model_class:
        return JsonResponse({'error': f'Model "{model_name}" not found'}, status=404)
    fields = _get_grid_columns_for_model(model_class)
    if not fields:
        fields = ['pk']
    return JsonResponse({'model': model_name, 'fields': fields})


def _get_numeric_fields_for_dashboard(model):
    """Retourne les champs numériques d'un modèle (pour dashboard)."""
    result = []
    for field in model._meta.get_fields():
        if hasattr(field, 'name'):
            try:
                field_obj = model._meta.get_field(field.name)
                if hasattr(field_obj, 'get_internal_type'):
                    ft = field_obj.get_internal_type()
                    if ft in ('DecimalField', 'IntegerField', 'FloatField', 'BigIntegerField',
                              'PositiveIntegerField', 'SmallIntegerField'):
                        result.append(field.name)
            except Exception:
                pass
    return result


@staff_member_required
@require_http_methods(["GET"])
def dashboard_models(request):
    """Retourne la liste des modèles avec leurs champs numériques."""
    result = []
    for app_config in apps.get_app_configs():
        if app_config.name in ('contenttypes', 'sessions', 'admin', 'auth', 'messages', 'staticfiles'):
            continue
        for model in app_config.get_models():
            if model._meta.abstract or model._meta.proxy:
                continue
            numeric_fields = _get_numeric_fields_for_dashboard(model)
            result.append({
                'app': app_config.label,
                'model': model.__name__,
                'verbose_name': str(model._meta.verbose_name),
                'numeric_fields': numeric_fields,
            })
    return JsonResponse({'models': result})


@staff_member_required
@require_http_methods(["GET", "POST"])
def dashboard_metrics(request):
    """Calcule les métriques (count, sum, avg) à partir d'une config JSON."""
    if request.method == 'GET':
        config_raw = request.GET.get('config', '[]')
        try:
            config = json.loads(config_raw) if config_raw else []
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON invalide'}, status=400)
    else:
        try:
            body = json.loads(request.body) if request.body else {}
            config = body.get('config', [])
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON invalide'}, status=400)

    if not isinstance(config, list):
        return JsonResponse({'error': 'config doit être une liste'}, status=400)

    results = []
    for item in config:
        if not isinstance(item, dict):
            continue
        app = item.get('app')
        model_name = item.get('model')
        metric_type = item.get('type', 'count')
        field = item.get('field')
        label = item.get('label', '')

        if not app or not model_name:
            continue

        try:
            model = apps.get_model(app, model_name)
        except LookupError:
            continue

        numeric_fields = _get_numeric_fields_for_dashboard(model)

        if metric_type == 'count':
            value = model.objects.count()
        elif metric_type == 'sum' and field and field in numeric_fields:
            agg = model.objects.aggregate(v=Sum(field))
            value = agg['v'] or 0
            if hasattr(value, '__float__'):
                value = float(value)
        elif metric_type == 'avg' and field and field in numeric_fields:
            agg = model.objects.aggregate(v=Avg(field))
            value = round(float(agg['v'] or 0), 2)
        else:
            continue

        admin_url = ''
        try:
            admin_url = reverse(
                f'admin:{model._meta.app_label}_{model._meta.model_name}_changelist'
            )
        except Exception:
            pass

        results.append({
            'label': label or f"{model._meta.verbose_name} ({metric_type})",
            'value': value,
            'admin_url': admin_url,
        })

    return JsonResponse({'metrics': results})


def _default_metrics_config():
    """Config par défaut des indicateurs (même structure que le modèle)."""
    from .models import default_dashboard_metrics_config
    return default_dashboard_metrics_config()


@staff_member_required
@require_http_methods(["GET"])
def dashboard_config_get(request):
    """Retourne la configuration des indicateurs du tableau de bord pour l'utilisateur connecté."""
    from .models import UserDashboardConfig
    try:
        config_obj = UserDashboardConfig.objects.get(user=request.user)
        config = config_obj.metrics_config
        if not isinstance(config, list) or len(config) == 0:
            config = _default_metrics_config()
    except UserDashboardConfig.DoesNotExist:
        config = _default_metrics_config()
    return JsonResponse({'config': config})


@staff_member_required
@require_http_methods(["POST"])
def dashboard_config_save(request):
    """Enregistre la configuration des indicateurs du tableau de bord pour l'utilisateur connecté."""
    from .models import UserDashboardConfig
    try:
        body = json.loads(request.body) if request.body else {}
        config = body.get('config', [])
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)
    if not isinstance(config, list):
        return JsonResponse({'error': 'config doit être une liste'}, status=400)
    obj, _ = UserDashboardConfig.objects.update_or_create(
        user=request.user,
        defaults={'metrics_config': config},
    )
    return JsonResponse({'ok': True, 'config': obj.metrics_config})


@staff_member_required
@require_http_methods(["GET"])
def dashboard_charts_get(request):
    """Retourne tous les graphiques sauvegardés pour l'utilisateur connecté."""
    from .models import DashboardChart
    charts = DashboardChart.objects.filter(user=request.user).order_by('-created_at')
    charts_data = []
    for chart in charts:
        charts_data.append({
            'id': chart.id,
            'name': chart.name,
            'chart_type': chart.chart_type,
            'model_name': chart.model_name,
            'field_name': chart.field_name,
            'frequency': chart.frequency,
            'operation': chart.operation,
        })
    return JsonResponse({'charts': charts_data})


@staff_member_required
@require_http_methods(["POST"])
def dashboard_chart_save(request):
    """Enregistre un graphique pour l'utilisateur connecté."""
    from .models import DashboardChart
    try:
        body = json.loads(request.body) if request.body else {}
        name = body.get('name', '').strip()
        chart_type = body.get('chart_type', 'line')
        model_name = body.get('model_name', '')
        field_name = body.get('field_name', '')
        frequency = body.get('frequency', 'month')
        operation = body.get('operation', 'sum')
        chart_id = body.get('id')  # Pour la mise à jour
        
        if not name or not model_name or not field_name:
            return JsonResponse({'error': 'Nom, modèle et champ sont requis'}, status=400)
        
        if chart_id:
            # Mise à jour
            try:
                chart = DashboardChart.objects.get(id=chart_id, user=request.user)
                chart.name = name
                chart.chart_type = chart_type
                chart.model_name = model_name
                chart.field_name = field_name
                chart.frequency = frequency
                chart.operation = operation
                chart.save()
            except DashboardChart.DoesNotExist:
                return JsonResponse({'error': 'Graphique non trouvé'}, status=404)
        else:
            # Création
            chart, created = DashboardChart.objects.get_or_create(
                name=name,
                user=request.user,
                defaults={
                    'chart_type': chart_type,
                    'model_name': model_name,
                    'field_name': field_name,
                    'frequency': frequency,
                    'operation': operation,
                }
            )
            if not created:
                return JsonResponse({'error': 'Un graphique avec ce nom existe déjà'}, status=400)
        
        return JsonResponse({
            'ok': True,
            'chart': {
                'id': chart.id,
                'name': chart.name,
                'chart_type': chart.chart_type,
                'model_name': chart.model_name,
                'field_name': chart.field_name,
                'frequency': chart.frequency,
                'operation': chart.operation,
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@staff_member_required
@require_http_methods(["POST"])
def dashboard_chart_delete(request):
    """Supprime un graphique pour l'utilisateur connecté."""
    from .models import DashboardChart
    try:
        body = json.loads(request.body) if request.body else {}
        chart_id = body.get('id')
        
        if not chart_id:
            return JsonResponse({'error': 'ID du graphique requis'}, status=400)
        
        try:
            chart = DashboardChart.objects.get(id=chart_id, user=request.user)
            chart.delete()
            return JsonResponse({'ok': True})
        except DashboardChart.DoesNotExist:
            return JsonResponse({'error': 'Graphique non trouvé'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)
