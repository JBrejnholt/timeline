# `service/` — FastAPI wrapper + tiny web UI for the NL-query pipeline

The notebook ([`../notebooks/02_nl_query_demo.ipynb`](../notebooks/02_nl_query_demo.ipynb))
is the exploratory surface. This is the platform-native one: same code path
([`../src/nl_query.py`](../src/nl_query.py)), exposed over HTTP, with a
one-page vanilla-HTML UI, deployed as a container.

**The UI is the live-demo surface.** A maintenance tech on a tablet types
a question, one chart + annotation appears in place of the previous one.
Same Kafka topic, same schema card in a ConfigMap, same three stages
under the hood.

## Endpoints

| Method | Path                  | Returns                                            |
|--------|-----------------------|----------------------------------------------------|
| `GET`  | `/`                   | redirects to `/static/index.html` (the UI)         |
| `GET`  | `/static/index.html`  | the one-page UI                                    |
| `GET`  | `/healthz`            | liveness + readiness + which LLM client is active  |
| `GET`  | `/schema`             | the schema card — the governance surface           |
| `POST` | `/plan`               | NL question → validated JSON plan                  |
| `POST` | `/ask`                | full pipeline: plan + stats + events + annotation + base64 chart PNG |

## Config (env)

| Variable           | Default                            | Notes                                                |
|--------------------|------------------------------------|------------------------------------------------------|
| `DATA_PATH`        | `/data/measurements.parquet`       | long-format parquet                                  |
| `EVENTS_PATH`      | `/data/events.parquet`             | events log                                           |
| `SCHEMA_CARD_PATH` | unset (uses in-code constant)      | in K8s: mounted ConfigMap key                        |
| `OLLAMA_HOST`      | `http://localhost:11434`           | use `http://ollama:11434` in-cluster                 |
| `MODEL`            | `qwen2.5:3b`                       | swap to `qwen2.5vl:3b` if that's what you have pulled|
| `USE_MOCK`         | unset                              | `1` forces the deterministic mock client             |
| `STATIC_DIR`       | `<app dir>/static`                 | override to point at a different UI bundle           |

## Run locally (no container)

```bash
cd talks/VELUX_05_2026
DATA_PATH=data/synthetic_factory.parquet \
EVENTS_PATH=data/synthetic_events.parquet \
.venv/bin/uvicorn app:app --app-dir service --port 8000
# Open http://localhost:8000/  → the UI
```

On startup the service warms the model in the lifespan hook so the first
audience question doesn't wait 30 seconds for cold-start inference.

Force mock mode for an offline rehearsal:

```bash
USE_MOCK=1 .venv/bin/uvicorn app:app --app-dir service --port 8000
```

## Build and run the container

```bash
# Build from the talk root (the Dockerfile assumes that working dir).
docker build -f service/Dockerfile -t velux-nl-query:0.1.0 .

# Run with mock client (no Ollama needed).
docker run --rm -p 8000:8000 -e USE_MOCK=1 velux-nl-query:0.1.0

# Open http://localhost:8000/
```

## Deploy to a cluster

See [`../deploy/`](../deploy/). Kustomize base with five resources, schema
card in a ConfigMap. `kubectl apply -k talks/VELUX_05_2026/deploy/base`
from any cluster you can reach.

## Production seams

The image bakes the parquet in for demo convenience. In a real factory
deployment those bytes come from somewhere else:

- A Kafka consumer writing a query-friendly store (object storage + Iceberg,
  ClickHouse, DuckDB on a PVC, etc.), and this service queries it.
- Or a separate analytical service entirely, and this becomes a thin NL
  adapter over it.

The point of the talk: *the AI layer is a thin platform component*. It
should look like the other things you already deploy.

## Pre-talk rehearsal checklist

1. Pull a model that's actually good at JSON: `ollama pull qwen2.5:3b`
2. `cd talks/VELUX_05_2026 && DATA_PATH=data/synthetic_factory.parquet EVENTS_PATH=data/synthetic_events.parquet .venv/bin/uvicorn app:app --app-dir service --port 8000`
3. Watch the logs for `model warm-up complete` before going on stage.
4. Open `http://localhost:8000/` full-screen on the projector.
5. Click the four chips top-to-bottom. Each should produce a fresh chart
   + annotation in 2-9 seconds.
6. If anything looks wrong: `USE_MOCK=1` and restart — the mock answers
   the three canonical questions in milliseconds.
