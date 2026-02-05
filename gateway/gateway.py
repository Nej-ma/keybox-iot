import json
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
from xbee_handler import XBeeService
from datetime import datetime

# --- CONFIGURATION ---
XBEE_PORT = "COM5"  # Windows: Silicon Labs CP210x USB (XBee) 
BAUD_RATE = 9600
MQTT_BROKER = "localhost"

# --- LOGGING UTILITIES ---
def log_exchange(direction, protocol, topic, qos=None, data=None, is_confirmable=True, status=""):
    """
    Log des échanges avec annotation complète
    
    Args:
        direction: 'RX' ou 'TX' ou 'SUBSCRIBE'
        protocol: 'MQTT' ou 'XBEE'
        topic: Le topic/resource utilisé
        qos: Niveau de QoS (0, 1, ou 2)
        data: Les données échangées
        is_confirmable: Si c'est un message confirmable (MQTT: toujours true, CoAP serait variable)
        status: Message de statut additionnel
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    qos_str = f"QoS={qos}" if qos is not None else "QoS=N/A"
    confirmable_str = "Confirmable" if is_confirmable else "Non-confirmable"
    status_str = f"| {status}" if status else ""
    
    print(f"[{timestamp}] [{protocol}] {direction} | Topic/Resource: {topic} | {qos_str} | {confirmable_str} {status_str}")
    if data:
        print(f"  -> Payload: {data}")

# Configuration du Client MQTT
mqtt_client = mqtt.Client(CallbackAPIVersion.VERSION2, "XBee_Gateway")

def on_connect(client, userdata, flags, reason_code, properties):
    log_exchange("CONNECT", "MQTT", "Broker", status=f"Code de connexion: {reason_code}")
    print(f"[GATEWAY] Connecte au Broker MQTT avec le code {reason_code}")

mqtt_client.on_connect = on_connect
mqtt_client.connect(MQTT_BROKER, 1883, 60)
mqtt_client.loop_start()

# Fonction appelee a chaque reception XBee
def process_xbee_data(data):
    log_exchange("RX", "XBEE", "XBee_Serial", data=data, status="Donnees Arduino")
    # data est le dictionnaire JSON venant de l'Arduino
    room = data.get('room', 'unknown')
    topic = f"ecole/salles/{room}/status"
    
    # Publication sur le Bus MQTT avec QoS=1 (au moins une fois)
    mqtt_client.publish(topic, json.dumps(data), qos=1, retain=True)
    log_exchange("TX", "MQTT", topic, qos=1, data=json.dumps(data), status="Donnees relayees du XBee")

# Lancement du service XBee
try:
    print("[GATEWAY] Initialisation du XBee...")
    # On force AP=1 dans ton XBee via XCTU pour que ce service fonctionne
    xbee_service = XBeeService(XBEE_PORT, BAUD_RATE, process_xbee_data)
    xbee_service.start()
    print("[GATEWAY] Pret a relayer les donnees.")
except Exception as e:
    print(f"[GATEWAY] Erreur fatale: {e}")

# Boucle infinie pour maintenir le script actif
import time
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("[GATEWAY] Arrêt du service.")