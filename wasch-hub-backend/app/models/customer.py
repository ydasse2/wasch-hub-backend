# -*- coding: utf-8 -*-
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class Customer(UserMixin, db.Model):
    """
    Der zahlende Endkunde. Login aktuell per Telefonnummer + Passwort -
    fuer den Zielmarkt waere SMS-OTP-Login (kein Passwort noetig) meist
    passender, ist hier aber bewusst nicht implementiert (braucht einen
    SMS-Versender), siehe README.

    balance_cents ist ein GECACHTER Wert fuer schnelle Anzeige. Die
    eigentliche Wahrheit steht im WalletTransaction-Ledger (app/models/
    wallet_transaction.py) - jede Aenderung von balance_cents passiert
    NUR ueber app/services/wallet.py, nie direkt.
    """
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    balance_cents = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    wallet_transactions = db.relationship("WalletTransaction", backref="customer", lazy=True)
    wash_sessions = db.relationship("WashSession", backref="customer", lazy=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # --- Login-Typ-Unterscheidung, siehe app/extensions.py user_loader ---
    def get_id(self):
        return f"customer:{self.id}"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "balance_cents": self.balance_cents,
        }
