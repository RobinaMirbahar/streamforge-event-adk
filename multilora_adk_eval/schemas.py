from typing import Any, Dict, List
from pydantic import BaseModel, Field


class LoraAdapterMetadata(BaseModel):
    """Metadata for a domain-specific QLoRA adapter streamed via Cloud Storage FUSE."""

    adapter_id: str = Field(..., description="Unique LoRA adapter identifier exposed by vLLM.")
    base_model: str = Field(
        default="google/gemma-4-27b-it",
        description="Frozen base open-weights model loaded once in Cloud Run GPU VRAM.",
    )
    gcs_fuse_path: str = Field(
        ..., description="Mounted Cloud Storage FUSE directory containing adapter_model.safetensors."
    )
    lora_rank: int = Field(default=16, ge=4, le=64, description="LoRA rank r.")
    lora_alpha: int = Field(default=32, ge=8, le=128, description="LoRA scaling factor alpha.")
    vram_overhead_mb: float = Field(
        ..., description="Additional GPU VRAM footprint of this adapter in megabytes."
    )


class MultiLoraToolCall(BaseModel):
    """Structured tool invocation captured during ADK agent execution."""

    tool_name: str = Field(..., description="Name of the Python tool invoked by the ADK sub-agent.")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Key-value arguments passed to the tool."
    )


class EvalCaseResult(BaseModel):
    """Per-case evaluation result comparing expected vs. actual ADK tool trajectories."""

    case_id: str = Field(..., description="Golden dataset test case identifier.")
    domain_adapter: str = Field(..., description="LoRA adapter or base model evaluated.")
    prompt: str = Field(..., description="User prompt evaluated.")
    expected_tool_calls: List[MultiLoraToolCall] = Field(
        ..., description="Golden reference tool trajectory."
    )
    actual_tool_calls: List[MultiLoraToolCall] = Field(
        ..., description="Observed tool trajectory emitted by the agent."
    )
    tool_trajectory_score: float = Field(
        ..., ge=0.0, le=1.0, description="Exact match score for tool sequence and arguments."
    )
    response_match_score: float = Field(
        ..., ge=0.0, le=1.0, description="ROUGE-1 / token overlap score against reference answer."
    )
    adapter_switch_latency_ms: float = Field(
        ..., description="vLLM runtime LoRA adapter switching overhead in milliseconds."
    )
    passed: bool = Field(..., description="True if both trajectory and response thresholds pass.")


class EvalSuiteSummary(BaseModel):
    """Complete CI/CD release gate report produced by the ADK evaluation runner."""

    suite_name: str = Field(..., description="Evaluation suite identifier.")
    base_model: str = Field(default="google/gemma-4-27b-it")
    registered_adapters: List[LoraAdapterMetadata] = Field(
        ..., description="LoRA adapters dynamically loaded onto the shared Cloud Run GPU."
    )
    base_model_trajectory_avg: float = Field(
        ..., description="Average tool_trajectory_avg_score using unadapted base Gemma 4."
    )
    multilora_trajectory_avg: float = Field(
        ..., description="Average tool_trajectory_avg_score using Multi-LoRA hot-swapping."
    )
    multilora_response_match_avg: float = Field(
        ..., description="Average response_match_score using Multi-LoRA hot-swapping."
    )
    threshold_tool_trajectory: float = Field(default=0.95)
    threshold_response_match: float = Field(default=0.85)
    release_gate_passed: bool = Field(
        ..., description="True if Multi-LoRA scores exceed CI/CD release gate thresholds."
    )
    case_results: List[EvalCaseResult] = Field(
        ..., description="Detailed per-case evaluation breakdown."
    )
