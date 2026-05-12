# `service/` — FastAPI wrapper for the NL-query pipeline

The notebook ([`../notebooks/02_nl_query_demo.ipynb`](../notebooks/02_nl_query_demo.ipynb))
is the exploratory surface. This is the platform-native one: same code path
([`../src/nl_query.py`](../src/nl_query.py)), exposed over HTTP, deployed
as a container, governed via a ConfigMap, shipped via Argo.

## Endpoints

| Method | Path        | Returns                                             |
|--------|-------------|-----------------------------------------------------|
| `GET`  | `/healthz`  | liveness + readiness + which LLM client is active   |
| `GET`  | `/schema`   | the schema card — the governance surface            |
| `POST` | `/plan`     | NL question → validated JSON plan                   |
| `POST` | `/ask`      | full pipeline: plan + stats + events + annotation   |

## Config (env)

| Variable           | Default                            | Notes                                                |
|--------------------|------------------------------------|------------------------------------------------------|
| `DATA_PATH`        | `/data/measurements.parquet`       | long-format parquet                                  |
| `EVENTS_PATH`      | `/data/events.parquet`             | events log                                           |
| `SCHEMA_CARD_PATH` | unset (uses in-code constant)      | in K8s: mounted ConfigMap key                        |
| `OLLAMA_HOST`      | `http://localhost:11434`           | use `http://ollama:11434` in-cluster                 |
| `MODEL`            | `qwen2.5:3b`                       | swap to `qwen2.5vl:3b` if that's what you have pulled|
| `USE_MOCK`         | unset                              | `1` forces the deterministic mock client             |

## Run locally (no container)

```bash
cd talks/VELUX_05_2026
.venv/bin/uvicorn app:app --app-dir service --reload \
    --env-file <(echo "DATA_PATH=data/synthetic_factory.parquet"; \
                 echo "EVENTS_PATH=data/synthetic_events.parquet")
```

Or just smoke-test in-process with FastAPI's TestClient — see the bottom
of this README.

## Build and run the container

```bash
# Build from the talk root (the Dockerfile assumes that working dir).
docker build -f service/Dockerfile -t velux-nl-query:0.1.0 .

# Run with mock client (no Ollama needed).
docker run --rm -p 8000:8000 -e USE_MOCK=1 velux-nl-query:0.1.0

curl -s localhost:8000/healthz | jq
curl -s localhost:8000/schema  | jq -r '.schema_card' | head
curl -s -X POST localhost:8000/ask \
     -H 'content-type: application/json' \
     -d '{"question":"Show me machines on line 2 that drifted last week"}' | jq
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
