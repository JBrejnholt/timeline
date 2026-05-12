"""Natural-language interface to the synthetic factory parquet.

The pipeline is deliberately three stages so the LLM is *only* the
communication layer:

    1. question  -> plan      (LLM call, structured JSON)
    2. plan      -> dataframe + stats   (deterministic pandas)
    3. plan,stats,events -> annotation  (LLM call, plain English)

Execution is never free-form SQL or free-form generation. The LLM picks
a signal, a machine list and a time window from a known set; pandas does
the rest. If the LLM is unreachable or returns garbage, a deterministic
mock client takes over so the live demo always runs.

Frame for the talk: "imagine this is one of your Kafka topics."
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Schema card — what the LLM sees about the dataset
# ---------------------------------------------------------------------------

SCHEMA_CARD = """\
You translate factory-floor questions into a JSON query plan.

The data is one Kafka topic, long format, one row per measurement:
  columns: timestamp (UTC), line_id, machine_id, signal, value, value_str

Signals (use these names exactly):
  - throughput_pcs_per_min   pieces per minute, float
  - motor_current_a          motor current in amps, float
  - temperature_c            motor temperature in C, float
  - vibration_rms_mm_s       vibration RMS in mm/s, float
  - packml_state             Execute / Idle / Stopped / Aborted (in value_str)

Lines and machines:
  line_1: folder_01, sash_assembler
  line_2: folder_02, glass_cutter
  line_3: edge_bonder, quality_station

Data window: 2026-05-04T00:00:00Z .. 2026-05-06T00:00:00Z (two days).
For date arithmetic treat "today" as 2026-05-06.
  "yesterday"       -> 2026-05-05T00:00:00Z .. 2026-05-06T00:00:00Z
  "Monday morning"  -> 2026-05-04T06:00:00Z .. 2026-05-04T12:00:00Z
  "last week"       -> the two available days

Return ONLY a JSON object with these keys:
  intent      : one of "lookup" | "drift" | "anomaly" | "compare"
  signal      : one signal name from the list above
  line_id     : one line name or null for all
  machine_id  : list of machine names or null for all
  time_window : {"start": ISO8601 UTC, "end": ISO8601 UTC}
  baseline    : {"start": ISO8601, "end": ISO8601} — only for intent="drift"
  aggregation : "mean" | "max" | "min" | "timeseries"

Do not invent machines or signals. machine_id is always a list (or null),
never a bare string. Output JSON only — no prose, no fences.

Examples (study these — then answer the actual question).

Q: What was the throughput on line 2 yesterday?
A: {"intent":"lookup","signal":"throughput_pcs_per_min","line_id":"line_2",
    "machine_id":null,
    "time_window":{"start":"2026-05-05T00:00:00Z","end":"2026-05-06T00:00:00Z"},
    "aggregation":"timeseries"}

Q: Show me machines on line 2 that drifted last week.
A: {"intent":"drift","signal":"vibration_rms_mm_s","line_id":"line_2",
    "machine_id":null,
    "time_window":{"start":"2026-05-05T00:00:00Z","end":"2026-05-06T00:00:00Z"},
    "baseline":{"start":"2026-05-04T00:00:00Z","end":"2026-05-04T18:00:00Z"},
    "aggregation":"mean"}

Q: What happened on the glass cutter Monday morning?
A: {"intent":"anomaly","signal":"throughput_pcs_per_min","line_id":"line_2",
    "machine_id":["glass_cutter"],
    "time_window":{"start":"2026-05-04T06:00:00Z","end":"2026-05-04T12:00:00Z"},
    "aggregation":"timeseries"}
"""


ANNOTATE_SYSTEM = """\
You explain factory-floor analysis results to engineers in plain English.

You will receive a JSON payload with:
  - question : the original natural-language question
  - stats    : numbers computed from the data (the per_machine list is
               per-machine; numbers there belong to one machine each, not
               to the whole line)
  - events   : alarms, MES messages and operator notes in the same window

Write 2-4 sentences. Cite each machine by name when quoting numbers. Do
NOT invent any number that is not in the stats. Do NOT compute or combine
numbers — only repeat what is in the stats. If stats are empty or n_rows
is 0, say plainly that the window had no data. Tone: concise, calm, Nordic.
"""


# ---------------------------------------------------------------------------
# LLM clients (swappable)
# ---------------------------------------------------------------------------

class LLMClient(Protocol):
    name: str
    def complete(self, system: str, prompt: str) -> str: ...


@dataclass
class OllamaClient:
    """Talks to a local Ollama server. Uses format=json for the plan stage."""

    model: str = "qwen2.5vl:3b"
    host: str = "http://localhost:11434"
    timeout_s: float = 30.0
    name: str = "ollama"

    def complete(self, system: str, prompt: str) -> str:
        body = json.dumps({
            "model": self.model,
            "system": system,
            "prompt": prompt,
            # Plan stage outputs JSON; annotate stage is short prose. format=json
            # is harmless for the prose stage with this model — it just nudges
            # structure. If you want freer prose, switch to format="" for annotate.
            "format": "json" if "intent" in system else "",
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 400},
        }).encode()
        req = urllib.request.Request(
            f"{self.host}/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
            return json.loads(resp.read()).get("response", "")

    @classmethod
    def available(cls, host: str = "http://localhost:11434", timeout_s: float = 1.5) -> bool:
        try:
            with urllib.request.urlopen(f"{host}/api/tags", timeout=timeout_s):
                return True
        except (urllib.error.URLError, OSError, TimeoutError):
            return False


@dataclass
class MockClient:
    """Deterministic fallback so the demo always runs.

    Returns pre-baked plans and annotations keyed by what the question is
    about. The point is *not* that the answers are pretend — the point is
    that this is what a small local model returns for these questions, and
    the live demo should never break on conference wifi.
    """

    plans: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)
    name: str = "mock"

    def complete(self, system: str, prompt: str) -> str:
        key = _mock_key(prompt)
        if "intent" in system:
            return self.plans.get(key, self.plans["__default__"])
        return self.annotations.get(key, self.annotations["__default__"])


def _mock_key(prompt: str) -> str:
    # The plan stage sends the raw question; the annotate stage sends a JSON
    # payload with a "question" field. Route off the question text in both
    # cases, otherwise events embedded in the annotate payload (e.g. the
    # glass_cutter alarm) trigger the wrong key.
    text = prompt
    s = prompt.lstrip()
    if s.startswith("{"):
        try:
            text = json.loads(s).get("question", prompt)
        except Exception:
            pass
    p = text.lower()
    if "drift" in p and ("line 2" in p or "line_2" in p):
        return "drift_line2"
    if "glass" in p or "stuck" in p:
        return "glass_cutter_event"
    if "throughput" in p and ("yesterday" in p or "tuesday" in p):
        return "throughput_line2_yesterday"
    if "vibration" in p or "bearing" in p:
        return "drift_line2"
    return "__default__"


def default_mock_client() -> MockClient:
    plans = {
        "throughput_line2_yesterday": json.dumps({
            "intent": "lookup",
            "signal": "throughput_pcs_per_min",
            "line_id": "line_2",
            "machine_id": None,
            "time_window": {"start": "2026-05-05T00:00:00Z", "end": "2026-05-06T00:00:00Z"},
            "aggregation": "timeseries",
        }),
        "drift_line2": json.dumps({
            "intent": "drift",
            "signal": "vibration_rms_mm_s",
            "line_id": "line_2",
            "machine_id": None,
            "time_window": {"start": "2026-05-05T00:00:00Z", "end": "2026-05-06T00:00:00Z"},
            "baseline": {"start": "2026-05-04T00:00:00Z", "end": "2026-05-04T18:00:00Z"},
            "aggregation": "mean",
        }),
        "glass_cutter_event": json.dumps({
            "intent": "anomaly",
            "signal": "throughput_pcs_per_min",
            "line_id": "line_2",
            "machine_id": ["glass_cutter"],
            "time_window": {"start": "2026-05-04T10:00:00Z", "end": "2026-05-04T11:00:00Z"},
            "aggregation": "timeseries",
        }),
        "__default__": json.dumps({
            "intent": "lookup",
            "signal": "throughput_pcs_per_min",
            "line_id": None,
            "machine_id": None,
            "time_window": {"start": "2026-05-04T00:00:00Z", "end": "2026-05-06T00:00:00Z"},
            "aggregation": "mean",
        }),
    }
    annotations = {
        "drift_line2": (
            "On line_2, folder_02 vibration drifted from ~2.5 mm/s during the "
            "baseline window to ~5.5 mm/s by the end of the comparison window — "
            "roughly a 2.2x increase. glass_cutter stayed within its normal "
            "range. Two warning alarms (VIB_W01, VIB_W02) and one error "
            "(VIB_E01, 3.5x spike at 09:30) fired on folder_02 — consistent "
            "with progressive bearing wear ending in a shedding event."
        ),
        "glass_cutter_event": (
            "At 10:30 Monday, glass_cutter throughput dropped to 0 pcs/min for "
            "8 minutes while motor current stayed near 5.5 A — a stuck-at "
            "signature. Alarm DRV_F042 (drive over-current) fired at 10:30; "
            "an operator note at 10:32 (in Danish) reported glass stuck on the "
            "conveyor, manually freed. Production resumed at 10:38."
        ),
        "throughput_line2_yesterday": (
            "On line_2 yesterday, folder_02 ran near its 14 pcs/min target and "
            "glass_cutter near its 10 pcs/min target, with the three usual "
            "shift-handover dips at 06/14/22. Throughput was nominal — but "
            "the events log shows vibration warnings on folder_02 worth a "
            "second look."
        ),
        "__default__": "Result computed; see chart and stats above.",
    }
    return MockClient(plans=plans, annotations=annotations)


def pick_client(prefer_local: bool = True, model: str | None = None) -> LLMClient:
    """Return an Ollama client if reachable, else the mock client.

    Use this from the notebook so the demo degrades cleanly on any laptop.
    """
    if prefer_local and OllamaClient.available():
        return OllamaClient(model=model) if model else OllamaClient()
    return default_mock_client()


# ---------------------------------------------------------------------------
# Stage 1 — plan
# ---------------------------------------------------------------------------

SIGNALS = {
    "throughput_pcs_per_min",
    "motor_current_a",
    "temperature_c",
    "vibration_rms_mm_s",
    "packml_state",
}
LINES = {"line_1", "line_2", "line_3"}
MACHINES = {
    "folder_01", "sash_assembler",
    "folder_02", "glass_cutter",
    "edge_bonder", "quality_station",
}


def make_plan(
    question: str,
    client: LLMClient,
    *,
    schema_card: str | None = None,
) -> dict:
    """Stage 1: NL question -> validated JSON plan.

    Tries the LLM first. If parsing or validation fails, falls back to the
    mock client's plan for the same question and prints a one-line note.

    `schema_card` lets a caller (e.g. the HTTP service) inject the card
    from a mounted ConfigMap rather than relying on the module constant.
    """
    sc = schema_card or SCHEMA_CARD
    try:
        raw = client.complete(sc, question)
        plan = _parse_json(raw)
        _validate_plan(plan)
        return plan
    except Exception as exc:
        if isinstance(client, MockClient):
            raise
        print(f"[plan] {client.name} returned unusable output ({exc}); "
              f"falling back to mock plan")
        fallback = default_mock_client()
        raw = fallback.complete(sc, question)
        plan = _parse_json(raw)
        _validate_plan(plan)
        return plan


def _parse_json(s: str) -> dict:
    s = s.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    m = re.search(r"\{.*\}", s, re.DOTALL)
    if not m:
        raise ValueError(f"no JSON object in model response: {s[:120]!r}")
    return json.loads(m.group(0))


def _validate_plan(plan: dict) -> None:
    if plan.get("signal") not in SIGNALS:
        raise ValueError(f"unknown signal: {plan.get('signal')!r}")
    line = plan.get("line_id")
    if line is not None and line not in LINES:
        raise ValueError(f"unknown line: {line!r}")
    # Small models often return machine_id as a bare string. Coerce in place.
    machines = plan.get("machine_id")
    if isinstance(machines, str):
        plan["machine_id"] = [machines]
        machines = plan["machine_id"]
    if machines is not None:
        if not isinstance(machines, list) or not set(machines).issubset(MACHINES):
            raise ValueError(f"unknown machine in: {machines!r}")
    tw = plan.get("time_window") or {}
    pd.Timestamp(tw["start"])  # raises if invalid
    pd.Timestamp(tw["end"])
    if plan.get("intent") == "drift":
        b = plan.get("baseline") or {}
        pd.Timestamp(b["start"])
        pd.Timestamp(b["end"])


# ---------------------------------------------------------------------------
# Stage 2 — deterministic execution
# ---------------------------------------------------------------------------

def execute_plan(plan: dict, measurements: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Stage 2: plan + dataframe -> (filtered window df, stats dict).

    No LLM here. Pandas only. The chart and the annotation are both grounded
    in `stats`.
    """
    df = measurements
    if plan.get("line_id"):
        df = df[df.line_id == plan["line_id"]]
    if plan.get("machine_id"):
        df = df[df.machine_id.isin(plan["machine_id"])]
    df = df[df.signal == plan["signal"]]

    start = pd.Timestamp(plan["time_window"]["start"])
    end = pd.Timestamp(plan["time_window"]["end"])
    window = df[(df.timestamp >= start) & (df.timestamp < end)].copy()

    stats: dict[str, Any] = {
        "intent": plan["intent"],
        "signal": plan["signal"],
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "n_rows": int(len(window)),
    }

    if plan["intent"] == "drift":
        b_start = pd.Timestamp(plan["baseline"]["start"])
        b_end = pd.Timestamp(plan["baseline"]["end"])
        base = df[(df.timestamp >= b_start) & (df.timestamp < b_end)]
        rows: list[dict[str, Any]] = []
        for machine, grp in window.groupby("machine_id"):
            base_grp = base[base.machine_id == machine]
            base_mean = float(base_grp.value.mean()) if len(base_grp) else float("nan")
            cur_mean = float(grp.value.mean())
            pct = ((cur_mean - base_mean) / base_mean * 100) if base_mean else float("nan")
            rows.append({
                "machine_id": machine,
                "baseline_mean": round(base_mean, 3),
                "current_mean": round(cur_mean, 3),
                "delta_pct": round(pct, 1),
            })
        stats["per_machine"] = rows
        stats["drifted_more_than_20pct"] = [
            r["machine_id"] for r in rows if abs(r["delta_pct"]) > 20
        ]
        stats["baseline_start"] = b_start.isoformat()
        stats["baseline_end"] = b_end.isoformat()

    elif plan["intent"] == "anomaly":
        rows = []
        for machine, grp in window.groupby("machine_id"):
            values = grp.value.dropna()
            rows.append({
                "machine_id": machine,
                "min": round(float(values.min()), 3) if len(values) else None,
                "max": round(float(values.max()), 3) if len(values) else None,
                "mean": round(float(values.mean()), 3) if len(values) else None,
                "samples_near_zero": int((values < 0.1).sum()),
                "samples_total": int(len(values)),
            })
        stats["per_machine"] = rows

    else:  # lookup / compare
        agg = plan.get("aggregation", "mean")
        op = agg if agg in {"mean", "max", "min", "sum"} else "mean"
        rows = []
        for machine, grp in window.groupby("machine_id"):
            val = float(getattr(grp.value, op)())
            rows.append({"machine_id": machine, op: round(val, 3)})
        stats["per_machine"] = rows

    return window, stats


# ---------------------------------------------------------------------------
# Stage 2b — chart
# ---------------------------------------------------------------------------

def plot_result(plan: dict, window: pd.DataFrame, stats: dict, ax=None):
    """Time-series plot of the filtered window. Highlights baseline for drift."""
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(12, 4))

    if window.empty:
        ax.text(0.5, 0.5,
                "No data in the requested window.\n"
                "Window: "
                f"{plan['time_window']['start']} → {plan['time_window']['end']}",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=11, color="gray")
        ax.set_title(_chart_title(plan))
        ax.set_xticks([]); ax.set_yticks([])
        return ax

    for machine, grp in window.sort_values("timestamp").groupby("machine_id"):
        g = grp.set_index("timestamp").value
        # 5-min rolling mean smooths the 10s raw signal for the audience.
        smooth = g.rolling("5min").mean()
        ax.plot(smooth.index, smooth.values, label=machine, linewidth=1.2)

    if plan["intent"] == "drift" and plan.get("baseline"):
        ax.axvspan(
            pd.Timestamp(plan["baseline"]["start"]),
            pd.Timestamp(plan["baseline"]["end"]),
            alpha=0.10, color="gray", label="baseline window",
        )

    ax.set_ylabel(plan["signal"])
    ax.set_title(_chart_title(plan))
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)
    return ax


def _chart_title(plan: dict) -> str:
    where = plan.get("line_id") or "all lines"
    intent = plan["intent"].capitalize()
    return f"{intent} — {plan['signal']} — {where}"


# ---------------------------------------------------------------------------
# Stage 3 — annotation
# ---------------------------------------------------------------------------

def relevant_events(plan: dict, events: pd.DataFrame) -> pd.DataFrame:
    """Subset of events that overlap the plan's window and scope."""
    start = pd.Timestamp(plan["time_window"]["start"])
    end = pd.Timestamp(plan["time_window"]["end"])
    df = events[(events.timestamp >= start) & (events.timestamp < end)]
    if plan.get("line_id"):
        df = df[df.line_id == plan["line_id"]]
    if plan.get("machine_id"):
        df = df[df.machine_id.isin(plan["machine_id"])]
    return df.reset_index(drop=True)


def annotate(
    question: str,
    stats: dict,
    events: pd.DataFrame,
    client: LLMClient,
) -> str:
    """Stage 3: ask the LLM to phrase the stats and events as plain English.

    The LLM is told what was computed; it must not invent numbers. If stats
    are empty (n_rows = 0 or no per_machine rows), return a deterministic
    refusal — never let the model hallucinate numbers into a void.
    """
    if stats.get("n_rows", 0) == 0 or not stats.get("per_machine"):
        return ("No measurements in the requested window — the model picked a "
                "time range outside the available data. Try a different "
                "question or widen the window.")
    payload = {
        "question": question,
        "stats": stats,
        "events": _events_for_prompt(events),
    }
    prompt = json.dumps(payload, default=str, indent=2)
    try:
        text = client.complete(ANNOTATE_SYSTEM, prompt).strip()
        return _strip_fences(text)
    except Exception as exc:
        if isinstance(client, MockClient):
            raise
        print(f"[annotate] {client.name} failed ({exc}); using mock annotation")
        fb = default_mock_client()
        return fb.complete(ANNOTATE_SYSTEM, prompt).strip()


def _events_for_prompt(events: pd.DataFrame) -> list[dict]:
    if events.empty:
        return []
    cols = ["timestamp", "machine_id", "event_type", "severity", "code", "message"]
    sub = events[cols].copy()
    sub["timestamp"] = sub["timestamp"].astype(str)
    return sub.to_dict(orient="records")


def _strip_fences(s: str) -> str:
    s = re.sub(r"^```(?:\w+)?\s*", "", s.strip())
    s = re.sub(r"\s*```$", "", s)
    return s.strip()


# ---------------------------------------------------------------------------
# Top-level convenience: ask(...) does all three stages
# ---------------------------------------------------------------------------

def ask(
    question: str,
    measurements: pd.DataFrame,
    events: pd.DataFrame,
    client: LLMClient,
    *,
    show: bool = True,
):
    """Full pipeline: question -> (plan, window, stats, events, annotation).

    Returns a dict with all intermediate artefacts so the notebook can print
    or render any of them. If show=True, draws the chart and prints stats
    and annotation inline.
    """
    plan = make_plan(question, client)
    window, stats = execute_plan(plan, measurements)
    rel = relevant_events(plan, events)
    text = annotate(question, stats, rel, client)

    if show:
        import matplotlib.pyplot as plt
        print(f"Q: {question}")
        print(f"  client: {client.name}   intent: {plan['intent']}   "
              f"signal: {plan['signal']}")
        plot_result(plan, window, stats)
        plt.tight_layout()
        plt.show()
        if "per_machine" in stats:
            print(pd.DataFrame(stats["per_machine"]).to_string(index=False))
        if not rel.empty:
            print()
            print("Events in window:")
            print(rel[["timestamp", "machine_id", "severity", "code", "message"]]
                  .to_string(index=False))
        print()
        print("Annotation:")
        print(text)

    return {
        "plan": plan,
        "window": window,
        "stats": stats,
        "events": rel,
        "annotation": text,
    }
