# -*- coding: utf-8 -*-
"""
Einstiegspunkt speziell fuer cPanel "Setup Python App" (Passenger).
cPanel/Passenger sucht standardmaessig nach einer Datei namens
"passenger_wsgi.py" mit einer Variable "application" - NICHT nach
wsgi.py/app wie bei gunicorn (Render/Railway). Deshalb diese duenne
Adapter-Datei zusaetzlich zu wsgi.py, beide zeigen auf dieselbe App.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app  # noqa: E402

application = create_app()
