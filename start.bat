@echo off
title CESI Smart Key System - Launcher
color 0A

echo ========================================
echo    CESI Smart Key System - Launcher
echo ========================================
echo.

:: Verifier si Mosquitto est installe
if not exist "C:\Program Files\mosquitto\mosquitto.exe" (
    echo [ERREUR] Mosquitto n'est pas installe!
    echo Installez-le avec: winget install EclipseFoundation.Mosquitto
    pause
    exit /b 1
)

:: Check if MQTT security is configured
set MQTT_CONFIG=%~dp0mqtt_config\mosquitto.conf
if not exist "%MQTT_CONFIG%" (
    echo [ATTENTION] Configuration MQTT securisee non trouvee!
    echo Execution de setup_mqtt_security.bat...
    echo.
    call "%~dp0setup_mqtt_security.bat"
    if %ERRORLEVEL% NEQ 0 (
        echo [ERREUR] La configuration de securite a echoue
        pause
        exit /b 1
    )
    echo.
)

:: Demarrer Mosquitto avec configuration TLS dans une nouvelle fenetre
echo [1/3] Demarrage de Mosquitto MQTT Broker (TLS)...
echo   Port 1883: MQTT avec authentification
echo   Port 8883: MQTTS (TLS) avec authentification
start "Mosquitto MQTT" cmd /k "cd /d "C:\Program Files\mosquitto" && mosquitto.exe -c "%MQTT_CONFIG%" -v"

:: Attendre que Mosquitto demarre
timeout /t 3 /nobreak > nul

:: Demarrer la Gateway dans une nouvelle fenetre
echo [2/3] Demarrage de la Gateway XBee...
start "Gateway XBee" cmd /k "cd /d "%~dp0gateway" && python gateway.py"

:: Attendre que la Gateway demarre
timeout /t 2 /nobreak > nul

:: Demarrer le Backend dans une nouvelle fenetre
echo [3/3] Demarrage du Backend Flask...
start "Backend Flask" cmd /k "cd /d "%~dp0backend" && python app.py"

:: Attendre que le Backend demarre
timeout /t 3 /nobreak > nul

echo.
echo ========================================
echo    Tous les services sont lances!
echo ========================================
echo.
echo Dashboard: http://localhost:5000
echo.
echo Pour arreter: fermez les 3 fenetres de terminal
echo.

:: Ouvrir le navigateur
start http://localhost:5000

pause
