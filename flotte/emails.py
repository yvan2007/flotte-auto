"""Envoi d'emails FLOTTE — bienvenue, notifications (templates HTML)."""
import logging
import sys
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.sites.models import Site

logger = logging.getLogger(__name__)


def _get_base_url():
    """URL de base de l'application (pour liens dans les emails)."""
    domain = getattr(settings, 'EMAIL_DOMAIN', None)
    if not domain:
        try:
            site = Site.objects.get_current()
            domain = site.domain
        except Exception:
            domain = '127.0.0.1:8000'
    protocol = 'https' if not getattr(settings, 'DEBUG', True) else 'http'
    if domain.startswith('http://') or domain.startswith('https://'):
        return domain.rstrip('/')
    return f'{protocol}://{domain}'.rstrip('/')


def send_mail_html(subject, body_html, to_emails, body_text=None, from_email=None):
    """
    Envoie un email avec version HTML (et optionnellement texte).
    to_emails: liste d'adresses ou une seule chaîne.
    """
    if not to_emails:
        return
    if isinstance(to_emails, str):
        to_emails = [to_emails]
    from_email = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@flotte.local')
    msg = EmailMultiAlternatives(subject, body_text or body_html, from_email, to_emails)
    msg.attach_alternative(body_html, 'text/html')
    try:
        msg.send(fail_silently=False)
    except Exception as e:
        logger.exception('Envoi email échoué: %s', e)
        if getattr(settings, 'DEBUG', False):
            print('[FLOTTE] Erreur envoi email (voir ci‑dessus):', e, file=sys.stderr)
        if not getattr(settings, 'FLOTTE_EMAIL_FAIL_SILENTLY', True):
            raise


def send_welcome_email(user):
    """
    Envoie l'email de bienvenue à un nouvel utilisateur (compte créé).
    Appelé par le signal post_save User (created=True).
    Les erreurs d'envoi sont loguées mais n'empêchent pas la création du compte.
    """
    if not getattr(user, 'email', None) or not str(user.email).strip():
        return
    try:
        base_url = _get_base_url()
        login_url = base_url.rstrip('/') + '/'
        prenom = (getattr(user, 'first_name', None) or '').strip() or user.username
        context = {
            'user': user,
            'prenom': prenom,
            'username': user.username,
            'login_url': login_url,
            'base_url': base_url,
        }
        subject = render_to_string('flotte/emails/welcome_subject.txt', context).strip()
        body_html = render_to_string('flotte/emails/welcome_email.html', context)
        body_text = render_to_string('flotte/emails/welcome_email.txt', context)
        send_mail_html(subject, body_html, [user.email], body_text=body_text)
    except Exception as e:
        logger.warning('Email de bienvenue non envoyé pour %s: %s', user.username, e)
        if getattr(settings, 'DEBUG', False):
            print('[FLOTTE] Email de bienvenue non envoyé:', e, file=sys.stderr)
