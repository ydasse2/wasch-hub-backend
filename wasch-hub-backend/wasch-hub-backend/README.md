# Wasch-Hub Backend

Backend fuer den ferngesteuerten, bezahlten Wasch-Hub-Service. Verwaltet
mehrere Standorte (Hubs), Waschmaschinen, **ein Kunden-Portal mit Guthaben-
Konto** und eine **strikt getrennte Admin-Plattform**.

## Zwei getrennte Oberflaechen

| | Kunden-Portal `/portal` | Admin-Plattform `/admin` |
|---|---|---|
| Fuer wen | Endkunden (Registrierung selbst moeglich) | Internes Personal (Konten nur von Admin angelegt) |
| Sieht | Nur eigenes Guthaben, eigene Waschgaenge, aktive Standorte | Alle Hubs, alle Kunden, alle Transaktionen, Hub-Tokens |
| Login-Daten | Telefonnummer + Passwort | Benutzername + Passwort |
| Kann ausloesen | Waschgang starten (vom eigenen Guthaben), Demo-Aufladung | Direkt-Freigabe ohne Kunde (Support/Demo), Guthaben-Korrekturen, Hub/Maschinen einsehen |

**Die Trennung ist technisch erzwungen, nicht nur durch Menufuehrung:**
`Customer` und `AdminUser` sind unterschiedliche Modelle, die sich zwar
einen `LoginManager` teilen (ueber ein Praefix in `get_id()`, siehe
`app/__init__.py`), aber `@customer_required` / `@admin_required`
(`app/services/auth.py`) pruefen den tatsaechlichen Objekttyp - ein Kunde,
der `/admin/` errät, bekommt 403, kein Redirect zum falschen Login. Getestet
in `tests/test_admin.py` (`test_customer_cannot_reach_admin_dashboard` etc.).

## Guthaben-Modell (warum, siehe Begruendung im Chat-Verlauf)

Kunde laedt per Mobile Money Guthaben auf `Customer.balance_cents` (gecached),
jede Bewegung wird IMMER zugleich im `WalletTransaction`-Ledger protokolliert
(`app/services/wallet.py` - einziger Ort, an dem sich der Kontostand aendert).
Ein Waschgang bucht vom Guthaben ab (`start_wash` in `machine_control.py`)
und legt eine `WashSession` an, die mit genau der `WalletTransaction`
verknuepft ist, die dafuer belastet wurde - bei einem Streitfall laesst
sich das 1:1 nachvollziehen.

## Projektstruktur (Ergaenzungen gegenueber der ersten Version)

```
app/
├── models/
│   ├── customer.py            # Kunde, get_id() mit "customer:"-Praefix
│   ├── wallet_transaction.py  # Ledger: topup/wash_charge/refund/admin_adjustment
│   ├── wash_session.py        # ein Waschvorgang, verknuepft mit WalletTransaction
│   └── user.py                # AdminUser, get_id() mit "admin:"-Praefix
├── services/
│   ├── wallet.py               # top_up / charge / refund / admin_adjustment
│   ├── machine_control.py      # start_wash (mit Guthaben), admin_force_start (ohne)
│   └── auth.py                 # @customer_required / @admin_required Decorators
├── api/
│   ├── portal.py                # /portal/* - Kunden-Blueprint
│   ├── admin.py                 # /admin/* - inkl. Kundenverwaltung
│   ├── router.py                # /api/router/* - unveraendert
│   └── payment.py               # Webhook laedt jetzt Guthaben auf (nicht mehr 1 Maschine direkt)
└── templates/
    ├── portal/    # dashboard, login, register, session (auto-refresh), history
    └── admin/     # dashboard, login, customers (Liste+Suche), customer_detail
```

## Warum diese Struktur (kurz begruendet)

| Entscheidung | Begruendung |
|---|---|
| **App-Factory-Pattern** (`create_app()`) | Saubere Tests (jeder Test bekommt eine frische App+DB-Instanz), Basis fuer spaetere Multi-Config (dev/staging/prod) |
| **SQLAlchemy + Flask-Migrate** statt JSON-Datei | Nebenlaeufigkeit (mehrere Hubs schreiben gleichzeitig), Schema-Aenderungen nachvollziehbar versioniert statt manuell |
| **SQLite lokal, Postgres via `DATABASE_URL` in Produktion** | Kein Setup-Aufwand fuer schnelles Testen, aber der Code aendert sich beim Wechsel NICHT - nur eine Env-Variable |
| **Ein Token PRO HUB** statt einem globalen Token | Kompromittiert ein Hub-Token, sind nicht automatisch alle anderen Standorte betroffen - wichtig sobald ihr auf 10+ Hubs skaliert |
| **Router pollt das Backend, nicht umgekehrt** | LTE-SIM-Karten haben fast immer keine oeffentliche IP (CGNAT) - das Backend kann den Router technisch gar nicht direkt erreichen |
| **Transaction-Tabelle von Anfang an** | Fuer einen bezahlten Service unverzichtbar: Abrechnung, Streitfaelle, spaeter Auswertungen (Umsatz/Hub, Auslastung/Maschine) - nachtraeglich einzubauen ist deutlich schmerzhafter |
| **Service-Layer** (`app/services/machine_control.py`) | Freigabe-Logik nur an EINER Stelle, egal ob der Aufruf vom Dashboard, vom Router-Report oder spaeter vom echten Payment-Webhook kommt |
| **Session-Login (Flask-Login)** statt Token in der URL | Tokens in URLs landen in Server-Logs, Browser-Verlauf, Referrer-Headern - fuer ein Admin-Interface ungeeignet |
| **Flask-Limiter auf Login + Router-Endpunkten** | Bremst Brute-Force auf den Login und Missbrauch der Router-API |

## Projektstruktur

```
wasch-hub-backend/
├── app/
│   ├── __init__.py          # App-Factory, Blueprint-Registrierung
│   ├── config.py            # Dev/Prod/Test-Konfiguration
│   ├── extensions.py        # db, migrate, login_manager, limiter
│   ├── models/               # Hub, Machine, Transaction, AdminUser
│   ├── api/
│   │   ├── router.py         # Router-Polling (/api/router/*), Hub-Token-Auth
│   │   ├── admin.py          # Dashboard-Aktionen, Session-Auth
│   │   └── payment.py        # STUB fuer Mobile-Money-Webhook
│   ├── services/
│   │   └── machine_control.py  # Zentrale Geschaeftslogik
│   └── templates/            # dashboard.html, login.html
├── migrations/                # Alembic-Migrationen (versioniert, im Git)
├── tests/                     # pytest, 14 Tests, siehe unten
├── scripts/seed.py            # Erzeugt Test-Hub + 3 Maschinen + Admin-Login
├── router_scripts/            # Vorlage fuers Router-seitige Polling-Skript
├── Dockerfile, docker-compose.yml, Procfile
└── wsgi.py                    # Einstiegspunkt fuer gunicorn
```

## Lokal starten

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # anpassen, v.a. SECRET_KEY
export FLASK_APP=wsgi.py

flask db upgrade              # Schema anlegen
python scripts/seed.py        # Test-Hub + Admin-Login erzeugen -> Token notieren!

python wsgi.py                # laeuft auf http://localhost:5000
```

Dashboard: `http://localhost:5000/admin/` (Login: admin / changeme-sofort-aendern
- **sofort aendern**, siehe unten).

## Mit Docker (naeher an Produktion, inkl. Postgres)

```bash
docker compose up --build
docker compose exec web flask db upgrade
docker compose exec web python scripts/seed.py
```

## Tests

```bash
pytest tests/ -v      # 28 Tests: Router-API, Admin/Portal-Trennung, Wallet, Geschaeftslogik
```

## Neuen Hub anlegen (zweiter Standort)

Aktuell per Python-Shell (ein eigener CLI-Befehl oder eine Admin-UI-Seite
dafuer ist ein guter naechster Ausbauschritt):

```python
from app import create_app
from app.extensions import db
from app.models import Hub, Machine

app = create_app()
with app.app_context():
    hub = Hub(name="Hub Yaounde Centre", location="Centre-ville", country="Cameroun")
    db.session.add(hub)
    db.session.flush()
    for i in range(1, 4):
        db.session.add(Machine(hub_id=hub.id, label=f"WM{i}"))
    db.session.commit()
    print("Token:", hub.token)   # dieses Token ins Router-Skript eintragen
```

## Was als Naechstes auszubauen ist (Prioritaet von oben nach unten)

1. **Echte Mobile-Money-Anbindung** in `app/api/payment.py` - Signaturpruefung
   des gewaehlten Anbieters (MTN MoMo/Orange Money) ist aktuell nur ein Stub
   und markiert **NICHT sicher fuer den Live-Betrieb**. Laedt bei echter
   Anbindung `Customer`-Guthaben auf (nicht mehr eine einzelne Maschine).
2. **`/portal/topup/demo` entfernen oder absichern**, bevor es live geht -
   aktuell kann sich jeder eingeloggte Kunde beliebig Guthaben "aufladen"
   ohne echte Zahlung. Ausdruecklich nur fuer Test/Demo gedacht.
3. **SMS-OTP-Login statt Passwort** fuer Kunden - im Zielmarkt realistischer
   als ein gemerktes Passwort, braucht aber einen SMS-Versender (z.B. ueber
   den gleichen Mobile-Money-/Telco-Anbieter oder einen SMS-Gateway-Dienst).
4. **Admin-UI zum Hub/Maschinen-Anlegen** statt Python-Shell.
5. **Rollen-Differenzierung testen**: `operator`-Rolle ist im Modell
   vorbereitet (nur eigener Hub, kein Kundenzugriff), aber noch keine UI,
   um operator-Nutzer anzulegen.
6. **Monitoring/Alarmierung** bei Hub offline (`Hub.is_online()` existiert
   schon als Property - fehlt: eine Benachrichtigung ab X Minuten Funkstille).
7. **Rate-Limiter-Storage** auf Redis umstellen, sobald mehr als ein
   Web-Prozess laeuft (aktuell In-Memory pro Worker).
8. **Datetime-Deprecation-Warnungen** beheben (`datetime.utcnow()` ->
   `datetime.now(timezone.utc)`) - funktioniert noch, aber in kuenftigem
   Python ein Breaking Change.

## Sicherheits-Checkliste vor dem ersten echten (nicht-Demo) Einsatz

- [ ] `SECRET_KEY` auf einen echten Zufallswert setzen (nicht den Default)
- [ ] Seed-Admin-Passwort sofort aendern
- [ ] `DATABASE_URL` auf Postgres umstellen (nicht SQLite in Produktion)
- [ ] Payment-Webhook-Signaturpruefung implementieren, bevor er live geht
- [ ] HTTPS erzwingen (Hoster-Einstellung; `SESSION_COOKIE_SECURE=True`
      ist in `ProductionConfig` schon gesetzt)
- [ ] `.env` ist in `.gitignore` - nie Secrets committen
