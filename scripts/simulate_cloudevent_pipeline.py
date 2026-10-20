"""End-to-end verification script simulating Eventarc CloudEvent delivery to StreamForge ADK."""

from __future__ import annotations

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from streamforge_agent.agent import (
    build_streamforge_event_pipeline,
    process_incoming_cloudevent,
)
from streamforge_agent.schemas import CloudEventEnvelope
from streamforge_agent.tools import reset_local_store


def main() -> None:
    print("=" * 88)
    print("STREAMFORGE: EVENT-DRIVEN ADK (PARALLELAGENT + LOOPAGENT) PIPELINE VERIFICATION")
    print("Trigger: Eventarc CloudEvent (google.cloud.storage.object.v1.finalized) | Gemma 3 12B")
    print("=" * 88)

    reset_local_store()
    topology = build_streamforge_event_pipeline()
    print("\n[STEP 1] Initialized Google ADK Hybrid Agent Graph:")
    if isinstance(topology, dict):
        for stage in topology["stages"]:
            print(f"  * {stage['stage']}: {stage['type']} ({stage['name']})")
    else:
        for sub in topology.sub_agents:
            print(f"  * {sub.__class__.__name__} ({sub.name})")

    envelope = CloudEventEnvelope(
        ce_id="ce-98104271-gcs-finalized",
        ce_type="google.cloud.storage.object.v1.finalized",
        ce_source="//storage.googleapis.com/projects/_/buckets/streamforge-launch-inbox",
        ce_time="2026-10-20T08:14:02Z",
        bucket="streamforge-launch-inbox",
        object_name="releases/2026-10/vertex-vector-sync-v4.2.json",
        generation="1729412042881001",
    )

    print("\n" + "-" * 88)
    print("[STEP 2] Delivering Eventarc CloudEvent #1 (POST /api/v1/cloudevent)")
    print(f"ce-id: {envelope.ce_id} | object: gs://{envelope.bucket}/{envelope.object_name}")
    print("-" * 88)

    receipt_1, session_state = process_incoming_cloudevent(envelope=envelope)

    print(f"Ack Status                 : {receipt_1.ack_status}")
    print(f"Parallel Branches Executed : {receipt_1.parallel_branches_executed} (SpecExtractor || Localization || PricingSim)")
    print(f"LoopAgent Critique Passes  : {receipt_1.loop_iterations_executed}")
    print(f"Firestore Manifest ID      : {receipt_1.manifest.manifest_id}")

    print("\n--- Stage 2 LoopAgent Self-Correction Trace (`session.state['loop_critique_trace']`) ---")
    print(json.dumps(session_state["loop_critique_trace"], indent=2, ensure_ascii=False))

    print("\n--- Stage 3 Validated Launch Manifest (`session.state['published_manifest']`) ---")
    print(json.dumps(receipt_1.manifest.to_dict(), indent=2, ensure_ascii=False))

    print("\n" + "-" * 88)
    print("[STEP 3] Simulating Pub/Sub At-Least-Once Duplicate Delivery (Same `ce-id`)")
    print("Verifying CloudEvent Deduplication Ledger (`cloudevent_dedup_ledger`)")
    print("-" * 88)

    receipt_2, dedup_meta = process_incoming_cloudevent(envelope=envelope)
    print(f"Ack Status                 : {receipt_2.ack_status}")
    print(f"Idempotent Replay          : {receipt_2.idempotent_replay}")
    print(f"Parallel Branches Executed : {receipt_2.parallel_branches_executed} (Zero redundant GPU inference)")
    print(f"Deduplication Metadata     : {json.dumps(dedup_meta)}")
    print("=" * 88)


if __name__ == "__main__":
    main()
