# -*- coding: utf-8 -*-
"""
STUB fuer die kuenftige Mobile-Money-Anbindung (MTN MoMo, Orange Money, etc.).
Aktuell NICHT produktiv nutzbar - es fehlt die Signaturpruefung des jeweiligen
Anbieters. Seit Einfuehrung des Guthaben-Modells laedt eine bestaetigte
Zahlung das KUNDENGUTHABEN auf (nicht mehr eine einzelne Maschine direkt) -
der Kunde startet den Waschgang danach selbst im Portal vom eigenen Guthaben.

Ablauf, sobald echt angebunden:
1. Kunde zahlt in seiner Mobile-Money-App an eine Merchant-Nummer,
   mit seiner Telefonnummer oder Kunden-ID als Referenz/Memo.
2. Anbieter ruft DIESEN Endpunkt auf (Server-zu-Server), sobald Zahlung
   bestaetigt ist.
3. Signatur pruefen (TODO, anbieterspezifisch).
4. wallet.top_up(...) aufrufen.
"""
from flask import Blueprint, request, jsonify, current_app
from app.models import Customer
from app.services import wallet

payment_api = Blueprint("payment_api", __name__, url_prefix="/api/payment")


def _verify_signature(req) -> bool:
    # TODO: durch echte Signaturpruefung des gewaehlten Anbieters ersetzen,
    # BEVOR dieser Endpunkt live geschaltet wird. Ohne das kann jeder
    # eine Aufladung vortaeuschen.
    current_app.logger.warning("Payment-Webhook: Signaturpruefung ist noch ein Stub!")
    return True


@payment_api.route("/webhook", methods=["POST"])
def webhook():
    if not _verify_signature(request):
        return jsonify({"error": "invalid signature"}), 401

    data = request.get_json(force=True, silent=True) or {}
    phone = data.get("customer_phone")
    amount_cents = data.get("amount_cents")
    reference = data.get("reference")

    customer = Customer.query.filter_by(phone=phone).first()
    if not customer:
        return jsonify({"error": "unknown customer"}), 404

    wallet.top_up(customer, amount_cents, payment_method="mobile_money", reference=reference)
    return jsonify({"ok": True, "new_balance_cents": customer.balance_cents})
