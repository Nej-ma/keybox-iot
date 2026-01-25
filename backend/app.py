from flask import Flask, render_template
from flask_socketio import SocketIO
from xbee_handler import XBeeService
import threading
import time

# --- CONFIGURATION ---
XBEE_PORT = "COM3"  # <--- TON EQUIPE DEVRA CHANGER CA (ex: /dev/ttyUSB0 sur Linux/Mac)
BAUD_RATE = 9600

app = Flask(__name__, template_folder="../frontend/templates")
app.config['SECRET_KEY'] = 'cesi_secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- FONCTION DECLENCHEE QUAND UN MESSAGE XBEE ARRIVE ---
def process_xbee_data(data):
    # data contient: {'room': 'A101', 'state': 'IN', ...}
    # On push l'info directement au frontend via WebSocket
    socketio.emit('update_room', data)

# --- LANCEMENT DU XBEE EN TACHE DE FOND ---
# On utilise un try/except pour que le serveur Web se lance même si l'XBee n'est pas branché (mode démo)
try:
    xbee_service = XBeeService(XBEE_PORT, BAUD_RATE, process_xbee_data)
    xbee_service.start()
except Exception as e:
    print(f"ATTENTION: XBee non démarré (Test UI uniquement). Erreur: {e}")

# --- ROUTES WEB ---
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # host='0.0.0.0' permet d'y accéder depuis le réseau local (Wifi CESI)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
