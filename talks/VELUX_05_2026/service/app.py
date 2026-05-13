"""HTTP service wrapping the NL-query pipeline.

Same three stages as the notebook (plan / execute / annotate), exposed as
a small FastAPI surface plus a tiny vanilla-HTML/JS UI. The notebook is
the exploratory surface; this is the platform-native one — container,
ConfigMap, Service, ready to be applied to any Kubernetes cluster.

Environment:
  DATA_PATH         parquet measurements path  (default /data/measurements.parquet)
  EVENTS_PATH       parquet events path        (default /data/events.parquet)
  SCHEMA_CARD_PATH  optional text file path. If set, its contents override
                    the in-code SCHEMA_CARD. In Kubernetes this points at a
                    mounted ConfigMap key — the governance surface lives in
                    git, not in the image.
  OLLAMA_HOST       e.g. http://ollama:11434  (Kubernetes service name)
  MODEL             e.g. qwen2.5:3b
  USE_MOCK          "1" forces the deterministic mock client
  STATIC_DIR        path to the UI static directory  (default /app/static)
"""

from __future__ import annotations

# Pin the matplotlib backend BEFORE any other matplotlib import. The server
# has no display; Agg is the headless-safe rasteriser.
import matplotlib
matplotlib.use("Agg")

import base64
import io
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from matplotlib.figure import Figure
from pydantic import BaseModel

# Allow running from the repo for local dev where nl_query lives in ../src,
# as well as from the container where it sits beside this file in /app.
_here = Path(__file__).resolve().parent
for candidate in (_here, _here.parent / "src"):
    if (candidate / "nl_query.py").exists() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import nl_query  # noqa: E402

log = logging.getLogger("nl_query.service")
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s %(message)s")


class State:
    measurements: pd.DataFrame | None = None
    events: pd.DataFrame | None = None
    client: nl_query.LLMClient | None = None
    schema_card: str = nl_query.SCHEMA_CARD


state = State()


def _load_client() -> nl_query.LLMClient:
    if os.environ.get("USE_MOCK") == "1":
        log.info("USE_MOCK=1 — using deterministic mock client")
        return nl_query.default_mock_client()
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    model = os.environ.get("MODEL", "qwen2.5:3b")
    if nl_query.OllamaClient.available(host):
        log.info("ollama reachable at %s — using %s", host, model)
        return nl_query.OllamaClient(model=model, host=host)
    log.warning("ollama unreachable at %s — falling back to mock", host)
    return nl_query.default_mock_client()


def _warm_model(client: nl_query.LLMClient) -> None:
    """Pre-load the model so the first user question isn't a 30-second wait.

    Cheap one-token generation. Silent on failure — graceful degradation
    will pick up the slack at request time.
    """
    if client.name != "ollama":
        return
    try:
        client.complete("Reply with the word OK.", "ping")
        log.info("model warm-up complete")
    except Exception as exc:  # pragma: no cover
        log.warning("model warm-up failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    data_path = Path(os.environ.get("DATA_PATH", "/data/measurements.parquet"))
    events_path = Path(os.environ.get("EVENTS_PATH", "/data/events.parquet"))
    state.measurements = pd.read_parquet(data_path)
    state.events = pd.read_parquet(events_path)
    log.info("loaded %d measurements, %d events",
             len(state.measurements), len(state.events))

    sp = os.environ.get("SCHEMA_CARD_PATH")
    if sp and Path(sp).exists():
        state.schema_card = Path(sp).read_text()
        log.info("schema card loaded from %s (%d chars)", sp, len(state.schema_card))

    state.client = _load_client()
    _warm_model(state.client)
    yield


app = FastAPI(
    title="VELUX NL-query for factory data",
    description="NL → JSON plan → pandas → annotation. Same three stages as "
                "the notebook; container-native deployment shape.",
    version="0.1.0",
    lifespan=lifespan,
)

# Serve the tiny vanilla UI. Mount before any wildcard routes.
_static_dir = Path(os.environ.get("STATIC_DIR", Path(__file__).parent / "static"))
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=_static_dir, html=True), name="static")


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/static/index.html")


class AskBody(BaseModel):
    question: str


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    ready = state.measurements is not None and state.client is not None
    return {
        "ok": True,
        "ready": ready,
        "client": state.client.name if state.client else None,
        "model": getattr(state.client, "model", None) if state.client else None,
        "rows": int(len(state.measurements)) if state.measurements is not None else 0,
    }


@app.get("/schema")
def schema() -> dict[str, str]:
    """Return the schema card. This is the governance surface."""
    return {"schema_card": state.schema_card}


@app.post("/plan")
def plan_endpoint(body: AskBody) -> dict:
    try:
        return nl_query.make_plan(body.question, state.client,
                                  schema_card=state.schema_card)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def _render_chart_png(plan: dict, window: pd.DataFrame, stats: dict) -> str:
    """Render the chart as a base64 PNG using the OO matplotlib interface.

    Same plot_result() the notebook uses — we pass an Axes from a Figure
    we own, so no pyplot state is touched (safer in a server context).
    """
    fig = Figure(figsize=(11, 4), dpi=110, layout="tight")
    ax = fig.add_subplot()
    nl_query.plot_result(plan, window, stats, ax=ax)
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    return base64.b64encode(buf.getvalue()).decode("ascii")


@app.post("/ask")
def ask_endpoint(body: AskBody) -> dict[str, Any]:
    try:
        plan = nl_query.make_plan(body.question, state.client,
                                  schema_card=state.schema_card)
        window, stats = nl_query.execute_plan(plan, state.measurements)
        rel = nl_query.relevant_events(plan, state.events)
        annotation = nl_query.annotate(body.question, stats, rel, state.client)
        chart_png = _render_chart_png(plan, window, stats)
        events = rel.assign(timestamp=lambda d: d.timestamp.astype(str))\
                    .to_dict(orient="records") if not rel.empty else []
        return {
            "plan": plan,
            "stats": stats,
            "events": events,
            "annotation": annotation,
            "chart_png": chart_png,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
