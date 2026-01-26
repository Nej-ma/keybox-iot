import json
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
from xbee_handler import XBeeService

# --- CONFIGURATION ---
XBEE_PORT = "/dev/tty.usbserial-0001" 
BAUD_RATE = 9600
MQTT_BROKER = "localhost"

# Configuration du Client MQTT
mqtt_client = mqtt.Client(CallbackAPIVersion.VERSION2, "XBee_Gateway")

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"[GATEWAY] Connecté au Broker MQTT avec le code {reason_code}")

mqtt_client.on_connect = on_connect
mqtt_client.connect(MQTT_BROKER, 1883, 60)
mqtt_client.loop_start()

# Fonction appelée à chaque réception XBee
def process_xbee_data(data):
    print(f"[GATEWAY] Données reçues du XBee: {data}")
    # data est le dictionnaire JSON venant de l'Arduino
    room = data.get('room', 'unknown')
    topic = f"ecole/salles/{room}/status"
    
    # Publication sur le Bus MQTT
    mqtt_client.publish(topic, json.dumps(data), retain=True)
    print(f"[GATEWAY -> MQTT] Donnée publiée sur {topic}")

# Lancement du service XBee
try:
    print("[GATEWAY] Initialisation du XBee...")
    # On force AP=1 dans ton XBee via XCTU pour que ce service fonctionne
    xbee_service = XBeeService(XBEE_PORT, BAUD_RATE, process_xbee_data)
    xbee_service.start()
    print("[GATEWAY] Prêt à relayer les données.")
except Exception as e:
    print(f"[GATEWAY] Erreur fatale : {e}")

# Boucle infinie pour maintenir le script actif
import time
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("[GATEWAY] Arrêt du service.")