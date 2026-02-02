"""
Configuration des tests FLOTTE — credentials et URL depuis l'environnement.
À utiliser pour les tests fonctionnels Selenium (site live ou LiveServerTestCase).
"""
import os

# URL de base pour les tests fonctionnels (Selenium).
# Vide = utilisation de LiveServerTestCase (URL fournie par le test).
FLOTTE_TEST_BASE_URL = os.environ.get('FLOTTE_TEST_BASE_URL', '')

# Compte utilisateur (rôle user — consultation seule)
FLOTTE_TEST_USER_USERNAME = os.environ.get('FLOTTE_TEST_USER_USERNAME', 'user')
FLOTTE_TEST_USER_PASSWORD = os.environ.get('FLOTTE_TEST_USER_PASSWORD', '52751040Ky')

# Compte gestionnaire (rôle manager — gestion + consultation)
FLOTTE_TEST_MANAGER_USERNAME = os.environ.get('FLOTTE_TEST_MANAGER_USERNAME', 'gestion')
FLOTTE_TEST_MANAGER_PASSWORD = os.environ.get('FLOTTE_TEST_MANAGER_PASSWORD', '52751040Ky')

# Compte administrateur (rôle admin)
FLOTTE_TEST_ADMIN_USERNAME = os.environ.get('FLOTTE_TEST_ADMIN_USERNAME', 'yvan')
FLOTTE_TEST_ADMIN_PASSWORD = os.environ.get('FLOTTE_TEST_ADMIN_PASSWORD', '5275')

# Pilote Chrome : headless=0 pour voir la fenêtre Chrome pendant les tests (déroulement visible).
# Mettre FLOTTE_TEST_HEADLESS=1 pour CI / sans interface.
FLOTTE_TEST_HEADLESS = os.environ.get('FLOTTE_TEST_HEADLESS', '0') == '1'

# Délai d'attente max (secondes) pour les éléments Selenium
FLOTTE_TEST_IMPLICIT_WAIT = int(os.environ.get('FLOTTE_TEST_IMPLICIT_WAIT', '10'))

# Pause (secondes) sur chaque page pendant les tests Selenium (Chrome visible) — pour voir le déroulement
FLOTTE_TEST_PAUSE_SECONDS = float(os.environ.get('FLOTTE_TEST_PAUSE_SECONDS', '2'))
