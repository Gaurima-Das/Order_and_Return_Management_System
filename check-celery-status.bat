@echo off
echo ========================================
echo CELERY WORKER STATUS CHECK
echo ========================================
echo.

REM Check for Python processes
echo Checking for Python processes...
tasklist | findstr /i "python" >nul
if %errorlevel% == 0 (
    echo [OK] Python processes found
    tasklist | findstr /i "python"
) else (
    echo [WARNING] No Python processes found
)

echo.
echo Checking for Celery broker database...
if exist "celery_broker.db" (
    echo [OK] Celery broker database exists
) else (
    echo [INFO] Celery broker database not found (will be created on first use)
)

echo.
echo ========================================
echo To start Celery worker, run:
echo   start-celery-worker.bat
echo.
echo Or manually:
echo   python -m celery -A app.celery_app worker --loglevel=info --pool=solo
echo ========================================
pause

