# -*- coding: utf-8 -*-
"""
Zentrale Konfiguration. Werte kommen aus Umgebungsvariablen (.env lokal,
echte Env-Vars beim Hoster) - nie Secrets im Code fest verdrahten.

DATABASE_URL bestimmt die Datenbank:
  - lokal/Demo:  sqlite:///wasch_hub.db  (Standard, kein Setup noetig)
  - Produktion:  postgresql://user:pass@host:5432/dbname  (skaliert mit,
                 unterstuetzt echte Nebenlaeufigkeit fuer viele Hubs gleichzeitig)

Der Code selbst aendert sich beim Wechsel SQLite -> Postgres NICHT,
nur die Env-Variable.
"""
import os
from datetime import timedelta


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///wasch_hub.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Nach wie vielen Sekunden ohne Meldung gilt ein Hub als "offline"?
    HUB_OFFLINE_THRESHOLD_SECONDS = int(os.environ.get("HUB_OFFLINE_THRESHOLD_SECONDS", 90))

    # Schwellenwerte fuer die Zyklus-Erkennung (Startwerte, siehe Bauanleitung -
    # pro Maschinenmodell in den ersten 10-20 Waeschen feinjustieren)
    CYCLE_START_WATTS = 20
    CYCLE_START_SECONDS = 45
    CYCLE_END_WATTS = 5
    CYCLE_END_SECONDS = 180
    CYCLE_GRACE_SECONDS = 150

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)


class DevConfig(BaseConfig):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # erzwingt HTTPS-only Cookies


class TestConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


CONFIG_MAP = {
    "development": DevConfig,
    "production": ProductionConfig,
    "testing": TestConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    return CONFIG_MAP.get(env, DevConfig)
