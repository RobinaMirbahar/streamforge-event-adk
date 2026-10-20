# StreamForge: Real-Time Event-Driven Multi-Agent Pipeline (`Google ADK ParallelAgent & LoopAgent` + `Gemma 3` + `Eventarc` + `Pub/Sub` + `Cloud Run`)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Google ADK](https://img.shields.io/badge/Google-Agent%20Development%20Kit-4285F4?logo=googlecloud&logoColor=white)](https://google.github.io/adk-docs/)
[![Model: Gemma 3](https://img.shields.io/badge/Open%20Weights-Gemma%203-34A853?logo=google&logoColor=white)](https://ai.google.dev/gemma)
[![Trigger: Eventarc CloudEvents](https://img.shields.io/badge/Eventarc-CloudEvents%20%2B%20Pub%2FSub-FBBC04?logo=googlecloud&logoColor=black)](https://cloud.google.com/eventarc/docs)

![Cover Banner: Beyond Chatbots & Cron — Event-Driven ADK Agents on Google Cloud](./assets/eventdriven_adk_cover_banner.jpg)

**StreamForge** is an end-to-end reference architecture for building **real-time, event-driven multi-agent pipelines** on **Google Cloud**—replacing both manual chat prompts and polling cron jobs with **Google Cloud Eventarc**, **Cloud Pub/Sub**, **Google Agent Development Kit (`ParallelAgent` + `LoopAgent` + `SequentialAgent`)**, and **open-weights Gemma 3 (`gemma3:12b`)** on **Cloud Run**.

Whenever a product engineering or catalog release file lands in **Google Cloud Storage** (`google.cloud.storage.object.v1.finalized`), **Eventarc** pushes a CNCF **CloudEvent** to a private **Cloud Run** service that orchestrates:

1. **Stage 1 — Concurrent Fan-Out (`ParallelAgent: ConcurrentEnrichmentFanOut`):** Runs three specialist `LlmAgent` workers simultaneously (`TechnicalSpecExtractorAgent`, `GlobalLocalizationAgent`, `RevenuePricingSimulatorAgent`), writing their outputs concurrently to `session.state`.
2. **Stage 2 — Self-Correcting Quality Loop (`LoopAgent: QualityCritiqueRefinementLoop`):** `LaunchReadinessCriticAgent` audits cross-agent consistency (such as regional EUR/JPY B2B pricing rounding rules), automatically repairing discrepancies across loop iterations and calling `exit_quality_loop()` (`tool_context.actions.escalate = True`) once `quality_score == 1.0`.
3. **Stage 3 — Validated Sink & CloudEvent Deduplication (`ReleasePublisherAgent`):** Enforces a strict Pydantic `EventDrivenLaunchManifest` schema and records the `ce-id` in Cloud Firestore (`cloudevent_dedup_ledger`) so Pub/Sub at-least-once redeliveries never trigger duplicate GPU inference.

![Figure 1: Real-Time Event-Driven Agent Architecture on Google Cloud](./assets/eventdriven_adk_end_to_end_arch.jpg)

---

## Hybrid ADK Topology (`ParallelAgent` Fan-Out + `LoopAgent` Self-Correction)

![Figure 2: Orchestrating ADK ParallelAgent Fan-Out and LoopAgent Self-Correction](./assets/eventdriven_adk_parallel_loop_topology.jpg)

---

## Quickstart & Local Verification

```bash
python scripts/simulate_cloudevent_pipeline.py
```

## Deploying to Google Cloud (Eventarc + Pub/Sub + Cloud Run)

```bash
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"

bash deploy/deploy_eventarc_adk.sh
```
