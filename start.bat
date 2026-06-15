@echo off
title Energy Tracker

echo Baslatiliyor...
echo.

start "Backend" cmd /c "cd /d "%~dp0backend" && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --host :: --port 8000"
start "Frontend" cmd /c "cd /d "%~dp0frontend" && npm run dev"

echo Backend ve Frontend baslatildi.
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Kapatmak icin terminalde Ctrl+C yapin.
pause
