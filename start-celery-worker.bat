@echo off
echo ========================================
echo Starting Celery Worker for Invoice Generation...
echo ========================================
echo.
echo Make sure the FastAPI server is running in another terminal.
echo.
echo Starting worker...
echo.
python -m celery -A app.celery_app worker --loglevel=info --pool=solo
pause

