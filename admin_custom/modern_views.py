"""
Vues pour l'interface Moderne (Design 1)
"""
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.apps import apps

from .auth_views import SESSION_INTERFACE_KEY, INTERFACE_MODERN, INTERFACE_CLASSIC
from .autodiscover import get_all_models_for_charts, get_all_models_for_grids


def get_custom_admin_site():
    from .admin_site import custom_admin_site
    return custom_admin_site


def _ensure_modern_interface(request):
    """Redirige vers l'interface classique si l'utilisateur a choisi classique."""
    if request.session.get(SESSION_INTERFACE_KEY) != INTERFACE_MODERN:
        return redirect('admin:index')
    return None


def _get_modern_context(request, extra=None):
    context = get_custom_admin_site().each_context(request)
    context['user_display'] = request.user.get_short_name() or request.user.get_username()
    context['user_initial'] = (context['user_display'][0] if context['user_display'] else 'A').upper()
    context['switch_to_classic_url'] = '/admin/switch-interface/?to=classic'
    context['switch_to_modern_url'] = '/admin/switch-interface/?to=modern'
    context['current_interface'] = request.session.get(SESSION_INTERFACE_KEY, INTERFACE_CLASSIC)
    if extra:
        context.update(extra)
    return context


@staff_member_required
def modern_dashboard(request):
    """Tableau de bord interface moderne."""
    redirect_check = _ensure_modern_interface(request)
    if redirect_check:
        return redirect_check

    # Stats - même logique que l'API stats
    from .views import get_model_class
    order_model = get_model_class('Order')
    invoice_model = get_model_class('Invoice')
    payment_model = get_model_class('Payment')
    product_model = get_model_class('Product')

    stats = {
        'orders': order_model.objects.count() if order_model else 0,
        'invoices': invoice_model.objects.count() if invoice_model else 0,
        'payments': payment_model.objects.count() if payment_model else 0,
        'products': product_model.objects.count() if product_model else 0,
        'revenue': 0,
    }

    total_revenue = 0
    for app_config in apps.get_app_configs():
        if app_config.name.startswith('django.contrib'):
            continue
        for model in app_config.get_models():
            if model._meta.abstract or model._meta.proxy:
                continue
            if hasattr(model, 'total_amount'):
                total_revenue += float(model.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0)
            elif hasattr(model, 'amount'):
                total_revenue += float(model.objects.aggregate(Sum('amount'))['amount__sum'] or 0)
    stats['revenue'] = total_revenue

    context = _get_modern_context(request, {
        'title': 'Tableau de bord',
        'page': 'dashboard',
        'stats': stats,
        'app_list': get_custom_admin_site().get_app_list(request),
    })
    return render(request, 'admin_custom/modern/dashboard.html', context)


@staff_member_required
def modern_charts(request):
    """Graphiques - interface moderne."""
    redirect_check = _ensure_modern_interface(request)
    if redirect_check:
        return redirect_check

    models = get_all_models_for_charts()
    context = _get_modern_context(request, {
        'title': 'Graphiques',
        'page': 'charts',
        'models': models,
        'app_list': get_custom_admin_site().get_app_list(request),
    })
    return render(request, 'admin_custom/modern/charts.html', context)


@staff_member_required
def modern_grids(request):
    """Grilles - interface moderne."""
    redirect_check = _ensure_modern_interface(request)
    if redirect_check:
        return redirect_check

    models = get_all_models_for_grids()
    context = _get_modern_context(request, {
        'title': 'Grilles de données',
        'page': 'grids',
        'models': models,
        'app_list': get_custom_admin_site().get_app_list(request),
    })
    return render(request, 'admin_custom/modern/grids.html', context)


@staff_member_required
def modern_settings(request):
    """Paramètres - accessible depuis les deux interfaces pour changer d'interface."""
    # Pas de redirection : la page paramètres doit être accessible pour changer d'interface

    context = _get_modern_context(request, {
        'title': 'Paramètres',
        'page': 'settings',
        'app_list': get_custom_admin_site().get_app_list(request),
    })
    return render(request, 'admin_custom/modern/settings.html', context)
