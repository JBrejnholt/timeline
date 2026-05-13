# Demo Cheat Sheet — VELUX, Thursday 2026-05-21

Every interesting thing in the synthetic dataset, with question phrasings
that have been verified to round-trip cleanly through `qwen2.5:3b`.

## Data window

`2026-05-18 00:00 UTC → 2026-05-20 23:59 UTC` — Monday, Tuesday, Wednesday.
The talk is Thursday 2026-05-21, so for the model:

- *"today"* = 2026-05-21
- *"yesterday"* = Wednesday 2026-05-20
- *"Monday morning"* = 2026-05-18 06:00–12:00
- *"last week"* = the three available days

## The 9 events at a glance

| When               | Line / machine          | Sev    | Code     | What                                          |
|--------------------|-------------------------|--------|----------|-----------------------------------------------|
| Mon 10:30          | line_2 / glass_cutter   | error  | DRV_F042 | Drive fault: motor over-current sustained     |
| Mon 10:32          | line_2 / glass_cutter   | info   | OP_NOTE  | (DA) Glass stuck on conveyor, manually freed  |
| Mon 10:38          | line_2 / glass_cutter   | info   | RESUMED  | Production resumed after manual intervention  |
| Mon 20:10          | line_2 / folder_02      | warn   | VIB_W01  | Vibration RMS rising above baseline (1.2x)    |
| Tue 02:00          | line_1 / sash_assembler | info   | PM_START | Planned maintenance window started            |
| Tue 04:05          | line_1 / sash_assembler | info   | PM_END   | Planned maintenance complete                  |
| Tue 08:15          | line_2 / folder_02      | warn   | VIB_W02  | Vibration sustained above warning for 12h     |
| Tue 09:30          | line_2 / folder_02      | error  | VIB_E01  | Vibration spike: 3.5x baseline — inspect bearing |
| Tue 09:45          | line_2 / folder_02      | info   | OP_NOTE  | (DA) Machine sounds different — needs maintenance |

## The three storylines

### 1. Glass cutter — stuck-at (Mon 10:30 → 10:38)

- **What happened in the data:** throughput dropped to 0 for 8 minutes;
  motor current pegged at 5.50 A (stall level); 49 PackML samples marked
  `Aborted`; current↔throughput correlation drops to 0.960 (vs 0.985 for
  healthy machines).
- **Operator note is in Danish** — talking point: *"the LLM correlates
  Danish operator notes with an English-named alarm code, no translation
  layer needed."*

**Question prompts that work:**
- *"What happened on the glass cutter Monday morning?"*  ← the chip
- *"Show me throughput on glass_cutter Monday morning"*
- *"Was there a fault on line_2 on Monday?"*
- *"Show me motor current on glass_cutter on Monday between 10 and 11"*

**Expected answer:** anomaly intent, throughput chart with the 8-minute
zero gap visible, three events surfaced (DRV_F042 alarm, the Danish
operator note, the RESUMED message).

---

### 2. folder_02 — bearing wear + shedding spike

Three things stacked on top of each other:

- **Drift** — vibration ramps from Mon 18:00 to Tue 06:00, then **holds**:
  Mon mean = **2.53 mm/s**, Tue mean = **5.05 mm/s**, Wed mean = **5.21 mm/s**.
  Mon-vs-Wed delta = **+105.5%**. Drift detector flags it as the only
  machine on line_2 that drifted >20%.
- **Spike** — Tue 09:30 reaches **~21 mm/s** for 3 minutes (the bearing
  "sheds material" moment).
- **Operator note** — Tue 09:45, in Danish: *"Maskinen lyder anderledes.
  Vil have vedligehold til at kigge på det inden næste skift."* (machine
  sounds different, wants maintenance to look at it before the next shift)

**Question prompts that work:**
- *"Show me machines on line 2 that drifted last week"*  ← the chip
- *"Was there any vibration drift on folder_02?"*
- *"Show me vibration on folder_02 from Monday to Wednesday"*
- *"Any bearing problems on line_2?"*

**Expected answer for the drift query:**
- Summary banner: `line_2: 1 of 2 machines drifted >20% on vibration_rms_mm_s`
- folder_02 baseline 2.381 → current 5.052 mm/s (+105.5%)
- glass_cutter baseline 2.381 → current 2.369 mm/s (-0.5%)
- Three events surface in the events table

---

### 3. sash_assembler — planned maintenance (Tue 02:00 → 04:00)

- Throughput ~ 0, motor current ~ 0.2 A, vibration ~ 0.05 mm/s for 2 hours.
- 721 PackML samples marked `Stopped` on Tuesday (vs 0 on Mon/Wed).
- Two MES messages bracket the window: PM_START at 02:00, PM_END at 04:05.
- **Talking point:** *"This one's planned downtime, not a fault — the
  LLM has to read the MES messages to distinguish 'stopped because broken'
  from 'stopped because we scheduled it.'"*

**Question prompts that work:**
- *"Was there any planned maintenance on Tuesday?"*
- *"Show me sash_assembler on Tuesday morning"*
- *"Why was sash_assembler stopped on Tuesday?"*
- *"What's the PackML state distribution for sash_assembler this week?"*

**Expected answer:** lookup or anomaly intent, throughput chart with the
2-hour zero block from 02:00-04:00 on Tuesday, two PM_START/PM_END events
visible.

## Healthy-baseline machines (use for "nothing happened" demos)

| Machine                | Throughput (pcs/min) | Current (A) | Vibration (mm/s) |
|------------------------|----------------------|-------------|------------------|
| line_1 / folder_01     | 13.15 every day      | 6.76        | 2.36             |
| line_3 / edge_bonder   | 10.3                 | 5.6         | 2.37             |
| line_3 / quality_station | 18.8 (highest)     | 9.0         | 2.37             |

**Question prompts to show clean answers:**
- *"How did line_1 perform yesterday?"*
- *"Show me throughput on line_3 yesterday"*
- *"Compare motor current across line_3 yesterday"*  ← the chip
- *"Any drift on edge_bonder?"*  → answers "no drift detected"

These are good for the *"the system is also confident when nothing is
wrong"* moment.

## Question recipe book — quick picks

Use these on the day. The first column is what to say; the second is
what the audience will see.

| Type                  | What to type                                         | The wow moment                            |
|-----------------------|------------------------------------------------------|-------------------------------------------|
| Lookup, scoped to line | *Throughput on line 2 yesterday*                     | Two machines plotted, dips at handovers   |
| Drift detection        | *Show me machines on line 2 that drifted last week*  | +105% summary banner, baseline highlighted |
| Anomaly + Danish note  | *What happened on the glass cutter Monday morning?*  | Throughput=0 gap, alarm + Danish OP_NOTE   |
| Planned downtime       | *Why was sash_assembler stopped on Tuesday?*         | 2h zero block + PM_START/PM_END events     |
| Compare across line    | *Compare motor current across line 3 yesterday*      | Two machines side-by-side, no events       |
| Negative result        | *Any drift on edge_bonder last week?*                | Honest "no, within normal range"           |
| Specific machine signal | *Show me vibration on folder_02 from Mon to Wed*   | The bearing-wear ramp shape, spike at 09:30|

## Phrasings that round-trip cleanly (verified)

These have been tested against `qwen2.5:3b` and produce the right plan:

- `What was the throughput on line 2 yesterday?`
- `Show me machines on line 2 that drifted last week`
- `What happened on the glass cutter Monday morning?`
- `How did line_1 perform yesterday?`
- `Show me throughput on line_3 yesterday`
- `Were there any planned maintenance windows yesterday?`
- `Compare motor current across line 3 yesterday`  ← use the space form

## Phrasings to AVOID on stage

Small models still fumble these — they parse but pick the wrong scope.
The validator catches some, but the chart will look off:

| Don't say                                          | Why                                                |
|---------------------------------------------------|----------------------------------------------------|
| *"Show me temperature on folder_02 yesterday"*    | Model often picks `glass_cutter` (proper-noun confusion) |
| *"What's the highest motor current right now?"*   | "Right now" maps to Thursday → no data → refuses    |
| *"Compare line_2 and line_3"*                     | Model can only filter on one line at a time         |
| *"Show me data from last month"*                  | Outside data window → validator rejects → mock fallback |
| *"Compare motor current across line_3 yesterday"* (with underscore) | Model sometimes returns `line_id: "edge_bonder"` → falls back to mock |

If a chip lands on a mock fallback, the audience still sees the right
answer — but you lose the *"watch the LLM do the work"* moment.

## Graceful-degradation talking points (when something does go wrong)

The system is built so failures land softly. If you get one of these,
treat it as the *moment to make the platform-engineering point*:

- **Plan validation rejects an out-of-window date** → *"The platform
  layer caught the LLM trying to query data that doesn't exist. The
  application doesn't see hallucinated dates — that's the discipline."*
- **Annotation refuses to fill NaN with prose** → *"The model wanted to
  write something. The execution layer told it there's nothing to say.
  This is the difference between AI-as-feature and AI-as-oracle."*
- **Ollama is slow** → *"This is a 3-billion-parameter model running on
  my laptop, no GPU. Six seconds for natural language → chart →
  explanation. In your cluster it'd be sub-second."*

## Numbers you might want to quote on stage

- **777,600 measurements** over three days × six machines × five signals
  at 10-second resolution (≈ one Kafka partition's worth for a small
  factory)
- **9 events** in the events log (alarms + MES + operator notes)
- **+105.5% drift** on folder_02 vibration, Monday baseline vs Wednesday
- **8-minute stuck-at** on glass_cutter, Monday 10:30–10:38
- **2-hour planned maintenance** on sash_assembler, Tuesday 02:00–04:00
- **49 PackML `Aborted` samples** on glass_cutter (the stuck-at event)
- **721 PackML `Stopped` samples** on sash_assembler (planned downtime)
- **3 of 6 machines** have an injected scenario; **3 are healthy baselines**

## Reload checklist before going on stage

1. `pkill -f 'uvicorn app:app'`
2. `ollama list` — confirm `qwen2.5:3b` is pulled
3. `.venv/bin/uvicorn app:app --app-dir service --port 8000`
4. Wait for the `model warm-up complete` log line
5. Open `http://localhost:8000/` full-screen on the projector
6. Click each chip once — confirm chart + summary + annotation appear
7. Open `/schema` in a second tab so you can flip to it during the
   "this is the governance surface" beat
