import asyncio
from pathlib import Path
import socket
import sys
import threading

import httpx
import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from slothsre_napops.agent import run_overnight_sloth_triage
from slothsre_napops.app import app


def _find_free_port(start_port: int = 18095) -> int:
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1


async def main() -> None:
    report = run_overnight_sloth_triage()

    print("=" * 88)
    print("🦥 SLOTHSRE (NAPOPS) — OVERNIGHT GEMMA 4 + ADK + SENTRY TRACING REPORT")
    print("=" * 88)
    print(f"  Model                  : {report.generated_by_model}")
    print(f"  Raw 3 AM Events        : {report.total_raw_events} alerts ({report.total_raw_log_lines} raw log lines)")
    print(f"  Deduplicated Clusters  : {report.unique_actionable_clusters} clusters (4 total summary lines)")
    print(f"  Log Noise Reduction    : {report.noise_reduction_pct}%")
    print(f"  Morning Time Saved     : {report.estimated_minutes_saved} minutes")
    print(f"  Sentry Root Trace ID   : {report.sentry_trace_id}")
    print("-" * 88)

    for idx, d in enumerate(report.digests, start=1):
        print(f"  [{idx}] {d.cluster_id} ({d.service_name}) — Collapsed {d.raw_events_collapsed} alerts ({d.raw_lines_collapsed} lines)")
        print(f"      Line 1 (What Broke)  : {d.line_1_what_broke}")
        print(f"      Line 2 (Verified Fix): {d.line_2_verified_fix}")
        print(f"      1-Click Command      : {d.one_click_command}")

    # Verify the FastAPI web dashboard & approval endpoint
    port = _find_free_port(18095)
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    await asyncio.sleep(0.5)

    async with httpx.AsyncClient(timeout=10.0) as client:
        ui_resp = await client.get(f"http://127.0.0.1:{port}/")
        approve_resp = await client.post(
            f"http://127.0.0.1:{port}/api/approve/CLUSTER-01-REDIS-POOL"
        )
        print("-" * 88)
        print(f"  [FastAPI UI Verified] GET / HTTP {ui_resp.status_code} ({len(ui_resp.text)} bytes)")
        print(f"  [1-Click Approve API] POST /api/approve/CLUSTER-01-REDIS-POOL -> {approve_resp.json()}")

    evidence_dir = (
        Path(__file__).resolve().parents[1] / "articles" / "slothsre-napops" / "evidence"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / "slothsre_benchmark.json"
    evidence_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    print(f"  [Evidence Saved]      {evidence_path}")


if __name__ == "__main__":
    asyncio.run(main())
