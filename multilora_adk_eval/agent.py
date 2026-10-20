import os
from typing import Any, Dict, Optional
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm


def diagnose_cloud_run_5xx_spike(
    service_name: str,
    region: str = "us-central1",
    window_minutes: int = 15,
) -> Dict[str, Any]:
    """Diagnoses HTTP 5xx latency and error spikes for a Cloud Run service."""
    return {
        "service_name": service_name,
        "region": region,
        "window_minutes": window_minutes,
        "p99_latency_ms": 4820,
        "error_rate_5xx_pct": 14.8,
        "root_cause": "Container concurrency limit (80) saturated by blocking synchronous DB calls",
        "recommended_remediation": (
            f"gcloud run services update {service_name} --region={region} "
            "--concurrency=200 --cpu=4 --memory=8Gi"
        ),
    }


def rightsize_cloud_run_gpu_allocation(
    service_name: str,
    target_concurrency: int = 16,
    min_instances: int = 0,
) -> Dict[str, Any]:
    """Computes FinOps GPU right-sizing and scale-to-zero savings for a Cloud Run GPU service."""
    return {
        "service_name": service_name,
        "target_concurrency": target_concurrency,
        "min_instances": min_instances,
        "estimated_monthly_savings_usd": 1480.00,
        "gpu_utilization_before_pct": 21.5,
        "gpu_utilization_after_pct": 78.4,
        "applied_command": (
            f"gcloud run services update {service_name} --region=us-central1 "
            f"--concurrency={target_concurrency} --min-instances={min_instances}"
        ),
    }


def quarantine_overprivileged_service_account(
    service_account_email: str,
    revoke_role: str = "roles/editor",
) -> Dict[str, Any]:
    """Revokes an over-privileged IAM role from a service account and binds least-privilege roles."""
    return {
        "service_account_email": service_account_email,
        "revoked_role": revoke_role,
        "replacement_role": "roles/run.invoker",
        "policy_id": "SEC-IAM-LEAST-PRIV-004",
        "status": "QUARANTINED_AND_REMEDIATED",
    }


def _build_vllm_model(
    lora_or_model_id: str,
    vllm_api_base: Optional[str] = None,
    id_token: Optional[str] = None,
) -> LiteLlm:
    """Creates a LiteLlm wrapper targeting a specific LoRA adapter ID on the shared vLLM GPU server."""
    base_url = vllm_api_base or os.environ.get(
        "VLLM_API_BASE", "http://127.0.0.1:18090/v1"
    )
    extra_headers: Dict[str, str] = {}
    if id_token:
        extra_headers["Authorization"] = f"Bearer {id_token}"

    return LiteLlm(
        model=f"openai/{lora_or_model_id}",
        api_base=base_url,
        api_key=id_token or "vllm-local-token",
        extra_headers=extra_headers if extra_headers else None,
    )


def build_multilora_adk_coordinator(
    vllm_api_base: Optional[str] = None,
    id_token: Optional[str] = None,
) -> LlmAgent:
    """Assembles the Google ADK Multi-LoRA Agent Hierarchy sharing a single Cloud Run L4 GPU."""
    sre_agent = LlmAgent(
        name="SreIncidentAgent",
        model=_build_vllm_model("sre-incident-lora", vllm_api_base, id_token),
        description="Handles Cloud Run HTTP 5xx spikes, latency degradation, and SRE root-cause diagnostics.",
        instruction=(
            "You are fine-tuned with the 'sre-incident-lora' adapter. "
            "Always call `diagnose_cloud_run_5xx_spike` with the exact service_name, region, "
            "and window_minutes before recommending a remediation command."
        ),
        tools=[diagnose_cloud_run_5xx_spike],
    )

    finops_agent = LlmAgent(
        name="FinOpsCostAgent",
        model=_build_vllm_model("finops-cost-lora", vllm_api_base, id_token),
        description="Handles Cloud Run GPU utilization right-sizing, concurrency tuning, and FinOps cost optimization.",
        instruction=(
            "You are fine-tuned with the 'finops-cost-lora' adapter. "
            "Always call `rightsize_cloud_run_gpu_allocation` with the exact service_name, "
            "target_concurrency, and min_instances."
        ),
        tools=[rightsize_cloud_run_gpu_allocation],
    )

    secops_agent = LlmAgent(
        name="SecOpsAuditAgent",
        model=_build_vllm_model("secops-audit-lora", vllm_api_base, id_token),
        description="Handles IAM privilege escalation alerts and service account quarantine actions.",
        instruction=(
            "You are fine-tuned with the 'secops-audit-lora' adapter. "
            "Always call `quarantine_overprivileged_service_account` with service_account_email "
            "and revoke_role."
        ),
        tools=[quarantine_overprivileged_service_account],
    )

    root_coordinator = LlmAgent(
        name="EnterpriseMultiLoraCoordinator",
        model=_build_vllm_model("google/gemma-4-27b-it", vllm_api_base, id_token),
        description="Root ADK Coordinator routing enterprise tasks across hot-swapped Multi-LoRA specialists.",
        instruction=(
            "Route production reliability incidents to SreIncidentAgent, "
            "GPU cost/concurrency optimization requests to FinOpsCostAgent, "
            "and IAM security alerts to SecOpsAuditAgent."
        ),
        sub_agents=[sre_agent, finops_agent, secops_agent],
    )
    return root_coordinator
