# CESI Smart Key System - IoT Edge Project

Système de gestion de clés de salles de classe en temps réel utilisant RFID/NFC, ZigBee, MQTT et architecture Edge Computing.

## Architecture du Système

```
[Arduino + RFID + XBee]
         ↓
[Gateway (XBee → MQTT)]
         ↓
[MQTT Broker]
         ↓
[Backend Flask + WebSocket] → [Dashboard Web Temps Réel]
```

### Composants par Salle

- **Arduino Uno R4 WiFi** avec lecteur **RC522 RFID**
- **XBee S2C ZigBee** (module émetteur en mode API)
- **Boîtier à clés** avec tags RFID/NFC uniques

### Infrastructure Edge (Récepteur)

- **MQTT Broker** (Mosquitto ou similaire) - Point central de communication
- **Gateway XBee** - Service Python qui écoute les données XBee et les publie sur MQTT
- **Backend Python** (Flask + SocketIO) - Traite les messages MQTT et met à jour le Dashboard
- **Dashboard HTML** - Interface temps réel WebSocket
- Stockage local des événements (pas de cloud)

---

## Structure du Projet

```
/keybox-iot
│
├── arduino_TX.cpp            # Code Arduino pour les salles (lecteur RFID + XBee)
│
├── /backend
│   ├── app.py                # Serveur Flask + WebSocket (écoute MQTT)
│   ├── corresponding_table.json  # Mapping clés ↔ salles
│   └── requirements.txt       # Dépendances Python
│
├── /gateway
│   ├── gateway.py            # Service XBee → MQTT
│   └── xbee_handler.py       # Gestion communication XBee
│
└── /frontend
    └── templates
        └── index.html        # Dashboard temps réel
```

---

## Installation et Configuration

### Prérequis

- Python 3.8+
- MQTT Broker installé et en cours d'exécution (Mosquitto)
- XBee Coordinator configuré en mode API
- Drivers USB pour XBee installés

### Étape 0: Lancer le Broker MQTT

```bash
# Sur macOS avec Homebrew
brew services start mosquitto

# Sur Linux
sudo service mosquitto start

# Ou avec Docker
docker run -d -p 1883:1883 eclipse-mosquitto
```

Vérifier que le Broker est actif sur `localhost:1883`

### Étape 1: Installation des Dépendances

```bash
cd backend
pip install -r requirements.txt
```

### Étape 2: Configuration du Port Série XBee (Gateway)

1. **Brancher l'XBee Coordinator** en USB sur le PC
2. **Identifier le port COM** :
   - **macOS** : `ls /dev/tty.usbserial*`
   - **Linux** : `ls /dev/ttyUSB*`
   - **Windows** : Gestionnaire de périphériques → Ports (COM et LPT)

3. **Modifier** [gateway/gateway.py](gateway/gateway.py) ligne 8 :
   ```python
   XBEE_PORT = "/dev/tty.usbserial-0001"  # Remplacer par votre port
   ```

### Étape 3: Démarrer les Services (ordre important)

**Terminal 1 - Gateway (XBee → MQTT)** :

```bash
cd gateway
python gateway.py
```

**Terminal 2 - Backend (MQTT → WebSocket)** :

```bash
cd backend
python app.py
```

Le serveur démarre sur `http://0.0.0.0:5000`

Si jamais le port 5000 est occupé (notamment sur MacOS avec AirPlay), modifier la ligne 141 de `app.py` :

```python
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, use_reloader=False)
```

### Étape 4: Accès au Dashboard

Ouvrir le navigateur :

- **Local** : `http://localhost:5000`
- **Réseau local** : `http://<IP_DU_PC>:5000` (depuis un autre appareil sur le même WiFi)

---

## Format des Données (CONTRAT de Communication)

### Arduino → Gateway (XBee)

L'Arduino envoie un payload JSON via XBee :

```json
{
  "room": "206",
  "key": "A3F2118C",
  "state": "IN"
}
```

- **`room`** : Identifiant de la salle (ex: "106", "107", "206")
- **`key`** : UID du tag RFID lu par le RC522
- **`state`** :
  - `"IN"` → Clé déposée (salle ouverte)
  - `"OUT"` → Clé retirée (salle fermée)

### Gateway → MQTT → Backend

**Topic MQTT** : `ecole/salles/{room}/status`

```json
{
  "room": "206",
  "key": "A3F2118C",
  "state": "IN",
  "timestamp": "2026-02-01T10:30:45"
}
```

Le backend s'abonne à : `ecole/salles/+/status` (wildcard pour toutes les salles)

### Exemple de Code Arduino (Émission XBee)

```cpp
#include <SoftwareSerial.h>
#include <ArduinoJson.h>

SoftwareSerial xbeeSerial(2, 3); // RX, TX

void sendKeyEvent(String room, String keyUID, String state) {
  StaticJsonDocument<128> doc;
  doc["room"] = room;
  doc["key"] = keyUID;
  doc["state"] = state;

  serializeJson(doc, xbeeSerial);
  xbeeSerial.println(); // Fin de trame
}

void loop() {
  // Après lecture RFID...
  if (cardDetected) {
    sendKeyEvent("206", "A3:F2:11:8C", "IN");
  }
}
```

---

## Fonctionnement du Dashboard

### Interface Visuelle

- **Carte verte** (bordure gauche) → Clé présente (salle ouverte)
- **Carte rouge** (bordure gauche) → Clé absente (salle fermée)
- Horodatage de la dernière mise à jour
- Création dynamique des salles (pas besoin de pré-configuration)

### Temps Réel

Le dashboard utilise **WebSocket (SocketIO)** pour recevoir les mises à jour instantanément sans rafraîchir la page.

---

## Test Sans Matériel (Mode Démo)

### Simuler des événements via MQTT

Utiliser un client MQTT pour publier des messages de test :

```bash
# Publier une clé déposée en salle 206
mosquitto_pub -h localhost -t "ecole/salles/206/status" -m '{"room":"206","key":"TEST_UID","state":"IN"}'

# Publier une clé retirée
mosquitto_pub -h localhost -t "ecole/salles/206/status" -m '{"room":"206","key":"TEST_UID","state":"OUT"}'
```

Le Backend et Dashboard se mettront à jour en temps réel.

---

## Configuration XBee (Rappel pour l'Équipe)

### XBee Émetteur (Arduino dans chaque salle)

- **Mode** : Router/End Device
- **API Mode** : API Mode 1 (ATAP=1)
- **PAN ID** : Identique pour tout le réseau (ex: 1234)
- **Baud Rate** : 9600

### XBee Coordinator (PC Serveur)

- **Mode** : Coordinator
- **API Mode** : API Mode 1 (ATAP=1)
- **PAN ID** : Identique au réseau
- **Baud Rate** : 9600

Configuration via **XCTU** (logiciel Digi).

---

## Dépannage

### Le Broker MQTT ne démarre pas

1. Vérifier que Mosquitto est installé : `mosquitto -v`
2. Si port 1883 déjà utilisé : `lsof -i :1883`
3. Redémarrer le service : `brew services restart mosquitto`

### La Gateway ne détecte pas l'XBee

1. Vérifier que le port COM est correct dans [gateway/gateway.py](gateway/gateway.py)
2. Vérifier que les drivers USB XBee sont installés
3. Tester : `ls /dev/tty.usbserial*` (macOS)
4. Vérifier les logs de la Gateway pour les erreurs

### La Gateway ne publie pas sur MQTT

1. Vérifier que le Broker MQTT est actif : `mosquitto_sub -h localhost -t "ecole/salles/+/status"`
2. Vérifier les logs de la Gateway : `[GATEWAY] Publié sur MQTT...`
3. Vérifier que `MQTT_BROKER = "localhost"` dans gateway.py

### Le Backend ne reçoit pas les messages MQTT

1. Ouvrir la console navigateur (F12) → Vérifier les messages WebSocket
2. Vérifier que le Backend s'est bien abonné : `[BACKEND] Connecté à MQTT` dans les logs
3. Regarder les logs du Backend Python (terminal)
4. Vérifier le `MQTT_TOPIC` dans [backend/app.py](backend/app.py)

### Le dashboard ne se met pas à jour

1. Vérifier que le WebSocket est actif (F12 → Network → WS)
2. Vérifier les logs du Backend pour les messages reçus
3. Vérifier le payload JSON du message MQTT

### Erreur "Permission denied" sur Linux/Mac

```bash
sudo chmod 666 /dev/tty.usbserial-0001
```

---

## Objectifs du Prototype

- ✅ Démontrer la communication ZigBee mesh (40 salles)
- ✅ Interface temps réel sans latence perceptible
- ✅ Architecture Edge (pas de cloud, pas de dépendance Internet)
- ✅ Détection de clés RFID et mise à jour instantanée
- ✅ Évolutivité (ajout automatique de nouvelles salles)

---

## Auteurs

Projet académique CESI - Gestion IoT de clés de salles de classe

---

## License

Projet éducatif - Usage académique uniquement
