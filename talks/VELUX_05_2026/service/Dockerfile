# Small single-stage image. Mirrors the notebook's three-stage pipeline,
# served behind FastAPI. The synthetic parquet is baked in for demo
# convenience — in production this is where you would either mount a PVC
# fed by a Kafka consumer or query a separate analytical store.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY service/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Shared helper module — same code path the notebook uses.
COPY src/nl_query.py /app/nl_query.py
COPY service/app.py /app/app.py
COPY service/static /app/static

# Demo data — see comment at top. Replace with a volume mount in prod.
COPY data/synthetic_factory.parquet /data/measurements.parquet
COPY data/synthetic_events.parquet  /data/events.parquet

RUN useradd --create-home --shell /bin/false svc \
 && chown -R svc:svc /app /data
USER svc

EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=3s --start-period=10s \
  CMD python -c "import urllib.request as r; r.urlopen('http://localhost:8000/healthz', timeout=2)" || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
