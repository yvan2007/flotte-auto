"""
Vues d'authentification personnalisées avec choix d'interface
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator


SESSION_INTERFACE_KEY = 'admin_interface'
INTERFACE_CLASSIC = 'classic'
INTERFACE_MODERN = 'modern'


def get_interface_redirect_url(request, interface):
    """Retourne l'URL de redirection selon l'interface choisie."""
    if interface == INTERFACE_MODERN:
        return reverse('admin:modern_dashboard')
    return reverse('admin:index')


@csrf_protect
@require_http_methods(["GET", "POST"])
def select_interface_login(request):
    """
    Page de connexion avec choix d'interface.
    L'utilisateur sélectionne Classique ou Moderne avant de se connecter.
    """
    if request.user.is_authenticated:
        interface = request.session.get(SESSION_INTERFACE_KEY, INTERFACE_CLASSIC)
        return redirect(get_interface_redirect_url(request, interface))

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        interface = request.POST.get('admin_interface', INTERFACE_CLASSIC)

        if not username or not password:
            return render(request, 'admin_custom/auth/login_with_interface.html', {
                'error_message': 'Veuillez saisir votre nom d\'utilisateur et mot de passe.',
                'username': username,
                'selected_interface': interface,
            })

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active and user.is_staff:
                login(request, user)
                request.session[SESSION_INTERFACE_KEY] = interface
                next_url = request.GET.get('next')
                if next_url:
                    return HttpResponseRedirect(next_url)
                return redirect(get_interface_redirect_url(request, interface))
            else:
                return render(request, 'admin_custom/auth/login_with_interface.html', {
                    'error_message': 'Ce compte n\'a pas les droits d\'accès.',
                    'username': username,
                    'selected_interface': interface,
                })
        else:
            return render(request, 'admin_custom/auth/login_with_interface.html', {
                'error_message': 'Nom d\'utilisateur ou mot de passe incorrect.',
                'username': username,
                'selected_interface': interface,
            })

    return render(request, 'admin_custom/auth/login_with_interface.html', {
        'selected_interface': request.session.get(SESSION_INTERFACE_KEY, INTERFACE_CLASSIC),
    })


@require_http_methods(["GET"])
def switch_interface(request):
    """
    Permet de basculer entre les interfaces.
    URL: /admin/switch-interface/?to=modern ou ?to=classic
    """
    if not request.user.is_authenticated:
        return redirect('admin:login')

    to_interface = request.GET.get('to', INTERFACE_CLASSIC)
    if to_interface not in (INTERFACE_CLASSIC, INTERFACE_MODERN):
        to_interface = INTERFACE_CLASSIC

    request.session[SESSION_INTERFACE_KEY] = to_interface
    return redirect(get_interface_redirect_url(request, to_interface))
