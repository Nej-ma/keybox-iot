import json
from digi.xbee.devices import XBeeDevice
from digi.xbee.exception import XBeeException

class XBeeService:
    def __init__(self, port, baud_rate, callback_function):
        self.device = XBeeDevice(port, baud_rate)
        self.callback = callback_function
        self.is_connected = False

    def start(self):
        try:
            self.device.open()
            self.device.add_data_received_callback(self._on_data_received)
            self.is_connected = True
            print(f"[XBEE] Connecté sur {self.device.get_serial_port()}")
        except XBeeException as e:
            print(f"[XBEE] Erreur de connexion : {e}")

    def _on_data_received(self, xbee_message):
        try:
            # Récupération de l'adresse source (l'ID du module XBee de la salle)
            sender = xbee_message.remote_device.get_64bit_addr()

            # Récupération du payload (les données JSON)
            data_str = xbee_message.data.decode('utf-8')
            json_data = json.loads(data_str)

            # Ajout de l'adresse MAC XBee pour debug
            json_data['xbee_id'] = str(sender)

            print(f"[XBEE] Reçu de {sender}: {json_data}")

            # On envoie les données au serveur web via le callback
            self.callback(json_data)

        except Exception as e:
            print(f"[XBEE] Erreur de parsing : {e}")

    def stop(self):
        if self.device.is_open():
            self.device.close()
