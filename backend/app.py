import json
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder="../frontend/templates")
app.config['SECRET_KEY'] = 'cesi_secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# --- CONFIGURATION MQTT ---
MQTT_BROKER = "localhost"
# On s'abonne à toutes les salles via le wildcard '+'
MQTT_TOPIC = "ecole/salles/+/status"

# Etat de la connexion MQTT
mqtt_connected = False

def on_connect(client, userdata, flags, reason_code, properties):
    global mqtt_connected
    print(f"[MQTT] Tentative de connexion au broker {MQTT_BROKER}...")
    print(f"[MQTT] Code de retour: {reason_code}")
    
    if reason_code == 0:
        mqtt_connected = True
        print(f"[MQTT] ✅ Connecté avec succès!")
        print(f"[MQTT] 📡 Abonnement au topic: {MQTT_TOPIC}")
        client.subscribe(MQTT_TOPIC)
    else:
        mqtt_connected = False
        print(f"[MQTT] ❌ Échec de connexion, code: {reason_code}")

def on_subscribe(client, userdata, mid, reason_code_list, properties):
    print(f"[MQTT] ✅ Abonnement confirmé au topic {MQTT_TOPIC}")
    print(f"[MQTT] 👂 En écoute des messages...")

def on_disconnect(client, userdata, flags, reason_code, properties):
    global mqtt_connected
    mqtt_connected = False
    print(f"[MQTT] ⚠️ Déconnecté du broker, code: {reason_code}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"[MQTT] 📨 Message reçu sur '{msg.topic}': {payload}")
        
        socketio.emit('update_room', payload)
        print(f"[SOCKETIO] ✅ Événement 'update_room' envoyé au frontend")
    except Exception as e:
        print(f"[MQTT] ❌ Erreur traitement message: {e}")

# Setup du Client MQTT pour le Web
web_mqtt_client = mqtt.Client(CallbackAPIVersion.VERSION2, "Web_Backend")
web_mqtt_client.on_connect = on_connect
web_mqtt_client.on_subscribe = on_subscribe
web_mqtt_client.on_disconnect = on_disconnect
web_mqtt_client.on_message = on_message

try:
    print(f"[MQTT] Connexion au broker {MQTT_BROKER}:1883...")
    web_mqtt_client.connect(MQTT_BROKER, 1883, 60)
    web_mqtt_client.loop_start()
    print(f"[MQTT] Boucle MQTT démarrée en arrière-plan")
except Exception as e:
    print(f"[MQTT] ❌ Erreur de connexion: {e}")

@socketio.on('connect')
def handle_web_connect():
    print(f"[WEB] Client web connecté. État MQTT: {'✅ Connecté' if mqtt_connected else '❌ Déconnecté'}")
    emit('mqtt_status', {'connected': mqtt_connected})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Port 5001 pour éviter le conflit AirPlay sur Mac
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, use_reloader=False)