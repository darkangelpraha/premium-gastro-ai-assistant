from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from typing import Any

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("depoto_mcp")

BASE_URL = os.getenv("DEPOTO_BASE_URL", "https://server1.depoto.cz").rstrip("/")
USERNAME = os.getenv("DEPOTO_USERNAME")
PASSWORD = os.getenv("DEPOTO_PASSWORD")

CLIENT_ID = os.getenv(
    "DEPOTO_CLIENT_ID",
    "23_47gmzz2fhsw08gs0o480gks0o8c484kgw4sw0k00s0scsgs0cg",
)
CLIENT_SECRET = os.getenv(
    "DEPOTO_CLIENT_SECRET",
    "3jwvev86i30g4w0kckc4ss4gokc48sko4s884wsk0g44wcsg0w",
)

AUTH_TIMEOUT_SECONDS = float(os.getenv("DEPOTO_AUTH_TIMEOUT_SECONDS", "10"))
REQUEST_TIMEOUT_SECONDS = float(os.getenv("DEPOTO_REQUEST_TIMEOUT_SECONDS", "30"))

READ_ONLY = os.getenv("DEPOTO_READ_ONLY", "1").strip().lower() not in {"0", "false", "no"}

MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio").strip().lower()
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
MCP_PATH = os.getenv("MCP_PATH", "/mcp/")

mcp = FastMCP("Depoto GraphQL")


class OAuthTokenCache:
    def __init__(self) -> None:
        self._token: str | None = None
        self._expires_at: float = 0.0
        self._lock = asyncio.Lock()

    def _is_valid(self) -> bool:
        return self._token is not None and time.time() < self._expires_at

    async def get(self) -> str:
        if self._is_valid():
            return self._token or ""

        async with self._lock:
            if self._is_valid():
                return self._token or ""

            token, expires_in = await _oauth_password_grant()
            self._token = token
            self._expires_at = time.time() + max(int(expires_in) - 30, 60)
            return token

    async def invalidate(self) -> None:
        async with self._lock:
            self._token = None
            self._expires_at = 0.0


TOKEN_CACHE = OAuthTokenCache()


def _require_creds() -> None:
    if not USERNAME or not PASSWORD:
        raise RuntimeError("Missing DEPOTO_USERNAME or DEPOTO_PASSWORD.")


async def _oauth_password_grant() -> tuple[str, int]:
    _require_creds()

    url = f"{BASE_URL}/oauth/v2/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "password",
        "username": USERNAME,
        "password": PASSWORD,
    }

    async with httpx.AsyncClient(timeout=AUTH_TIMEOUT_SECONDS, follow_redirects=True) as client:
        resp = await client.post(
            url,
            data=data,
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        payload = resp.json()

    token = payload.get("access_token")
    expires_in = payload.get("expires_in")
    if not token or not expires_in:
        raise RuntimeError("Depoto OAuth response missing access_token/expires_in.")

    logger.info("Depoto OAuth token obtained.")
    return str(token), int(expires_in)


async def _graphql_request(
    query: str,
    variables: dict[str, Any] | None,
    operation_name: str | None,
) -> httpx.Response:
    token = await TOKEN_CACHE.get()

    url = f"{BASE_URL}/graphql"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {token}",
    }

    body: dict[str, Any] = {"query": query}
    if variables is not None:
        body["variables"] = variables
    if operation_name:
        body["operationName"] = operation_name

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=True) as client:
        resp = await client.post(url, headers=headers, json=body)

    if resp.status_code != 401:
        return resp

    logger.info("Depoto returned 401; refreshing token and retrying once.")
    await TOKEN_CACHE.invalidate()

    token2 = await TOKEN_CACHE.get()
    headers["Authorization"] = f"Bearer {token2}"

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=True) as client:
        resp2 = await client.post(url, headers=headers, json=body)

    return resp2


def _truncate(s: str, max_len: int) -> str:
    if len(s) <= max_len:
        return s
    return s[:max_len] + "\n...[truncated]..."


def _looks_like_mutation(query: str) -> bool:
    q = query.lower()
    return "mutation" in q


@mcp.tool()
async def depoto_graphql(
    query: str,
    variables: dict[str, Any] | None = None,
    operation_name: str | None = None,
) -> str:
    if READ_ONLY and _looks_like_mutation(query):
        return "Write operations are disabled (DEPOTO_READ_ONLY=1)."

    try:
        resp = await _graphql_request(query=query, variables=variables, operation_name=operation_name)
        body = _truncate(resp.text, int(os.getenv("DEPOTO_MAX_RESPONSE_CHARS", "200000")))
        return f"Status: {resp.status_code}\nResponse: {body}"
    except httpx.HTTPStatusError as e:
        body = _truncate(e.response.text, 20000)
        return f"HTTP error: {e.response.status_code}\nResponse: {body}"
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


if __name__ == "__main__":
    if MCP_TRANSPORT == "http":
        mcp.run(transport="http", host=MCP_HOST, port=MCP_PORT, path=MCP_PATH)
    else:
        mcp.run()
