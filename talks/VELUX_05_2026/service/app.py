"""HTTP service wrapping the NL-query pipeline.

Same three stages as the notebook (plan / execute / annotate), exposed as
a small FastAPI surface. The notebook is the exploratory surface; this is
the platform-native one — container, ConfigMap, Service, Argo Application.

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
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import nl_query

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
    yield


app = FastAPI(
    title="VELUX NL-query for factory data",
    description="NL → JSON plan → pandas → annotation. Same three stages as "
                "the notebook; container-native deployment shape.",
    version="0.1.0",
    lifespan=lifespan,
)


class AskBody(BaseModel):
    question: str


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    ready = state.measurements is not None and state.client is not None
    return {
        "ok": True,
        "ready": ready,
        "client": state.client.name if state.client else None,
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


@app.post("/ask")
def ask_endpoint(body: AskBody) -> dict[str, Any]:
    try:
        plan = nl_query.make_plan(body.question, state.client,
                                  schema_card=state.schema_card)
        _, stats = nl_query.execute_plan(plan, state.measurements)
        rel = nl_query.relevant_events(plan, state.events)
        annotation = nl_query.annotate(body.question, stats, rel, state.client)
        events = rel.assign(timestamp=lambda d: d.timestamp.astype(str))\
                    .to_dict(orient="records") if not rel.empty else []
        return {
            "plan": plan,
            "stats": stats,
            "events": events,
            "annotation": annotation,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
