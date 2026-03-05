# AI Runtime Policy (All Clients)

This policy applies to VS Code, Cursor, Antigravity, and regular chat workflows.

## Mandatory Rules

1. Knowledge tasks must use Qdrant as the single source of truth (SSoT).
2. Retrieval must happen before drafting factual answers when repository/business knowledge is requested.
3. Local Ollama is the default provider for embeddings/inference.
4. Paid cloud providers are opt-in only and must be explicitly enabled.

## Required Environment Defaults

```
KNOWLEDGE_SSOT=qdrant
ENFORCE_QDRANT_SSOT=1
LLM_PROVIDER_DEFAULT=ollama
QDRANT_EMBEDDING_PROVIDER=ollama
ALLOW_PAID_LLM=0
```

## Controlled Paid-LLM Escape Hatch

Only when intentionally approved:

```
ALLOW_PAID_LLM=1
QDRANT_EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=...
```

After emergency usage, revert to:

```
ALLOW_PAID_LLM=0
QDRANT_EMBEDDING_PROVIDER=ollama
```
