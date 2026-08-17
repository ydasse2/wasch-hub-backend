# -*- coding: utf-8 -*-
"""
Zentrale Geschaeftslogik rund um Waschvorgaenge. Routen (app/api/*) rufen
NUR diese Funktionen auf, statt Models direkt zu manipulieren.
"""
from datetime import datetime
from app.extensions import db
from app.models import Machine, MachineState, WashSession, WashSessionStatus
from app.services import wallet
from app.services.wallet import InsufficientBalance


class MachineBusy(Exception):
    pass


def start_wash(customer, machine: Machine) -> WashSession:
    """
    Kompletter Start-Ablauf: Verfuegbarkeit pruefen -> Guthaben abbuchen
    -> WashSession anlegen -> Sollzustand auf 'running' setzen.
    Wirft MachineBusy oder InsufficientBalance, wenn etwas nicht passt -
    die aufrufende Route entscheidet, wie das dem Nutzer angezeigt wird.
    """
    active = WashSession.query.filter_by(
        machine_id=machine.id, status=WashSessionStatus.ACTIVE
    ).first()
    if active or machine.actual_state == MachineState.RUNNING:
        raise MachineBusy(f"{machine.label} wird gerade benutzt")

    # Kann InsufficientBalance werfen - dann wird NICHTS angelegt (Abbuchung
    # und WashSession muessen zusammen passieren, nie nur eins von beiden)
    wallet_tx = wallet.charge(customer, machine.price_cents, note=f"Waschgang {machine.label}")

    session = WashSession(
        customer_id=customer.id,
        machine_id=machine.id,
        wallet_transaction_id=wallet_tx.id,
        price_cents=machine.price_cents,
        status=WashSessionStatus.ACTIVE,
    )
    db.session.add(session)

    machine.desired_state = MachineState.RUNNING
    machine.last_activated_at = datetime.utcnow()
    db.session.commit()
    return session


def admin_force_start(machine: Machine):
    """Freigabe direkt durch Admin, OHNE Kunde/Guthaben - fuer Support/Demo/Test.
    Erzeugt bewusst KEINE WashSession (die gehoert einem Kunden), nur den
    physischen Zustand."""
    machine.desired_state = MachineState.RUNNING
    machine.last_activated_at = datetime.utcnow()
    db.session.commit()


def stop_machine(machine: Machine):
    machine.desired_state = MachineState.OFF
    active = WashSession.query.filter_by(
        machine_id=machine.id, status=WashSessionStatus.ACTIVE
    ).first()
    if active:
        active.status = WashSessionStatus.CANCELLED
        active.ended_at = datetime.utcnow()
    db.session.commit()


def apply_router_report(machine: Machine, actual_state: str, power_w: float):
    """
    Verarbeitet eine Zustandsmeldung vom Router. Meldet der Router 'done',
    wird die zugehoerige aktive WashSession abgeschlossen und der
    Sollzustand zurueckgesetzt, damit die Maschine nicht wieder anspringt.
    """
    if actual_state not in MachineState.ALLOWED:
        raise ValueError(f"Ungueltiger Zustand vom Router: {actual_state}")

    machine.actual_state = actual_state
    machine.power_w = power_w
    machine.last_report_at = datetime.utcnow()

    if actual_state == MachineState.DONE:
        machine.desired_state = MachineState.OFF
        active = WashSession.query.filter_by(
            machine_id=machine.id, status=WashSessionStatus.ACTIVE
        ).first()
        if active:
            active.status = WashSessionStatus.COMPLETED
            active.ended_at = datetime.utcnow()

    db.session.commit()


def commands_for_hub(hub) -> dict:
    return {m.label: m.desired_state for m in hub.machines}
