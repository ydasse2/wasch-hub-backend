# -*- coding: utf-8 -*-
def login_admin(client, username="admin", password="testpass123"):
    return client.post("/admin/login", data={"username": username, "password": password},
                        follow_redirects=True)


def login_customer(client, phone="+237699999999", password="testpass123"):
    return client.post("/portal/login", data={"phone": phone, "password": password},
                        follow_redirects=True)


def test_dashboard_requires_login(client):
    r = client.get("/admin/", follow_redirects=False)
    assert r.status_code == 302


def test_login_wrong_password_rejected(client, admin_user):
    login_admin(client, password="falsch")
    r2 = client.get("/admin/", follow_redirects=False)
    assert r2.status_code == 302


def test_login_success_reaches_dashboard(client, admin_user, hub_with_machines):
    r = login_admin(client)
    assert r.status_code == 200
    assert "Dashboard".encode() in r.data


def test_admin_force_start_does_not_create_wash_session(client, admin_user, hub_with_machines, app):
    from app.models import Machine, WashSession
    login_admin(client)
    hub_id, token = hub_with_machines
    with app.app_context():
        m = Machine.query.filter_by(label="WM1").first()
        machine_id = m.id

    client.post(f"/admin/machine/{machine_id}/activate", follow_redirects=True)

    with app.app_context():
        m = Machine.query.get(machine_id)
        assert m.desired_state == "running"
        # bewusst KEINE WashSession - das ist eine Admin-Direktfreigabe ohne Kunde
        assert WashSession.query.filter_by(machine_id=machine_id).count() == 0


def test_customer_cannot_reach_admin_dashboard(client, customer):
    login_customer(client)
    r = client.get("/admin/", follow_redirects=False)
    assert r.status_code == 403


def test_admin_cannot_reach_customer_portal(client, admin_user):
    login_admin(client)
    r = client.get("/portal/", follow_redirects=False)
    assert r.status_code == 403


def test_anonymous_cannot_reach_either(client):
    r1 = client.get("/admin/", follow_redirects=False)
    r2 = client.get("/portal/", follow_redirects=False)
    assert r1.status_code == 302
    assert r2.status_code == 302
