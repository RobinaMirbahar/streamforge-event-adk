"""StreamForge: Event-Driven Multi-Agent Pipeline built with Google ADK (ParallelAgent + LoopAgent) & Gemma 3."""

from .agent import (
    build_streamforge_event_pipeline,
    process_incoming_cloudevent,
)
from .schemas import (
    CloudEventEnvelope,
    CloudEventProcessingReceipt,
    EventDrivenLaunchManifest,
    LoopCritiqueVerdict,
    ParallelEnrichmentBundle,
)

__all__ = [
    "build_streamforge_event_pipeline",
    "process_incoming_cloudevent",
    "CloudEventEnvelope",
    "CloudEventProcessingReceipt",
    "EventDrivenLaunchManifest",
    "LoopCritiqueVerdict",
    "ParallelEnrichmentBundle",
]
