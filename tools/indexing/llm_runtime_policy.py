#!/usr/bin/env python3
"""Runtime policy for knowledge tasks and model-provider selection.

This module enforces two invariants:
1) Qdrant is the single source of truth for knowledge tasks.
2) Local Ollama is the default embedding provider; paid providers are opt-in.
"""

from __future__ import annotations

import os


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def enforce_qdrant_ssot(component: str) -> None:
    """Fail fast when the knowledge SSoT is configured away from Qdrant."""
    if not _as_bool(os.environ.get("ENFORCE_QDRANT_SSOT"), True):
        return
    ssot = (os.environ.get("KNOWLEDGE_SSOT", "qdrant") or "").strip().lower()
    if ssot != "qdrant":
        raise RuntimeError(
            f"{component}: KNOWLEDGE_SSOT must be 'qdrant' (got {ssot!r}). "
            "This repository standard requires Qdrant as the knowledge SSoT."
        )


def resolve_embedding_provider(requested_provider: str, has_openai_api_key: bool) -> str:
    """Return an allowed provider based on repository policy."""
    provider = (requested_provider or "").strip().lower()
    if not provider or provider == "auto":
        provider = (os.environ.get("LLM_PROVIDER_DEFAULT", "ollama") or "ollama").strip().lower()

    if provider not in {"ollama", "openai"}:
        raise RuntimeError(
            f"Unsupported embedding provider {provider!r}. "
            "Allowed values: ollama, openai."
        )

    if provider == "openai":
        if not _as_bool(os.environ.get("ALLOW_PAID_LLM"), False):
            raise RuntimeError(
                "OpenAI embedding provider is blocked by policy. "
                "Set ALLOW_PAID_LLM=1 to enable paid LLM usage intentionally."
            )
        if not has_openai_api_key:
            raise RuntimeError("OPENAI_API_KEY missing while provider is set to openai.")

    return provider
