from contextlib import contextmanager
import hashlib
import os
import time
from typing import Dict, Generator, List, Optional

from slothsre_napops.schemas import SentryAgentSpanRecord

try:
    import sentry_sdk  # type: ignore
except ImportError:
    sentry_sdk = None


class SlothSentryTracer:
    """Instruments Gemma 4 + ADK agent runs with Sentry Agent Tracing (gen_ai.* spans)."""

    def __init__(self, dsn: Optional[str] = None) -> None:
        self.dsn = dsn or os.environ.get("SENTRY_DSN", "")
        self.trace_id = hashlib.sha256(b"slothsre-napops-2026-10-20").hexdigest()[:32]
        self.spans: List[SentryAgentSpanRecord] = []

        if sentry_sdk is not None and self.dsn:
            sentry_sdk.init(
                dsn=self.dsn,
                traces_sample_rate=1.0,
                environment="napops-local-gemma4",
            )

    @contextmanager
    def trace_agent_step(
        self,
        op: str,
        description: str,
        model_id: str = "ollama/gemma4:27b",
        input_tokens: int = 0,
        output_tokens: int = 0,
        simulated_ms: Optional[float] = None,
    ) -> Generator[Dict[str, object], None, None]:
        """Records a Sentry gen_ai.* span with token usage and model metadata."""
        t0 = time.perf_counter()
        span_hash = hashlib.sha1(f"{op}:{description}:{len(self.spans)}".encode("utf-8")).hexdigest()[:16]
        ctx: Dict[str, object] = {"span_id": span_hash, "op": op, "description": description}

        if sentry_sdk is not None and self.dsn:
            with sentry_sdk.start_span(op=op, name=description) as sentry_span:
                sentry_span.set_data("gen_ai.system", "gemma4-local")
                sentry_span.set_data("gen_ai.request.model", model_id)
                sentry_span.set_data("gen_ai.usage.input_tokens", input_tokens)
                sentry_span.set_data("gen_ai.usage.output_tokens", output_tokens)
                yield ctx
        else:
            yield ctx

        elapsed_ms = simulated_ms if simulated_ms is not None else round((time.perf_counter() - t0) * 1000.0, 2)
        self.spans.append(
            SentryAgentSpanRecord(
                span_id=span_hash,
                op=op,
                description=description,
                model_id=model_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=elapsed_ms,
                status="ok",
            )
        )
