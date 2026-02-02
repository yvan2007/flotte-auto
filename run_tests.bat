@echo off
set PROJECT_ROOT=%~dp0
cd /d "%PROJECT_ROOT%"
set FLOTTE_TEST_HEADLESS=0
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
if "%1"=="no_selenium" (
    coverage run --source=flotte,flotte_project manage.py test flotte.tests.unit flotte.tests.integration --verbosity=2
) else if "%1"=="html" (
    coverage run --source=flotte,flotte_project manage.py test flotte --verbosity=2
    if errorlevel 1 exit /b 1
    coverage html
    start htmlcov\index.html
) else (
    coverage run --source=flotte,flotte_project manage.py test flotte --verbosity=2
)
if errorlevel 1 exit /b 1
echo.
echo === Rapport de couverture ===
coverage report
exit /b 0
