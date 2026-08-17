# -*- coding: utf-8 -*-
from datetime import datetime
from app.extensions import db


class WalletTransactionType:
    TOPUP = "topup"                  # Aufladung, z.B. per Mobile Money
    WASH_CHARGE = "wash_charge"      # Abbuchung fuer einen Waschgang
    REFUND = "refund"                # Rueckerstattung (z.B. Maschine defekt)
    ADMIN_ADJUSTMENT = "admin_adjustment"   # manuelle Korrektur durch Admin


class WalletTransaction(db.Model):
    """
    Unveraenderlicher Ledger-Eintrag - jede Bewegung auf dem Kundenguthaben
    wird HIER protokolliert, nie nur als Zahlaenderung auf Customer.balance_cents.
    amount_cents ist vorzeichenbehaftet (positiv = Gutschrift, negativ = Abbuchung).
    balance_after_cents ist ein Snapshot fuer schnelle Historie-Anzeige/Debugging,
    OHNE dass man die ganze Kette aufsummieren muss.
    """
    __tablename__ = "wallet_transactions"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)

    amount_cents = db.Column(db.Integer, nullable=False)
    balance_after_cents = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(30), nullable=False)
    payment_method = db.Column(db.String(40), nullable=True)   # z.B. "mtn_momo", "cash", "admin"
    reference = db.Column(db.String(120), nullable=True)
    note = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "amount_cents": self.amount_cents,
            "balance_after_cents": self.balance_after_cents,
            "type": self.type,
            "payment_method": self.payment_method,
            "created_at": self.created_at.isoformat(),
        }
