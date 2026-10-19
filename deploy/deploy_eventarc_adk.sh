#!/usr/bin/env bash
# ==============================================================================
# StreamForge: Event-Driven ADK Pipeline Deployment (Eventarc + Pub/Sub + Cloud Run)
# ==============================================================================
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
SERVICE_NAME="streamforge-event-adk"
INBOX_BUCKET="${PROJECT_ID}-streamforge-inbox"
DLQ_TOPIC="streamforge-cloudevent-dlq"
RUNTIME_SA="streamforge-runtime-sa@${PROJECT_ID}.iam.gserviceaccount.com"
EVENTARC_SA="streamforge-eventarc-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "==> [1/6] Enabling Cloud Run, Eventarc, Pub/Sub, Storage, and Firestore APIs..."
gcloud services enable \
  run.googleapis.com \
  eventarc.googleapis.com \
  pubsub.googleapis.com \
  storage.googleapis.com \
  firestore.googleapis.com \
  --project="${PROJECT_ID}"

echo "==> [2/6] Creating Cloud Storage Inbox Bucket & Dead-Letter Pub/Sub Topic..."
gcloud storage buckets create "gs://${INBOX_BUCKET}" \
  --location="${REGION}" \
  --project="${PROJECT_ID}" || true

gcloud pubsub topics create "${DLQ_TOPIC}" --project="${PROJECT_ID}" || true

echo "==> [3/6] Creating Least-Privilege Service Accounts..."
gcloud iam service-accounts create streamforge-runtime-sa \
  --display-name="StreamForge ADK Runtime Service Account" \
  --project="${PROJECT_ID}" || true

gcloud iam service-accounts create streamforge-eventarc-sa \
  --display-name="StreamForge Eventarc OIDC Trigger Service Account" \
  --project="${PROJECT_ID}" || true

# Grant Cloud Storage read + Firestore write to runtime SA
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/datastore.user" --condition=None

gcloud storage buckets add-iam-policy-binding "gs://${INBOX_BUCKET}" \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/storage.objectViewer"

echo "==> [4/6] Deploying StreamForge ADK Service to Cloud Run (private ingress)..."
gcloud run deploy "${SERVICE_NAME}" \
  --source=. \
  --dockerfile=deploy/Dockerfile \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --service-account="${RUNTIME_SA}" \
  --no-allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --concurrency=4 \
  --timeout=300s \
  --min-instances=0 \
  --max-instances=10 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},STREAMFORGE_RUNTIME_MODE=cloud_run_vllm,STREAMFORGE_MODEL_NAME=google/gemma-3-12b-it"

echo "==> [5/6] Granting Cloud Run Invoker + Eventarc EventReceiver to Eventarc SA..."
gcloud run services add-iam-policy-binding "${SERVICE_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --member="serviceAccount:${EVENTARC_SA}" \
  --role="roles/run.invoker"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${EVENTARC_SA}" \
  --role="roles/eventarc.eventReceiver" --condition=None

# Grant Cloud Storage service agent permission to publish CloudEvents to Pub/Sub
GCS_SERVICE_AGENT="$(gcloud storage service-agent --project="${PROJECT_ID}")"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${GCS_SERVICE_AGENT}" \
  --role="roles/pubsub.publisher" --condition=None

echo "==> [6/6] Creating Eventarc Trigger for google.cloud.storage.object.v1.finalized..."
gcloud eventarc triggers create streamforge-gcs-release-trigger \
  --location="${REGION}" \
  --project="${PROJECT_ID}" \
  --destination-run-service="${SERVICE_NAME}" \
  --destination-run-region="${REGION}" \
  --destination-run-path="/api/v1/cloudevent" \
  --event-filters="type=google.cloud.storage.object.v1.finalized" \
  --event-filters="bucket=${INBOX_BUCKET}" \
  --service-account="${EVENTARC_SA}"

echo "=============================================================================="
echo "Event-Driven ADK Pipeline Deployed!"
echo "Test by uploading a release spec to gs://${INBOX_BUCKET}/releases/:"
echo "  gcloud storage cp sample_release.json gs://${INBOX_BUCKET}/releases/2026-10/vertex-vector-sync-v4.2.json"
echo "=============================================================================="
