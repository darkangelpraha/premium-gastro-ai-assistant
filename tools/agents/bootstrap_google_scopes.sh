#!/usr/bin/env bash
set -euo pipefail

SCOPES="https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/analytics.readonly,https://www.googleapis.com/auth/tagmanager.readonly"

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud not found in PATH"
  exit 1
fi

echo "Configuring Application Default Credentials with GA4/GTM scopes..."
gcloud auth application-default login --scopes="$SCOPES"

echo "Verifying ADC token retrieval..."
gcloud auth application-default print-access-token --scopes="$SCOPES" >/dev/null

echo "OK: ADC is configured for GA4/GTM agent jobs."
