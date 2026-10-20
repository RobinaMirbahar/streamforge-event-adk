"""FastAPI Cloud Run receiver for Google Cloud Eventarc & Pub/Sub CloudEvents."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, Request

from streamforge_agent.agent import process_incoming_cloudevent
from streamforge_agent.schemas import CloudEventEnvelope
from streamforge_agent.tools import check_cloudevent_idempotency

app = FastAPI(
    title="StreamForge Event-Driven ADK Multi-Agent Service",
    description="Real-time Eventarc + Pub/Sub CloudEvent receiver running Google ADK ParallelAgent & LoopAgent with Gemma 3.",
    version="1.0.0",
)


@app.get("/healthz")
def health_check() -> Dict[str, str]:
    return {
        "status": "healthy",
        "service": "streamforge-event-adk",
        "model": os.getenv("STREAMFORGE_MODEL_NAME", "ollama_chat/gemma3:12b"),
    }


@app.post("/api/v1/cloudevent")
async def receive_eventarc_cloudevent(
    request: Request,
    ce_id: Optional[str] = Header(default=None, alias="ce-id"),
    ce_type: Optional[str] = Header(default=None, alias="ce-type"),
    ce_source: Optional[str] = Header(default=None, alias="ce-source"),
    ce_time: Optional[str] = Header(default=None, alias="ce-time"),
) -> Dict[str, Any]:
    """Handles binary-mode or structured-mode CNCF CloudEvents delivered by Eventarc."""
    body = await request.json()
    envelope = CloudEventEnvelope(
        ce_id=ce_id or body.get("ce_id", "ce-98104271-gcs-finalized"),
        ce_type=ce_type or body.get("ce_type", "google.cloud.storage.object.v1.finalized"),
        ce_source=ce_source or body.get("ce_source", "//storage.googleapis.com/projects/_/buckets/streamforge-launch-inbox"),
        ce_time=ce_time or body.get("ce_time", "2026-10-20T08:14:02Z"),
        bucket=body.get("bucket", "streamforge-launch-inbox"),
        object_name=body.get("name") or body.get("object_name", "releases/2026-10/vertex-vector-sync-v4.2.json"),
        generation=str(body.get("generation", "1729412042881001")),
    )
    receipt, _ = process_incoming_cloudevent(envelope=envelope)
    return receipt.to_dict()


@app.get("/api/v1/manifests/{ce_id}")
def get_manifest_by_cloudevent(ce_id: str) -> Dict[str, Any]:
    doc = check_cloudevent_idempotency(ce_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"No manifest found for ce-id={ce_id}")
    return doc
