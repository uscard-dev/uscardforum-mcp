# Deploy USCardForum MCP Server to Cloud Run

<walkthrough-author name="USCardForum" analyticsId="UA-000000-0"></walkthrough-author>

## Introduction

This tutorial will guide you through deploying the USCardForum MCP Server to Google Cloud Run.

**Time to complete**: About 5 minutes

Click **Start** to begin.

## Set up your project

First, select or create a Google Cloud project.

<walkthrough-project-setup></walkthrough-project-setup>

Set the project ID:

```bash
gcloud config set project {{project-id}}
```

## Enable required APIs

Enable Cloud Run and Cloud Build APIs:

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

## Deploy to Cloud Run

Deploy the MCP server using Cloud Run's source-based deployment:

```bash
gcloud run deploy uscardforum-mcp \
  --source . \
  --region us-west1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8000 \
  --memory 512Mi \
  --set-env-vars "MCP_TRANSPORT=streamable-http,MCP_HOST=0.0.0.0,MCP_PORT=8000"
```

This will:
1. Build the Docker image using Cloud Build
2. Push it to Container Registry
3. Deploy it to Cloud Run

## Configure secrets (Optional)

To enable MCP authentication, create a secret and attach it:

```bash
# Create secret for MCP auth token
echo -n "your-secret-token" | gcloud secrets create nitan-token --data-file=-

# Grant Cloud Run access to the secret
gcloud secrets add-iam-policy-binding nitan-token \
  --member="serviceAccount:{{project-number}}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Update the service with the secret
gcloud run services update uscardforum-mcp \
  --set-secrets="NITAN_TOKEN=nitan-token:latest" \
  --region us-west1
```

## Get your service URL

Get the URL of your deployed service:

```bash
gcloud run services describe uscardforum-mcp --region us-west1 --format='value(status.url)'
```

Your MCP endpoint will be at: `<service-url>/mcp`

## Connect from Cursor

Add to your `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "uscardforum": {
      "url": "<your-service-url>/mcp",
      "headers": {
        "Authorization": "Bearer your-secret-token"
      }
    }
  }
}
```

## Congratulations!

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

You've successfully deployed the USCardForum MCP Server to Cloud Run!

### Next steps

- [View your Cloud Run services](https://console.cloud.google.com/run)
- [Set up continuous deployment](https://cloud.google.com/run/docs/continuous-deployment-with-cloud-build)
- [Configure custom domains](https://cloud.google.com/run/docs/mapping-custom-domains)






