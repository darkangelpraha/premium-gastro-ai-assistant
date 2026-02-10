from __future__ import annotations

import logging
import os
import sys
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
logger = logging.getLogger("toptrans_mcp")

BASE_URL = os.getenv("TOPTRANS_BASE_URL", "https://zp.toptrans.cz").rstrip("/")
API_FORMAT = os.getenv("TOPTRANS_FORMAT", "json").strip().lower()
USERNAME = os.getenv("TOPTRANS_USERNAME")
PASSWORD = os.getenv("TOPTRANS_PASSWORD")

TIMEOUT_SECONDS = float(os.getenv("TOPTRANS_TIMEOUT_SECONDS", "30"))

# Safe default: disallow mutating operations unless explicitly enabled.
READ_ONLY = os.getenv("TOPTRANS_READ_ONLY", "1").strip().lower() not in {"0", "false", "no"}

MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio").strip().lower()
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
MCP_PATH = os.getenv("MCP_PATH", "/mcp/")

mcp = FastMCP("TopTrans API")


def _require_creds() -> None:
    if not USERNAME or not PASSWORD:
        raise RuntimeError("Missing TOPTRANS_USERNAME or TOPTRANS_PASSWORD.")


def _normalize_format(fmt: str) -> str:
    f = (fmt or "").strip().lower()
    if f in {"json", "xml"}:
        return f
    raise ValueError("TOPTRANS_FORMAT must be json or xml")


def _is_potentially_mutating(path: str) -> bool:
    p = path.strip().lower().lstrip("/")

    # Conservative blocklist for safety.
    blocked = (
        "order/save",
        "order/send",
        "order/delete",
        "order/archive",
        "order/print-unsent-labels",
        "order/print-labels",
        "register/add",
        "register/delete",
        "register/update",
    )
    return any(p.startswith(b) for b in blocked)


def _truncate(s: str, max_len: int) -> str:
    if len(s) <= max_len:
        return s
    return s[:max_len] + "\n...[truncated]..."


@mcp.tool()
async def toptrans_call(
    path: str,
    payload: dict[str, Any] | None = None,
    fmt: str | None = None,
) -> str:
    """Call TopTrans ZP API.

    path: e.g. `order/price`, `order/save`, `order/search`
    payload: request body (dict)
    fmt: `json` or `xml` (defaults to TOPTRANS_FORMAT)

    Notes:
    - Uses HTTP Basic auth.
    - Safe-by-default: mutating calls are blocked unless TOPTRANS_READ_ONLY=0.
    """

    _require_creds()
    format_used = _normalize_format(fmt or API_FORMAT)

    if not path or not path.strip():
        return "Error: path is required"

    normalized_path = path.strip().lstrip("/")

    if READ_ONLY and _is_potentially_mutating(normalized_path):
        return "Write operations are disabled (TOPTRANS_READ_ONLY=1)."

    url = f"{BASE_URL}/api/{format_used}/{normalized_path}/"

    try:
        async with httpx.AsyncClient(
            timeout=TIMEOUT_SECONDS,
            follow_redirects=True,
            auth=(USERNAME, PASSWORD),
            headers={"Accept": "application/json"},
        ) as client:
            resp = await client.post(url, json=payload or {})

        body = _truncate(resp.text, int(os.getenv("TOPTRANS_MAX_RESPONSE_CHARS", "200000")))
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
