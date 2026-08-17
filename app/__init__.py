# -*- coding: utf-8 -*-
import logging
import os
from flask import Flask
from app.config import get_config
from app.extensions import db, migrate, login_manager, limiter


def create_app(config_object=None):
    """
    App-Factory statt globaler Flask-App-Instanz: noetig fuer sauberes
    Testen (jeder Test kann eine frische App-Instanz mit eigener Test-DB
    erzeugen) und falls spaeter mehrere Worker-Konfigurationen noetig sind.
    """
    app = Flask(__name__)
    app.config.from_object(config_object or get_config())

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "admin_bp.login"
    limiter.init_app(app)

    # Alle Modelle importieren, BEVOR Migrate/create_all laufen - sonst
    # registrieren sie sich nicht bei SQLAlchemy's Metadata und Alembic
    # erkennt sie beim Autogenerate nicht (stiller Bug, schwer zu finden).
    # Alle Modelle importieren, BEVOR Migrate/create_all laufen - sonst
    # registrieren sie sich nicht bei SQLAlchemy's Metadata und Alembic
    # erkennt sie beim Autogenerate nicht (stiller Bug, schwer zu finden).
    from app.models import Hub, Machine, Customer, WalletTransaction, WashSession, AdminUser  # noqa: F401

    @login_manager.user_loader
    def load_user(prefixed_id):
        """
        Zwei komplett getrennte Nutzer-Typen (Customer, AdminUser) teilen
        sich hier EINEN LoginManager. Unterscheidung ueber ein Praefix in
        get_id() (siehe Customer.get_id / AdminUser.get_id) - so kann ein
        Kunde niemals versehentlich als Admin geladen werden und umgekehrt,
        selbst wenn beide zufaellig dieselbe Datenbank-ID haetten.
        """
        kind, _, raw_id = prefixed_id.partition(":")
        if kind == "admin":
            return AdminUser.query.get(int(raw_id))
        if kind == "customer":
            return Customer.query.get(int(raw_id))
        return None

    from app.api.router import router_api
    from app.api.admin import admin_bp
    from app.api.payment import payment_api
    from app.api.portal import portal_bp

    app.register_blueprint(router_api)
    app.register_blueprint(admin_bp)
    app.register_blueprint(payment_api)
    app.register_blueprint(portal_bp)

    @app.route("/")
    def index():
        return {"service": "wasch-hub-backend", "status": "ok"}

    @app.route("/healthz")
    def healthz():
        # Fuer Uptime-Monitoring / Load-Balancer-Healthchecks beim Skalieren
        return {"status": "healthy"}, 200

    if not app.debug:
        logging.basicConfig(level=logging.INFO)

    return app
