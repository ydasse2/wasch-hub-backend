#!/bin/sh
# ============================================================================
# TEMPLATE - Router-seitiges Poll-Skript fuer RUT951 (RutOS User Scripts)
#
# WICHTIG: Dies ist ein Geruest, kein fertig getestetes Skript. Vor Ort
# gegen die tatsaechliche RutOS-Version und das verbaute I/O-Modul pruefen:
#   1. Modbus-CLI-Tool verfuegbar? (z.B. "mbpoll") -> which mbpoll
#      Alternative: RutOS Services -> Data to Server -> Modbus (Report-
#      Richtung), fuer die Command-Richtung trotzdem Skript/MQTT noetig.
#   2. curl/wget verfuegbar? (meist ja unter BusyBox)
#   3. Register-Adressen haengen vom I/O-Modul ab (ICP DAS != Waveshare!)
#
# Einrichtung: RutOS -> System -> Maintenance -> Troubleshoot -> User Scripts,
# per Cron (Scheduled Tasks) alle 15-30s ausfuehren.
#
# NEU gegenueber der ersten Demo-Version: Auth jetzt per Hub-Token im Header
# (X-Hub-Token), Maschinen werden per Label (WM1, WM2, WM3) angesprochen,
# nicht mehr per Nummer - das Label steht im Dashboard und in der DB.
# ============================================================================

BACKEND_URL="https://DEIN-BACKEND-URL"
HUB_TOKEN="DAS-TOKEN-AUS-DEM-SEED-SCRIPT-OUTPUT"

# --- 1. Befehle vom Backend abholen (GET, Header-Auth) ----------------------
COMMANDS=$(curl -s -H "X-Hub-Token: $HUB_TOKEN" "$BACKEND_URL/api/router/commands")
echo "Empfangene Befehle: $COMMANDS"
# Beispiel Antwort: {"WM1":"running","WM2":"off","WM3":"off"}

# --- 2. Je Maschine: gewuenschten mit aktuellem Zustand vergleichen --------
#   und bei Abweichung das passende Modbus-Coil schreiben (Register je nach
#   I/O-Modul-Datenblatt anpassen - Beispiel mit mbpoll, Slave-Adresse 1):
#     mbpoll -a 1 -t 0 -r 1 -1 /dev/ttyUSB0 -- 1   # Relais 1 EIN
#     mbpoll -a 1 -t 0 -r 1 -1 /dev/ttyUSB0 -- 0   # Relais 1 AUS

# --- 3. Energiezaehler lesen (Beispiel SDM120, Register je Datenblatt) -----
#     POWER_M1=$(mbpoll -a 2 -t 4:float -r 12 -c 1 /dev/ttyUSB0 | ...)

# --- 4. Lokale Schwellenwert-Logik (Start/Ende-Erkennung) ------------------
#   WICHTIG: laeuft lokal auf dem Router, nicht im Backend - damit die
#   Maschine auch bei kurzem Verbindungsabbruch sauber abschaltet.
#   Start: > 20W fuer 45-60s | Ende: < 5W fuer 180-300s + 2-3 Min Grace Period
#   (siehe Bauanleitung; Werte pro Maschinenmodell in ersten 10-20 Waeschen
#   feinjustieren)

# --- 5. Ergebnis an Backend melden (POST, JSON, Header-Auth) --------------
#     curl -s -X POST -H "X-Hub-Token: $HUB_TOKEN" \
#          -H "Content-Type: application/json" \
#          -d '{"WM1":{"actual_state":"running","power_w":1180}}' \
#          "$BACKEND_URL/api/router/report"
#
#   actual_state ist eines von: "off" | "running" | "done"
#   "done" setzt im Backend automatisch den Sollzustand zurueck auf "off".

echo "Skript-Geruest - siehe Kommentare oben fuer die noetigen Anpassungen."
