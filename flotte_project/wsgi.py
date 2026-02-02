"""WSGI config for flotte_project — point d'entrée pour déploiement."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flotte_project.settings')
application = get_wsgi_application()
