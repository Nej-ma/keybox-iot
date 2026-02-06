@echo off
setlocal enabledelayedexpansion
title CESI Smart Key System - MQTT Security Setup
color 0A

echo ========================================
echo   MQTT Security Setup - TLS ^& Auth
echo ========================================
echo.

:: Check for OpenSSL
where openssl >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] OpenSSL not found!
    echo Please install OpenSSL from: https://slproweb.com/products/Win32OpenSSL.html
    pause
    exit /b 1
)

:: Check for Mosquitto
where mosquitto_passwd >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Mosquitto not found!
    echo Please install: winget install EclipseFoundation.Mosquitto
    pause
    exit /b 1
)

:: Directories
set CERT_DIR=%~dp0mqtt_certs
set CONFIG_DIR=%~dp0mqtt_config

:: Create directories
echo [1/5] Creating directories...
if not exist "%CERT_DIR%" mkdir "%CERT_DIR%"
if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"
echo   Certificates: %CERT_DIR%
echo   Config: %CONFIG_DIR%
echo.

:: Generate CA
echo [2/5] Generating Certificate Authority (CA)...
openssl req -new -x509 -days 3650 -extensions v3_ca -keyout "%CERT_DIR%\ca.key" -out "%CERT_DIR%\ca.crt" -subj "/C=FR/ST=IDF/L=Paris/O=CESI/OU=IOT/CN=CESI-MQTT-CA" -passout pass:cesi123
echo.

:: Generate Server Certificate
echo [3/5] Generating Server Certificate...
openssl genrsa -out "%CERT_DIR%\server.key" 2048
openssl req -new -key "%CERT_DIR%\server.key" -out "%CERT_DIR%\server.csr" -subj "/C=FR/ST=IDF/L=Paris/O=CESI/OU=IOT/CN=localhost"
openssl x509 -req -in "%CERT_DIR%\server.csr" -CA "%CERT_DIR%\ca.crt" -CAkey "%CERT_DIR%\ca.key" -CAcreateserial -out "%CERT_DIR%\server.crt" -days 3650 -passin pass:cesi123
echo.

:: Generate Client Certificate
echo [4/5] Generating Client Certificate...
openssl genrsa -out "%CERT_DIR%\client.key" 2048
openssl req -new -key "%CERT_DIR%\client.key" -out "%CERT_DIR%\client.csr" -subj "/C=FR/ST=IDF/L=Paris/O=CESI/OU=IOT/CN=cesi-client"
openssl x509 -req -in "%CERT_DIR%\client.csr" -CA "%CERT_DIR%\ca.crt" -CAkey "%CERT_DIR%\ca.key" -CAcreateserial -out "%CERT_DIR%\client.crt" -days 3650 -passin pass:cesi123
echo.

:: Create Mosquitto users
echo [5/5] Creating MQTT users...
type nul > "%CONFIG_DIR%\passwd"
mosquitto_passwd -b "%CONFIG_DIR%\passwd" gateway cesi123
mosquitto_passwd -b "%CONFIG_DIR%\passwd" backend cesi123
mosquitto_passwd -b "%CONFIG_DIR%\passwd" admin cesi123
echo.

::  Create Mosquitto configuration
(
echo # CESI KeyBox - Mosquitto Configuration with TLS
echo.
echo # Global settings
echo allow_anonymous false
echo password_file %CONFIG_DIR%\passwd
echo.
echo # Logging
echo log_dest stdout
echo log_type all
echo log_timestamp true
echo.
echo # Port standard non-TLS (pour tests^)
echo listener 1883
echo protocol mqtt
echo.
echo # Port TLS/SSL
echo listener 8883
echo protocol mqtt
echo.
echo # TLS Configuration
echo cafile %CERT_DIR%\ca.crt
echo certfile %CERT_DIR%\server.crt
echo keyfile %CERT_DIR%\server.key
echo.
echo # TLS Version (minimum TLS 1.2^)
echo tls_version tlsv1.2
echo.
echo # Require certificate from clients
echo require_certificate false
) > "%CONFIG_DIR%\mosquitto.conf"

:: Create .env file if it doesn't exist
if not exist "%~dp0.env" (
    echo Creating .env file...
    (
        echo # MQTT Configuration
        echo MQTT_BROKER=localhost
        echo MQTT_PORT=8883
        echo MQTT_USE_TLS=true
        echo MQTT_USERNAME=backend
        echo MQTT_PASSWORD=cesi123
        echo MQTT_CA_CERT=mqtt_certs/ca.crt
        echo MQTT_CLIENT_CERT=mqtt_certs/client.crt
        echo MQTT_CLIENT_KEY=mqtt_certs/client.key
        echo.
        echo # Gateway MQTT Configuration
        echo GATEWAY_MQTT_USERNAME=gateway
        echo GATEWAY_MQTT_PASSWORD=cesi123
        echo.
        echo # Flask Configuration
        echo FLASK_SECRET_KEY=cesi-keybox-secret-2026
        echo FLASK_PORT=5001
        echo.
        echo # Admin Credentials
        echo ADMIN_USERNAME=admin
        echo ADMIN_PASSWORD=admin123
        echo.
        echo # XBee Configuration
        echo XBEE_PORT=COM3
    ) > "%~dp0.env"
    echo .env file created
) else (
    echo .env file already exists, skipping...
    echo Please update it manually with MQTT credentials
)

echo.
echo ========================================
echo    Setup Complete!
echo ========================================
echo.
echo Certificates created in: %CERT_DIR%
echo Configuration created in: %CONFIG_DIR%
echo.
echo MQTT Users created:
echo   - gateway:backend (password: cesi123^)
echo   - backend:backend (password: cesi123^)
echo   - admin:admin (password: cesi123^)
echo.
echo Mosquitto will listen on:
echo   - Port 1883 (Non-TLS with auth^)
echo   - Port 8883 (TLS with auth^)
echo.
echo Next: Run 'start.bat' to start the system
echo.
pause
