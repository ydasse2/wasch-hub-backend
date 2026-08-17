# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_user, logout_user, current_user
from app.extensions import db, limiter
from app.models import Hub, Machine, AdminUser, Customer, WashSession
from app.services import machine_control, wallet
from app.services.wallet import InsufficientBalance
from app.services.auth import admin_required
from app.config import get_config

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin")
CFG = get_config()


@admin_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if request.method == "POST":
        user = AdminUser.query.filter_by(username=request.form.get("username")).first()
        if user and user.check_password(request.form.get("password", "")):
            login_user(user)
            return redirect(url_for("admin_bp.dashboard"))
        flash("Benutzername oder Passwort falsch.")
    return render_template("admin/login.html")


@admin_bp.route("/logout")
@admin_required
def logout():
    logout_user()
    return redirect(url_for("admin_bp.login"))


@admin_bp.route("/")
@admin_required
def dashboard():
    if current_user.role == "superadmin":
        hubs = Hub.query.all()
    else:
        hubs = Hub.query.filter_by(id=current_user.hub_id).all()
    return render_template("admin/dashboard.html", hubs=hubs,
                            threshold=CFG.HUB_OFFLINE_THRESHOLD_SECONDS)


@admin_bp.route("/account", methods=["GET", "POST"])
@admin_required
def account():
    """Self-Service Passwort-Aenderung - bewusst als erste Ergaenzung nach
    dem ersten Live-Deploy, da die Seed-Zugangsdaten oeffentlich im Deploy-
    Log sichtbar waren und sofort geaendert werden sollten."""
    if request.method == "POST":
        current_pw = request.form.get("current_password", "")
        new_pw = request.form.get("new_password", "")
        confirm_pw = request.form.get("confirm_password", "")

        if not current_user.check_password(current_pw):
            flash("Aktuelles Passwort ist falsch.")
        elif len(new_pw) < 8:
            flash("Neues Passwort muss mindestens 8 Zeichen haben.")
        elif new_pw != confirm_pw:
            flash("Die beiden neuen Passwoerter stimmen nicht ueberein.")
        else:
            current_user.set_password(new_pw)
            db.session.commit()
            flash("Passwort erfolgreich geaendert.")
            return redirect(url_for("admin_bp.dashboard"))

    return render_template("admin/account.html")


@admin_bp.route("/machine/<int:machine_id>/activate", methods=["POST"])
@admin_required
def machine_activate(machine_id):
    """Direkt-Freigabe durch Admin OHNE Kundenkonto/Guthaben - fuer Support/Demo.
    Erzeugt bewusst keine WashSession (die gehoert einem Kunden)."""
    machine = Machine.query.get_or_404(machine_id)
    if not current_user.can_access_hub(machine.hub_id):
        abort(403)
    machine_control.admin_force_start(machine)
    return redirect(url_for("admin_bp.dashboard"))


@admin_bp.route("/machine/<int:machine_id>/stop", methods=["POST"])
@admin_required
def machine_stop(machine_id):
    machine = Machine.query.get_or_404(machine_id)
    if not current_user.can_access_hub(machine.hub_id):
        abort(403)
    machine_control.stop_machine(machine)
    return redirect(url_for("admin_bp.dashboard"))


# ---------------------------------------------------------------
# Kundenverwaltung - Themen, auf die Kunden selbst KEINEN Zugriff haben:
# Liste aller Kunden, fremde Guthaben einsehen, manuelle Korrekturen.
# ---------------------------------------------------------------

@admin_bp.route("/customers")
@admin_required
def customers():
    if current_user.role != "superadmin":
        abort(403)   # Kundendaten nur fuer Superadmin, nicht pro-Hub-Operator
    q = request.args.get("q", "").strip()
    query = Customer.query
    if q:
        query = query.filter(
            db.or_(Customer.name.ilike(f"%{q}%"), Customer.phone.ilike(f"%{q}%"))
        )
    all_customers = query.order_by(Customer.created_at.desc()).limit(200).all()
    return render_template("admin/customers.html", customers=all_customers, q=q)


@admin_bp.route("/customers/<int:customer_id>")
@admin_required
def customer_detail(customer_id):
    if current_user.role != "superadmin":
        abort(403)
    customer = Customer.query.get_or_404(customer_id)
    sessions = WashSession.query.filter_by(customer_id=customer.id) \
        .order_by(WashSession.started_at.desc()).limit(30).all()
    wallet_txs = sorted(customer.wallet_transactions, key=lambda t: t.created_at, reverse=True)[:30]
    return render_template("admin/customer_detail.html", customer=customer,
                            sessions=sessions, wallet_txs=wallet_txs)


@admin_bp.route("/customers/<int:customer_id>/adjust", methods=["POST"])
@admin_required
def customer_adjust(customer_id):
    """Manuelle Guthaben-Korrektur (z.B. Bar-Zahlung erfasst, Kulanz nach
    Stoerung). Grund ist PFLICHT - landet im Ledger, damit spaeter
    nachvollziehbar bleibt, wer wann warum manuell eingegriffen hat."""
    if current_user.role != "superadmin":
        abort(403)
    customer = Customer.query.get_or_404(customer_id)
    amount = int(request.form.get("amount_cents", 0))
    note = request.form.get("note", "").strip()
    if not note:
        flash("Bitte einen Grund fuer die Korrektur angeben.")
        return redirect(url_for("admin_bp.customer_detail", customer_id=customer.id))
    try:
        wallet.admin_adjustment(customer, amount, note=f"{note} (durch {current_user.username})")
    except InsufficientBalance:
        flash("Korrektur wuerde das Guthaben negativ machen - abgelehnt.")
    return redirect(url_for("admin_bp.customer_detail", customer_id=customer.id))
