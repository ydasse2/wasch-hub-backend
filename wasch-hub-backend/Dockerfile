FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_ENV=production
EXPOSE 8000

# 4 Worker als Startwert - bei mehr gleichzeitigen Hubs/Kunden hochskalieren
# (Faustregel: 2-4 x CPU-Kerne). Bei echter Skalierung eher mehrere Container-
# Instanzen hinter einem Load Balancer als einen Container mit vielen Workern.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "wsgi:app"]
