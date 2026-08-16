# -*- coding: utf-8 -*-
import secrets
from datetime import datetime, timedelta
from app.extensions import db


class Hub(db.Model):
    """
    Ein physischer Standort (Schaltschrank) mit 1-N Waschmaschinen.
    Jeder Hub hat sein EIGENES Token - kompromittiert ein Router-Token,
    sind nicht automatisch alle anderen Hubs betroffen.
    """
    __tablename__ = "hubs"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(200))
    country = db.Column(db.String(80), default="Cameroun")
    token = db.Column(db.String(64), unique=True, nullable=False,
                       default=lambda: secrets.token_urlsafe(32))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    machines = db.relationship("Machine", backref="hub", lazy=True,
                                cascade="all, delete-orphan")

    def is_online(self, threshold_seconds: int) -> bool:
        last_reports = [m.last_report_at for m in self.machines if m.last_report_at]
        if not last_reports:
            return False
        most_recent = max(last_reports)
        return (datetime.utcnow() - most_recent) < timedelta(seconds=threshold_seconds)

    def to_dict(self, threshold_seconds: int = 90):
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "country": self.country,
            "is_active": self.is_active,
            "is_online": self.is_online(threshold_seconds),
            "machines": [m.to_dict() for m in self.machines],
        }
