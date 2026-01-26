from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from xbee_handler import XBeeService
import threading
import time

# --- CONFIGURATION ---
XBEE_PORT = "/dev/tty.usbserial-0001"  # <--- TON EQUIPE DEVRA CHANGER CA (ex: /dev/ttyUSB0 sur Linux/Mac)
BAUD_RATE = 9600

app = Flask(__name__, template_folder="../frontend/templates")
app.config['SECRET_KEY'] = 'cesi_secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Variable globale pour tracker l'état de connexion XBee
xbee_connected = False

# --- FONCTION DECLENCHEE QUAND UN MESSAGE XBEE ARRIVE ---
def process_xbee_data(data):
    # data contient: {'room': 'A101', 'state': 'IN', ...}
    # On push l'info directement au frontend via WebSocket

    print(f"[SERVER] Préparation de l'envoi de 'update_room' avec les données: {data}")

    socketio.emit('update_room', data)

    print("[SERVER] 'update_room' a été envoyé à tous les clients.")

# --- LANCEMENT DU XBEE EN TACHE DE FOND ---
# On utilise un try/except pour que le serveur Web se lance même si l'XBee n'est pas branché (mode démo)
try:
    xbee_service = XBeeService(XBEE_PORT, BAUD_RATE, process_xbee_data)
    xbee_service.start()
    xbee_connected = True
    print("[SUCCESS] XBee connecté et opérationnel!")
except Exception as e:
    xbee_connected = False
    print(f"ATTENTION: XBee non démarré (Test UI uniquement). Erreur: {e}")

# --- ÉVÉNEMENT: Quand un client se connecte au WebSocket ---
@socketio.on('connect')
def handle_connect():
    # On envoie immédiatement l'état du XBee au client
    emit('xbee_status', {'connected': xbee_connected})


# --- ROUTES WEB ---
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # host='0.0.0.0' permet d'y accéder depuis le réseau local (Wifi CESI) à changé si ça marche pas
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, use_reloader=False)
