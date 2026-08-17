# -*- coding: utf-8 -*-
"""
Kunden-Frontend. Strikt getrennt vom Admin-Bereich (app/api/admin.py) -
ein Kunde sieht ausschliesslich seine eigenen Daten (eigenes Guthaben,
eigene Waschgaenge), nie andere Kunden oder interne Hub-Tokens.
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db, limiter
from app.models import Hub, Machine, Customer, WashSession
from app.services import wallet, machine_control
from app.services.wallet import InsufficientBalance
from app.services.machine_control import MachineBusy
from app.services.auth import customer_required

portal_bp = Blueprint("portal_bp", __name__, url_prefix="/portal")


@portal_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def register():
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")

        if not phone or not name or len(password) < 6:
            flash("Bitte Name, Telefonnummer und ein Passwort (min. 6 Zeichen) angeben.")
            return render_template("portal/register.html")

        if Customer.query.filter_by(phone=phone).first():
            flash("Diese Telefonnummer ist bereits registriert.")
            return render_template("portal/register.html")

        customer = Customer(name=name, phone=phone)
        customer.set_password(password)
        db.session.add(customer)
        db.session.commit()
        login_user(customer)
        return redirect(url_for("portal_bp.dashboard"))

    return render_template("portal/register.html")


@portal_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if request.method == "POST":
        customer = Customer.query.filter_by(phone=request.form.get("phone", "").strip()).first()
        if customer and customer.check_password(request.form.get("password", "")):
            login_user(customer)
            return redirect(url_for("portal_bp.dashboard"))
        flash("Telefonnummer oder Passwort falsch.")
    return render_template("portal/login.html")


@portal_bp.route("/logout")
@customer_required
def logout():
    logout_user()
    return redirect(url_for("portal_bp.login"))


@portal_bp.route("/")
@customer_required
def dashboard():
    hubs = Hub.query.filter_by(is_active=True).all()
    active_session = WashSession.query.filter_by(
        customer_id=current_user.id, status="active"
    ).first()
    return render_template("portal/dashboard.html", hubs=hubs,
                            active_session=active_session)


@portal_bp.route("/machine/<int:machine_id>/start", methods=["POST"])
@customer_required
@limiter.limit("20 per minute")
def start(machine_id):
    machine = Machine.query.get_or_404(machine_id)
    try:
        session = machine_control.start_wash(current_user, machine)
    except InsufficientBalance:
        flash("Guthaben reicht nicht aus. Bitte zuerst aufladen.")
        return redirect(url_for("portal_bp.dashboard"))
    except MachineBusy:
        flash(f"{machine.label} wird gerade von jemand anderem benutzt.")
        return redirect(url_for("portal_bp.dashboard"))
    return redirect(url_for("portal_bp.session_detail", session_id=session.id))


@portal_bp.route("/session/<int:session_id>")
@customer_required
def session_detail(session_id):
    session = WashSession.query.get_or_404(session_id)
    if session.customer_id != current_user.id:
        abort(403)   # fremde Session - kein Zugriff, auch nicht lesend
    return render_template("portal/session.html", session=session)


@portal_bp.route("/history")
@customer_required
def history():
    sessions = WashSession.query.filter_by(customer_id=current_user.id) \
        .order_by(WashSession.started_at.desc()).limit(50).all()
    wallet_txs = current_user.wallet_transactions
    wallet_txs = sorted(wallet_txs, key=lambda t: t.created_at, reverse=True)[:50]
    return render_template("portal/history.html", sessions=sessions, wallet_txs=wallet_txs)


@portal_bp.route("/topup/demo", methods=["POST"])
@customer_required
@limiter.limit("10 per minute")
def topup_demo():
    """
    NUR FUER DEMO/TEST: simuliert eine Mobile-Money-Aufladung ohne echten
    Zahlungsanbieter. In Produktion ersetzt der echte Payment-Webhook
    (app/api/payment.py) diesen Weg - dieser Button muss dann entfernt
    oder hinter eine Admin-/Testflag gesperrt werden.
    """
    amount = int(request.form.get("amount_cents", 0))
    if amount <= 0:
        abort(400)
    wallet.top_up(current_user, amount, payment_method="demo", reference="manual-demo-topup")
    return redirect(url_for("portal_bp.dashboard"))
