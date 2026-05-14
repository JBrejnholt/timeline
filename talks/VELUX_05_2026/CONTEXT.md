# VELUX Talk — May 2026 — Working Context

This file captures the decisions and context behind the talk and demo so the
work can continue in any tool (Cowork, Claude Code, future you).

## The engagement

- **Audience.** ~30 engineers in the VELUX Innovation Center, Skjern. They build
  the VELUX IIoT platform (served via container platform) that other VELUX
  factories use to inject, store and analyse machine data. They code against
  real machines and at platform level.
- **Host.** Kasper Korsholm Christiansen — Platform Owner, VELUX IIoT. Ex-PLC
  programmer, MES integration background, 17+ years at VELUX. He invited me.
- **Slot.** 1 hour, on site.
- **Goal.** (1) Inspire the team and give them clarity on AI. (2) Land a
  follow-up advisory engagement to help them get started. (3) Help the team —
  they are nice people and I want them to succeed.
- **Headwind.** New platform lead is anti-AI, amplifies negative AI news.
  Address this implicitly, never by name. Frame as *governed AI vs shadow AI*,
  not *AI vs no AI*.

## My history with this room

- May 2021 → Apr 2023 at VELUX, building and leading the CCoE.
- **Five years ago (2021) I introduced the centralized container platform and
  the centralized Kafka platform.** These are the substrate this IIoT team
  runs on today.
- Left VELUX → returned to Saxo Bank as Global Head of Cloud and Container
  Platforms.
- Currently on garden leave until end of July 2026, building Bitecloud
  (senior platform advisory).

This is the credibility lever. The Kafka backbone is mine — and theirs.

## The talk arc (60 min, no formal break)

| Time         | Segment                                                   | Purpose                                                                |
|--------------|-----------------------------------------------------------|------------------------------------------------------------------------|
| 0:00 – 0:20  | Keynote — deer story → reframe → 3 short stories → ask    | Inspire. Reframe AI from threat to leverage.                            |
| 0:20 – 0:30  | Live demo on factory-shaped time-series data              | Prove the keynote is real. Implicit consulting pitch.                   |
| 0:30 – 0:45  | What other Nordic companies are doing                     | Substance. Patterns from Saxo, Novo, LEGO, DFDS, JYSK. Open-source.     |
| 0:45 – 1:00  | Q&A (curated via Slido throughout)                        | Open the room.                                                          |

## The keynote core

**Opening story — the deer.** Two deer in a field. Lion appears. One deer
starts drinking Red Bull. The other says "that won't help you outrun the lion."
She replies: "I don't need to outrun the lion. I just need to outrun you."

**The reframe.** AI is not coming for your job. The engineer in the next
building who learned to use AI is coming for your job. The difference is not
intelligence or experience — it is whether the last six months were spent
trying things or arguing about AI. *But* you have what that engineer probably
does not: domain knowledge of factories, machines, IIoT. AI without that is a
tourist with Google Maps. With it, you become irreplaceable.

**The Kafka callback (after the reframe, before the substance).**
> "Five years ago we agreed Kafka was the right backbone for the IIoT platform.
> Today the data is flowing through it. The next conversation is not whether
> to add AI on top — it is how to do it on your terms."

**The closing line.**
> "You don't have to outrun the lion. You just have to be the engineer who
> tied her shoes."

## The demo (0:20 – 0:30) — decision and as-built

Anomaly detection alone is a **weak** demo for this audience — they understand
statistics and classical ML already solves it. Built:

- **Primary (as shipped):** Natural-language interface to factory data,
  delivered as a small FastAPI service with a one-page vanilla-HTML UI.
  *"Show me machines on line 2 that drifted last week."* → JSON plan →
  pandas filter + stats → matplotlib chart + plain-language annotation +
  events table. The UI replaces the notebook as the live-demo surface —
  notebooks are dev-grade, not presentation-grade. The notebook
  (`02_nl_query_demo.ipynb`) stays as the engineering artifact.
- **Deferred:** Hybrid classical-detect + LLM-explain (`03_*`). Cut from
  the talk after weighing 60-minute slot vs additional live-demo
  surface area. Adds risk without strengthening the platform-engineering
  framing. May ship after the talk if useful.

The web UI has two tabs:
- **Demo** — context strip (topic / window / signals / row counts),
  factory-floor schematic (3 lines × 2 machines with kind icons that
  highlight on each query), ask form + four canned-question chips,
  response panel (deterministic summary banner, plan-repair notice,
  LLM annotation, chart, plan JSON, events table).
- **Deployment** — K8s topology diagram with the same component names
  (Service → Pod → ConfigMap → Service → Pod), plus the demo-vs-prod
  seam table. Flipping to this tab IS the closing slide.

Synthetic data: shape-realistic, three days at 10-second resolution.
Monday 2026-05-18 → Wednesday 2026-05-20 UTC. ~778k measurements + 9
events including alarms, MES messages, and operator notes (some in
Danish) keyed to embedded scenarios — bearing wear + spike on
`folder_02`, stuck-at on `glass_cutter`, planned maintenance on
`sash_assembler`. Frame in the talk as *"imagine this is one of your
Kafka topics."*

### Engineering discipline that lands on stage

Three deterministic safety layers wrap the LLM — these are talk
material in their own right:

1. **Plan validation** — rejects plans whose dates fall outside the
   data window (catches the model inventing "previous week" baselines
   that don't exist).
2. **Plan repair** — scans the question text for line names, machine
   names, day-of-week, and patches the plan if the model dropped scope.
   Amber notice in the UI when this fires — *the question wins over
   the LLM's choice*. Strongest credibility moment in the demo.
3. **Events guard** — if events are in the payload but the LLM's
   annotation doesn't cite any of their codes, prepend a structured
   summary so the operator never sees "no alarms" when alarms are
   present.

Combined message: *"The model is allowed to be wrong; the system is
not allowed to be wrong."* This is the engineering discipline that
makes it Nordic-enterprise deployable.

## Substance segment (0:30 – 0:45) — what to cover

Use Nordic-enterprise patterns from this week's AI exchange and from Saxo:

- Where companies actually sit (mostly between productivity tools and pilots).
- The five practical patterns (productivity, software delivery, enterprise
  data, agents, platform capability).
- Open-source / private / commercial trade-off — *the question is not "open
  or commercial" but "what needs control, locality, cost discipline, and
  optionality."* Reference `bitecloud.dk/insights/meta-did-not-kill-open-source`.
- The thin platform layer — extend the existing container + Kafka platform,
  do not build a new AI platform.
- *"Adoption is not access. Governance must create paths. Ownership makes it
  real."*

## Slido

- Used throughout the talk to collect questions in writing, not just for the
  Q&A slot.
- Open at 0:00, prompt at start: *"Drop questions on Slido as we go — I'll
  pull the best ones at the end."*
- At 0:45, surface the three best ones first. Engineers in this room know me
  from CCoE — they will engage; Slido is for *curating*, not cold-starting.

## Expected hard questions (prepare for these)

- *"How do we get this past leadership?"* — the question about the new
  platform lead, asked safely. Answer: *"You don't sell AI to him. You build
  one tiny, observable, low-blast-radius pilot, let it run for six weeks,
  let the result speak for itself. Same way the first Kubernetes workloads
  got past the same shape of objection five years ago. Permission follows
  evidence."* This is also the consulting pitch.
- *"What's the ROI?"* — Honest: ROI is hard when AI isn't integrated into
  workflow. Argue for *measurable pilots with kill criteria*, not big-bang.
- *"Did Saxo actually do this?"* — Stay specific and within what's public.
  Lean on patterns observed at the AI exchange more than confidential detail.
- *"Which models do you actually recommend?"* — Be willing to name 2-3 small
  open-weight models worth trying on factory time-series and on RAG.

## What this is NOT

- A briefing dressed as a keynote.
- A maturity-curve walkthrough.
- An "AI for everything" pitch — the credibility comes from saying *use AI
  where it uniquely helps, keep classical tools where they're better, the
  discipline is knowing the difference.*

## Repo layout

```
talks/VELUX_05_2026/
├── CONTEXT.md                          # this file — read first
├── README.md                           # how to run the demo
├── CHEATSHEET.md                       # every defect / event / scenario + verified question phrasings
├── TALK_NOTES.md                       # stage cheat — read morning of, leave behind
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
├── service/                            # ← THE LIVE-DEMO SURFACE
│   ├── app.py                          # FastAPI: /healthz /schema /meta /plan /ask
│   ├── static/index.html               # vanilla UI, two tabs (Demo / Deployment)
│   ├── Dockerfile                      # slim, non-root, baked-in demo data
│   ├── requirements.txt
│   └── README.md                       # local + container + deploy runbook
└── deploy/                             # ← THE CLOSING-SLIDE MATERIAL
    ├── README.md                       # topology, apply commands, prod-vs-demo table
    └── base/                           # kustomize: 5 manifests
        ├── kustomization.yaml
        ├── schema-configmap.yaml       # governance surface (matches src/nl_query.SCHEMA_CARD)
        ├── nl-query-deployment.yaml    # non-root, readOnlyRootFS, probes, limits
        ├── nl-query-service.yaml
        ├── ollama-deployment.yaml
        └── ollama-service.yaml
```

## Working preferences (mine)

- Direct, precise, useful. Cut filler.
- Bitecloud voice for any external-facing text — senior, calm, opinionated,
  Nordic-enterprise appropriate.
- Do not oversimplify Kubernetes, Kafka, platform or IAM topics unless asked.
- For platform/infra: think about blast radius, rollout safety, observability,
  backward compatibility, identity, recovery path.
- Push back when something will weaken the brand positioning or won't work.
- Do not invent VELUX internal facts. Do not put words in Saxo's mouth.

## Next steps (working list)

1. **Done:** Scaffold folder, write this CONTEXT.
2. **Done:** Generate three-day synthetic factory data (`01_generate_data.ipynb`).
3. **Done:** Build the NL-query pipeline + notebook (`02_nl_query_demo.ipynb`).
4. **Done:** Wrap the pipeline in a FastAPI service with a vanilla-HTML UI
   (Demo + Deployment tabs) — this is the live-demo surface, not the notebook.
5. **Done:** Kustomize base for `kubectl apply -k` to any cluster (`deploy/base/`).
6. **Done:** Plan-repair pass + events guard — engineering discipline that
   makes the small-model fumbles land softly on stage.
7. **Done:** `CHEATSHEET.md` (every defect + verified question phrasings) and
   `TALK_NOTES.md` (stage cheat for the day).
8. **Deferred:** Hybrid classical-detect + LLM-explain (`03_*`). Cut from the
   talk. May ship after as a follow-up.
9. **Done:** Slides drafted in `slides.md` (Marp), integrated into the
   Bitecloud website. Rendered at <https://bitecloud.dk/presentations/velux-ai>.
10. **Open:** Rehearse the 20-min keynote arc out loud. Multiple times.

## Working in Claude Code from here

If switching to Claude Code: start by reading this file
(`talks/VELUX_05_2026/CONTEXT.md`) and the user's global `CLAUDE.md`. Pick up
from the *Next steps* list. The folder is a regular git repo — commit small,
commit often.

To start the live demo locally:

```bash
cd talks/VELUX_05_2026
.venv/bin/uvicorn app:app --app-dir service --port 8000
# open http://localhost:8000/
```

Or in a cluster: `kubectl apply -k deploy/base`. The Dockerfile is in
`service/`; bake it with `docker build -f service/Dockerfile -t velux-nl-query:0.1.0 .`
from the talk root.
