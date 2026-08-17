# -*- coding: utf-8 -*-
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class AdminUser(UserMixin, db.Model):
    """
    Echte Admin-Anmeldung (Session-Cookie nach Login) statt Token in der URL.
    role='superadmin' sieht alle Hubs, role='operator' nur den eigenen
    (hub_id gesetzt) - relevant sobald mehrere Standort-Teams Zugriff brauchen.
    """
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="operator")   # "superadmin" | "operator"
    hub_id = db.Column(db.Integer, db.ForeignKey("hubs.id"), nullable=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def can_access_hub(self, hub_id: int) -> bool:
        return self.role == "superadmin" or self.hub_id == hub_id

    # --- Login-Typ-Unterscheidung, siehe app/extensions.py user_loader ---
    def get_id(self):
        return f"admin:{self.id}"
