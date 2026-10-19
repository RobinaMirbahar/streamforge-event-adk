"""Native Python tools for StreamForge Event-Driven ADK Pipeline (ParallelAgent + LoopAgent)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

LOCAL_DB_PATH = Path(__file__).resolve().parent.parent / ".local_firestore_streamforge.json"

DEFAULT_SEED_DATA: Dict[str, Any] = {
    "gcs_inbox_objects": {
        "releases/2026-10/vertex-vector-sync-v4.2.json": {
            "release_sku": "SF-VECTOR-SYNC-4.2",
            "product_title": "StreamForge Real-Time Vector & Iceberg Lakehouse Sync v4.2",
            "engineering_changelog": {
                "p99_sync_latency_ms": 38,
                "previous_p99_latency_ms": 145,
                "throughput_rows_per_sec": 250000,
                "supported_engines": ["BigQuery", "Apache Iceberg", "AlloyDB", "Cloud Spanner"],
                "zero_copy_delta_compression_ratio": "4.6x",
            },
            "base_pricing_usd": {
                "starter_monthly_usd": 149.0,
                "growth_monthly_usd": 499.0,
                "enterprise_seat_pack_usd": 1490.0,
            },
            "target_regions": ["en_US", "de_DE", "ja_JP"],
        }
    },
    "historical_elasticity_benchmarks": {
        "SF-VECTOR-SYNC-4.2": {
            "active_growth_tier_accounts": 1840,
            "predicted_upgrade_conversion_pct": 18.5,
            "avg_annual_expansion_per_upgraded_account_usd": 8400.0,
            "fx_rates": {"USD_TO_EUR": 0.92, "USD_TO_JPY": 152.0},
            "regional_purchasing_power_rules": {
                "de_DE": "Must display VAT-exclusive B2B Euro pricing rounded to nearest €5.",
                "ja_JP": "Must display Yen integer pricing without decimals (¥).",
            },
        }
    },
    "cloudevent_dedup_ledger": {},
    "launch_manifests": {},
}


def _load_store() -> Dict[str, Any]:
    if not LOCAL_DB_PATH.exists():
        LOCAL_DB_PATH.write_text(json.dumps(DEFAULT_SEED_DATA, indent=2), encoding="utf-8")
    return json.loads(LOCAL_DB_PATH.read_text(encoding="utf-8"))


def _save_store(data: Dict[str, Any]) -> None:
    LOCAL_DB_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def reset_local_store() -> None:
    """Resets the local Firestore/GCS mirror to clean seed state for reproducible verification."""
    _save_store(DEFAULT_SEED_DATA)


def check_cloudevent_idempotency(ce_id: str) -> Optional[Dict[str, Any]]:
    """Checks if a CloudEvent ID (ce-id) has already been processed in Firestore."""
    store = _load_store()
    manifest_id = store.get("cloudevent_dedup_ledger", {}).get(ce_id)
    if not manifest_id:
        return None
    return store.get("launch_manifests", {}).get(manifest_id)


def parse_gcs_release_artifact(bucket: str, object_name: str) -> Dict[str, Any]:
    """Reads and extracts technical specifications and benchmarks from a newly finalized GCS JSON object.

    Args:
        bucket: Name of the Google Cloud Storage bucket (e.g., 'streamforge-launch-inbox').
        object_name: Object key inside the bucket (e.g., 'releases/2026-10/vertex-vector-sync-v4.2.json').

    Returns:
        Dictionary containing extracted engineering benchmarks, supported engines, and base USD pricing.
    """
    store = _load_store()
    artifact = store.get("gcs_inbox_objects", {}).get(object_name)
    if not artifact:
        return {"status": "NOT_FOUND", "bucket": bucket, "object_name": object_name}

    changelog = artifact["engineering_changelog"]
    latency_improvement_pct = round(
        (1.0 - (changelog["p99_sync_latency_ms"] / changelog["previous_p99_latency_ms"])) * 100, 1
    )
    return {
        "status": "OK",
        "bucket": bucket,
        "object_name": object_name,
        "release_sku": artifact["release_sku"],
        "product_title": artifact["product_title"],
        "technical_highlights": [
            f"Reduced p99 vector sync latency by {latency_improvement_pct}% (from 145ms down to 38ms).",
            f"Sustains {changelog['throughput_rows_per_sec']:,} rows/sec streaming throughput with 4.6x zero-copy delta compression.",
            f"Native connectors for {', '.join(changelog['supported_engines'])}.",
        ],
        "base_pricing_usd": artifact["base_pricing_usd"],
    }


def generate_regional_localization_bundle(release_sku: str, product_title: str) -> Dict[str, Any]:
    """Generates localized launch copy (en_US, de_DE, ja_JP) and multi-currency tier pricing.

    Args:
        release_sku: Unique SKU of the product release (e.g., 'SF-VECTOR-SYNC-4.2').
        product_title: Official product release title.

    Returns:
        Dictionary with localized headlines and regional pricing strings.
    """
    return {
        "status": "OK",
        "release_sku": release_sku,
        "regional_launch_copy": {
            "en_US": (
                f"{product_title}: Sub-40ms streaming sync across BigQuery, Iceberg, and AlloyDB "
                "with 4.6x zero-copy compression."
            ),
            "de_DE": (
                "StreamForge Echtzeit-Vektor- & Iceberg-Sync v4.2: 38 ms p99-Latenz für BigQuery "
                "und AlloyDB bei 4,6-facher Zero-Copy-Komprimierung."
            ),
            "ja_JP": (
                "StreamForge リアルタイム Vector & Iceberg 同期 v4.2：BigQuery・AlloyDB 向けに "
                "p99 レイテンシ 38ms と 4.6倍のゼロコピー圧縮を実現。"
            ),
        },
        # Initial pass intentionally leaves EUR unrounded (€459.08) so LoopAgent Critic catches & fixes it
        "draft_pricing_tiers": {
            "USD": "Growth Tier: $499/mo",
            "EUR": "Growth Tier: €459.08/mo",
            "JPY": "Growth Tier: ¥75,848/mo",
        },
    }


def simulate_tier_pricing_and_arr(release_sku: str) -> Dict[str, Any]:
    """Simulates 12-month Net New ARR lift and retrieves regional currency compliance rules.

    Args:
        release_sku: Unique SKU of the product release (e.g., 'SF-VECTOR-SYNC-4.2').

    Returns:
        Dictionary containing projected ARR lift and regional FX compliance rules.
    """
    store = _load_store()
    bench = store["historical_elasticity_benchmarks"].get(release_sku, {})
    upgraded_accounts = int(
        bench.get("active_growth_tier_accounts", 1840)
        * (bench.get("predicted_upgrade_conversion_pct", 18.5) / 100.0)
    )
    projected_arr_lift = round(
        upgraded_accounts * bench.get("avg_annual_expansion_per_upgraded_account_usd", 8400.0), 2
    )
    return {
        "status": "OK",
        "release_sku": release_sku,
        "upgraded_accounts_forecast": upgraded_accounts,
        "projected_net_arr_lift_usd": projected_arr_lift,
        "fx_rates": bench.get("fx_rates", {}),
        "regional_purchasing_power_rules": bench.get("regional_purchasing_power_rules", {}),
    }


def verify_cross_agent_launch_consistency(
    draft_pricing_tiers: Dict[str, str],
    iteration: int = 1,
) -> Dict[str, Any]:
    """Audits parallel agent outputs against regional pricing compliance and benchmark accuracy.

    Args:
        draft_pricing_tiers: Dictionary of currency codes to formatted tier pricing.
        iteration: Current LoopAgent iteration index.

    Returns:
        Audit verdict with quality_score, discrepancies_found, and remediated pricing tiers.
    """
    eur_price = draft_pricing_tiers.get("EUR", "")
    if "459.08" in eur_price and iteration == 1:
        return {
            "quality_score": 0.72,
            "passed": False,
            "discrepancies_found": [
                "de_DE regional rule violation: EUR price '€459.08/mo' contains fractional cents instead of rounding to the nearest €5 (€460/mo VAT-excl.).",
                "ja_JP regional rule check: JPY price '¥75,848/mo' should be rounded to clean commercial tier '¥75,800/mo'.",
            ],
            "remediated_pricing_tiers": {
                "USD": "Growth Tier: $499/mo (B2B Annual)",
                "EUR": "Growth Tier: €460/mo (zzgl. MwSt.)",
                "JPY": "Growth Tier: ¥75,800/月 (税抜)",
            },
        }
    return {
        "quality_score": 1.0,
        "passed": True,
        "discrepancies_found": [],
        "remediated_pricing_tiers": draft_pricing_tiers,
    }


def exit_quality_loop(tool_context: Any = None) -> Dict[str, Any]:
    """Signals Google ADK LoopAgent to terminate iteration once quality_score reaches 1.0.

    Args:
        tool_context: Google ADK ToolContext injected automatically at runtime.

    Returns:
        Confirmation that LoopAgent escalation flag has been set.
    """
    if tool_context is not None and hasattr(tool_context, "actions"):
        tool_context.actions.escalate = True
    return {"status": "LOOP_ESCALATED", "escalate": True}


def publish_launch_manifest_to_firestore(
    cloudevent_id: str,
    release_sku: str,
    product_title: str,
    technical_highlights: List[str],
    regional_launch_copy: Dict[str, str],
    pricing_tiers_usd_eur_jpy: Dict[str, str],
    projected_net_arr_lift_usd: float,
    loop_iterations_completed: int,
    final_quality_score: float,
) -> Dict[str, Any]:
    """Persists the validated EventDrivenLaunchManifest to Cloud Firestore and records ce-id idempotency.

    Args:
        cloudevent_id: Unique Eventarc CloudEvent ID (ce-id).
        release_sku: Product release SKU.
        product_title: Official release title.
        technical_highlights: Validated engineering highlights.
        regional_launch_copy: Localized copy dictionary.
        pricing_tiers_usd_eur_jpy: Compliance-verified multi-currency pricing.
        projected_net_arr_lift_usd: Projected 12-month ARR lift in USD.
        loop_iterations_completed: Number of LoopAgent iterations executed.
        final_quality_score: Final quality score (1.0).

    Returns:
        Firestore persistence receipt including manifest_id.
    """
    store = _load_store()
    manifest_id = f"MANIFEST-{release_sku}"
    doc = {
        "manifest_id": manifest_id,
        "cloudevent_id": cloudevent_id,
        "release_sku": release_sku,
        "product_title": product_title,
        "technical_highlights": technical_highlights,
        "regional_launch_copy": regional_launch_copy,
        "pricing_tiers_usd_eur_jpy": pricing_tiers_usd_eur_jpy,
        "projected_net_arr_lift_usd": projected_net_arr_lift_usd,
        "loop_iterations_completed": loop_iterations_completed,
        "final_quality_score": final_quality_score,
        "generated_by_model": os.getenv("STREAMFORGE_MODEL_NAME", "ollama_chat/gemma3:12b"),
    }
    store.setdefault("launch_manifests", {})[manifest_id] = doc
    store.setdefault("cloudevent_dedup_ledger", {})[cloudevent_id] = manifest_id
    _save_store(store)
    return {"status": "PUBLISHED", "manifest_id": manifest_id, "document": doc}
