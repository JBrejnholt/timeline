# Talk Notes — VELUX Skjern, Thursday 2026-05-21

Read once the morning of. Leave behind on the day. Pair with
[`CHEATSHEET.md`](./CHEATSHEET.md) for the per-question reference.

## 30 minutes before you walk on

```bash
# 1. Confirm model is pulled
ollama list   # should include qwen2.5:3b

# 2. Stop any old uvicorn, start fresh
pkill -f 'uvicorn app:app'
cd talks/VELUX_05_2026
.venv/bin/uvicorn app:app --app-dir service --port 8000
# Wait for: "model warm-up complete"

# 3. Open two browser tabs / windows, both full-screen-ready:
#    a. https://bitecloud.dk/presentations/velux-ai   ← slides
#    b. http://localhost:8000/                        ← live demo
#
#    On the demo tab: click each of the four chips once — confirm clean
#    answer for all. Click the Deployment tab — confirm topology renders.
#    Click back to Demo. Leave on Demo.
#
#    On the slides tab: walk through with arrow keys. F for full-screen.
```

If the model is slow on the first question after the talk starts:
`USE_MOCK=1` in the env and restart. Demo runs in milliseconds with
canned answers; the audience can't tell the difference for the four
chips.

## The arc — and what to say where

### 0:00 — 0:20 keynote (deer story → reframe → 3 stories → Kafka callback)

> *"Five years ago we agreed Kafka was the right backbone for this
> platform. Today the data flows through it. The next conversation
> isn't whether to add AI on top — it's how to do it on your terms."*

### 0:20 — 0:30 live demo

You're on the Demo tab. The chips and the context strip are already
loaded.

**Opening line for the demo:**

> *"What I'm about to show isn't a research notebook — that was the
> engineering artifact. This is what a maintenance technician sees on
> a tablet. Same Kafka topic, same schema card in a ConfigMap, same
> three-stage pipeline. I type a question, the platform answers."*

**Click chip 1 — "Throughput on line 2 yesterday"** (~6s with Ollama)

While it loads:
> *"The model just translated my English into a structured query —
> a signal name, two machine names, a time window. The chart you'll
> see in a second is pure pandas. The model doesn't compute anything;
> it picks what to compute, and later it phrases the result."*

When it lands, point at the schematic:
> *"Notice folder_02 and glass_cutter lit up — that's both machines
> on line_2. Throughput around 13 and 9 pcs/min, the dips are the
> shift handovers at 06/14/22. So far, classical analytics — your
> team already does this."*

**Click chip 2 — "Drift on line 2 last week"** (~8s)

When the summary banner lands:
> *"Line line_2: one of two machines drifted more than 20%. That
> banner is deterministic — it's pandas computing the means and the
> delta. Below it, the LLM writes the narrative. folder_02 baseline
> 2.5 mm/s on Monday, 5.2 by Wednesday, plus 105% on vibration RMS."*

> *"And here's what's interesting — by the time you'd notice this
> on a Grafana dashboard, the warning alarm at 20:10 Monday has
> already fired, the operator on Tuesday morning has noticed the
> machine sounds different, and there's a note in Danish in the
> events log saying so. The LLM correlates the alarm, the drift,
> and the Danish note. No translation layer needed."*

**Click chip 3 — "Glass cutter Monday morning"** (~7s)

When it lands:
> *"Throughput dropped to zero for 8 minutes Monday at 10:30. Motor
> current pegged at 5.5 amps — the motor was trying to run, the
> mechanism was stuck. Drive over-current alarm. Operator note: 'Glas
> blev hængende på transportbåndet. Manuelt frigjort.' Production
> resumed at 10:38. The system tied a Danish operator note to an
> English-named alarm code and a throughput collapse — all in one
> answer."*

**Optional — type a question live, if confident.** Recommended:

> "Was there a issue on line_2 on Monday"  *(deliberately rough phrasing)*

> *"Watch what happens here. I'm going to type a sloppy question, on
> purpose."*

When the amber repair notice appears:
> *"Look at this. The model dropped both scope dimensions — ignored
> 'line_2' and 'Monday' that I literally typed. A naïve LLM pipeline
> would give you everything-everywhere and call it done. The platform
> layer scanned the question, found what the model missed, and
> patched the plan. The amber notice tells you exactly what was
> repaired. Chart, events, schematic — all reflect what I actually
> asked. This is the discipline: trust the model to be useful, design
> the system to be safe."*

This is your strongest talking point. Don't rush it.

### 0:28 — 0:30 flip to Deployment tab

Click "Deployment". The audience watches the same browser change.

> *"Same browser, same names. This is what runs in your cluster."*

Walk down the topology in order:

> *"At the top: the client. Could be this browser. Could be the
> maintenance tablet I mentioned. POST to a Service. The Service
> forwards to a Pod running the FastAPI app — non-root,
> read-only root filesystem, dropped capabilities, probes,
> resource limits. The kind of pod-security context you already
> require for every other workload."*

> *"Mounted into that pod: the schema ConfigMap. That's the
> governance surface — the schema card lives in git, changes go
> through PR review. Not a kubectl edit. Not a model knob. Reviewable
> by humans who don't know what an LLM is."*

> *"The app talks to a second Service for inference. ollama runs as
> its own Deployment in this base. Demo-grade — model on emptyDir,
> 1 CPU request. In production, this is your shared inference plane,
> model pre-populated on a PVC, GPU node pool, governed and metered
> separately from the application plane. The discipline is the same
> as how you run any other shared platform component."*

Point to the data source box:
> *"And here, the seam that matters most. Today the parquet is baked
> into the image. That's demo-grade. In your factory, this is where
> the Kafka consumer plugs in — same shape as the data layer you
> already operate, writing to whatever query store fits: Iceberg on
> object storage, ClickHouse, DuckDB on a PVC, your existing
> analytical service. The AI plane stays unchanged — only the data
> layer behind it moves."*

Scroll to the demo-vs-prod table:
> *"None of this is research. It's applied platform engineering this
> room already does for every other workload. The AI plane is a new
> application; it isn't a new platform."*

Land the closing line of the demo:
> *"One kustomize base, six manifests, kubectl apply minus k, done.
> The thing that's new is not the deployment story. The deployment
> story is the same story you've told for five years. The thing
> that's new is the language layer on top. That's the only place AI
> added value here — and it's a 200-line Python service and a
> three-billion-parameter model that already lives on your laptop."*

### 0:30 — 0:45 substance segment

See CONTEXT.md. Patterns from Saxo, Novo, LEGO, DFDS, JYSK. The
open-source/private/commercial trade-off framed as
*"what needs control, locality, cost discipline, optionality."*

### 0:45 — 1:00 Q&A

Open Slido. Pull the three best ones first. See *Anticipated questions*
below for likely ones.

## Per-manifest talking points

Use these if asked, or if there's time at minute ~29 to walk through
the deployment view in detail.

### `nl-query-deployment.yaml`

> *"FastAPI in a slim Python image. Non-root user. Read-only root
> filesystem. All capabilities dropped. seccompProfile RuntimeDefault.
> Liveness and readiness probes on /healthz. CPU and memory requests
> and limits. automountServiceAccountToken: false because this pod
> doesn't talk to the API server. Same checklist your platform team
> already enforces — Kyverno, OPA, whatever you run."*

### `ollama-deployment.yaml`

> *"Separate Deployment, not a sidecar. Two reasons. One: scales
> independently — five nl-query pods, one ollama pod, or the other
> way around, you decide. Two: governed separately — model choice,
> GPU placement, license auditing, all happen at the inference
> plane, not in every app team's repo. In production you don't run
> ollama as a Deployment at all — it's a centralised inference
> service the whole platform shares."*

### `schema-configmap.yaml`

> *"The schema card lives in git as a ConfigMap. Not a Secret —
> there's nothing secret about it. Not an env var — it's multi-line
> structured text. Mounted read-only into the pod. Editing means
> opening a PR, getting review, and Argo syncs it. That's how you
> govern what the model is allowed to be asked, with the same
> mechanism you govern every other config in the cluster."*

### `nl-query-service.yaml` and `ollama-service.yaml`

> *"Both ClusterIP. The nl-query Service is fronted by whatever
> ingress you already run — gateway, mesh, the same path every
> other internal API takes. The ollama Service is internal only —
> the only thing that should reach it is nl-query, enforced via
> NetworkPolicy in production. No reason for the inference plane
> to be reachable from anywhere else."*

### `kustomization.yaml`

> *"Kustomize, not Helm, because there's no templating needed —
> this is config, not a chart. Image tag is pinned at the base
> level so promotion is a git diff. Adding NetworkPolicy,
> PodDisruptionBudget, HPA — those are overlays your platform team
> probably already has a base for."*

## The five things to do next (for a real deployment)

When the audience asks *"so we'd ship this tomorrow?"* — be honest.
These are the deltas:

1. **Data source** — replace the baked-in parquet with a Kafka
   consumer writing to a query store. Same nl-query service code; only
   the volume mount and the read path changes.
2. **Inference plane** — move ollama to your shared inference service,
   or a model serving stack (vLLM, TGI, whatever standardises). Model
   on a PVC pre-populated by an init job, GPU node pool, model
   selection via env in the Deployment.
3. **Identity and AuthN** — Workload Identity on the pod, AuthN at
   the gateway in front of the Service, OAuth/OIDC for the human
   client. Same shape as every other internal service.
4. **NetworkPolicy** — egress-default-deny, allow only ollama. PDB
   on both Deployments. HPA on nl-query keyed to request queue
   depth.
5. **Governance** — the schema card is the surface. Add a CI check
   that validates the schema_card against the live data shape. Add
   an audit log of every NL query + the plan it produced, written to
   the same observability stack you already run.

None of these are *AI* problems. They're the platform problems you've
already solved for everything else.

## Anticipated Q&A

### *"How do we get this past leadership?"*

> *"You don't sell AI to him. You build one tiny, observable,
> low-blast-radius pilot, let it run for six weeks, let the result
> speak for itself. Same way the first Kubernetes workloads got past
> the same shape of objection five years ago. Permission follows
> evidence."*

### *"What's the ROI?"*

> *"Honest answer — ROI is hard when AI isn't integrated into
> workflow. What I'd argue for instead is measurable pilots with
> kill criteria. Pick one workflow where time-to-answer matters,
> instrument it, run for a quarter, decide. Big-bang ROI questions
> are usually a way to never start."*

### *"What about hallucinations?"*

> *"You saw it happen live — the model dropped scope on the
> line_2/Monday question. The platform layer caught it and the
> amber notice told you what was repaired. The deterministic guards
> are not optional — they're the discipline. The model is allowed to
> be wrong; the system is not allowed to be wrong."*

### *"Which models do you actually recommend?"*

Be willing to name 2-3 small open-weight models. As of mid-2026:
qwen2.5:3b for JSON-shaped tasks (what we used today), llama3.2:3b
for general prose, phi-3.5 for tight contexts. For RAG on factory
docs, larger context windows matter — qwen2.5:7b or llama3.1:8b on a
shared GPU node. Stay away from anything that requires the data to
leave the building unless there's a specific reason.

### *"Why a local model, not OpenAI?"*

> *"Three reasons. One: locality — the factory floor data doesn't
> leave the building, no shared inference vendor, no DPA. Two: cost
> discipline at scale — a 3B model on a shared inference pod is
> measurable. Per-token API pricing isn't, at any factory volume.
> Three: optionality — when the better model comes out next month,
> you change one env var, not a contract."*

### *"Can we use [our existing model serving]?"*

> *"Yes. The Service interface is HTTP, JSON in, JSON out. ollama
> happens to implement an OpenAI-compatible API. If you've got vLLM
> or TGI or Triton, swap the env var. The application code doesn't
> change."*

### *"Did Saxo actually do this?"*

Stay specific and within what's public. Lean on the AI-exchange
patterns. Don't put words in Saxo's mouth.

### *"What about Danish?"*

> *"You saw it work — the operator note in Danish was correlated
> with an English-named alarm code, no translation layer. Modern
> 3B+ open-weight models handle Danish reasonably well for
> classification and summarisation. For high-stakes translation,
> add a dedicated translation step. For demo-grade comprehension,
> they're fine out of the box."*

## On running kind live — my honest take

**Don't do `kubectl apply` live on stage.** It's high-risk, low
value-add. Three things will go wrong on conference wifi: the ollama
image pull (it's ~700 MB), the model pull (qwen2.5:3b is ~2 GB),
and your kind node running out of disk. Even if it works, you're
spending three minutes of a 60-minute slot watching pods come up.

**The Deployment tab in the UI already gives the proof the audience
needs.** They're platform engineers. They can read a Service +
Deployment + ConfigMap manifest and trust that `kubectl apply -k`
works. The topology view with the same component names *is* the
verification.

### If you want cluster proof anyway — pre-stage it

Do this **the night before**, not live:

```bash
# 1. Spin up kind with enough memory for ollama
cat <<EOF > /tmp/kind-velux.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            system-reserved: memory=2Gi
EOF
kind create cluster --name velux --config /tmp/kind-velux.yaml

# 2. Build and load the image (kind doesn't pull from your local Docker)
docker build -f talks/VELUX_05_2026/service/Dockerfile \
  -t velux-nl-query:0.1.0 talks/VELUX_05_2026/
kind load docker-image velux-nl-query:0.1.0 --name velux

# 3. Apply
kubectl create namespace nl-query-demo
kubectl apply -k talks/VELUX_05_2026/deploy/base

# 4. Pull the model into the running ollama pod
kubectl -n nl-query-demo rollout status deploy/ollama
kubectl -n nl-query-demo exec deploy/ollama -- ollama pull qwen2.5:3b

# 5. Port-forward and confirm
kubectl -n nl-query-demo port-forward svc/nl-query 8001:80 &
curl -s localhost:8001/healthz | jq
```

Then on stage, **don't drive the demo through the cluster** — keep
the demo on `:8000` (your local uvicorn) for speed. Use a terminal
beside the browser only for *proof reads*:

```bash
kubectl get pods -n nl-query-demo
kubectl describe configmap nl-query-schema -n nl-query-demo | head -40
kubectl logs deploy/nl-query -n nl-query-demo --tail=20
```

Audience sees the names from the topology diagram appearing in real
cluster output. That's the credibility moment. No live apply, no
image pulls, no risk.

If even *that* feels like too much surface area: skip kind entirely.
The Deployment tab does the job.

## Closing line

After the substance segment, before Q&A:

> *"AI is not coming for your jobs. The engineer in the next
> building who learned to use AI is coming for your job. The
> difference is not intelligence or experience — it's whether the
> last six months were spent trying things, or arguing about AI.
> But you have what that engineer probably doesn't: domain knowledge
> of factories, machines, IIoT. AI without that is a tourist with
> Google Maps. With it, you become irreplaceable."*

> *"You don't have to outrun the lion. You just have to be the
> engineer who tied her shoes."*
