"""Mixins pour les vues FLOTTE (restriction admin, manager, user).
Décorateurs et classes pour contrôle d'accès par rôle."""
from functools import wraps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


def user_role(request):
    """Retourne le rôle de l'utilisateur (admin, manager, user)."""
    if not request.user.is_authenticated:
        return None
    if request.user.is_superuser:
        return 'admin'
    if hasattr(request.user, 'profil_flotte'):
        return request.user.profil_flotte.role
    return 'user'


def is_admin(request):
    """True si l'utilisateur a le rôle admin ou est superuser."""
    return request.user.is_authenticated and (
        request.user.is_superuser or user_role(request) == 'admin'
    )


def is_manager_or_admin(request):
    """True si l'utilisateur peut créer/modifier (manager ou admin)."""
    role = user_role(request)
    return request.user.is_authenticated and role in ('admin', 'manager')


class AdminRequiredMixin(LoginRequiredMixin):
    """Vue réservée aux utilisateurs avec rôle admin (ou superuser)."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_superuser or user_role(request) == 'admin'):
            raise PermissionDenied('Accès réservé aux administrateurs.')
        return super().dispatch(request, *args, **kwargs)


class ManagerRequiredMixin(LoginRequiredMixin):
    """Vue réservée aux utilisateurs manager ou admin (création / modification)."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not is_manager_or_admin(request):
            raise PermissionDenied('Accès réservé aux gestionnaires ou administrateurs.')
        return super().dispatch(request, *args, **kwargs)


def manager_or_admin_required(view_func):
    """
    Décorateur pour vues fonction : login requis + rôle manager ou admin.
    Utilisateur simple (user) → 403. Utilisé pour Import, Ventes, CA, Location (liste/détail).
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if not is_manager_or_admin(request):
            raise PermissionDenied(
                'Accès réservé aux gestionnaires ou administrateurs. '
                'En tant qu\'utilisateur, vous pouvez consulter le tableau de bord, le parc, '
                'les réparations, documents, maintenance, carburant et conducteurs.'
            )
        return view_func(request, *args, **kwargs)
    return _wrapped
