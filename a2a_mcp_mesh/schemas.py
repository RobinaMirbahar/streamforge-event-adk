from typing import Dict, List
from pydantic import BaseModel, Field


class AgentSkillCard(BaseModel):
    """Skill advertised inside an A2A /.well-known/agent.json AgentCard."""

    id: str = Field(description="Unique A2A skill identifier.")
    name: str = Field(description="Human-readable skill name.")
    description: str = Field(description="Capability summary used by the root ADK coordinator.")
    tags: List[str] = Field(description="Routing tags for horizontal A2A delegation.")


class A2AAgentCard(BaseModel):
    """Standard Agent-to-Agent (A2A) discovery card served at /.well-known/agent.json."""

    name: str = Field(description="Remote ADK specialist agent name.")
    url: str = Field(description="Private Cloud Run HTTPS endpoint for JSON-RPC tasks/send.")
    version: str = Field(default="1.0.0", description="A2A agent contract version.")
    authentication: str = Field(default="google-cloud-run-oidc", description="Required IAM auth scheme.")
    skills: List[AgentSkillCard] = Field(description="Advertised A2A capabilities.")


class SpannerBlastRadiusReport(BaseModel):
    """Output returned by the Cloud Spanner Graph MCP server via GQL traversal."""

    root_service_id: str = Field(description="Originating microservice ID.")
    failing_commit_sha: str = Field(description="Suspected regression commit SHA.")
    hop_count: int = Field(description="Maximum GQL graph traversal depth.")
    impacted_downstream_services: List[str] = Field(description="Downstream services on the call path.")
    impacted_enterprise_tenants: int = Field(description="Active enterprise tenants affected.")
    sla_breach_risk_usd: float = Field(description="Projected hourly SLA penalty exposure in USD.")


class AlloyDBRunbookMatch(BaseModel):
    """Output returned by the AlloyDB pgvector ScaNN hybrid search MCP server."""

    runbook_id: str = Field(description="Canonical SRE runbook identifier.")
    similarity_score: float = Field(description="Cosine similarity score from AlloyDB ScaNN index.")
    remediation_strategy: str = Field(description="Verified mitigation procedure.")
    required_safety_checks: List[str] = Field(description="Pre-rollback verification gates.")


class MeshSafetyAuditVerdict(BaseModel):
    """Iterative verification output produced inside the ADK LoopAgent."""

    iteration: int = Field(description="1-based LoopAgent iteration index.")
    safety_score: float = Field(description="Composite remediation safety score from 0.0 to 1.0.")
    policy_violations: List[str] = Field(description="Detected blast-radius or rollout policy violations.")
    remediation_adjustment: str = Field(description="Adjustment applied during this loop iteration.")
    escalate_exit: bool = Field(description="True when ToolContext.actions.escalate is triggered.")


class IncidentMeshManifest(BaseModel):
    """Final validated remediation manifest produced by the A2A + Multi-MCP Mesh."""

    manifest_id: str = Field(description="Deterministic incident remediation manifest ID.")
    incident_id: str = Field(description="Incoming production incident identifier.")
    root_service_id: str = Field(description="Failing service identified in Spanner Graph.")
    impacted_services: List[str] = Field(description="Downstream services discovered via 3-hop GQL query.")
    matched_runbook_id: str = Field(description="AlloyDB pgvector ScaNN matched runbook ID.")
    a2a_delegated_agent: str = Field(description="Remote A2A specialist agent invoked via tasks/send.")
    github_rollback_pr_url: str = Field(description="GitHub Pull Request URL created via GitHub MCP.")
    rollout_strategy: str = Field(description="Canary traffic split enforced by the LoopAgent safety gate.")
    loop_iterations_completed: int = Field(description="Number of LoopAgent verification passes.")
    final_safety_score: float = Field(description="Final LoopAgent safety score (1.0).")
    model_name: str = Field(description="Gemma 4 model identifier served on Cloud Run GPU.")
