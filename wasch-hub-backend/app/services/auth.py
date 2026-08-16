# -*- coding: utf-8 -*-
"""
Decorators, die sicherstellen, dass ein eingeloggter Kunde NIEMALS eine
Admin-Route erreichen kann und umgekehrt - auch nicht durch Erraten der
URL. login_required allein reicht nicht, weil beide Nutzer-Typen denselben
LoginManager teilen (siehe app/__init__.py load_user).
"""
from functools import wraps
from flask import abort
from flask_login import login_required, current_user
from app.models import Customer, AdminUser


def customer_required(f):
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not isinstance(current_user, Customer):
            abort(403)
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not isinstance(current_user, AdminUser):
            abort(403)
        return f(*args, **kwargs)
    return wrapper
