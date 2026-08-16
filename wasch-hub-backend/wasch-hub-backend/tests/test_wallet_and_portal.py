# -*- coding: utf-8 -*-
import pytest
from app.models import Customer
from app.services import wallet
from app.services.wallet import InsufficientBalance


def test_top_up_increases_balance_and_logs_ledger(app, customer):
    with app.app_context():
        c = Customer.query.get(customer)
        start = c.balance_cents
        tx = wallet.top_up(c, 20000, payment_method="mobile_money", reference="ref123")
        assert c.balance_cents == start + 20000
        assert tx.balance_after_cents == c.balance_cents
        assert tx.type == "topup"


def test_charge_decreases_balance(app, customer):
    with app.app_context():
        c = Customer.query.get(customer)
        wallet.charge(c, 30000, note="test")
        assert c.balance_cents == 70000


def test_charge_more_than_balance_raises(app, customer):
    with app.app_context():
        c = Customer.query.get(customer)
        with pytest.raises(InsufficientBalance):
            wallet.charge(c, 999999999)
        assert c.balance_cents == 100000  # unveraendert


def test_admin_adjustment_can_go_negative_input_but_not_negative_balance(app, customer):
    with app.app_context():
        c = Customer.query.get(customer)
        with pytest.raises(InsufficientBalance):
            wallet.admin_adjustment(c, -999999999, note="zu viel")
        assert c.balance_cents == 100000


def test_registration_creates_customer_and_logs_in(client):
    r = client.post("/portal/register",
                     data={"name": "Neu", "phone": "+237622222222", "password": "abcdef"},
                     follow_redirects=True)
    assert "Neu".encode() in r.data


def test_registration_duplicate_phone_rejected(client, customer):
    r = client.post("/portal/register",
                     data={"name": "Doppelt", "phone": "+237699999999", "password": "abcdef"},
                     follow_redirects=True)
    assert "bereits registriert".encode() in r.data


def test_start_without_balance_shows_flash(client, hub_with_machines):
    client.post("/portal/register",
                data={"name": "Arm", "phone": "+237633333333", "password": "abcdef"},
                follow_redirects=True)
    hub_id, _ = hub_with_machines
    from app.models import Machine
    m = Machine.query.filter_by(hub_id=hub_id, label="WM1").first()
    r = client.post(f"/portal/machine/{m.id}/start", follow_redirects=True)
    assert "reicht nicht".encode() in r.data
