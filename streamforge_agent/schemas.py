"""Strict Pydantic and dataclass schemas for StreamForge Event-Driven ADK ParallelAgent + LoopAgent."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

try:
    from pydantic import BaseModel, Field

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object  # type: ignore


if PYDANTIC_AVAILABLE:

    class CloudEventEnvelope(BaseModel):
        """Standard CNCF CloudEvents v1.0 envelope delivered by Google Cloud Eventarc."""

        ce_id: str = Field(description="Unique CloudEvent ID (ce-id header) used for idempotency.")
        ce_type: str = Field(
            default="google.cloud.storage.object.v1.finalized",
            description="CloudEvent type emitted by Cloud Storage or BigQuery.",
        )
        ce_source: str = Field(description="CloudEvent source URI.")
        ce_time: str = Field(description="ISO-8601 event timestamp.")
        bucket: str = Field(description="GCS bucket name.")
        object_name: str = Field(description="GCS object path that triggered the pipeline.")
        generation: str = Field(description="GCS object generation number.")

        def to_dict(self) -> Dict[str, Any]:
            return self.model_dump()

    class ParallelEnrichmentBundle(BaseModel):
        """Combined outputs written concurrently to session.state by the 3 ParallelAgent workers."""

        extracted_specs: Dict[str, Any] = Field(description="Output from TechnicalSpecExtractorAgent.")
        localized_copy: Dict[str, Any] = Field(description="Output from GlobalLocalizationAgent.")
        pricing_simulation: Dict[str, Any] = Field(description="Output from RevenuePricingSimulatorAgent.")

        def to_dict(self) -> Dict[str, Any]:
            return self.model_dump()

    class LoopCritiqueVerdict(BaseModel):
        """Iterative verification output produced inside ADK LoopAgent (QualityCritiqueRefinementLoop)."""

        iteration: int = Field(description="1-based LoopAgent iteration index.")
        quality_score: float = Field(description="Composite readiness score from 0.0 to 1.0.")
        discrepancies_found: List[str] = Field(description="Detected cross-agent inconsistencies.")
        remediation_applied: str = Field(description="Correction applied during this loop iteration.")
        escalate_exit: bool = Field(description="True when ToolContext.actions.escalate is triggered.")

        def to_dict(self) -> Dict[str, Any]:
            return self.model_dump()

    class EventDrivenLaunchManifest(BaseModel):
        """Final validated launch package persisted to Cloud Firestore and BigQuery."""

        manifest_id: str = Field(description="Deterministic manifest ID tied to release SKU.")
        cloudevent_id: str = Field(description="Originating Eventarc ce-id.")
        release_sku: str = Field(description="Product release SKU identifier.")
        product_title: str = Field(description="Official release title.")
        technical_highlights: List[str] = Field(description="Validated engineering specs and benchmarks.")
        regional_launch_copy: Dict[str, str] = Field(description="Localized launch headlines (en_US, de_DE, ja_JP).")
        pricing_tiers_usd_eur_jpy: Dict[str, str] = Field(description="Parity-verified multi-currency pricing.")
        projected_net_arr_lift_usd: float = Field(description="Simulated 12-month ARR expansion in USD.")
        loop_iterations_completed: int = Field(description="Number of LoopAgent self-correction passes.")
        final_quality_score: float = Field(description="Final LoopAgent readiness score (1.0).")
        generated_by_model: str = Field(description="Model identifier used by Google ADK.")

        def to_dict(self) -> Dict[str, Any]:
            return self.model_dump()

    class CloudEventProcessingReceipt(BaseModel):
        """HTTP response returned to Eventarc / Cloud Pub/Sub push subscription."""

        ack_status: str = Field(description="ACK_PROCESSED or ACK_DUPLICATE_CLOUDEVENT.")
        ce_id: str = Field(description="CloudEvent ID.")
        ce_type: str = Field(description="CloudEvent type.")
        idempotent_replay: bool = Field(description="True if ce-id was already processed.")
        parallel_branches_executed: int = Field(description="Number of concurrent ParallelAgent branches.")
        loop_iterations_executed: int = Field(description="Number of LoopAgent critique iterations.")
        execution_latency_ms: int = Field(description="Total processing time in milliseconds.")
        manifest: EventDrivenLaunchManifest = Field(description="Persisted launch manifest.")

        def to_dict(self) -> Dict[str, Any]:
            return self.model_dump()

else:

    @dataclass
    class CloudEventEnvelope:  # type: ignore[no-redef]
        ce_id: str
        ce_type: str
        ce_source: str
        ce_time: str
        bucket: str
        object_name: str
        generation: str

        def to_dict(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class ParallelEnrichmentBundle:  # type: ignore[no-redef]
        extracted_specs: Dict[str, Any]
        localized_copy: Dict[str, Any]
        pricing_simulation: Dict[str, Any]

        def to_dict(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class LoopCritiqueVerdict:  # type: ignore[no-redef]
        iteration: int
        quality_score: float
        discrepancies_found: List[str]
        remediation_applied: str
        escalate_exit: bool

        def to_dict(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class EventDrivenLaunchManifest:  # type: ignore[no-redef]
        manifest_id: str
        cloudevent_id: str
        release_sku: str
        product_title: str
        technical_highlights: List[str] = field(default_factory=list)
        regional_launch_copy: Dict[str, str] = field(default_factory=dict)
        pricing_tiers_usd_eur_jpy: Dict[str, str] = field(default_factory=dict)
        projected_net_arr_lift_usd: float = 0.0
        loop_iterations_completed: int = 2
        final_quality_score: float = 1.0
        generated_by_model: str = "ollama_chat/gemma3:12b"

        def to_dict(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class CloudEventProcessingReceipt:  # type: ignore[no-redef]
        ack_status: str
        ce_id: str
        ce_type: str
        idempotent_replay: bool
        parallel_branches_executed: int
        loop_iterations_executed: int
        execution_latency_ms: int
        manifest: EventDrivenLaunchManifest

        def to_dict(self) -> Dict[str, Any]:
            return asdict(self)
