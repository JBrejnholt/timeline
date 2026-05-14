# VELUX Talk — May 2026 — Project Context

A 1-hour talk at the VELUX Innovation Center, Skjern, on Thursday
2026-05-21, for the platform-engineering team that runs the VELUX IIoT
platform. This file captures the technical decisions behind the demo so
the work can continue in any tool.

## The talk arc (60 min)

| Time         | Segment                                                   |
|--------------|-----------------------------------------------------------|
| 0:00 – 0:20  | Keynote — reframe AI from threat to leverage               |
| 0:20 – 0:30  | Live demo on factory-shaped time-series data               |
| 0:30 – 0:45  | Substance — what Nordic enterprises are actually doing     |
| 0:45 – 1:00  | Q&A (curated via Slido throughout)                          |

The slides for the keynote + substance segments are at
<https://bitecloud.dk/presentations/velux-ai>. `slides.md` is the
editable Marp source.

## The demo (0:20 – 0:30) — decision and as-built

Anomaly detection alone is a **weak** demo for this audience — they
understand statistics and classical ML already solves it. Built instead:

- **Primary:** Natural-language interface to factory data, delivered as a
  small FastAPI service with a one-page vanilla-HTML UI.
  *"Show me machines on line 2 that drifted last week."* → JSON plan →
  pandas filter + stats → matplotlib chart + plain-language annotation +
  events table. The UI replaces the notebook as the live-demo surface —
  notebooks are dev-grade, not presentation-grade. The notebook
  (`02_nl_query_demo.ipynb`) stays as the engineering artifact.
- **Deferred:** Hybrid classical-detect + LLM-explain (`03_*`). Cut from
  the talk after weighing 60-minute slot vs additional live-demo surface
  area. Adds risk without strengthening the platform-engineering framing.
  May ship after the talk if useful.

The web UI has two tabs:

- **Demo** — context strip, factory-floor schematic (3 lines × 2 machines
  with kind icons that highlight on each query), ask form + four
  canned-question chips, response panel (deterministic summary banner,
  plan-repair notice, LLM annotation, chart, plan JSON, events table).
- **Deployment** — K8s topology diagram with the same component names
  (Service → Pod → ConfigMap → Service → Pod), plus the demo-vs-prod
  seam table. Flipping to this tab is the closing visual.

Synthetic data: shape-realistic, three days at 10-second resolution.
Monday 2026-05-18 → Wednesday 2026-05-20 UTC. ~778k measurements + 9
events including alarms, MES messages and operator notes (some in
Danish) keyed to embedded scenarios — bearing wear + spike on
`folder_02`, stuck-at on `glass_cutter`, planned maintenance on
`sash_assembler`. Framed in the talk as *"imagine this is one of your
Kafka topics."*

### Engineering discipline that lands on stage

Three deterministic safety layers wrap the LLM:

1. **Plan validation** — rejects plans whose dates fall outside the data
   window (catches the model inventing "previous week" baselines that
   don't exist).
2. **Plan repair** — scans the question text for line names, machine
   names, day-of-week, and patches the plan if the model dropped scope.
   Amber notice in the UI when this fires.
3. **Events guard** — if events are in the payload but the LLM's
   annotation doesn't cite any of their codes, prepend a structured
   summary so the operator never sees "no alarms" when alarms are
   present.

Combined message: *the model is allowed to be wrong; the system is not
allowed to be wrong.*

## Substance segment (0:30 – 0:45) — themes

- Where Nordic enterprises actually sit (mostly between productivity
  tools and pilots).
- The five practical patterns (productivity, software delivery,
  enterprise data, agents, platform capability).
- The open-source / private / commercial trade-off reframed as *control
  / locality / cost discipline / optionality.* See
  `bitecloud.dk/insights/meta-did-not-kill-open-source`.
- The thin platform layer — extend the existing container + Kafka
  platform, do not build a new AI platform.
- *Adoption is not access. Governance must create paths. Ownership
  makes it real.*

## What this is NOT

- A briefing dressed as a keynote.
- A maturity-curve walkthrough.
- An "AI for everything" pitch — the credibility comes from saying
  *use AI where it uniquely helps, keep classical tools where they're
  better, the discipline is knowing the difference.*

## Repo layout

```
talks/VELUX_05_2026/
├── CONTEXT.md                          # this file
├── README.md                           # how to run the demo
├── CHEATSHEET.md                       # data inventory + verified question phrasings
├── slides.md                           # Marp source — rendered on bitecloud.dk
├── requirements.txt                    # numpy, pandas, pyarrow, matplotlib, jupyterlab
├── data/
│   ├── synthetic_factory.parquet       # 3 days × 6 machines × 5 signals, ~778k rows
│   ├── synthetic_events.parquet        # 9 events (alarms, MES, operator notes)
│   └── sanity_plots/                   # PNGs from 01's sanity checks
├── notebooks/
│   ├── 01_generate_data.ipynb          # generates the parquets
│   └── 02_nl_query_demo.ipynb          # dev artifact — same pipeline as the service
├── src/
│   ├── factory_data.py                 # synthetic data generator
│   └── nl_query.py                     # 3-stage pipeline + plan-repair + events-guard
├── service/                            # ← live-demo surface
│   ├── app.py                          # FastAPI: /healthz /schema /meta /plan /ask
│   ├── static/index.html               # vanilla UI, two tabs (Demo / Deployment)
│   ├── Dockerfile                      # slim, non-root, baked-in demo data
│   ├── requirements.txt
│   └── README.md                       # local + container + deploy runbook
└── deploy/                             # ← closing visual
    ├── README.md                       # topology, apply commands, prod-vs-demo table
    └── base/                           # kustomize: 5 manifests
        ├── kustomization.yaml
        ├── schema-configmap.yaml       # governance surface
        ├── nl-query-deployment.yaml
        ├── nl-query-service.yaml
        ├── ollama-deployment.yaml
        └── ollama-service.yaml
```

## Working in Claude Code from here

If picking this back up: start by reading this file. The folder is a
regular git repo — commit small, commit often.

To start the live demo locally:

```bash
cd talks/VELUX_05_2026
.venv/bin/uvicorn app:app --app-dir service --port 8000
# open http://localhost:8000/
```

Or in a cluster: `kubectl apply -k deploy/base`. The Dockerfile is in
`service/`; bake with `docker build -f service/Dockerfile -t velux-nl-query:0.1.0 .`
from the talk root.
