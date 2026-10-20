---
title: "SlothSRE (NapOps): An Overnight Gemma 4 & ADK Agent That Compresses 418 Lines of 3 AM Alerts into a 2-Line Morning Digest"
published: false
description: "How I built a local-first open-weights Gemma 4, Google ADK, and Sentry Agent Tracing pipeline that deduplicates overnight stack traces, verifies git patches in a local pytest sandbox, and lets on-call engineers sleep until 8 AM."
tags: devchallenge, hf26challenge, gemma, opensource
cover_image: https://raw.githubusercontent.com/RobinaMirbahar/streamforge-event-adk/main/articles/slothsre-napops/cover.1eb32148.jpg
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)*

## What I Built

On-call software engineers lose sleep to noisy alert floods that repeat the same failure dozens of times before sunrise. When a Redis connection pool saturates during a batch job or an upstream webhook adds a new status string, alerting pipelines emit hundreds of lines of redundant stack traces across logs, CI runs, and chat channels. **SlothSRE (NapOps)** is an open-source, local-first overnight triage agent built with open-weights **Gemma 4**, **Google Agent Development Kit (ADK)**, and **Sentry Agent Tracing** so engineers can sleep through 3 AM alert storms and wake up to a two-line summary with a sandbox-tested git patch ready for one-click approval.

Instead of paging a human for every retry loop, SlothSRE buffers non-critical overnight errors and runs a three-stage `SequentialAgent` pipeline locally on `google/gemma-4-27b-it` via Ollama or vLLM. In our benchmark run across 96 raw overnight alerts totaling 418 lines of stack traces and chat logs, SlothSRE collapsed the entire flood into 2 unique incident clusters (4 total summary lines), achieving a 99.04% reduction in morning reading volume and saving 42 minutes of manual log digging.

![SlothSRE NapOps Architecture with Open-Weights Gemma 4, Google ADK, and Sentry Agent Tracing](https://raw.githubusercontent.com/RobinaMirbahar/streamforge-event-adk/main/articles/slothsre-napops/slothsre_napops_arch.jpg)

| Overnight Metric | Manual 3 AM Triage | SlothSRE (NapOps) with Gemma 4 |
| :--- | :--- | :--- |
| Raw Overnight Events Ingested | 96 separate alerts | 2 deduplicated root-cause clusters |
| Log & Stack-Trace Lines to Read | 418 raw lines | 4 summary lines (2 lines per cluster) |
| Log Noise Reduction | 0% | 99.04% |
| Patch Verification Before 8 AM | None (manual reproduction) | Automated local `pytest` sandbox (312.4 ms & 184.6 ms) |
| Morning Triage Effort | 42 minutes of log correlation | 1-click patch apply & PR creation |

## Demo

You can run the complete SlothSRE benchmark and launch the interactive FastAPI Morning Dashboard in one command from the repository:

```bash
python scripts/run_slothsre_demo.py
```

Running the demo executes the three-stage Gemma 4 + ADK overnight pipeline, records `gen_ai.agent` and `gen_ai.tool` spans via Sentry Agent Tracing, and verifies the live FastAPI dashboard endpoints (`GET /` and `POST /api/approve/CLUSTER-01-REDIS-POOL`):

```text
========================================================================================
🦥 SLOTHSRE (NAPOPS) — OVERNIGHT GEMMA 4 + ADK + SENTRY TRACING REPORT
========================================================================================
  Model                  : google/gemma-4-27b-it (local Ollama / vLLM)
  Raw 3 AM Events        : 96 alerts (418 raw log lines)
  Deduplicated Clusters  : 2 clusters (4 total summary lines)
  Log Noise Reduction    : 99.04%
  Morning Time Saved     : 42 minutes
  Sentry Root Trace ID   : 0772dffd4fbfd83d5e340590efbf735e
----------------------------------------------------------------------------------------
  [1] CLUSTER-01-REDIS-POOL (billing-worker) — Collapsed 62 alerts (310 lines)
      Line 1 (What Broke)  : At 03:10 UTC, billing-worker exhausted its 10-connection Redis pool during the nightly invoice batch, triggering 62 duplicate retry alerts.
      Line 2 (Verified Fix): Gemma 4 raised max_connections to 64 with 30s health checks in redis_client.py and passed all 18 local pytest assertions in 312.4 ms.
      1-Click Command      : git apply .slothsre/patches/CLUSTER-01-REDIS-POOL.patch && gh pr create --fill
  [2] CLUSTER-02-PYDANTIC-V2-ENUM (webhook-ingest) — Collapsed 34 alerts (108 lines)
      Line 1 (What Broke)  : At 04:15 UTC, upstream payment webhooks began sending status='refund_queued', causing 34 Pydantic Literal validation rejections in webhook-ingest.
      Line 2 (Verified Fix): Gemma 4 added 'refund_queued' to WebhookEvent.status in models.py and verified schema round-trip compatibility in 184.6 ms.
      1-Click Command      : git apply .slothsre/patches/CLUSTER-02-PYDANTIC-V2-ENUM.patch && gh pr create --fill
----------------------------------------------------------------------------------------
  [FastAPI UI Verified] GET / HTTP 200 (7491 bytes)
  [1-Click Approve API] POST /api/approve/CLUSTER-01-REDIS-POOL -> {'status': 'APPROVED_AND_APPLIED', 'cluster_id': 'CLUSTER-01-REDIS-POOL', 'service_name': 'billing-worker', 'executed_command': 'git apply .slothsre/patches/CLUSTER-01-REDIS-POOL.patch && gh pr create --fill'}
```

To open the interactive browser dashboard on port 8095 and click the approval buttons directly:

```bash
uvicorn slothsre_napops.app:app --host 127.0.0.1 --port 8095
```

## Code

The full open-source implementation is available on GitHub in the `slothsre_napops/` package of [RobinaMirbahar/streamforge-event-adk](https://github.com/RobinaMirbahar/streamforge-event-adk):

- `slothsre_napops/schemas.py`: Strict Pydantic v2 contracts (`RawOvernightEvent`, `VerifiedPatchArtifact`, `TwoLineIncidentDigest`, `SentryAgentSpanRecord`, and `SlothMorningReport`).
- `slothsre_napops/agent.py`: Three-stage Google ADK `SequentialAgent` (`SlothSreOvernightPipeline`) wired to local open-weights Gemma 4 via `LiteLlm`.
- `slothsre_napops/sentry_tracing.py`: Sentry Agent Tracing instrumentation recording `gen_ai.agent` and `gen_ai.tool` spans with input/output token counts and step durations.
- `slothsre_napops/app.py`: FastAPI backend and Morning Coffee Digest web dashboard.
- `scripts/run_slothsre_demo.py`: Reproducible benchmark script that generates `articles/slothsre-napops/evidence/slothsre_benchmark.json`.

## How I Built It

SlothSRE is structured around three open-source pillars: **open-weights Gemma 4** for local reasoning, **Google Agent Development Kit (ADK)** for deterministic multi-agent orchestration, and **Sentry Agent Tracing (`sentry-sdk`)** for observability across autonomous background steps.

### 1. Enforcing the Two-Line Morning Contract with Pydantic v2

To make sure the agent never replaces a 418-line log flood with a 400-word essay, `slothsre_napops/schemas.py` enforces a strict schema where each incident cluster must resolve to `line_1_what_broke`, `line_2_verified_fix`, a `one_click_command`, and a `VerifiedPatchArtifact`:

```python
class TwoLineIncidentDigest(BaseModel):
    """Strict 2-line morning summary enforcing the 'Slow and Steady' anti-burnout contract."""

    cluster_id: str = Field(..., description="Deduplicated incident cluster ID.")
    service_name: str = Field(..., description="Impacted microservice.")
    raw_events_collapsed: int = Field(
        ..., description="Number of duplicate raw overnight alerts merged into this digest."
    )
    raw_lines_collapsed: int = Field(
        ..., description="Number of raw stack-trace lines compressed into 2 lines."
    )
    line_1_what_broke: str = Field(
        ..., description="Line 1: Plain-English root cause in a single sentence."
    )
    line_2_verified_fix: str = Field(
        ..., description="Line 2: Exact verified fix and test result in a single sentence."
    )
    one_click_command: str = Field(
        ..., description="Single CLI or git command to apply/merge the verified fix."
    )
    patch: VerifiedPatchArtifact = Field(..., description="Attached sandbox-verified patch.")
```

### 2. Orchestrating Gemma 4 Locally with Google ADK SequentialAgent

In `slothsre_napops/agent.py`, three specialized `LlmAgent` stages share a local `ollama/gemma4:27b` endpoint through `LiteLlm`:

1. **`NoiseFilterAgent`**: Ingests raw overnight events (62 Redis pool exhaustion errors totaling 310 lines and 34 Pydantic webhook errors totaling 108 lines) and groups them into 2 unique root-cause clusters.
2. **`SandboxPatchAgent`**: Generates a unified git diff for `services/billing_worker/redis_client.py` and `services/webhook_ingest/models.py`, then executes `pytest` in a local sandbox (`312.4 ms` and `184.6 ms`) before marking the fix ready.
3. **`TwoLineBriefAgent`**: Formats the verified patches into the `SlothMorningReport` output schema.

```python
def build_slothsre_adk_pipeline(model_name: Optional[str] = None) -> SequentialAgent:
    """Builds the 3-stage Google ADK SequentialAgent powered by open-weights Gemma 4."""
    gemma_model = _build_local_gemma4_model(model_name)

    noise_filter_agent = LlmAgent(
        name="NoiseFilterAgent",
        model=gemma_model,
        description="Deduplicates hundreds of 3 AM stack traces, CI failures, and chat messages into unique root causes.",
        instruction=(
            "You are the SlothSRE NoiseFilterAgent running open-weights Gemma 4 locally while the human sleeps. "
            "Group duplicate stack traces and flaky retries using `deduplicate_overnight_alerts`."
        ),
        tools=[deduplicate_overnight_alerts],
        output_key="deduplicated_clusters",
    )

    sandbox_patch_agent = LlmAgent(
        name="SandboxPatchAgent",
        model=gemma_model,
        description="Drafts minimal git diffs for each overnight cluster and runs local pytest verification.",
        instruction=(
            "For each unique incident cluster in {deduplicated_clusters}, generate a minimal patch "
            "and verify it with `verify_patch_in_local_sandbox`."
        ),
        tools=[verify_patch_in_local_sandbox],
        output_key="verified_patches",
    )

    two_line_brief_agent = LlmAgent(
        name="TwoLineBriefAgent",
        model=gemma_model,
        description="Distills verified overnight patches into a strict 2-line Morning Coffee Digest.",
        instruction=(
            "Compress {verified_patches} into a SlothMorningReport where every incident has "
            "exactly 2 sentences (Line 1: What broke; Line 2: Verified fix) plus a 1-click command."
        ),
        output_schema=SlothMorningReport,
        output_key="morning_report",
    )

    return SequentialAgent(
        name="SlothSreOvernightPipeline",
        description="Sequential ADK pipeline that triages overnight alerts locally with Gemma 4.",
        sub_agents=[noise_filter_agent, sandbox_patch_agent, two_line_brief_agent],
    )
```

### 3. Instrumenting Overnight Agent Runs with Sentry Agent Tracing

When an autonomous agent runs while you are asleep, you need verifiable proof of which tools it called, how many tokens it consumed, and how long each step took. In `slothsre_napops/sentry_tracing.py`, `SlothSentryTracer` wraps each ADK agent and tool invocation in a Sentry span with `gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`, and `gen_ai.usage.output_tokens`:

| Span ID | Sentry Op | Agent / Tool Step | Input / Output Tokens | Duration (ms) |
| :--- | :--- | :--- | :--- | :--- |
| `de8105cb2e489d3e` | `gen_ai.agent` | `NoiseFilterAgent.deduplicate_overnight_alerts` | 3840 / 192 | 412.6 ms |
| `482510772a320ab9` | `gen_ai.tool` | `SandboxPatchAgent.verify_patch_in_local_sandbox[CLUSTER-01-REDIS-POOL]` | 620 / 148 | 312.4 ms |
| `ca536bd9739c2577` | `gen_ai.tool` | `SandboxPatchAgent.verify_patch_in_local_sandbox[CLUSTER-02-PYDANTIC-V2-ENUM]` | 540 / 116 | 184.6 ms |
| `a2b713fa35fa6773` | `gen_ai.agent` | `TwoLineBriefAgent.synthesize_morning_report` | 890 / 210 | 268.4 ms |

## Why Does Open Innovation Matter?

Production stack traces, internal repository paths, database connection strings, and on-call chat transcripts contain sensitive infrastructure metadata that many teams cannot upload to third-party proprietary LLM endpoints. Building SlothSRE on **open-weights Gemma 4** and the open-source **Google Agent Development Kit (ADK)** unlocks three critical advantages that closed APIs cannot match:

1. **Zero Data Exfiltration for Raw Logs and Code:** Running `google/gemma-4-27b-it` locally via Ollama or on a private VPC-isolated Cloud Run GPU keeps every stack trace, environment variable name, and git diff inside your own machine or private network perimeter.
2. **Zero Per-Token Anxiety During Alert Storms:** A runaway retry loop at 3 AM can generate thousands of log lines in minutes. Piping an unbounded log storm into a metered commercial API risks a surprise bill before breakfast; running open-weights Gemma 4 locally incurs zero per-token API fees no matter how noisy the alert storm gets.
3. **Offline & Local-Sandbox Determinism:** Because both the model weights and the ADK `SequentialAgent` pipeline run locally alongside `pytest`, SlothSRE can test candidate patches against the local codebase without requiring external network access.

## The Lazy Payoff

Before SlothSRE, reviewing an overnight batch failure meant opening four browser tabs (Cloud Run logs, GitHub Actions, Slack `#oncall-sre`, and local IDE search), scrolling through 418 lines of repeated tracebacks across 96 alerts, reproducing the failure locally, and writing a PR description from scratch.

With SlothSRE running on open-weights Gemma 4, those 96 noisy alerts are already collapsed into 2 two-line cards with passing `pytest` checks (`312.4 ms` and `184.6 ms`) before 8:00 AM. That saves 42 minutes of manual morning triage per incident storm and lets the on-call engineer review, approve, and open both pull requests in under 30 seconds.

## Prize Categories

- **Best Use of Gemma**: Uses open-weights **Gemma 4 (`google/gemma-4-27b-it`)** via local Ollama / vLLM as the reasoning engine across all three Google ADK sub-agents (`NoiseFilterAgent`, `SandboxPatchAgent`, and `TwoLineBriefAgent`).
- **Best Use of Sentry Agent Tracing**: Instruments every overnight agent step and sandbox tool call with `sentry-sdk` `gen_ai.agent` and `gen_ai.tool` spans (`gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`) and surfaces the trace table directly in the morning dashboard.
