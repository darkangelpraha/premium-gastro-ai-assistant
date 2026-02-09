# DevTools Cleanup Audit (2026-02-09)

Goal: reduce chaos without data loss. Strategy: quarantine first, then salvage, then delete only after explicit approval.

## Canonical locations

- DevTools root: `/Users/premiumgastro/Projects/06-Development-Tools`
- Git repos: `/Users/premiumgastro/Projects/06-Development-Tools/GitHub/<owner>/<repo>`
- Quarantine: `/Users/premiumgastro/Projects/06-Development-Tools/_Quarantine/`

## Actions performed

- Created clean DevTools structure:
  - `GitHub/`
  - `Configs/`
  - `Scripts/`
  - `_Quarantine/`
- Moved everything previously in DevTools root into a timestamped quarantine folder.
- Salvaged Git repos out of quarantine into `GitHub/` and replaced the original quarantine locations with symlinks.

## Evidence / audit logs

- DevTools root quarantine move:
  - `/tmp/06-devtools_root_quarantine_20260209-190936.jsonl`
- Repo salvage logs (one or more files):
  - `/tmp/devtools_quarantine_salvage_*.jsonl`

## Current quarantine inventory (high level)

Quarantine folder:
`/Users/premiumgastro/Projects/06-Development-Tools/_Quarantine/06-Development-Tools_root__20260209-190936`

Top directories by *disk allocation* (note: cloud placeholders may show small allocated size but large apparent size in Finder):

- `go/` (~2.2G): Go toolchain/cache (typically rebuildable)
- `skyvern_env/` (~866M): Python virtualenv (rebuildable)
- `SDKs/` (~611M): SDK installs (typically reinstallable)
- `CLI_Tools/` (~39M): mixed; contains at least one real git repo (`cli-1`) already salvaged

Notable contents:

- Several repo pointers exist as symlinks inside quarantine (these point to the canonical `GitHub/` copies).
- There is/was a symlink named similar to `ps@premium-gastro.com - Google Drive` pointing into Google Drive CloudStorage. This is high risk clutter: avoid keeping such symlinks inside toolboxes.

## Delete candidates (NOT deleted)

These are typical safe-to-delete categories *after explicit approval*:

- Virtualenvs: `skyvern_env/`
- SDK installs that can be reinstalled: `SDKs/`
- Language caches/toolchains: `go/`
- Empty/placeholder folders: `Installers/`, `Missicw/`, `rag-postgres-data/`, `openwork/` (verify before deleting)

## Safety rule

No hard deletes performed in this work. Any future deletion must be explicitly approved and must be logged.
