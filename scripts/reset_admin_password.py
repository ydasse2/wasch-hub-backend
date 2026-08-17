# -*- coding: utf-8 -*-
"""
Einmaliger Passwort-Reset fuer einen Admin-Account, falls das Passwort
vergessen wurde. Sicher in den normalen Start-Ablauf integrierbar, weil er
NICHTS tut, solange die Umgebungsvariable ADMIN_RESET_PASSWORD nicht gesetzt
ist - kann also dauerhaft in entrypoint.sh bleiben, ohne ein Risiko zu sein.

Nutzung bei vergessenem Passwort:
1. In Render -> Environment: ADMIN_RESET_PASSWORD=<neues Passwort> setzen
   (optional ADMIN_RESET_USERNAME=<name>, Standard ist "admin")
2. Redeploy ausloesen (z.B. "Manual Deploy" -> "Deploy latest commit")
3. Im Log nach "Passwort zurueckgesetzt" suchen, zur Bestaetigung
4. WICHTIG: ADMIN_RESET_PASSWORD danach wieder aus den Environment
   Variables LOESCHEN und nochmal redeployen - sonst bleibt das neue
   Passwort im Klartext in den Render-Einstellungen sichtbar.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import AdminUser

new_password = os.environ.get("ADMIN_RESET_PASSWORD")

if not new_password:
    print("--> Kein ADMIN_RESET_PASSWORD gesetzt, ueberspringe Passwort-Reset.")
else:
    username = os.environ.get("ADMIN_RESET_USERNAME", "admin")
    app = create_app()
    with app.app_context():
        user = AdminUser.query.filter_by(username=username).first()
        if not user:
            print(f"--> WARNUNG: Admin-User '{username}' nicht gefunden, nichts zurueckgesetzt.")
        else:
            user.set_password(new_password)
            db.session.commit()
            print(f"--> Passwort zurueckgesetzt fuer '{username}'.")
            print("--> WICHTIG: ADMIN_RESET_PASSWORD jetzt aus den Environment Variables")
            print("    entfernen und nochmal deployen, sonst bleibt es im Klartext sichtbar.")
