import json
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import database as db

# Charger .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__,
            template_folder="../frontend/templates",
            static_folder="../frontend/static")
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# --- CONFIG ---
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_TOPIC = "ecole/salles/+/status"
mqtt_connected = False

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))

# Sessions
authenticated_sessions = {}
login_attempts = {}
MAX_ATTEMPTS = 5
BLOCK_DURATION = 15

def hash_password(password):
    salt = os.getenv('FLASK_SECRET_KEY', 'CESI_KeyBox')
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def is_ip_blocked(ip):
    if ip not in login_attempts:
        return False
    data = login_attempts[ip]
    if 'blocked_until' in data and datetime.now() < data['blocked_until']:
        return True
    if 'blocked_until' in data:
        del login_attempts[ip]
    return False

def record_attempt(ip, success):
    if success:
        login_attempts.pop(ip, None)
        return
    if ip not in login_attempts:
        login_attempts[ip] = {'count': 0}
    login_attempts[ip]['count'] += 1
    if login_attempts[ip]['count'] >= MAX_ATTEMPTS:
        login_attempts[ip]['blocked_until'] = datetime.now() + timedelta(minutes=BLOCK_DURATION)

# Table correspondance
CORRESPONDING_TABLE_PATH = os.path.join(os.path.dirname(__file__), 'corresponding_table.json')
with open(CORRESPONDING_TABLE_PATH, 'r', encoding='utf-8') as f:
    corresponding_table = json.load(f)

def verify_key(room, key):
    if key == 'N/A':
        return {'valid': False, 'message': f"Aucune cle salle {room}", 'key_name': None}
    if key not in corresponding_table:
        return {'valid': False, 'message': f"Cle inconnue '{key}'", 'key_name': None}
    info = corresponding_table[key]
    if info['salle'] == room:
        return {'valid': True, 'message': f"OK - {info['nom_cle']}", 'key_name': info['nom_cle']}
    return {'valid': False, 'message': f"ERREUR - {info['nom_cle']} (salle {info['salle']})", 'key_name': info['nom_cle']}

# --- MQTT ---
def on_connect(client, userdata, flags, rc, properties):
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        print(f"[MQTT] Connecte")
        client.subscribe(MQTT_TOPIC)
    else:
        mqtt_connected = False

def on_disconnect(client, userdata, flags, rc, properties):
    global mqtt_connected
    mqtt_connected = False

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        room, key, state = payload.get('room'), payload.get('key'), payload.get('state')
        print(f"[MQTT] Salle {room}: {state} - {key}")

        is_swap, is_multi = False, False

        if state == "ALERT" and key.startswith("MULTI:"):
            uids = key.replace("MULTI:", "").split(",")
            is_multi = True
            payload.update({
                'key_valid': False, 'key_name': f"{len(uids)} badges",
                'verification_message': f"ALERTE: {len(uids)} badges!", 'multi_badge': True
            })
        elif state == "SWAP":
            is_swap = True
            v = verify_key(room, key)
            payload.update({
                'key_valid': v['valid'], 'key_name': v['key_name'],
                'verification_message': f"SWAP! {v['message']}", 'swap_detected': True
            })
        else:
            v = verify_key(room, key)
            payload.update({
                'key_valid': v['valid'], 'key_name': v['key_name'],
                'verification_message': v['message']
            })

        # Sauvegarder en DB
        db.add_log(room, state, key, payload.get('key_name'), payload.get('key_valid'),
                   payload.get('verification_message'), is_swap, is_multi)
        db.update_room_state(room, state, key, payload.get('key_name'), payload.get('key_valid'))

        socketio.emit('update_room', payload)
    except Exception as e:
        print(f"[MQTT] Erreur: {e}")

mqtt_client = mqtt.Client(CallbackAPIVersion.VERSION2, "Web_Backend")
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_message = on_message

try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"[MQTT] Erreur: {e}")

# --- SOCKET EVENTS ---
@socketio.on('connect')
def handle_connect(auth=None):
    emit('mqtt_status', {'connected': mqtt_connected})
    # Envoyer l'etat actuel des salles
    states = db.get_room_states()
    for room, data in states.items():
        emit('update_room', {
            'room': room, 'state': data['state'], 'key': data['key_uid'],
            'key_valid': bool(data['key_valid']), 'key_name': data['key_name']
        })

@socketio.on('disconnect')
def handle_disconnect():
    authenticated_sessions.pop(request.sid, None)

@socketio.on('admin_login')
def handle_login(data):
    sid, ip = request.sid, request.remote_addr or 'unknown'

    if is_ip_blocked(ip):
        emit('admin_login_response', {'success': False, 'message': 'IP bloquee', 'blocked': True})
        return

    username, password = data.get('username', '').strip(), data.get('password', '')

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        record_attempt(ip, True)
        token = secrets.token_hex(16)
        authenticated_sessions[sid] = {'username': username, 'token': token}
        print(f"[ADMIN] Login: {username}")

        # Envoyer logs et stats
        logs = db.get_logs(limit=200)
        stats = db.get_stats()

        emit('admin_login_response', {
            'success': True, 'token': token, 'username': username,
            'logs': logs, 'stats': stats
        })
    else:
        record_attempt(ip, False)
        left = MAX_ATTEMPTS - login_attempts.get(ip, {}).get('count', 0)
        emit('admin_login_response', {'success': False, 'message': f'Erreur ({left} essais)'})

@socketio.on('admin_logout')
def handle_logout():
    authenticated_sessions.pop(request.sid, None)
    emit('admin_logout_response', {'success': True})

@socketio.on('admin_verify')
def handle_verify(data):
    sid, token = request.sid, data.get('token')
    if sid in authenticated_sessions and authenticated_sessions[sid]['token'] == token:
        logs = db.get_logs(limit=200)
        stats = db.get_stats()
        emit('admin_verify_response', {
            'valid': True, 'username': authenticated_sessions[sid]['username'],
            'logs': logs, 'stats': stats
        })
    else:
        emit('admin_verify_response', {'valid': False})

@socketio.on('admin_get_logs')
def handle_get_logs(data):
    if request.sid not in authenticated_sessions:
        return
    filter_type = data.get('filter')
    logs = db.get_logs(limit=500, filter_type=filter_type)
    stats = db.get_stats()
    emit('admin_logs_response', {'logs': logs, 'stats': stats})

@socketio.on('admin_clear_logs')
def handle_clear_logs():
    if request.sid not in authenticated_sessions:
        return
    db.clear_logs()
    emit('admin_logs_response', {'logs': [], 'stats': {'in': 0, 'out': 0, 'alert': 0, 'total': 0}})

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/api/logs')
def api_logs():
    """API pour exporter les logs"""
    logs = db.get_logs(limit=10000)
    return jsonify(logs)

if __name__ == '__main__':
    print("=" * 50)
    print("  CESI KeyBox")
    print("=" * 50)
    print(f"  Dashboard: http://localhost:{FLASK_PORT}")
    print(f"  Admin: http://localhost:{FLASK_PORT}/admin")
    print("=" * 50)
    socketio.run(app, host='0.0.0.0', port=FLASK_PORT, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
