#!/usr/bin/env bash
set -euo pipefail

export PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-gcp-project-id}"
export REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
export MODEL_BUCKET="${PROJECT_ID}-gemma4-weights"
export VPC_NETWORK="default"
export VPC_SUBNET="default"

echo "==> [1/7] Enabling Cloud Run, Spanner, AlloyDB, Artifact Registry, and Compute APIs..."
gcloud services enable \
  run.googleapis.com \
  spanner.googleapis.com \
  alloydb.googleapis.com \
  compute.googleapis.com \
  artifactregistry.googleapis.com \
  --project="${PROJECT_ID}"

echo "==> [2/7] Creating Least-Privilege Service Accounts for Gemma 4 GPU, MCP Servers, and A2A Coordinator..."
gcloud iam service-accounts create gemma4-vllm-gpu-sa --display-name="Gemma 4 Cloud Run GPU Service Account" --project="${PROJECT_ID}" || true
gcloud iam service-accounts create mcp-data-mesh-sa --display-name="Spanner Graph & AlloyDB MCP Service Account" --project="${PROJECT_ID}" || true
gcloud iam service-accounts create adk-mesh-coordinator-sa --display-name="ADK A2A & Multi-MCP Coordinator Service Account" --project="${PROJECT_ID}" || true

echo "==> [3/7] Provisioning Cloud Storage Model Cache Bucket (${MODEL_BUCKET}) for Zero-Download GCS FUSE Mount..."
gcloud storage buckets create "gs://${MODEL_BUCKET}" --location="${REGION}" --uniform-bucket-level-access --project="${PROJECT_ID}" || true
gcloud storage buckets add-iam-policy-binding "gs://${MODEL_BUCKET}" \
  --member="serviceAccount:gemma4-vllm-gpu-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

echo "==> [4/7] Deploying Open-Weights Gemma 4 (google/gemma-4-27b-it) on Cloud Run NVIDIA L4 GPU with Direct VPC Egress..."
gcloud run deploy gemma4-27b-vllm-service \
  --image="us-docker.pkg.dev/vertex-ai/vertex-vision-model-garden-dockers/pytorch-vllm-serve:202604" \
  --region="${REGION}" \
  --cpu=8 \
  --memory=32Gi \
  --gpu=1 \
  --gpu-type=nvidia-l4 \
  --no-gpu-zonal-redundancy \
  --min-instances=0 \
  --max-instances=3 \
  --concurrency=16 \
  --no-allow-unauthenticated \
  --service-account="gemma4-vllm-gpu-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --network="${VPC_NETWORK}" \
  --subnet="${VPC_SUBNET}" \
  --vpc-egress=private-ranges-only \
  --add-volume=name=gemma-weights,type=cloud-storage,bucket="${MODEL_BUCKET}",readonly=true \
  --add-volume-mount=volume=gemma-weights,mount-path=/mnt/models \
  --set-env-vars="MODEL_ID=/mnt/models/gemma-4-27b-it,MAX_MODEL_LEN=16384,ENABLE_AUTO_TOOL_CHOICE=true,TOOL_CALL_PARSER=pythonic"

echo "==> [5/7] Deploying Cloud Spanner Graph MCP & AlloyDB pgvector MCP Servers (Private Cloud Run SSE)..."
gcloud run deploy spanner-graph-mcp-server \
  --source=. \
  --command="python,-m,a2a_mcp_mesh.mcp_servers.spanner_graph_mcp" \
  --region="${REGION}" \
  --cpu=2 \
  --memory=2Gi \
  --no-allow-unauthenticated \
  --service-account="mcp-data-mesh-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --network="${VPC_NETWORK}" \
  --subnet="${VPC_SUBNET}" \
  --vpc-egress=private-ranges-only

gcloud run deploy alloydb-vector-mcp-server \
  --source=. \
  --command="python,-m,a2a_mcp_mesh.mcp_servers.alloydb_vector_mcp" \
  --region="${REGION}" \
  --cpu=2 \
  --memory=2Gi \
  --no-allow-unauthenticated \
  --service-account="mcp-data-mesh-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --network="${VPC_NETWORK}" \
  --subnet="${VPC_SUBNET}" \
  --vpc-egress=private-ranges-only

echo "==> [6/7] Deploying Remote A2A GitHub Remediation Specialist Agent (/.well-known/agent.json)..."
gcloud run deploy github-remediation-a2a-agent \
  --source=. \
  --command="uvicorn,a2a_mcp_mesh.a2a_remote_github_agent:app,--host,0.0.0.0,--port,8080" \
  --region="${REGION}" \
  --cpu=2 \
  --memory=2Gi \
  --no-allow-unauthenticated \
  --service-account="mcp-data-mesh-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "==> [7/7] Granting roles/run.invoker to ADK Coordinator Service Account & Deploying Root Coordinator..."
for svc in gemma4-27b-vllm-service spanner-graph-mcp-server alloydb-vector-mcp-server github-remediation-a2a-agent; do
  gcloud run services add-iam-policy-binding "${svc}" \
    --region="${REGION}" \
    --member="serviceAccount:adk-mesh-coordinator-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/run.invoker"
done

gcloud run deploy adk-a2a-mcp-mesh-coordinator \
  --source=. \
  --region="${REGION}" \
  --cpu=2 \
  --memory=4Gi \
  --no-allow-unauthenticated \
  --service-account="adk-mesh-coordinator-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --network="${VPC_NETWORK}" \
  --subnet="${VPC_SUBNET}" \
  --vpc-egress=private-ranges-only

echo "Deployment complete: Cloud Run A2A & Multi-MCP Mesh is active in ${REGION}."
