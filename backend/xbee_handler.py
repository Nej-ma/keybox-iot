import json
from digi.xbee.devices import XBeeDevice
from digi.xbee.exception import XBeeException

class XBeeService:
    def __init__(self, port, baud_rate, callback_function):
        # Utilisation de l'objet natif de la bibliothèque digi-xbee
        self.device = XBeeDevice(port, baud_rate)
        self.callback = callback_function
        self.is_connected = False

    def start(self):
        try:
            self.device.open()
            # Correction ici : on utilise la propriété .serial_port
            print(f"[XBEE] Connecté sur {self.device.serial_port}")
            
            # Définition du callback de réception
            self.device.add_data_received_callback(self._on_data_received)
            self.is_connected = True
        except XBeeException as e:
            self.is_connected = False
            print(f"[XBEE] Erreur de connexion : {e}")
            raise e # On remonte l'erreur pour app.py

    def _on_data_received(self, xbee_message):
        try:
            # Récupération de l'adresse MAC du module émetteur (Salle)
            sender = xbee_message.remote_device.get_64bit_addr()
            
            # Décodage du message reçu
            data_raw = xbee_message.data.decode('utf-8').strip()
            print(f"[XBEE] Données brutes reçues de {sender}: {data_raw}")

            # --- LOGIQUE DE PARSING ---
            # Si ton Arduino envoie "SALLE1:PRESENTE", on le transforme en dictionnaire
            payload = None
            try:
                # On essaie d'abord de parser le message comme du JSON
                payload = json.loads(data_raw)
                payload['xbee_id'] = str(sender)
            except json.JSONDecodeError:
                # Si le parsing JSON échoue, on traite le format "ROOM:STATE"
                print("[XBEE] Ce n'est pas du JSON, on essaie le format simple.")
                if ":" in data_raw:
                    parts = data_raw.split(":")
                    if len(parts) >= 2:
                        payload = {
                            "room": parts[0],
                            "state": parts[1],
                            "xbee_id": str(sender)
                        }

            # Si aucune méthode n'a fonctionné, on envoie les données brutes
            if payload is None:
                payload = {"raw": data_raw, "xbee_id": str(sender)}

            print(f"[XBEE] Données parsées: {payload}")
            # Envoi au serveur Flask via SocketIO
            self.callback(payload)

        except Exception as e:
            print(f"[XBEE] Erreur de traitement : {e}")

    def stop(self):
        if self.device is not None and self.device.is_open():
            self.device.close()
            print("[XBEE] Connexion fermée.")