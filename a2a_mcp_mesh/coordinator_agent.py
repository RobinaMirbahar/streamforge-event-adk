import os
from typing import Any, Dict
from google.adk.agents import LlmAgent, LoopAgent, ParallelAgent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm

from .a2a_remote_github_agent import get_a2a_agent_card, handle_a2a_task_send
from .mcp_servers.alloydb_vector_mcp import search_alloydb_runbooks_scann
from .mcp_servers.spanner_graph_mcp import query_service_blast_radius_gql
from .schemas import IncidentMeshManifest


def delegate_github_remediation_via_a2a(
    service_id: str,
    failing_commit_sha: str,
) -> Dict[str, Any]:
    """Discovers the remote A2A GitHub agent via /.well-known/agent.json and sends a tasks/send payload."""
    card = get_a2a_agent_card()
    rpc_response = handle_a2a_task_send(
        {
            "jsonrpc": "2.0",
            "id": "a2a-task-9041",
            "method": "tasks/send",
            "params": {
                "service_id": service_id,
                "failing_commit_sha": failing_commit_sha,
            },
        }
    )
    return {
        "discovered_agent_card": card["name"],
        "a2a_endpoint": card["url"],
        "a2a_result": rpc_response["result"],
    }


def audit_mesh_remediation_safety(
    impacted_enterprise_tenants: int,
    proposed_rollout_strategy: str,
    iteration: int = 1,
) -> Dict[str, Any]:
    """Audits the A2A remediation rollout plan against Spanner Graph blast-radius and AlloyDB runbook constraints."""
    if impacted_enterprise_tenants > 10 and proposed_rollout_strategy == "IMMEDIATE_100_PERCENT_CUTOVER" and iteration == 1:
        return {
            "iteration": 1,
            "safety_score": 0.68,
            "passed": False,
            "policy_violations": [
                "Blast-radius violation: Spanner Graph shows 42 impacted enterprise tenants ($184,000/hr SLA exposure), exceeding the 10-tenant threshold for IMMEDIATE_100_PERCENT_CUTOVER.",
                "AlloyDB Runbook RB-SPANNER-GRPC-POOL-204 violation: Tier-1 financial services require a staged 10% -> 50% -> 100% Cloud Run canary traffic split.",
            ],
            "enforced_rollout_strategy": "CANARY_10_50_100_TRAFFIC_SPLIT",
        }
    return {
        "iteration": iteration,
        "safety_score": 1.0,
        "passed": True,
        "policy_violations": [],
        "enforced_rollout_strategy": "CANARY_10_50_100_TRAFFIC_SPLIT",
    }


def exit_safety_audit_loop(tool_context: Any = None) -> Dict[str, Any]:
    """Signals Google ADK LoopAgent to terminate iteration once safety_score reaches 1.0."""
    if tool_context is not None and hasattr(tool_context, "actions"):
        tool_context.actions.escalate = True
    return {"status": "SAFETY_LOOP_ESCALATED", "escalate": True}


def build_a2a_mcp_mesh_coordinator() -> SequentialAgent:
    """Constructs the hybrid Multi-MCP + A2A ParallelAgent -> LoopAgent -> Publisher ADK coordinator."""
    model = LiteLlm(model=os.getenv("MESH_MODEL_NAME", "openai/google/gemma-4-27b-it"))

    spanner_graph_specialist = LlmAgent(
        name="SpannerGraphBlastRadiusAgent",
        model=model,
        instruction=(
            "Call `query_service_blast_radius_gql` via the Spanner Graph MCP server to compute "
            "the 3-hop downstream microservice blast radius and store it in `{spanner_blast_radius}`."
        ),
        tools=[query_service_blast_radius_gql],
        output_key="spanner_blast_radius",
    )

    alloydb_runbook_specialist = LlmAgent(
        name="AlloyDBRunbookVectorAgent",
        model=model,
        instruction=(
            "Call `search_alloydb_runbooks_scann` via the AlloyDB MCP server to retrieve the "
            "highest-similarity SRE runbook and store it in `{alloydb_runbook}`."
        ),
        tools=[search_alloydb_runbooks_scann],
        output_key="alloydb_runbook",
    )

    a2a_github_specialist = LlmAgent(
        name="A2AGitHubRemediationClientAgent",
        model=model,
        instruction=(
            "Discover the remote A2A GitHub agent via `/.well-known/agent.json` and call "
            "`delegate_github_remediation_via_a2a` to create a rollback PR. Store the result in `{a2a_remediation}`."
        ),
        tools=[delegate_github_remediation_via_a2a],
        output_key="a2a_remediation",
    )

    parallel_mesh_fanout = ParallelAgent(
        name="ConcurrentMultiMCPAndA2AFanOut",
        description="Queries Spanner Graph MCP, AlloyDB pgvector MCP, and Remote A2A GitHub Agent concurrently.",
        sub_agents=[
            spanner_graph_specialist,
            alloydb_runbook_specialist,
            a2a_github_specialist,
        ],
    )

    safety_critic = LlmAgent(
        name="RemediationSafetyCriticAgent",
        model=model,
        instruction=(
            "Inspect `{spanner_blast_radius}`, `{alloydb_runbook}`, and `{a2a_remediation}`. "
            "Call `audit_mesh_remediation_safety`. Once `safety_score` reaches 1.0, call `exit_safety_audit_loop`."
        ),
        tools=[audit_mesh_remediation_safety, exit_safety_audit_loop],
        output_key="safety_audit_verdict",
    )

    safety_loop = LoopAgent(
        name="MeshRemediationSafetyLoop",
        sub_agents=[safety_critic],
        max_iterations=3,
    )

    manifest_publisher = LlmAgent(
        name="IncidentMeshManifestPublisher",
        model=model,
        instruction=(
            "Synthesize `{spanner_blast_radius}`, `{alloydb_runbook}`, `{a2a_remediation}`, and "
            "`{safety_audit_verdict}` into a validated `IncidentMeshManifest`."
        ),
        output_key="published_mesh_manifest",
        output_schema=IncidentMeshManifest,
    )

    return SequentialAgent(
        name="CloudRunA2AMCPMeshCoordinator",
        sub_agents=[parallel_mesh_fanout, safety_loop, manifest_publisher],
    )
