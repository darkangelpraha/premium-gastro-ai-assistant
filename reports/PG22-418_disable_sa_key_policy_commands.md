# PG22-418 — Disable Service Account Key Creation Block (Org-wide)

Use these commands exactly as-is.

## 0) Set org IDs from the ticket

```bash
# Org where policy delete command was shown
ORG_ID=102989649831924626485

# Org prefix used in custom constraint names from the ticket
ALT_ORG_ID=846614026320
```

## 1) Disable the managed org policy that blocks SA key creation

```bash
gcloud org-policies delete constraints/iam.disableServiceAccountKeyCreation --organization=$ORG_ID
```

## 2) Disable custom constraint policy bindings shown in the ticket

```bash
gcloud org-policies delete organizations/$ALT_ORG_ID/customConstraints/custom.disableServiceAccountKeyCreation --organization=$ALT_ORG_ID

gcloud org-policies delete organizations/$ALT_ORG_ID/constraints/iam.managed.disableServiceAccountApiKeyCreation --organization=$ALT_ORG_ID
```

## 3) Optional: delete the custom constraint definition itself

```bash
gcloud org-policies custom-constraints delete custom.disableServiceAccountKeyCreation --organization=$ALT_ORG_ID
```

## 4) Verify effective state on org

```bash
gcloud org-policies describe constraints/iam.disableServiceAccountKeyCreation --organization=$ORG_ID

gcloud org-policies list --organization=$ALT_ORG_ID | rg "disableServiceAccountKeyCreation|disableServiceAccountApiKeyCreation|custom.disableServiceAccountKeyCreation"
```

## 5) Verify no folder/project overrides remain

```bash
# list folders under org
for F in $(gcloud resource-manager folders list --organization=$ORG_ID --format='value(name)'); do
  echo "=== $F ==="
  gcloud org-policies describe constraints/iam.disableServiceAccountKeyCreation --folder=${F#folders/} --effective 2>/dev/null || true
done

# list projects under org
for P in $(gcloud projects list --filter="parent.id=$ORG_ID parent.type=organization" --format='value(projectId)'); do
  echo "=== $P ==="
  gcloud org-policies describe constraints/iam.disableServiceAccountKeyCreation --project=$P --effective 2>/dev/null || true
done
```

## 6) Smoke test key creation

```bash
PROJECT_ID="your-project-id"
SA_EMAIL="backup-sa@$PROJECT_ID.iam.gserviceaccount.com"

mkdir -p /tmp/sa-key-test

gcloud iam service-accounts keys create /tmp/sa-key-test/key.json \
  --iam-account="$SA_EMAIL" \
  --project="$PROJECT_ID"
```
