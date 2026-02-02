# FLOTTE — Lance le serveur Django après activation du venv
# Usage : .\runserver.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

if (-not (Test-Path "$ProjectRoot\.venv\Scripts\Activate.ps1")) {
    Write-Host "Erreur : environnement virtuel .venv introuvable. Créez-le avec : python -m venv .venv" -ForegroundColor Red
    exit 1
}

& "$ProjectRoot\.venv\Scripts\Activate.ps1"
Set-Location $ProjectRoot
Write-Host "Venv activé. Démarrage du serveur sur http://127.0.0.1:8000/" -ForegroundColor Green
python manage.py runserver
