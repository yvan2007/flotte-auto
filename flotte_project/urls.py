"""FLOTTE — URLs principales (racine du projet).
Inclut les URLs statiques en DEBUG et pendant les tests."""
import sys
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve

# Servir /static/ et /media/ en PREMIER quand DEBUG=True OU pendant les tests (LiveServerTestCase)
# (Django met DEBUG=False pendant les tests, donc on détecte aussi 'test' dans sys.argv)
_serve_static = settings.DEBUG or 'test' in sys.argv
if _serve_static:
    urlpatterns = [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATICFILES_DIRS[0]}),
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
        path('admin/', admin.site.urls),
        path('', include('flotte.urls', namespace='flotte')),
    ]
else:
    urlpatterns = [
        path('admin/', admin.site.urls),
        path('', include('flotte.urls', namespace='flotte')),
    ]
