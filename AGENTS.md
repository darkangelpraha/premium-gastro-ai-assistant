# Agent Runtime Rules

All agents (including Antigravity-style and regular chat agents) must follow `AI_POLICY.md`.

## Non-negotiable constraints

1. Qdrant is the knowledge SSoT for repository/business knowledge tasks.
2. Use retrieval-first patterns before producing factual answers.
3. Local Ollama is the default LLM/embedding provider.
4. Paid cloud provider calls are blocked unless explicitly approved and enabled (`ALLOW_PAID_LLM=1`).

## Operational behavior

- If retrieval data is unavailable, state that and request indexing/refresh instead of guessing.
- Keep secrets out of prompts, logs, and repository files.
- Execution-first: do not repeatedly ask user to choose technical implementation details.
- Default flow is `move/unify -> verify -> delete last`; ask only for destructive/irreversible actions or missing access.
