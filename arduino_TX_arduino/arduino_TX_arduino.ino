#include <SPI.h>
#include <MFRC522.h>
#include <ArduinoJson.h>

// --- CONFIGURATION MATERIELLE ---
#define SS_PIN 10
#define RST_PIN 9
MFRC522 rfid(SS_PIN, RST_PIN);

#define xbeeSerial Serial1

// --- VARIABLES DE SUIVI ---
String roomID = "206";
String dernierUID = "";
String tousLesUIDs = "";  // Stocke tous les UIDs detectes
int nombreCartes = 0;
unsigned long derniereLecture = 0;
const unsigned long TIMEOUT_ABSENCE = 800; // ms sans lecture = carte retiree

void setup() {
  Serial.begin(9600);
  xbeeSerial.begin(9600);

  SPI.begin();
  rfid.PCD_Init();

  Serial.println("=== KeyBox Multi-Badge ===");
  Serial.println("Salle: " + roomID);
  Serial.println("Detection swap + multi-badges active");
  Serial.println("==========================");
}

void sendKeyEvent(String room, String keyUID, String state) {
  StaticJsonDocument<128> doc;
  doc["room"] = room;
  doc["key"] = keyUID;
  doc["state"] = state;

  serializeJson(doc, xbeeSerial);
  xbeeSerial.println();

  Serial.print(">>> ");
  serializeJson(doc, Serial);
  Serial.println();
}

String getUIDString() {
  String res = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) res += "0";
    res += String(rfid.uid.uidByte[i], HEX);
    if (i < rfid.uid.size - 1) res += ":";
  }
  res.toUpperCase();
  return res;
}

// Detecte toutes les cartes presentes (jusqu'a 3)
int detecterToutesLesCartes(String uids[], int maxCartes) {
  int count = 0;

  for (int tentative = 0; tentative < maxCartes && count < maxCartes; tentative++) {
    rfid.PCD_Init();
    delay(10);

    if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
      String uid = getUIDString();

      // Verifier si cette carte n'est pas deja dans la liste
      bool dejaVu = false;
      for (int i = 0; i < count; i++) {
        if (uids[i] == uid) {
          dejaVu = true;
          break;
        }
      }

      if (!dejaVu) {
        uids[count] = uid;
        count++;
        Serial.print("  Carte ");
        Serial.print(count);
        Serial.print(": ");
        Serial.println(uid);
      }

      // Mettre cette carte en pause pour detecter les autres
      rfid.PICC_HaltA();
      rfid.PCD_StopCrypto1();
    }
  }

  return count;
}

void loop() {
  String cartesDetectees[3];
  int nbCartes = detecterToutesLesCartes(cartesDetectees, 3);

  if (nbCartes > 0) {
    derniereLecture = millis();

    // Construire la liste des UIDs
    String listeUIDs = "";
    for (int i = 0; i < nbCartes; i++) {
      if (i > 0) listeUIDs += ",";
      listeUIDs += cartesDetectees[i];
    }

    // ALERTE: Plusieurs cartes detectees!
    if (nbCartes > 1) {
      Serial.println("!! ALERTE: MULTI-BADGES DETECTES !!");
      sendKeyEvent(roomID, "MULTI:" + listeUIDs, "ALERT");
    }
    // Swap detecte: UID different du precedent
    else if (dernierUID != "" && cartesDetectees[0] != dernierUID) {
      Serial.println("!! SWAP DETECTE !!");
      Serial.print("   Ancien: ");
      Serial.println(dernierUID);
      Serial.print("   Nouveau: ");
      Serial.println(cartesDetectees[0]);
      sendKeyEvent(roomID, cartesDetectees[0], "SWAP");
    }
    // Nouvelle carte (rien avant)
    else if (dernierUID == "") {
      sendKeyEvent(roomID, cartesDetectees[0], "IN");
    }

    dernierUID = cartesDetectees[0];
    tousLesUIDs = listeUIDs;
    nombreCartes = nbCartes;
  }

  // Carte retiree (timeout)
  if (dernierUID != "" && (millis() - derniereLecture > TIMEOUT_ABSENCE)) {
    Serial.println("Carte(s) retiree(s)");
    sendKeyEvent(roomID, "N/A", "OUT");
    dernierUID = "";
    tousLesUIDs = "";
    nombreCartes = 0;
  }

  delay(150);
}
