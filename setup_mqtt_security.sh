#!/bin/bash

# CESI Smart Key System - MQTT Security Setup Script
# Creates self-signed certificates and configures Mosquitto for TLS

echo "========================================"
echo "  MQTT Security Setup - TLS & Auth"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Directories
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CERT_DIR="$SCRIPT_DIR/mqtt_certs"
CONFIG_DIR="$SCRIPT_DIR/mqtt_config"

# Create directories
mkdir -p "$CERT_DIR"
mkdir -p "$CONFIG_DIR"

echo -e "${GREEN}[1/5] Creating directories...${NC}"
echo "  Certificates: $CERT_DIR"
echo "  Config: $CONFIG_DIR"
echo ""

# Generate CA (Certificate Authority)
echo -e "${GREEN}[2/5] Generating Certificate Authority (CA)...${NC}"
openssl req -new -x509 -days 3650 -extensions v3_ca \
    -keyout "$CERT_DIR/ca.key" \
    -out "$CERT_DIR/ca.crt" \
    -subj "/C=FR/ST=IDF/L=Paris/O=CESI/OU=IOT/CN=CESI-MQTT-CA" \
    -passout pass:cesi123

echo ""

# Generate Server Key and Certificate
echo -e "${GREEN}[3/5] Generating Server Certificate...${NC}"
openssl genrsa -out "$CERT_DIR/server.key" 2048

openssl req -new -key "$CERT_DIR/server.key" \
    -out "$CERT_DIR/server.csr" \
    -subj "/C=FR/ST=IDF/L=Paris/O=CESI/OU=IOT/CN=localhost"

openssl x509 -req -in "$CERT_DIR/server.csr" \
    -CA "$CERT_DIR/ca.crt" \
    -CAkey "$CERT_DIR/ca.key" \
    -CAcreateserial \
    -out "$CERT_DIR/server.crt" \
    -days 3650 \
    -passin pass:cesi123

echo ""

# Generate Client Key and Certificate
echo -e "${GREEN}[4/5] Generating Client Certificate...${NC}"
openssl genrsa -out "$CERT_DIR/client.key" 2048

openssl req -new -key "$CERT_DIR/client.key" \
    -out "$CERT_DIR/client.csr" \
    -subj "/C=FR/ST=IDF/L=Paris/O=CESI/OU=IOT/CN=cesi-client"

openssl x509 -req -in "$CERT_DIR/client.csr" \
    -CA "$CERT_DIR/ca.crt" \
    -CAkey "$CERT_DIR/ca.key" \
    -CAcreateserial \
    -out "$CERT_DIR/client.crt" \
    -days 3650 \
    -passin pass:cesi123

echo ""

# Create Mosquitto password file
echo -e "${GREEN}[5/5] Creating MQTT users...${NC}"
# Create password file with users
touch "$CONFIG_DIR/passwd"

# Add users (password: cesi123)
mosquitto_passwd -b "$CONFIG_DIR/passwd" gateway cesi123
mosquitto_passwd -b "$CONFIG_DIR/passwd" backend cesi123
mosquitto_passwd -b "$CONFIG_DIR/passwd" admin cesi123

echo ""

# Create Mosquitto configuration
cat > "$CONFIG_DIR/mosquitto.conf" << 'EOF'
# CESI KeyBox - Mosquitto Configuration with TLS

# Global settings
allow_anonymous false
password_file /mqtt_config/passwd

# Logging
log_dest stdout
log_type all
log_timestamp true

# Port standard non-TLS (pour tests)
listener 1883
protocol mqtt

# Port TLS/SSL
listener 8883
protocol mqtt

# TLS Configuration
cafile /mqtt_certs/ca.crt
certfile /mqtt_certs/server.crt
keyfile /mqtt_certs/server.key

# TLS Version (minimum TLS 1.2)
tls_version tlsv1.2

# Require certificate from clients (optional - can be set to false)
require_certificate false
EOF

# Update config file paths to absolute
sed -i.bak "s|/mqtt_config/passwd|$CONFIG_DIR/passwd|g" "$CONFIG_DIR/mosquitto.conf"
sed -i.bak "s|/mqtt_certs/ca.crt|$CERT_DIR/ca.crt|g" "$CONFIG_DIR/mosquitto.conf"
sed -i.bak "s|/mqtt_certs/server.crt|$CERT_DIR/server.crt|g" "$CONFIG_DIR/mosquitto.conf"
sed -i.bak "s|/mqtt_certs/server.key|$CERT_DIR/server.key|g" "$CONFIG_DIR/mosquitto.conf"
rm "$CONFIG_DIR/mosquitto.conf.bak"

# Set permissions
chmod 600 "$CERT_DIR"/*.key
chmod 644 "$CERT_DIR"/*.crt
chmod 600 "$CONFIG_DIR/passwd"
chmod 644 "$CONFIG_DIR/mosquitto.conf"

echo ""
echo "========================================"
echo -e "${GREEN}   Setup Complete!${NC}"
echo "========================================"
echo ""
echo "Certificates created in: $CERT_DIR"
echo "Configuration created in: $CONFIG_DIR"
echo ""
echo "MQTT Users created:"
echo "  - gateway:backend (password: cesi123)"
echo "  - backend:backend (password: cesi123)"
echo "  - admin:admin (password: cesi123)"
echo ""
echo "Mosquitto will listen on:"
echo "  - Port 1883 (Non-TLS with auth)"
echo "  - Port 8883 (TLS with auth)"
echo ""
echo -e "${YELLOW}Next: Run './start.sh' to start the system${NC}"
echo ""
