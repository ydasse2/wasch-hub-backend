# -*- coding: utf-8 -*-
from datetime import datetime
from app.extensions import db


class WashSessionStatus:
    ACTIVE = "active"          # laeuft gerade (oder wartet auf Start)
    COMPLETED = "completed"    # Zyklusende vom Router bestaetigt
    CANCELLED = "cancelled"    # abgebrochen, z.B. Admin-Eingriff


class WashSession(db.Model):
    """
    Ein Waschvorgang eines Kunden. Verknuepft mit genau EINER
    WalletTransaction (die Abbuchung) - so lassen sich Guthaben-Bewegung
    und tatsaechlicher Waschvorgang jederzeit gegeneinander pruefen
    (Streitfall: 'ich wurde belastet, aber die Maschine lief nie').
    """
    __tablename__ = "wash_sessions"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    machine_id = db.Column(db.Integer, db.ForeignKey("machines.id"), nullable=False)
    wallet_transaction_id = db.Column(db.Integer, db.ForeignKey("wallet_transactions.id"), nullable=True)

    price_cents = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default=WashSessionStatus.ACTIVE)

    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)

    machine = db.relationship("Machine")
    wallet_transaction = db.relationship("WalletTransaction")

    def to_dict(self):
        return {
            "id": self.id,
            "machine_id": self.machine_id,
            "machine_label": self.machine.label if self.machine else None,
            "price_cents": self.price_cents,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }
