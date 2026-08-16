#!/bin/sh
# Laeuft bei jedem Container-Start: richtet Datenbank-Schema ein (falls noch
# nicht vorhanden/aktuell) und legt Demo-Daten an (falls noch nicht vorhanden -
# scripts/seed.py prueft das selbst und ueberspringt sich dann), bevor der
# eigentliche Server startet. Dadurch braucht es in Render's Docker-Modus
# KEIN separates Start Command Feld - alles steckt in der Dockerfile.
set -e

export FLASK_APP=wsgi.py

echo "--> Datenbank-Migration..."
flask db upgrade

echo "--> Seed-Daten pruefen/anlegen..."
python scripts/seed.py

echo "--> Starte Server..."
exec gunicorn --bind 0.0.0.0:8000 --workers 4 wsgi:app
