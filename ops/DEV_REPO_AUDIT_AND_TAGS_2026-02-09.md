# Dev Repo Audit + Finder Tags (macOS)

This note documents a safe, non-destructive way to:
- get a single inventory of local git repos under `~/Projects`
- visually classify them in Finder using color tags (for non-IT orientation)

The workflow is designed to be repeatable and to minimize stress:
- nothing is deleted
- nothing is moved
- only Finder tag metadata is written

## Finder Tag Legend

Primary tags (mutually exclusive):
- `dev OK` (green): actively relevant to current stack / business
- `dev MAY` (orange): keepable tools/experiments; not critical day-to-day
- `dev NO` (red): legacy/quarantine/recovered; not in active use

Secondary tag (additive):
- `dev WEB` (blue): web-ish repo (frontend/webapp tooling)

## Step 1: Generate Inventory TSV (Read-only)

Script: `tools/indexing/dev_repo_inventory.py`

Example:
```bash
ts=$(date +%Y%m%d-%H%M%S)
python3 tools/indexing/dev_repo_inventory.py \
  --out /tmp/dev_audit_git_repos_${ts}.tsv \
  --log /tmp/dev_audit_git_repos_${ts}.jsonl
```

Output TSV columns include:
- `path`, `projects_bucket`, `size_mb`
- `origin`, `gh_owner`, `gh_repo`
- `head`, `last_commit`, `dirty_files`
- `tag_suggest`, `tag_reason`
- `is_web`, `web_reason`

## Step 2: Apply Finder Tags (Metadata only)

Script: `tools/indexing/finder_tags_apply.py`

Important behavior:
- default is DRY RUN (no writes)
- use `--apply` to actually set Finder tags
- primary tags are enforced to be one of `dev OK/MAY/NO`
- `dev WEB` is added when `is_web=1`, without removing other non-dev tags

Dry run:
```bash
ts=$(date +%Y%m%d-%H%M%S)
python3 tools/indexing/finder_tags_apply.py \
  --tsv /tmp/dev_audit_git_repos_${ts}.tsv \
  --report /tmp/finder_tag_apply_${ts}.tsv \
  --log /tmp/finder_tag_apply_${ts}.jsonl
```

Apply:
```bash
ts=$(date +%Y%m%d-%H%M%S)
python3 tools/indexing/finder_tags_apply.py \
  --tsv /tmp/dev_audit_git_repos_${ts}.tsv \
  --apply \
  --report /tmp/finder_tag_apply_${ts}.tsv \
  --log /tmp/finder_tag_apply_${ts}.jsonl
```

## Notes (Non-IT Friendly)

- Finder tags do not change the folder contents.
- `dev NO` does not mean “delete”; it means “not in active use” and helps reduce noise.
- Some repos are used indirectly (read-only) by tools and automations. Tagging is safe; deleting is not.

