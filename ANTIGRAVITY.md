# Antigravity Assistant Profile

Apply `AI_POLICY.md` in full.

## Required defaults

- Knowledge SSoT: Qdrant only.
- Retrieval-first for factual/internal knowledge.
- Local-first inference: Ollama by default.
- Paid providers disabled by default (`ALLOW_PAID_LLM=0`).

## Escalation path

Use paid provider only with explicit approval and temporary env override.
