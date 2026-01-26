#include <SPI.h>
#include <MFRC522.h>
#include <ArduinoJson.h>

// --- CONFIGURATION MATÉRIELLE ---
#define SS_PIN 10
#define RST_PIN 9
MFRC522 rfid(SS_PIN, RST_PIN);

// On utilise Serial1 (Broches 0 et 1) pour le XBee sur R4
// Si tu tiens absolument à SoftwareSerial, garde tes pins 2 et 3
#define xbeeSerial Serial1 

// --- VARIABLES DE SUIVI ---
bool clePresenteActuellement = false;
String roomID = "206"; 

void setup() {
  Serial.begin(9600);   // Console PC (USB)
  xbeeSerial.begin(9600); // Communication XBee
  
  SPI.begin();           
  rfid.PCD_Init();       
  
  Serial.println("Système KeyBox Initialisé - Salle " + roomID);
}

// Fonction d'envoi JSON
void sendKeyEvent(String room, String keyUID, String state) {
  StaticJsonDocument<128> doc;
  doc["room"] = room;
  doc["key"] = keyUID;
  doc["state"] = state;

  // Envoi vers le XBee
  serializeJson(doc, xbeeSerial);
  xbeeSerial.println(); // Fin de trame pour le serveur Python
  
  // Debug sur le PC
  Serial.print("JSON Envoyé : ");
  serializeJson(doc, Serial);
  Serial.println();
}

// Fonction pour transformer l'UID en String lisible
String getUIDString(MFRC522::Uid uid) {
  String res = "";
  for (byte i = 0; i < uid.size; i++) {
    res += String(uid.uidByte[i] < 0x10 ? "0" : "");
    res += String(uid.uidByte[i], HEX);
    if (i < uid.size - 1) res += ":";
  }
  res.toUpperCase();
  return res;
}

void loop() {
  // 1. Tentative de détection
  bool lectureReussie = rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial();
  
  // 2. Vérification de présence continue (si pas de nouvelle carte)
  if (!lectureReussie && clePresenteActuellement) {
     byte bufferATQA[2];
     byte bufferSize = sizeof(bufferATQA);
     MFRC522::StatusCode status = rfid.PICC_WakeupA(bufferATQA, &bufferSize);
     lectureReussie = (status == MFRC522::STATUS_OK);
  }

  // 3. Gestion des événements (Envoi uniquement si changement)
  if (lectureReussie != clePresenteActuellement) {
    if (lectureReussie) {
      String uid = getUIDString(rfid.uid);
      sendKeyEvent(roomID, uid, "IN");
    } else {
      // Quand on retire la clé, l'UID n'est plus lisible, on envoie "UNKNOWN" ou le dernier connu
      sendKeyEvent(roomID, "N/A", "OUT");
    }
    clePresenteActuellement = lectureReussie;
  }

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  delay(500); 
}