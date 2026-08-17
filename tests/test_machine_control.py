# -*- coding: utf-8 -*-
import pytest
from app.models import Hub, Machine, Customer, MachineState, WashSession, WashSessionStatus
from app.services.machine_control import (
    start_wash, admin_force_start, stop_machine, apply_router_report,
    commands_for_hub, MachineBusy
)
from app.services.wallet import InsufficientBalance


@pytest.fixture
def machine(app, hub_with_machines):
    hub_id, _ = hub_with_machines
    with app.app_context():
        return Machine.query.filter_by(hub_id=hub_id, label="WM1").first()


def test_start_wash_charges_wallet_and_sets_running(app, machine, customer):
    with app.app_context():
        m = Machine.query.get(machine.id)
        c = Customer.query.get(customer)
        session = start_wash(c, m)
        assert m.desired_state == MachineState.RUNNING
        assert c.balance_cents == 100000 - m.price_cents
        assert session.status == WashSessionStatus.ACTIVE
        assert session.wallet_transaction.amount_cents == -m.price_cents


def test_start_wash_insufficient_balance_raises_and_nothing_committed(app, machine, customer):
    with app.app_context():
        m = Machine.query.get(machine.id)
        c = Customer.query.get(customer)
        m.price_cents = 999999999  # mehr als das Guthaben
        with pytest.raises(InsufficientBalance):
            start_wash(c, m)
        assert m.desired_state == MachineState.OFF
        assert WashSession.query.filter_by(machine_id=m.id).count() == 0


def test_start_wash_on_busy_machine_raises(app, machine, customer):
    with app.app_context():
        m = Machine.query.get(machine.id)
        c = Customer.query.get(customer)
        start_wash(c, m)
        with pytest.raises(MachineBusy):
            start_wash(c, m)


def test_admin_force_start_no_wallet_involved(app, machine):
    with app.app_context():
        m = Machine.query.get(machine.id)
        admin_force_start(m)
        assert m.desired_state == MachineState.RUNNING


def test_stop_cancels_active_session(app, machine, customer):
    with app.app_context():
        m = Machine.query.get(machine.id)
        c = Customer.query.get(customer)
        session = start_wash(c, m)
        stop_machine(m)
        assert m.desired_state == MachineState.OFF
        s = WashSession.query.get(session.id)
        assert s.status == WashSessionStatus.CANCELLED


def test_router_report_done_completes_session_and_resets_desired(app, machine, customer):
    with app.app_context():
        m = Machine.query.get(machine.id)
        c = Customer.query.get(customer)
        session = start_wash(c, m)
        apply_router_report(m, "running", 1200)
        apply_router_report(m, "done", 0)
        assert m.desired_state == MachineState.OFF
        s = WashSession.query.get(session.id)
        assert s.status == WashSessionStatus.COMPLETED
        assert s.ended_at is not None


def test_apply_router_report_invalid_state_raises(app, machine):
    with app.app_context():
        m = Machine.query.get(machine.id)
        with pytest.raises(ValueError):
            apply_router_report(m, "ungueltig", 10)


def test_commands_for_hub_reflects_desired_states(app, hub_with_machines):
    hub_id, _ = hub_with_machines
    with app.app_context():
        hub = Hub.query.get(hub_id)
        cmds = commands_for_hub(hub)
        assert set(cmds.keys()) == {"WM1", "WM2", "WM3"}
        assert all(v == "off" for v in cmds.values())
