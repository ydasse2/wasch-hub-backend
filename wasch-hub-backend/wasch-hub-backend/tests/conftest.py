# -*- coding: utf-8 -*-
import pytest
from app import create_app
from app.config import TestConfig
from app.extensions import db as _db
from app.models import Hub, Machine, AdminUser, Customer


@pytest.fixture
def app():
    app = create_app(config_object=TestConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def hub_with_machines(app):
    with app.app_context():
        hub = Hub(name="Test Hub", location="Testville")
        _db.session.add(hub)
        _db.session.flush()
        for i in range(1, 4):
            _db.session.add(Machine(hub_id=hub.id, label=f"WM{i}", price_cents=50000))
        _db.session.commit()
        _db.session.refresh(hub)
        return hub.id, hub.token


@pytest.fixture
def admin_user(app):
    with app.app_context():
        user = AdminUser(username="admin", role="superadmin")
        user.set_password("testpass123")
        _db.session.add(user)
        _db.session.commit()
        return user.id


@pytest.fixture
def customer(app):
    with app.app_context():
        c = Customer(name="Test Kunde", phone="+237699999999", balance_cents=100000)
        c.set_password("testpass123")
        _db.session.add(c)
        _db.session.commit()
        return c.id
