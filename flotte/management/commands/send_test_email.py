"""Commande : python manage.py send_test_email [adresse] — envoie un email de test (ou affiche en console)."""
from django.core.management.base import BaseCommand
from django.conf import settings
from flotte.emails import send_mail_html


class Command(BaseCommand):
    help = "Envoie un email de test pour vérifier la configuration (bienvenue, SMTP/console)."

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            nargs='?',
            default='',
            help='Adresse de destination (si vide, le backend console affichera l\'email dans le terminal).',
        )

    def handle(self, *args, **options):
        to = (options.get('email') or '').strip()
        if not to:
            to = 'test@example.com'
            self.stdout.write(
                self.style.WARNING(
                    'Aucune adresse fournie : envoi vers test@example.com '
                    '(avec backend console l\'email s\'affiche ci‑dessous).'
                )
            )
        backend = getattr(settings, 'EMAIL_BACKEND', '')
        self.stdout.write(f'Backend email actuel : {backend}')
        if 'smtp' in backend.lower():
            self.stdout.write(
                self.style.WARNING(
                    'SMTP activé : vérifiez EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD dans .env'
                )
            )
        try:
            send_mail_html(
                subject='[FLOTTE] Email de test',
                body_html=(
                    '<p>Si vous recevez ce message, l’envoi d’emails FLOTTE est correctement configuré.</p>'
                    '<p>— L’équipe FLOTTE</p>'
                ),
                to_emails=[to],
                body_text='Si vous recevez ce message, l’envoi d’emails FLOTTE est correctement configuré.\n— L’équipe FLOTTE',
            )
            self.stdout.write(self.style.SUCCESS(f'Email de test envoyé vers {to}.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Échec envoi : {e}'))
            raise
