from __future__ import annotations

import os
import sys
from typing import Any

import httpx


def _need(name: str) -> str:
    v = os.getenv(name)
    if v:
        return v
    print(f"Missing env var: {name}", file=sys.stderr)
    raise SystemExit(2)


def _truncate(s: str, n: int = 1200) -> str:
    if len(s) <= n:
        return s
    return s[:n] + "\n...[truncated]..."


def _oauth_token(base_url: str) -> str:
    url = f"{base_url}/oauth/v2/token"
    data = {
        "client_id": _need("DEPOTO_CLIENT_ID"),
        "client_secret": _need("DEPOTO_CLIENT_SECRET"),
        "grant_type": "password",
        "username": _need("DEPOTO_USERNAME"),
        "password": _need("DEPOTO_PASSWORD"),
    }

    timeout = float(os.getenv("DEPOTO_AUTH_TIMEOUT_SECONDS", "10"))

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        r = client.post(url, data=data, headers={"Accept": "application/json"})

    if r.status_code >= 400:
        raise RuntimeError(f"OAuth failed HTTP {r.status_code}: {_truncate(r.text)}")

    payload = r.json()
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"OAuth response missing access_token: {_truncate(r.text)}")
    return str(token)


def _graphql(base_url: str, token: str, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{base_url}/graphql"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {token}",
    }

    body: dict[str, Any] = {"query": query}
    if variables is not None:
        body["variables"] = variables

    timeout = float(os.getenv("DEPOTO_REQUEST_TIMEOUT_SECONDS", "30"))

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        r = client.post(url, headers=headers, json=body)

    if r.status_code >= 400:
        raise RuntimeError(f"GraphQL failed HTTP {r.status_code}: {_truncate(r.text)}")

    return r.json()


def main() -> int:
    base_url = os.getenv("DEPOTO_BASE_URL", "https://server1.depoto.cz").rstrip("/")

    token = _oauth_token(base_url)

    # Minimal, read-only query that should always succeed in GraphQL.
    payload = _graphql(base_url, token, "query { __typename }")

    if payload.get("errors"):
        raise RuntimeError(f"GraphQL returned errors: {_truncate(str(payload.get("errors")))}")

    data = payload.get("data")
    if not isinstance(data, dict) or "__typename" not in data:
        raise RuntimeError(f"Unexpected GraphQL payload: {_truncate(str(payload))}")

    print("DEPOTO_SMOKE_OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"DEPOTO_SMOKE_FAIL: {type(e).__name__}: {e}", file=sys.stderr)
        raise SystemExit(1)
