# VELUX Talk — May 2026

Demo code and notes for a 1-hour session with the VELUX IIoT platform team in
Skjern on Thursday 2026-05-21.

**Rendered slides:** <https://bitecloud.dk/presentations/velux-ai>

**Working docs:**
- [`CONTEXT.md`](./CONTEXT.md) — project context, technical decisions, repo
  layout. Read first.
- [`CHEATSHEET.md`](./CHEATSHEET.md) — every defect, drift and event in the
  data, with verified question phrasings.
- [`TALK_NOTES.md`](./TALK_NOTES.md) — pre-demo runbook (30-min checklist,
  optional `kind` staging).
- [`slides.md`](./slides.md) — Marp source for the deck. Rendered at the URL
  above.

## Layout

```
.
├── CONTEXT.md / CHEATSHEET.md / TALK_NOTES.md      # docs
├── requirements.txt
├── data/
│   ├── synthetic_factory.parquet                   # 3 days × 6 machines × 5 signals
│   ├── synthetic_events.parquet                    # 9 alarms / MES / operator notes
│   └── sanity_plots/                               # PNGs from 01's sanity checks
├── notebooks/
│   ├── 01_generate_data.ipynb                      # generates the parquets
│   └── 02_nl_query_demo.ipynb                      # dev artifact — not for stage
├── src/
│   ├── factory_data.py                             # synthetic data generator
│   └── nl_query.py                                 # 3-stage pipeline + guards
├── service/                                        # ← live-demo surface
│   ├── app.py                                      # FastAPI
│   ├── static/index.html                           # vanilla UI, Demo + Deployment tabs
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md                                   # runbook
└── deploy/                                         # ← closing-slide material
    ├── README.md
    └── base/                                       # kustomize: 5 manifests
```

## What this demo proves

The talk argues: *use AI where it uniquely helps, keep classical tools where
they're better, the engineering discipline is knowing the difference.* The
demo lands all three:

- **The web UI** (the live-demo surface) shows something classical analytics
  alone cannot do — a natural-language interface to factory time-series, with
  the LLM strictly as the communication layer. Pandas does the actual work;
  the LLM only translates English ↔ structured query and structured stats ↔
  English. Three deterministic guards (plan validation, plan repair, events
  guard) catch what small models routinely fumble.
- **The Deployment tab in the same UI** shows the platform-engineering shape
  — Service + Deployment + ConfigMap + Service + Deployment — the same
  substrate the audience already runs for every other workload.
- **The notebook** (`02_nl_query_demo.ipynb`) is the engineering artifact —
  reuses the same `src/nl_query.py` as the service. Kept in the repo for
  reproducibility; not shown on stage.

The framing in the room: *"imagine this is one of your Kafka topics."*

## Running locally

The demo is a FastAPI service plus a tiny vanilla-HTML UI. One command:

```bash
cd talks/VELUX_05_2026
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt -r service/requirements.txt

# Generate the data (one-time)
jupyter lab notebooks/01_generate_data.ipynb   # run-all

# Start the demo
ollama pull qwen2.5:3b        # one-time, ~2 GB
uvicorn app:app --app-dir service --port 8000

# Open http://localhost:8000/
```

`USE_MOCK=1` forces the deterministic mock client — useful for rehearsal
without an LLM, or when conference wifi is hostile.

See [`service/README.md`](./service/README.md) for the full runbook (env
vars, container build, smoke-test commands).

## Deploying to a Kubernetes cluster

Kustomize base, no Helm. Five manifests, no Argo dependency:

```bash
kubectl apply -k deploy/base
kubectl -n nl-query-demo rollout status deploy/ollama
kubectl -n nl-query-demo exec deploy/ollama -- ollama pull qwen2.5:3b
kubectl -n nl-query-demo port-forward svc/nl-query 8000:80
# Open http://localhost:8000/
```

See [`deploy/README.md`](./deploy/README.md) for the topology diagram and
the demo-grade-vs-production seam table.
