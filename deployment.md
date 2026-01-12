# Deployment Guide - Cloud Run

This guide covers deploying the DialQ Scraping Service to Google Cloud Run.

## Prerequisites

- Google Cloud account with billing enabled
- [Google Cloud CLI (gcloud)](https://cloud.google.com/sdk/docs/install) installed and authenticated
- Docker installed (optional, for local testing)
- A Google Gemini API key

## Initial Setup

### 1. Authenticate with Google Cloud

```bash
gcloud auth login && gcloud auth configure-docker
```

### 2. Set Your Project

```bash
gcloud config set project dialiq-474815
```

Replace `YOUR_PROJECT_ID` with your actual GCP project ID.

### 3. Enable Required APIs

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

---

## First-Time Deployment

### Option A: Deploy Using Cloud Build (Recommended)

This builds the image in the cloud and deploys directly:

```bash
gcloud run deploy scraping-service \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --port 9500
```

## Updating the Service (After Code Changes)

### Quick Update (Recommended)

After making code changes, run this single command to rebuild and redeploy:

```bash
gcloud run deploy scraping-service --source . --region us-central1
```

This command:
- Detects code changes
- Rebuilds the Docker image in Cloud Build
- Deploys the new revision to Cloud Run
- Preserves existing environment variables and configuration

### Update with New Environment Variables

If you need to update environment variables along with code:

```bash
gcloud run deploy scraping-service --source . --region us-central1 --set-env-vars "GEMINI_API_KEY=new-api-key"
```

### Update Only Environment Variables (No Code Changes)

```bash
gcloud run services update scraping-service --region us-central1 --set-env-vars "GEMINI_API_KEY=new-api-key"
```

### Using Artifact Registry for Updates

If using the Artifact Registry approach, update with a new tag:

```bash
gcloud builds submit --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/scraping-repo/scraping-service:v2 && \
gcloud run deploy scraping-service \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/scraping-repo/scraping-service:v2 \
  --region us-central1
```

---

## Configuration Options

### Memory and CPU

The service requires adequate resources for running Playwright/Chromium:

| Setting | Recommended | Minimum |
|---------|-------------|---------|
| Memory  | 2Gi         | 1Gi     |
| CPU     | 2           | 1       |
| Timeout | 300s        | 60s     |

### Scaling Configuration

```bash
gcloud run deploy scraping-service \
  --source . \
  --region us-central1 \
  --min-instances 0 \
  --max-instances 10 \
  --concurrency 10
```

### Private Service (Authentication Required)

Remove `--allow-unauthenticated` to require authentication:

```bash
gcloud run deploy scraping-service \
  --source . \
  --region us-central1 \
  --no-allow-unauthenticated
```

---

## Using Secret Manager (Recommended for Production)

Instead of passing API keys directly, use Secret Manager:

### Step 1: Create Secret

```bash
echo -n "your-gemini-api-key" | gcloud secrets create gemini-api-key --data-file=-
```

### Step 2: Grant Access to Cloud Run

```bash
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Step 3: Deploy with Secret

```bash
gcloud run deploy scraping-service \
  --source . \
  --region us-central1 \
  --set-secrets "GEMINI_API_KEY=gemini-api-key:latest"
```

---

## Useful Commands

### View Service URL

```bash
gcloud run services describe scraping-service --region us-central1 --format="value(status.url)"
```

### View Logs

```bash
gcloud run services logs read scraping-service --region us-central1 --limit 50
```

### Stream Logs (Real-time)

```bash
gcloud run services logs tail scraping-service --region us-central1
```

### List All Revisions

```bash
gcloud run revisions list --service scraping-service --region us-central1
```

### Rollback to Previous Revision

```bash
gcloud run services update-traffic scraping-service --region us-central1 --to-revisions REVISION_NAME=100
```

### Delete Service

```bash
gcloud run services delete scraping-service --region us-central1
```

---

## Local Testing with Docker

### Build Image Locally

```bash
docker build -t scraping-service .
```

### Run Locally

```bash
docker run -p 9500:9500 -e GEMINI_API_KEY=your-api-key scraping-service
```

### Test the API

```bash
curl http://localhost:9500/
```

---

## Troubleshooting

### Container Fails to Start

Check logs for errors:
```bash
gcloud run services logs read scraping-service --region us-central1 --limit 100
```

Common issues:
- Missing `GEMINI_API_KEY` environment variable
- Insufficient memory for Chromium (increase to 2Gi+)
- Port mismatch (ensure `--port 9500` matches Dockerfile)

### Timeout Errors

Increase timeout for long-running crawl operations:
```bash
gcloud run services update scraping-service --region us-central1 --timeout 600
```

### Cold Start Issues

Set minimum instances to avoid cold starts:
```bash
gcloud run services update scraping-service --region us-central1 --min-instances 1
```

---

## Cost Optimization

- Use `--min-instances 0` to scale to zero when not in use
- Set appropriate `--max-instances` to limit costs
- Use `--cpu-throttling` for non-latency-sensitive workloads:
  ```bash
  gcloud run deploy scraping-service --source . --region us-central1 --cpu-throttling
  ```

---

## Quick Reference

| Action | Command |
|--------|---------|
| First deploy | `gcloud run deploy scraping-service --source . --region us-central1 --memory 2Gi --cpu 2 --set-env-vars "GEMINI_API_KEY=xxx" --port 9500 --allow-unauthenticated` |
| Update code | `gcloud run deploy scraping-service --source . --region us-central1` |
| Update env vars | `gcloud run services update scraping-service --region us-central1 --set-env-vars "KEY=value"` |
| View URL | `gcloud run services describe scraping-service --region us-central1 --format="value(status.url)"` |
| View logs | `gcloud run services logs read scraping-service --region us-central1` |
| Delete | `gcloud run services delete scraping-service --region us-central1` |
