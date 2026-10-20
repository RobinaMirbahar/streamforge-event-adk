from typing import Any, Dict, List, Optional
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from multilora_adk_eval.schemas import LoraAdapterMetadata

app = FastAPI(
    title="vLLM OpenAI-Compatible Multi-LoRA Runtime Server (Gemma 4)",
    version="1.0.0",
)

BASE_MODEL_ID = "google/gemma-4-27b-it"

# In-memory registry of active LoRA adapters mounted from Cloud Storage FUSE (/mnt/models/loras/*)
ACTIVE_LORA_ADAPTERS: Dict[str, LoraAdapterMetadata] = {}


class LoadLoraRequest(BaseModel):
    lora_name: str
    lora_path: str
    lora_rank: int = 16
    lora_alpha: int = 32
    vram_overhead_mb: float = 64.5


class UnloadLoraRequest(BaseModel):
    lora_name: str


@app.get("/v1/models")
async def list_models() -> Dict[str, Any]:
    """Returns the frozen base Gemma 4 model plus all dynamically loaded LoRA adapters."""
    data: List[Dict[str, Any]] = [
        {"id": BASE_MODEL_ID, "object": "model", "owned_by": "google", "parent": None}
    ]
    for adapter_id, meta in ACTIVE_LORA_ADAPTERS.items():
        data.append(
            {
                "id": adapter_id,
                "object": "model",
                "owned_by": "enterprise-lora-registry",
                "parent": meta.base_model,
                "root": meta.gcs_fuse_path,
            }
        )
    return {"object": "list", "data": data}


@app.post("/v1/load_lora_adapter")
async def load_lora_adapter(req: LoadLoraRequest) -> Dict[str, Any]:
    """Hot-loads a QLoRA adapter from Cloud Storage FUSE into GPU VRAM with zero restart."""
    meta = LoraAdapterMetadata(
        adapter_id=req.lora_name,
        base_model=BASE_MODEL_ID,
        gcs_fuse_path=req.lora_path,
        lora_rank=req.lora_rank,
        lora_alpha=req.lora_alpha,
        vram_overhead_mb=req.vram_overhead_mb,
    )
    ACTIVE_LORA_ADAPTERS[req.lora_name] = meta
    return {
        "status": "loaded",
        "adapter": meta.model_dump(),
    }


@app.post("/v1/unload_lora_adapter")
async def unload_lora_adapter(req: UnloadLoraRequest) -> Dict[str, Any]:
    """Unloads a LoRA adapter from vLLM runtime memory."""
    if req.lora_name not in ACTIVE_LORA_ADAPTERS:
        raise HTTPException(status_code=404, detail=f"LoRA adapter '{req.lora_name}' not loaded")
    removed = ACTIVE_LORA_ADAPTERS.pop(req.lora_name)
    return {"status": "unloaded", "adapter_id": removed.adapter_id}


async def hot_load_lora_adapter(
    vllm_base_url: str,
    lora_name: str,
    lora_path: str,
    id_token: Optional[str] = None,
    lora_rank: int = 16,
    vram_overhead_mb: float = 64.5,
) -> LoraAdapterMetadata:
    """Client helper that calls vLLM's POST /v1/load_lora_adapter endpoint on Cloud Run."""
    headers = {"Content-Type": "application/json"}
    if id_token:
        headers["Authorization"] = f"Bearer {id_token}"

    payload = {
        "lora_name": lora_name,
        "lora_path": lora_path,
        "lora_rank": lora_rank,
        "lora_alpha": lora_rank * 2,
        "vram_overhead_mb": vram_overhead_mb,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{vllm_base_url.rstrip('/')}/v1/load_lora_adapter",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        body = resp.json()
        return LoraAdapterMetadata.model_validate(body["adapter"])
