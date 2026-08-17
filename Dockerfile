FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh

ENV FLASK_ENV=production
EXPOSE 8000

# entrypoint.sh richtet bei jedem Start die DB ein (Migration + Seed,
# beide sicher mehrfach ausfuehrbar) und startet danach gunicorn.
# 4 Worker als Startwert - bei mehr gleichzeitigen Hubs/Kunden hochskalieren
# (Faustregel: 2-4 x CPU-Kerne). Bei echter Skalierung eher mehrere Container-
# Instanzen hinter einem Load Balancer als einen Container mit vielen Workern.
CMD ["./entrypoint.sh"]
