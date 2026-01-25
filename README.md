# CESI Smart Key System - IoT Edge Project

Système de gestion de clés de salles de classe en temps réel utilisant RFID/NFC, ZigBee et architecture Edge Computing.

## Architecture du Système

```
[Arduino + RFID + XBee] → [XBee Coordinator USB] → [Serveur Edge PC/RPi] → [Dashboard Web Temps Réel]
```

### Composants par Salle

- **Arduino Uno R4 WiFi** avec lecteur **RC522 RFID**
- **XBee S2C ZigBee** (module émetteur en mode API)
- **Boîtier à clés** avec tags RFID/NFC uniques

### Serveur Edge (Récepteur)

- **XBee Coordinator** branché en USB
- **Backend Python** (Flask + SocketIO)
- **Dashboard HTML** en temps réel
- Stockage local des événements (pas de cloud)

---

## Structure du Projet

```
/keybox-iot
│
├── /backend
│   ├── app.py                # Serveur Flask + WebSocket
│   ├── xbee_handler.py       # Gestion communication XBee
│   └── requirements.txt      # Dépendances Python
│
└── /frontend
    └── templates
        └── index.html        # Dashboard temps réel
```

---

## Installation et Configuration

### Prérequis

- Python 3.8+
- XBee Coordinator configuré en mode API
- Drivers USB pour XBee installés

### Étape 1: Installation des Dépendances

```bash
cd backend
pip install -r requirements.txt
```

### Étape 2: Configuration du Port Série

1. **Brancher l'XBee Coordinator** en USB sur le PC
2. **Identifier le port COM** :
   - **Windows** : Gestionnaire de périphériques → Ports (COM et LPT) → Noter le numéro (ex: `COM4`)
   - **Linux/Mac** : `ls /dev/tty*` → Chercher `/dev/ttyUSB0` ou similaire

3. **Modifier** [backend/app.py](backend/app.py) ligne 9 :
   ```python
   XBEE_PORT = "COM4"  # Remplacer par votre port
   ```

### Étape 3: Lancement du Serveur

```bash
cd backend
python app.py
```

Le serveur démarre sur `http://0.0.0.0:5000`

### Étape 4: Accès au Dashboard

Ouvrir le navigateur :
- **Local** : `http://localhost:5000`
- **Réseau local** : `http://<IP_DU_PC>:5000` (depuis un autre appareil sur le même WiFi)

---

## Format des Données (CONTRAT Arduino ↔ Serveur)

L'Arduino doit envoyer un payload JSON via XBee :

```json
{
  "room": "B202",
  "key": "UID_RFID_DE_LA_CLE",
  "state": "IN"
}
```

- **`room`** : Identifiant de la salle (ex: "A101", "B202")
- **`key`** : UID du tag RFID lu par le RC522
- **`state`** :
  - `"IN"` → Clé déposée (salle ouverte)
  - `"OUT"` → Clé retirée (salle fermée)

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
    sendKeyEvent("B202", "A3:F2:11:8C", "IN");
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

Le serveur peut démarrer même si l'XBee n'est pas branché (message d'avertissement affiché).

Pour simuler un événement depuis Python (console interactive) :

```python
from backend.app import socketio

# Simuler une clé déposée en salle A101
socketio.emit('update_room', {'room': 'A101', 'state': 'IN', 'key': 'TEST_UID'})
```

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

### Le serveur ne détecte pas l'XBee

1. Vérifier que le port COM est correct dans [backend/app.py](backend/app.py)
2. Vérifier que les drivers USB XBee sont installés
3. Tester avec XCTU que l'XBee répond

### Le dashboard ne se met pas à jour

1. Ouvrir la console navigateur (F12) → Vérifier les messages WebSocket
2. Vérifier que le payload Arduino est bien en JSON
3. Regarder les logs du serveur Python (terminal)

### Erreur "Permission denied" sur Linux/Mac

```bash
sudo chmod 666 /dev/ttyUSB0
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
