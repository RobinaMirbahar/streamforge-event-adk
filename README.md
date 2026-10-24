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

---

## 👩‍💻 About the Author

<div align="center">
  <img src="https://raw.githubusercontent.com/RobinaMirbahar/RobinaMirbahar/main/ProfileImages/Hi-Robina.gif" height="75" width="75" alt="Robina Mirbahar" />

  ### **Robina Mirbahar — Google Cloud & AI Architect**

  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=18&pause=1000&color=4285F4&center=true&vCenter=true&width=720&lines=Google+Cloud+%26+Agentic+AI+Solutions+Architect;Author+of+'AI+Engineering'+(2026);Pakistan+Lead+%40+IEEE+AI+Caravan+(94+Countries);Women+Techmakers+Ambassador+%26+Mentor+%40+Google+for+Startups" alt="Robina Mirbahar Dynamic Headline" />

  <p>
    AI Researcher, Cloud Solutions Architect, and Author of <b><i>"AI Engineering: From Classical ML to RAG &amp; Agentic AI Systems"</i> (2026)</b>.<br/>
    Bridging cutting-edge open-weights AI research (Gemma 4, Google ADK, Multi-LoRA, MCP &amp; A2A) with production-grade Cloud Run &amp; Vertex AI engineering.
  </p>

  [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/robinamirbahar)
  [![Amazon Book](https://img.shields.io/badge/Amazon-Book%20(2026)-FF9900?style=for-the-badge&logo=amazon&logoColor=white)](https://amazon.com/dp/B0GWCZWCF4)
  [![Google Developer](https://img.shields.io/badge/Google%20Developer-Profile-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://developers.google.com/profile/u/106918534005910641104)
  [![DEV Community](https://img.shields.io/badge/DEV-Articles-0A0A0A?style=for-the-badge&logo=devdotto&logoColor=white)](https://dev.to/robinamirbahar)
  [![Medium](https://img.shields.io/badge/Medium-Blog-12100E?style=for-the-badge&logo=medium&logoColor=white)](https://medium.com/@robinamirbahar)
  [![YouTube](https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@robinacodesai)
  [![Twitter/X](https://img.shields.io/badge/X-000000?style=for-the-badge&logo=x&logoColor=white)](https://twitter.com/robinamirbahar)
  [![Stack Overflow](https://img.shields.io/badge/Stack%20Overflow-F58025?style=for-the-badge&logo=stackoverflow&logoColor=white)](https://stackoverflow.com/users/21196122/robina-mirbahar)
  [![Credly](https://img.shields.io/badge/Credly-FF6B35?style=for-the-badge&logo=credly&logoColor=white)](https://www.credly.com/users/robinamirbahar)

</div>

### 🚀 Featured Google Cloud & Agentic AI Repositories by Robina Mirbahar

| Repository | Architecture Focus | Live Repo & Dynamic Status |
| :--- | :--- | :--- |
| **[gemma4-multilora-adk-eval](https://github.com/RobinaMirbahar/gemma4-multilora-adk-eval)** | Dynamic Multi-LoRA Hot-Swapping & CI/CD Agent Evaluation (`adk eval`) on Cloud Run GPUs with Gemma 4 & vLLM | ![Stars](https://img.shields.io/github/stars/RobinaMirbahar/gemma4-multilora-adk-eval?style=flat-square&color=4285F4) ![Last Commit](https://img.shields.io/github/last-commit/RobinaMirbahar/gemma4-multilora-adk-eval?style=flat-square) |
| **[slothsre-napops](https://github.com/RobinaMirbahar/slothsre-napops)** | SlothSRE ("NapOps") — Overnight Gemma 4 & Google ADK Incident Digest Agent with OpenTelemetry & Sentry AI Monitoring | ![Stars](https://img.shields.io/github/stars/RobinaMirbahar/slothsre-napops?style=flat-square&color=34A853) ![Last Commit](https://img.shields.io/github/last-commit/RobinaMirbahar/slothsre-napops?style=flat-square) |
| **[streamforge-event-adk](https://github.com/RobinaMirbahar/streamforge-event-adk)** | Real-Time Event-Driven Multi-Agent Pipelines on Google Cloud with ADK (`ParallelAgent` & `LoopAgent`), Eventarc & Pub/Sub | ![Stars](https://img.shields.io/github/stars/RobinaMirbahar/streamforge-event-adk?style=flat-square&color=FBBC04) ![Last Commit](https://img.shields.io/github/last-commit/RobinaMirbahar/streamforge-event-adk?style=flat-square) |
| **[a2a-mcp-mesh-cloudrun](https://github.com/RobinaMirbahar/a2a-mcp-mesh-cloudrun)** | Agent-to-Agent (A2A) & Multi-MCP Mesh on Cloud Run with Gemma 4, Google ADK, Spanner Graph & AlloyDB | ![Stars](https://img.shields.io/github/stars/RobinaMirbahar/a2a-mcp-mesh-cloudrun?style=flat-square&color=EA4335) ![Last Commit](https://img.shields.io/github/last-commit/RobinaMirbahar/a2a-mcp-mesh-cloudrun?style=flat-square) |
| **[cloudguard-gemma-agent](https://github.com/RobinaMirbahar/cloudguard-gemma-agent)** | 6-Part Production Gemma Enterprise Agent Series (ADK, Cloud Run L4 GPU, Firestore, Model Armor, Vertex AI QLoRA) | ![Stars](https://img.shields.io/github/stars/RobinaMirbahar/cloudguard-gemma-agent?style=flat-square&color=4285F4) ![Last Commit](https://img.shields.io/github/last-commit/RobinaMirbahar/cloudguard-gemma-agent?style=flat-square) |
| **[cozy-ai-agent-cafe-game](https://github.com/RobinaMirbahar/cozy-ai-agent-cafe-game)** | Prompt Paws: 60 FPS Cozy AI Agent Bakery Simulation Game teaching RAG, Guardrails, Context Caching & Multi-Agent Loops | ![Stars](https://img.shields.io/github/stars/RobinaMirbahar/cozy-ai-agent-cafe-game?style=flat-square&color=7928CA) ![Last Commit](https://img.shields.io/github/last-commit/RobinaMirbahar/cozy-ai-agent-cafe-game?style=flat-square) |

<div align="center">
  <img src="https://raw.githubusercontent.com/RobinaMirbahar/RobinaMirbahar/main/ProfileImages/GithubBanner.svg" alt="Robina Mirbahar Banner" width="100%" />
</div>

---

## Star, Fork & Sponsor This Project

[![Star on GitHub](https://img.shields.io/github/stars/RobinaMirbahar/streamforge-event-adk?style=for-the-badge&logo=github&label=Star)](https://github.com/RobinaMirbahar/streamforge-event-adk)
[![Fork on GitHub](https://img.shields.io/github/forks/RobinaMirbahar/streamforge-event-adk?style=for-the-badge&logo=github&label=Fork)](https://github.com/RobinaMirbahar/streamforge-event-adk/fork)
[![Sponsor RobinaMirbahar](https://img.shields.io/badge/Sponsor-%40RobinaMirbahar-ea4aaa?style=for-the-badge&logo=githubsponsors)](https://github.com/sponsors/RobinaMirbahar)

If this project is helpful to your work:
* **Star this Repository:** [**Star `RobinaMirbahar/streamforge-event-adk` on GitHub**](https://github.com/RobinaMirbahar/streamforge-event-adk) to bookmark it and help others discover it.
* **Fork & Customize:** [**Fork `RobinaMirbahar/streamforge-event-adk`**](https://github.com/RobinaMirbahar/streamforge-event-adk/fork) to build and experiment with your own workflows.
* **Sponsor on GitHub:** [**Sponsor `@RobinaMirbahar` on GitHub Sponsors (`github.com/sponsors/RobinaMirbahar`)**](https://github.com/sponsors/RobinaMirbahar) to support open-source AI, Google Cloud, and Gemini engineering projects!

