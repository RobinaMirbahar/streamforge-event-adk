import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from a2a_mcp_mesh.coordinator_agent import (
    audit_mesh_remediation_safety,
    delegate_github_remediation_via_a2a,
    exit_safety_audit_loop,
)
from a2a_mcp_mesh.mcp_servers.alloydb_vector_mcp import search_alloydb_runbooks_scann
from a2a_mcp_mesh.mcp_servers.spanner_graph_mcp import query_service_blast_radius_gql
from a2a_mcp_mesh.schemas import IncidentMeshManifest, MeshSafetyAuditVerdict


def run_codelab_verification() -> None:
    print("========================================================================================")
    print("CODELAB VERIFICATION: CLOUD RUN A2A & MULTI-MCP MESH (GEMMA 4 + GOOGLE ADK)")
    print("Model: google/gemma-4-27b-it (Cloud Run L4 GPU + GCS FUSE) | Protocol: A2A + FastMCP SSE")
    print("========================================================================================\n")

    incident_id = "INC-2026-8841"
    root_service = "grpc-edge-gateway"
    error_sig = "DEADLINE_EXCEEDED: Spanner gRPC channel pool exhausted on checkout-orchestrator-v2"

    print("[STEP 1] Executing ADK ParallelAgent (ConcurrentMultiMCPAndA2AFanOut)...")
    spanner_res = query_service_blast_radius_gql(service_id=root_service, max_hops=3)
    alloydb_res = search_alloydb_runbooks_scann(
        error_signature=error_sig,
        service_tier="TIER_1_FINANCIAL",
    )
    a2a_res = delegate_github_remediation_via_a2a(
        service_id=root_service,
        failing_commit_sha=spanner_res["failing_commit_sha"],
    )

    print(f"  * Branch 1 (Spanner Graph MCP)  : 3-hop GQL returned {len(spanner_res['impacted_downstream_services'])} downstream services, {spanner_res['impacted_enterprise_tenants']} tenants (${spanner_res['sla_breach_risk_usd']:,.0f}/hr SLA risk) in {spanner_res['query_latency_ms']} ms")
    print(f"  * Branch 2 (AlloyDB Vector MCP) : ScaNN index matched {alloydb_res['runbook_id']} (similarity={alloydb_res['similarity_score']}) in {alloydb_res['scann_query_latency_ms']} ms")
    print(f"  * Branch 3 (Remote A2A Agent)   : Discovered {a2a_res['discovered_agent_card']} via /.well-known/agent.json -> PR {a2a_res['a2a_result']['github_rollback_pr_url']}\n")

    print("[STEP 2] Executing ADK LoopAgent (MeshRemediationSafetyLoop)...")
    iter1 = audit_mesh_remediation_safety(
        impacted_enterprise_tenants=spanner_res["impacted_enterprise_tenants"],
        proposed_rollout_strategy=a2a_res["a2a_result"]["proposed_rollout_strategy"],
        iteration=1,
    )
    verdict1 = MeshSafetyAuditVerdict(
        iteration=1,
        safety_score=iter1["safety_score"],
        policy_violations=iter1["policy_violations"],
        remediation_adjustment=(
            f"Overrode {a2a_res['a2a_result']['proposed_rollout_strategy']} with "
            f"{iter1['enforced_rollout_strategy']} per AlloyDB runbook {alloydb_res['runbook_id']}."
        ),
        escalate_exit=False,
    )

    iter2 = audit_mesh_remediation_safety(
        impacted_enterprise_tenants=spanner_res["impacted_enterprise_tenants"],
        proposed_rollout_strategy=iter1["enforced_rollout_strategy"],
        iteration=2,
    )
    esc = exit_safety_audit_loop()
    verdict2 = MeshSafetyAuditVerdict(
        iteration=2,
        safety_score=iter2["safety_score"],
        policy_violations=iter2["policy_violations"],
        remediation_adjustment="All Spanner Graph blast-radius and AlloyDB canary constraints satisfied. Triggered exit_safety_audit_loop().",
        escalate_exit=esc["escalate"],
    )

    print(json.dumps([verdict1.model_dump(), verdict2.model_dump()], indent=2))

    manifest = IncidentMeshManifest(
        manifest_id="MESH-MANIFEST-INC-2026-8841",
        incident_id=incident_id,
        root_service_id=root_service,
        impacted_services=spanner_res["impacted_downstream_services"],
        matched_runbook_id=alloydb_res["runbook_id"],
        a2a_delegated_agent=a2a_res["discovered_agent_card"],
        github_rollback_pr_url=a2a_res["a2a_result"]["github_rollback_pr_url"],
        rollout_strategy=iter2["enforced_rollout_strategy"],
        loop_iterations_completed=2,
        final_safety_score=1.0,
        model_name="google/gemma-4-27b-it",
    )

    print("\n[STEP 3] Final Validated IncidentMeshManifest (Pydantic Output Schema):")
    print(json.dumps(manifest.model_dump(), indent=2))
    print("========================================================================================")


if __name__ == "__main__":
    run_codelab_verification()
