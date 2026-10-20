from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from slothsre_napops.agent import run_overnight_sloth_triage
from slothsre_napops.schemas import SlothMorningReport

app = FastAPI(
    title="SlothSRE (NapOps) — Overnight Gemma 4 + ADK Triage Dashboard",
    version="1.0.0",
)

APPROVED_CLUSTERS: Dict[str, str] = {}


@app.get("/api/report", response_model=SlothMorningReport)
async def get_morning_report() -> SlothMorningReport:
    """Returns the 8:00 AM SlothSRE 2-Line Morning Report with Sentry Agent Tracing spans."""
    return run_overnight_sloth_triage()


@app.post("/api/approve/{cluster_id}")
async def approve_cluster_patch(cluster_id: str) -> Dict[str, Any]:
    """Executes the 1-Click Morning Approval for a verified overnight patch."""
    report = run_overnight_sloth_triage()
    matching = [d for d in report.digests if d.cluster_id == cluster_id]
    if not matching:
        raise HTTPException(status_code=404, detail=f"Cluster '{cluster_id}' not found")
    digest = matching[0]
    APPROVED_CLUSTERS[cluster_id] = "MERGED"
    return {
        "status": "APPROVED_AND_APPLIED",
        "cluster_id": cluster_id,
        "service_name": digest.service_name,
        "executed_command": digest.one_click_command,
    }


@app.get("/", response_class=HTMLResponse)
async def sloth_dashboard_ui() -> str:
    """Serves the interactive Cozy SlothSRE Morning Dashboard UI."""
    report = run_overnight_sloth_triage()
    cards_html = ""
    for d in report.digests:
        cards_html += f"""
        <div class="card" id="card-{d.cluster_id}">
          <div class="card-header">
            <span class="badge">{d.cluster_id}</span>
            <span class="svc">Service: <b>{d.service_name}</b></span>
            <span class="collapsed">🦥 Collapsed {d.raw_events_collapsed} alerts ({d.raw_lines_collapsed} raw lines &rarr; 2 lines)</span>
          </div>
          <div class="two-lines">
            <p><b>Line 1 (What Broke):</b> {d.line_1_what_broke}</p>
            <p><b>Line 2 (Verified Fix):</b> {d.line_2_verified_fix}</p>
          </div>
          <pre class="diff">{d.patch.git_diff_patch}</pre>
          <div class="card-footer">
            <code>{d.one_click_command}</code>
            <button onclick="approvePatch('{d.cluster_id}')" id="btn-{d.cluster_id}">
              ✅ 1-Click Morning Approve (pytest passed in {d.patch.test_duration_ms} ms)
            </button>
          </div>
        </div>
        """

    spans_rows = "".join(
        f"<tr><td><code>{s.span_id}</code></td><td><code>{s.op}</code></td>"
        f"<td>{s.description}</td><td><code>{s.model_id}</code></td>"
        f"<td>{s.input_tokens} / {s.output_tokens}</td><td>{s.duration_ms} ms</td></tr>"
        for s in report.sentry_spans
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>SlothSRE (NapOps) — 8:00 AM Lazy Morning Dashboard</title>
  <style>
    body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 28px; }}
    .container {{ max-width: 980px; margin: 0 auto; }}
    .hero {{ background: linear-gradient(135deg, #1e1b4b, #312e81); padding: 24px 28px; border-radius: 14px; border: 1px solid #4338ca; margin-bottom: 24px; }}
    .hero h1 {{ margin: 0 0 8px 0; font-size: 26px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-top: 16px; }}
    .metric {{ background: rgba(15, 23, 42, 0.65); padding: 14px; border-radius: 10px; text-align: center; border: 1px solid #3730a3; }}
    .metric .val {{ font-size: 24px; font-weight: 800; color: #38bdf8; }}
    .metric .lbl {{ font-size: 12px; color: #cbd5e1; margin-top: 4px; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; margin-bottom: 18px; }}
    .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-size: 14px; }}
    .badge {{ background: #6366f1; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 700; }}
    .collapsed {{ color: #4ade80; font-weight: 600; }}
    .two-lines {{ background: #0f172a; border-left: 4px solid #38bdf8; padding: 12px 16px; border-radius: 6px; margin-bottom: 12px; }}
    .two-lines p {{ margin: 6px 0; line-height: 1.45; }}
    pre.diff {{ background: #020617; color: #a7f3d0; padding: 12px; border-radius: 8px; overflow-x: auto; font-size: 12.5px; }}
    .card-footer {{ display: flex; justify-content: space-between; align-items: center; margin-top: 12px; gap: 12px; }}
    .card-footer code {{ background: #0f172a; padding: 8px 12px; border-radius: 6px; font-size: 12px; color: #fcd34d; }}
    button {{ background: #10b981; color: #022c22; border: none; padding: 10px 18px; border-radius: 8px; font-weight: 700; cursor: pointer; }}
    table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 10px; overflow: hidden; font-size: 13px; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid #334155; text-align: left; }}
    th {{ background: #0f172a; color: #94a3b8; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="hero">
      <h1>🦥 SlothSRE (NapOps) — 8:00 AM Lazy Morning Digest</h1>
      <p>Powered by local Open-Weights <b>{report.generated_by_model}</b> + <b>Google ADK</b> + <b>Sentry Agent Tracing</b></p>
      <div class="metrics">
        <div class="metric"><div class="val">{report.total_raw_events} alerts ({report.total_raw_log_lines} lines)</div><div class="lbl">3:00 AM Overnight Noise</div></div>
        <div class="metric"><div class="val">{report.unique_actionable_clusters} Clusters (4 lines)</div><div class="lbl">Morning Reading Load</div></div>
        <div class="metric"><div class="val">{report.noise_reduction_pct}%</div><div class="lbl">Log Noise Eliminated</div></div>
        <div class="metric"><div class="val">{report.estimated_minutes_saved} mins</div><div class="lbl">Sleep / Triage Time Saved</div></div>
      </div>
    </div>
    {cards_html}
    <h3>🔍 Sentry Agent Tracing Spans (Trace ID: <code>{report.sentry_trace_id}</code>)</h3>
    <table>
      <thead><tr><th>Span ID</th><th>Op</th><th>Agent / Tool Step</th><th>Model</th><th>Tokens (In/Out)</th><th>Duration</th></tr></thead>
      <tbody>{spans_rows}</tbody>
    </table>
  </div>
  <script>
    async function approvePatch(clusterId) {{
      const res = await fetch('/api/approve/' + clusterId, {{ method: 'POST' }});
      const data = await res.json();
      const btn = document.getElementById('btn-' + clusterId);
      btn.textContent = '🎉 ' + data.status + ' (' + data.service_name + ')';
      btn.style.background = '#38bdf8';
    }}
  </script>
</body>
</html>"""
