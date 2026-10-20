#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project)}"
REGION="${REGION:-us-central1}"
MODEL_BUCKET="${MODEL_BUCKET:-${PROJECT_ID}-gemma4-lora-weights}"

echo "=== 1. Deploying Shared Gemma 4 27B Multi-LoRA Server on Cloud Run NVIDIA L4 GPU ==="
gcloud run deploy gemma4-multilora-vllm \
  --image="us-docker.pkg.dev/vertex-ai/vertex-vision-model-garden-dockers/pytorch-vllm-serve:202501" \
  --region="${REGION}" \
  --cpu=8 \
  --memory=32Gi \
  --gpu=1 \
  --gpu-type=nvidia-l4 \
  --no-gpu-zonal-redundancy \
  --min-instances=0 \
  --max-instances=3 \
  --concurrency=16 \
  --execution-environment=gen2 \
  --add-volume="name=lora-weights,type=cloud-storage,bucket=${MODEL_BUCKET},readonly=true" \
  --add-volume-mount="volume=lora-weights,mount-path=/mnt/models" \
  --set-env-vars="VLLM_ALLOW_RUNTIME_LORA_UPDATING=true,HF_HUB_OFFLINE=1" \
  --args="--model=/mnt/models/gemma-4-27b-it" \
  --args="--enable-lora" \
  --args="--max-loras=4" \
  --args="--max-lora-rank=32" \
  --args="--lora-modules=sre-incident-lora=/mnt/models/loras/sre-incident-v1,finops-cost-lora=/mnt/models/loras/finops-cost-v1,secops-audit-lora=/mnt/models/loras/secops-audit-v1" \
  --args="--gpu-memory-utilization=0.92" \
  --args="--max-model-len=8192" \
  --args="--port=8080" \
  --no-allow-unauthenticated

echo "=== 2. Deploying Google ADK Multi-LoRA Coordinator Service on Cloud Run ==="
VLLM_URL=$(gcloud run services describe gemma4-multilora-vllm --region="${REGION}" --format="value(status.url)")

gcloud run deploy adk-multilora-coordinator \
  --source=. \
  --region="${REGION}" \
  --cpu=2 \
  --memory=4Gi \
  --concurrency=80 \
  --set-env-vars="VLLM_API_BASE=${VLLM_URL}/v1" \
  --no-allow-unauthenticated
