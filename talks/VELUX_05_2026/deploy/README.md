# `deploy/` — the demo, deployed the way you actually deploy things

This is the closing-slide material. The notebook proves the pattern. This
proves the pattern fits on the substrate you already run: a kustomize base
that any Kubernetes cluster can apply.

## Topology

```
                                  ┌──────────────────────────┐
                                  │   ConfigMap              │
                                  │   nl-query-schema        │
                                  │   (the governance        │
                                  │    surface lives in git) │
                                  └────────────┬─────────────┘
                                               │ mounted at
                                               │ /etc/nl-query/schema_card.txt
                                               ▼
   ┌──────────────┐    POST /ask    ┌─────────────────────┐    POST /api/generate    ┌──────────────┐
   │  client      │ ──────────────▶ │  nl-query           │ ───────────────────────▶ │  ollama      │
   │  (UI, CLI,   │                 │  Deployment+Service │                          │  Deployment  │
   │   chatbot,   │ ◀────────────── │  (FastAPI)          │ ◀─────────────────────── │  +Service    │
   │   etc.)      │   plan+stats+   │  /healthz /schema   │   JSON response          │  qwen2.5:3b  │
   └──────────────┘   annotation    │  /plan /ask         │                          └──────────────┘
                                    └─────────────────────┘
                                            │
                                            │ reads (demo only — baked into image)
                                            ▼
                                       parquet files
                                       (in production: Kafka consumer → query store)
```

## Layout

```
deploy/
├── README.md                        # this file
└── base/
    ├── kustomization.yaml
    ├── schema-configmap.yaml        # the schema card, in git
    ├── nl-query-deployment.yaml     # FastAPI app, readOnlyRootFilesystem,
    │                                # non-root, resource limits, probes
    ├── nl-query-service.yaml        # ClusterIP, port 80 -> 8000
    ├── ollama-deployment.yaml       # local inference, demo-grade
    └── ollama-service.yaml          # ClusterIP, port 11434
```

## Apply

```bash
# Render to see what will be applied.
kubectl kustomize talks/VELUX_05_2026/deploy/base

# Apply.
kubectl create namespace nl-query-demo
kubectl apply -k talks/VELUX_05_2026/deploy/base

# Pull the model once the ollama pod is up (~30s).
kubectl -n nl-query-demo rollout status deploy/ollama
kubectl -n nl-query-demo exec deploy/ollama -- ollama pull qwen2.5:3b

# Verify.
kubectl -n nl-query-demo port-forward svc/nl-query 8000:80 &
curl -s localhost:8000/healthz | jq
curl -s -X POST localhost:8000/ask \
     -H 'content-type: application/json' \
     -d '{"question":"Show me machines on line 2 that drifted last week"}' | jq
```

## What this is — and isn't

It **is** the deployment shape the talk's last slide should land on:

- One `kubectl apply -k` away from a running service
- Non-root container, readOnlyRootFilesystem, dropped capabilities, probes,
  resource requests and limits
- ConfigMap-driven schema card — change governance by editing a file in git
- Separate inference deployment so the AI plane scales (and is governed)
  independently of the query plane

It **is not** production-ready. The seams worth honest answers about:

| What's demo-grade here              | What real looks like                                  |
|-------------------------------------|-------------------------------------------------------|
| Parquet baked into the image        | Kafka consumer → query store (Iceberg, ClickHouse, …) |
| Ollama in-cluster, `emptyDir` model | Shared inference plane, model PVC, GPU node pool      |
| Single replica, no HPA              | HPA + PodDisruptionBudget                             |
| `default` ServiceAccount disabled   | Workload identity (Workload Identity Federation / IRSA / Azure AD WI) |
| No NetworkPolicy                    | Egress-default-deny, allow only `ollama`              |
| No mTLS / no AuthN                  | Mesh or gateway in front; AuthN at the edge           |
| `latest` Ollama image               | Pinned digest, scanned                                |
| `kubectl apply -k` from a laptop    | GitOps — Argo, Flux, whatever you already run         |

None of these are research problems for the room — they're applied
platform engineering they already do for every other workload. The point
is exactly that.
