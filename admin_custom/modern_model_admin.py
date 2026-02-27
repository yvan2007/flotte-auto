"""
Mixin pour utiliser les templates Design 1 (moderne) lorsque l'interface moderne est active.
"""
from django.utils.html import format_html
from django.urls import reverse

from .auth_views import SESSION_INTERFACE_KEY, INTERFACE_MODERN


def _use_modern_templates(request):
    return request.session.get(SESSION_INTERFACE_KEY) == INTERFACE_MODERN


class ModernTemplateMixin:
    """
    Mixin à hériter pour les ModelAdmin. Bascule automatiquement vers
    les templates Design 1 (change_list, change_form, object_history)
    lorsque admin_interface=modern dans la session.
    """
    change_list_template = 'admin_custom/change_list.html'

    def get_list_display(self, request):
        """En mode moderne, ajoute une colonne Actions (voir, modifier) avec icônes."""
        list_display = list(super().get_list_display(request))
        if self._use_modern_templates(request) and 'modern_actions' not in list_display:
            list_display.append('modern_actions')
        return list_display

    def modern_actions(self, obj):
        """Colonne Actions : icône œil (voir), crayon (modifier) et corbeille (supprimer) pour chaque enregistrement."""
        if obj is None:
            return ''
        opts = self.model._meta
        change_url = reverse(
            'admin:%s_%s_change' % (opts.app_label, opts.model_name),
            args=[obj.pk],
            current_app=self.admin_site.name
        )
        delete_url = reverse(
            'admin:%s_%s_delete' % (opts.app_label, opts.model_name),
            args=[obj.pk],
            current_app=self.admin_site.name
        )
        view_link = format_html(
            '<a href="{}" title="Voir" class="action-icon view-icon">'
            '<i class="fa-solid fa-eye"></i></a>',
            change_url
        )
        edit_link = format_html(
            '<a href="{}" title="Modifier" class="action-icon edit-icon">'
            '<i class="fa-solid fa-pen"></i></a>',
            change_url
        )
        delete_link = format_html(
            '<a href="{}" title="Supprimer" class="action-icon delete-icon" style="color:var(--color-danger);">'
            '<i class="fa-solid fa-trash"></i></a>',
            delete_url
        )
        return format_html(
            '<span class="modern-row-actions">{} {} {}</span>',
            view_link, edit_link, delete_link
        )

    modern_actions.short_description = 'Actions'
    change_form_template = 'admin_custom/change_form.html'
    object_history_template = 'admin_custom/object_history.html'
    add_form_template = None  # Utilise change_form avec add=True

    # Templates modernes (admin_frontend)
    modern_change_list_template = 'admin_custom/modern/change_list.html'
    modern_change_form_template = 'admin_custom/modern/change_form.html'
    modern_object_history_template = 'admin_custom/modern/object_history.html'
    modern_add_form_template = None  # Surcharge pour User: 'admin_custom/modern/auth/user/add_form.html'
    modern_delete_confirmation_template = 'admin_custom/modern/delete_confirmation.html'
    modern_delete_selected_confirmation_template = 'admin_custom/modern/delete_selected_confirmation.html'

    def _use_modern_templates(self, request):
        return _use_modern_templates(request)

    def changelist_view(self, request, extra_context=None):
        use_modern = self._use_modern_templates(request)
        orig = self.change_list_template
        
        if use_modern:
            self.change_list_template = self.modern_change_list_template
            admin_base_template = 'admin_custom/modern/admin_base.html'
        else:
            self.change_list_template = 'admin_custom/change_list.html'
            admin_base_template = 'admin_custom/base.html'
        
        # Ajouter admin_base_template au contexte
        if extra_context is None:
            extra_context = {}
        extra_context['admin_base_template'] = admin_base_template
        
        try:
            return super().changelist_view(request, extra_context)
        finally:
            self.change_list_template = orig

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        use_modern = self._use_modern_templates(request)
        orig_form = self.change_form_template
        orig_add = self.add_form_template
        
        if use_modern:
            self.change_form_template = self.modern_change_form_template
            admin_base_template = 'admin_custom/modern/admin_base.html'
            if object_id is None and getattr(self, 'modern_add_form_template', None):
                self.add_form_template = self.modern_add_form_template
        else:
            self.change_form_template = 'admin_custom/change_form.html'
            admin_base_template = 'admin_custom/base.html'
        
        # Ajouter admin_base_template au contexte
        if extra_context is None:
            extra_context = {}
        extra_context['admin_base_template'] = admin_base_template
        
        try:
            return super().changeform_view(request, object_id, form_url, extra_context)
        finally:
            self.change_form_template = orig_form
            self.add_form_template = orig_add

    def history_view(self, request, object_id, extra_context=None):
        orig = self.object_history_template
        if self._use_modern_templates(request):
            self.object_history_template = self.modern_object_history_template
        try:
            return super().history_view(request, object_id, extra_context)
        finally:
            self.object_history_template = orig

    def delete_view(self, request, object_id, extra_context=None):
        orig = self.delete_confirmation_template
        if self._use_modern_templates(request):
            self.delete_confirmation_template = self.modern_delete_confirmation_template
        try:
            return super().delete_view(request, object_id, extra_context)
        finally:
            self.delete_confirmation_template = orig
