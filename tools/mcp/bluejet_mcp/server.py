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
logger = logging.getLogger("bluejet_mcp")

API_BASE_URL = os.getenv("BLUEJET_BASE_URL", "https://czeco.bluejet.cz").rstrip("/")
TOKEN_ID = os.getenv("BLUEJET_API_TOKEN_ID")
TOKEN_HASH = os.getenv("BLUEJET_API_TOKEN_HASH")

# Safe default: disallow writes unless explicitly enabled.
READ_ONLY = os.getenv("BLUEJET_READ_ONLY", "1").strip().lower() not in {"0", "false", "no"}

# BlueJet docs state the auth token is valid for 24 hours.
# Default to 23h to reduce surprises from clock drift.
TOKEN_TTL_SECONDS = int(os.getenv("BLUEJET_TOKEN_TTL_SECONDS", str(23 * 60 * 60)))

AUTH_TIMEOUT_SECONDS = float(os.getenv("BLUEJET_AUTH_TIMEOUT_SECONDS", "10"))
REQUEST_TIMEOUT_SECONDS = float(os.getenv("BLUEJET_REQUEST_TIMEOUT_SECONDS", "30"))

# Transport config for running in Docker as a stable HTTP MCP endpoint.
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio").strip().lower()
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
MCP_PATH = os.getenv("MCP_PATH", "/mcp/")

mcp = FastMCP("BlueJet CRM")


class TokenCache:
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

            token = await authenticate_bluejet()
            self._token = token
            self._expires_at = time.time() + max(TOKEN_TTL_SECONDS, 60)
            return token

    async def invalidate(self) -> None:
        async with self._lock:
            self._token = None
            self._expires_at = 0.0


TOKEN_CACHE = TokenCache()


async def authenticate_bluejet() -> str:
    if not TOKEN_ID or not TOKEN_HASH:
        raise RuntimeError(
            "Missing BLUEJET_API_TOKEN_ID or BLUEJET_API_TOKEN_HASH. "
            "Set them as environment variables."
        )

    url = f"{API_BASE_URL}/api/v1/users/authenticate"
    payload = {"tokenID": TOKEN_ID, "tokenHash": TOKEN_HASH}

    async with httpx.AsyncClient(
        timeout=AUTH_TIMEOUT_SECONDS,
        follow_redirects=True,
        headers={"Accept": "application/json"},
    ) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    token = data.get("token")
    if data.get("succeeded") and token:
        logger.info("BlueJet authentication ok.")
        return str(token)

    msg = data.get("message") or "unknown error"
    raise RuntimeError(f"BlueJet authentication failed: {msg}")


async def _do_request(
    method: str,
    endpoint: str,
    *,
    payload: dict[str, Any] | None,
    params: dict[str, Any] | None,
) -> httpx.Response:
    token = await TOKEN_CACHE.get()

    clean_endpoint = endpoint.lstrip("/")
    url = f"{API_BASE_URL}/{clean_endpoint}"

    headers: dict[str, str] = {
        "Accept": "application/json",
        "X-Token": token,
    }

    if payload is not None:
        headers["Content-Type"] = "application/json"

    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT_SECONDS,
        follow_redirects=True,
    ) as client:
        resp = await client.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=payload,
            params=params,
        )

    if resp.status_code != 401:
        return resp

    logger.info("BlueJet returned 401; refreshing token and retrying once.")
    await TOKEN_CACHE.invalidate()

    token2 = await TOKEN_CACHE.get()
    headers["X-Token"] = token2

    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT_SECONDS,
        follow_redirects=True,
    ) as client:
        resp2 = await client.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=payload,
            params=params,
        )

    return resp2


def _truncate(s: str, max_len: int) -> str:
    if len(s) <= max_len:
        return s
    return s[:max_len] + "\n...[truncated]..."


@mcp.tool()
async def bluejet_request(
    method: str,
    endpoint: str,
    payload: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> str:
    """Raw BlueJet REST request (safe by default).

    method: GET/POST/PUT/DELETE
    endpoint: API path without base URL, e.g. api/v1/Data?no=222
    payload: JSON body for POST/PUT
    params: query params as dict
    """

    m = method.strip().upper()
    if READ_ONLY and m != "GET":
        return "Write operations are disabled (BLUEJET_READ_ONLY=1)."

    try:
        resp = await _do_request(m, endpoint, payload=payload, params=params)
        body = _truncate(resp.text, int(os.getenv("BLUEJET_MAX_RESPONSE_CHARS", "200000")))
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

