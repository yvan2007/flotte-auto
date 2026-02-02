@echo off
REM FLOTTE — Lance le serveur Django après activation du venv
REM Usage : runserver.bat

cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo Erreur : environnement virtuel .venv introuvable. Creez-le avec : python -m venv .venv
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
echo Venv active. Demarrage du serveur sur http://127.0.0.1:8000/
python manage.py runserver
pause
