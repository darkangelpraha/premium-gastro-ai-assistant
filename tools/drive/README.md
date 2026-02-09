# Drive Toolkit

Tools for cleaning up cloud-synced drives (Google Drive for Desktop) in a **safe, reversible** way.

Principles
- Default is **dry-run**.
- **Never delete**. When changes are applied, they are either:
  - `rename/move` within the same Drive (reversible)
  - or `copy` out of a backup snapshot into local `~/Projects` (source stays intact)
- Every run writes a **log** and a **report**.

## gdrive_quarantine_dev_artifacts.py

Purpose
- Detect obvious dev artifacts that should not live at the root of Google Drive "My Drive".
- Move them into a quarantine folder inside the same Drive.

Why this works
- Google Drive conflict handling creates huge duplication trees like `rimraf (123)` / `glob (244)`.
- Git internals can appear as folders named like `06 (11)` (2-hex) or long hex IDs.

What it touches
- Only the **top-level** of "My Drive".
- It does not scan deep folders.

Output
- Creates `__QUARANTINE__DevArtifacts__YYYY-MM-DD/_logs/*.jsonl` under "My Drive".

## restore_backup_repos_to_projects.py

Purpose
- A Drive backup snapshot (example: `.../Backup/Petr.local/Users/<user>/...`) may contain many `.git` folders.
- GitHub Desktop sometimes points at those backup paths.
- This tool copies repos out of the backup snapshot into local `~/Projects/99-Legacy/RESTORE__GDriveBackup__YYYY-MM-DD`.

Dedup logic
- If a local repo with the same `origin` and `HEAD` exists and both are clean, the restore is skipped.
- Otherwise, the repo is copied into the restore destination to avoid any overwrite.

Output
- Writes TSV + JSONL into `ops/_local/dev_audit/` (gitignored).

Unicode note (important)
- The Czech "Můj disk" can use a combining diacritic. The tools locate "My Drive" using Unicode normalization.
