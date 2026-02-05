@echo off
title CESI Smart Key System - Stop
color 0C

echo ========================================
echo    Arret des services CESI Smart Key
echo ========================================
echo.

echo Arret de Mosquitto...
taskkill /F /IM mosquitto.exe 2>nul

echo Arret des scripts Python...
taskkill /F /FI "WINDOWTITLE eq Gateway*" 2>nul
taskkill /F /FI "WINDOWTITLE eq Backend*" 2>nul

echo.
echo ========================================
echo    Tous les services sont arretes
echo ========================================
echo.

pause
