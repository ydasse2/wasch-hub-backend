# -*- coding: utf-8 -*-
"""
Einmalig ausfuehren, um die Datenbank mit einem Test-Hub, 3 Maschinen und
einem Superadmin-Login zu befuellen.

Aufruf:
    python scripts/seed.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import Hub, Machine, AdminUser, Customer

app = create_app()

with app.app_context():
    db.create_all()

    if AdminUser.query.filter_by(username="admin").first():
        print("Seed-Daten existieren bereits - nichts getan.")
        sys.exit(0)

    hub = Hub(name="Hub Douala Akwa", location="Akwa, Douala", country="Cameroun")
    db.session.add(hub)
    db.session.flush()  # damit hub.id verfuegbar ist

    for i in range(1, 4):
        db.session.add(Machine(hub_id=hub.id, label=f"WM{i}", price_cents=50000))

    admin = AdminUser(username="admin", role="superadmin")
    admin.set_password("changeme-sofort-aendern")
    db.session.add(admin)

    demo_customer = Customer(name="Demo Kunde", balance_cents=150000, phone="+237600000000")
    demo_customer.set_password("changeme123")
    db.session.add(demo_customer)

    db.session.commit()

    print("Seed abgeschlossen.")
    print(f"  Hub-Token (fuer den Router):  {hub.token}")
    print(f"  Admin-Login: admin / changeme-sofort-aendern  <- SOFORT AENDERN")
    print(f"  Demo-Kunde: +237600000000 / changeme123 (Guthaben: 1500.00)")
