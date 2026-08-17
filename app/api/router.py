# -*- coding: utf-8 -*-
"""
Endpunkte, die der Router (nicht ein Mensch) aufruft. Auth ueber das
Hub-eigene Token im Header 'X-Hub-Token' - jeder Hub hat ein eigenes,
kompromittiert einer nicht automatisch alle anderen.
"""
from flask import Blueprint, request, jsonify
from app.extensions import db, limiter
from app.models import Hub
from app.services.machine_control import commands_for_hub, apply_router_report

router_api = Blueprint("router_api", __name__, url_prefix="/api/router")


def _authenticate_hub():
    token = request.headers.get("X-Hub-Token")
    if not token:
        return None
    return Hub.query.filter_by(token=token, is_active=True).first()


@router_api.route("/commands", methods=["GET"])
@limiter.limit("120 per minute")   # ein Poll alle ~0.5s waere Missbrauch, alle 15-30s normal
def get_commands():
    hub = _authenticate_hub()
    if not hub:
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(commands_for_hub(hub))


@router_api.route("/report", methods=["POST"])
@limiter.limit("120 per minute")
def post_report():
    """
    Erwartetes JSON:
    {"WM1": {"actual_state": "running", "power_w": 1180},
     "WM2": {"actual_state": "off", "power_w": 0}}
    """
    hub = _authenticate_hub()
    if not hub:
        return jsonify({"error": "unauthorized"}), 401

    payload = request.get_json(force=True, silent=True) or {}
    machines_by_label = {m.label: m for m in hub.machines}

    errors = []
    for label, data in payload.items():
        machine = machines_by_label.get(label)
        if not machine:
            errors.append(f"unbekannte Maschine: {label}")
            continue
        try:
            apply_router_report(machine, data.get("actual_state", "off"), data.get("power_w", 0))
        except ValueError as e:
            errors.append(str(e))

    if errors:
        return jsonify({"ok": False, "errors": errors}), 400
    return jsonify({"ok": True})
