# -*- coding: utf-8 -*-
from datetime import datetime
from app.extensions import db


class MachineState:
    """Erlaubte Zustaende - als Konstanten statt freier Strings, damit
    Tippfehler beim Vergleich sofort auffallen statt still falsch zu laufen."""
    OFF = "off"
    RUNNING = "running"
    DONE = "done"
    ALLOWED = {OFF, RUNNING, DONE}


class Machine(db.Model):
    __tablename__ = "machines"

    id = db.Column(db.Integer, primary_key=True)
    hub_id = db.Column(db.Integer, db.ForeignKey("hubs.id"), nullable=False)
    label = db.Column(db.String(40), nullable=False)          # z.B. "WM1"
    price_cents = db.Column(db.Integer, default=50000)         # Standardpreis, z.B. 500 FCFA = 50000 (falls Centimes) - Waehrung siehe Hub.country

    # Sollzustand (vom Admin/Zahlungssystem gesetzt) vs. Istzustand (vom Router gemeldet)
    desired_state = db.Column(db.String(20), default=MachineState.OFF)
    actual_state = db.Column(db.String(20), default=MachineState.OFF)

    power_w = db.Column(db.Float, default=0.0)
    last_report_at = db.Column(db.DateTime, nullable=True)
    last_activated_at = db.Column(db.DateTime, nullable=True)

    # Rueckverweis auf WashSession kommt automatisch ueber deren eigenes
    # relationship("Machine") in wash_session.py - hier keine Definition noetig.

    def to_dict(self):
        return {
            "id": self.id,
            "label": self.label,
            "desired_state": self.desired_state,
            "actual_state": self.actual_state,
            "power_w": self.power_w,
            "last_report_at": self.last_report_at.isoformat() if self.last_report_at else None,
        }
