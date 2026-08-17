# -*- coding: utf-8 -*-
from app.models import Hub, Machine


def test_commands_requires_valid_token(client, hub_with_machines):
    hub_id, token = hub_with_machines
    r = client.get("/api/router/commands", headers={"X-Hub-Token": "falsch"})
    assert r.status_code == 401


def test_commands_returns_desired_states(client, hub_with_machines):
    hub_id, token = hub_with_machines
    r = client.get("/api/router/commands", headers={"X-Hub-Token": token})
    assert r.status_code == 200
    data = r.get_json()
    assert data == {"WM1": "off", "WM2": "off", "WM3": "off"}


def test_report_updates_actual_state(client, hub_with_machines, app):
    hub_id, token = hub_with_machines
    r = client.post("/api/router/report", headers={"X-Hub-Token": token},
                     json={"WM1": {"actual_state": "running", "power_w": 1200}})
    assert r.status_code == 200

    with app.app_context():
        m = Machine.query.filter_by(label="WM1").first()
        assert m.actual_state == "running"
        assert m.power_w == 1200


def test_report_done_resets_desired_state(client, hub_with_machines, app):
    hub_id, token = hub_with_machines
    from app.extensions import db
    with app.app_context():
        m = Machine.query.filter_by(label="WM1").first()
        m.desired_state = "running"
        db.session.commit()

    client.post("/api/router/report", headers={"X-Hub-Token": token},
                json={"WM1": {"actual_state": "done", "power_w": 0}})

    r = client.get("/api/router/commands", headers={"X-Hub-Token": token})
    assert r.get_json()["WM1"] == "off"


def test_report_rejects_unknown_machine_label(client, hub_with_machines):
    hub_id, token = hub_with_machines
    r = client.post("/api/router/report", headers={"X-Hub-Token": token},
                     json={"DOES_NOT_EXIST": {"actual_state": "running", "power_w": 10}})
    assert r.status_code == 400


def test_report_rejects_invalid_state(client, hub_with_machines):
    hub_id, token = hub_with_machines
    r = client.post("/api/router/report", headers={"X-Hub-Token": token},
                     json={"WM1": {"actual_state": "explodiert", "power_w": 10}})
    assert r.status_code == 400
