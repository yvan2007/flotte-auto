# Script pour lancer les tests FLOTTE avec couverture (coverage).
# Chrome s'ouvre visiblement pour les tests Selenium (FLOTTE_TEST_HEADLESS=0 par défaut).
# Usage: .\run_tests.ps1
#        .\run_tests.ps1 -NoSelenium   # sans tests Selenium (plus rapide)
#        .\run_tests.ps1 -Html          # génère et ouvre le rapport HTML

param(
    [switch]$NoSelenium,
    [switch]$Html
)

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot

# Chrome visible pour Selenium (fenêtre qui s'ouvre et déroule les scénarios)
$env:FLOTTE_TEST_HEADLESS = "0"

Push-Location $projectRoot

try {
    # Activer l'environnement virtuel si présent
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        . .venv\Scripts\Activate.ps1
    }

    # Nettoyer une ancienne couverture
    if (Test-Path "htmlcov") { Remove-Item -Recurse -Force htmlcov }
    if (Test-Path ".coverage") { Remove-Item -Force .coverage }

    if ($NoSelenium) {
        Write-Host "Tests sans Selenium (unit + integration)..." -ForegroundColor Cyan
        coverage run --source=flotte,flotte_project manage.py test flotte.tests.unit.test_models flotte.tests.integration.test_views_permissions --verbosity=2
    } else {
        Write-Host "Tous les tests (unit + integration + Selenium avec Chrome visible)..." -ForegroundColor Cyan
        coverage run --source=flotte,flotte_project manage.py test flotte --verbosity=2
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Echec des tests." -ForegroundColor Red
        exit 1
    }

    # Rapport en console
    Write-Host ""
    Write-Host "=== Rapport de couverture ===" -ForegroundColor Green
    coverage report

    if ($Html) {
        coverage html
        Write-Host ""
        Write-Host "Rapport HTML : htmlcov\index.html" -ForegroundColor Green
        Start-Process "htmlcov\index.html"
    }
} finally {
    Pop-Location
}
