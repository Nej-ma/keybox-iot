#!/bin/bash

# CESI Smart Key System - Launcher (Mac/Linux)

echo "========================================"
echo "   CESI Smart Key System - Launcher"
echo "========================================"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Repertoire du script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Fonction pour arreter proprement
cleanup() {
    echo ""
    echo -e "${YELLOW}Arret des services...${NC}"
    kill $MOSQUITTO_PID 2>/dev/null
    kill $GATEWAY_PID 2>/dev/null
    kill $BACKEND_PID 2>/dev/null
    echo -e "${GREEN}Services arretes.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Verifier Mosquitto
if ! command -v mosquitto &> /dev/null; then
    echo -e "${RED}[ERREUR] Mosquitto n'est pas installe!${NC}"
    echo "Sur Mac: brew install mosquitto"
    echo "Sur Linux: sudo apt install mosquitto"
    exit 1
fi

# Demarrer Mosquitto
echo -e "${GREEN}[1/3] Demarrage de Mosquitto MQTT Broker...${NC}"
mosquitto -v &
MOSQUITTO_PID=$!
sleep 2

# Verifier que Mosquitto a demarre
if ! kill -0 $MOSQUITTO_PID 2>/dev/null; then
    echo -e "${RED}[ERREUR] Mosquitto n'a pas pu demarrer${NC}"
    exit 1
fi

# Demarrer la Gateway
echo -e "${GREEN}[2/3] Demarrage de la Gateway XBee...${NC}"
cd "$SCRIPT_DIR/gateway"
python3 gateway.py &
GATEWAY_PID=$!
sleep 2

# Demarrer le Backend
echo -e "${GREEN}[3/3] Demarrage du Backend Flask...${NC}"
cd "$SCRIPT_DIR/backend"
python3 app.py &
BACKEND_PID=$!
sleep 2

echo ""
echo "========================================"
echo -e "${GREEN}   Tous les services sont lances!${NC}"
echo "========================================"
echo ""
echo "Dashboard: http://localhost:5000"
echo ""
echo "Appuyez sur Ctrl+C pour arreter tous les services"
echo ""

# Ouvrir le navigateur (Mac)
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:5000
fi

# Attendre
wait
