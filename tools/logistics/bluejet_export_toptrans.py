#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import parse, request


class BlueJetError(RuntimeError):
    pass


_GUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def _is_guid(v: Any) -> bool:
    return isinstance(v, str) and bool(_GUID_RE.match(v.strip()))


def _load_dotenv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _require_env(name: str, env: dict[str, str]) -> str:
    v = env.get(name) or os.getenv(name)
    if not v:
        raise BlueJetError(f"Missing env var: {name}")
    return v


@dataclass(frozen=True)
class BlueJetCreds:
    base_url: str
    token_id: str
    token_hash: str


class BlueJetClient:
    def __init__(self, creds: BlueJetCreds, *, timeout_seconds: float = 30.0) -> None:
        self._base = creds.base_url.rstrip("/")
        self._token_id = creds.token_id
        self._token_hash = creds.token_hash
        self._timeout_seconds = timeout_seconds
        self._token: str | None = None

    def _auth_token(self) -> str:
        if self._token:
            return self._token

        url = f"{self._base}/api/v1/users/authenticate"
        payload = json.dumps({"tokenID": self._token_id, "tokenHash": self._token_hash}).encode("utf-8")
        req = request.Request(
            url,
            data=payload,
            headers={"content-type": "application/json"},
            method="POST",
        )
        raw = request.urlopen(req, timeout=self._timeout_seconds).read().decode("utf-8", "replace")
        obj = json.loads(raw)
        tok = obj.get("token")
        if not isinstance(tok, str) or not tok.strip():
            raise BlueJetError(f"BlueJet auth failed: {raw[:300]}")
        self._token = tok
        return tok

    def data(
        self,
        *,
        no: int,
        limit: int = 1,
        offset: int = 0,
        sort: str | None = None,
        condition: str | None = None,
    ) -> dict[str, Any]:
        qs: dict[str, str] = {
            "no": str(no),
            "limit": str(limit),
            "offset": str(offset),
        }
        if sort:
            qs["sort"] = sort
        if condition:
            qs["condition"] = condition

        url = f"{self._base}/api/v1/Data?{parse.urlencode(qs, safe='|=,')}"
        req = request.Request(url, headers={"X-Token": self._auth_token()})
        raw = request.urlopen(req, timeout=self._timeout_seconds).read().decode("utf-8", "replace")
        try:
            return json.loads(raw)
        except Exception as e:
            raise BlueJetError(f"BlueJet returned non-JSON: {e}: {raw[:300]}") from e

    @staticmethod
    def row_to_dict(row: dict[str, Any]) -> dict[str, Any]:
        cols = row.get("columns")
        if not isinstance(cols, list):
            return {}
        out: dict[str, Any] = {}
        for c in cols:
            if not isinstance(c, dict):
                continue
            name = c.get("name")
            if not isinstance(name, str) or not name:
                continue
            out[name] = c.get("value")
        return out


def _pick_shipping_address_id(offer: dict[str, Any]) -> str:
    candidates = [
        offer.get("prijemcezboziadsupl"),
        offer.get("mainprijemcezboziadsupl"),
        offer.get("prijemadd"),
        offer.get("prijemfakturyadd"),
    ]
    for v in candidates:
        if _is_guid(v):
            return str(v).strip()
    raise BlueJetError("Offer does not contain a usable shipping address id (expected GUID in prijemcezboziadsupl)")


def build_toptrans_shipments(
    *,
    offer_code: str,
    address: dict[str, Any],
    kg: float,
    pack_quantity: int,
) -> dict[str, Any]:
    name = str(address.get("recipient") or "").strip()
    city = str(address.get("town") or "").strip()
    street = str(address.get("street1") or "").strip() or None
    zip_code = str(address.get("zipcode") or "").strip() or None

    if not name:
        raise BlueJetError("Address is missing recipient (name)")
    if not city:
        raise BlueJetError("Address is missing town (city)")
    if kg <= 0:
        raise BlueJetError("kg must be > 0")
    if pack_quantity <= 0:
        raise BlueJetError("pack_quantity must be > 0")

    return {
        "shipments": [
            {
                "external_id": offer_code,
                "discharge": {
                    "name": name,
                    "address": {
                        "city": city,
                        "street": street,
                        "zip": zip_code,
                    },
                },
                "kg": kg,
                "pack_quantity": pack_quantity,
                "label": offer_code,
            }
        ]
    }


def run(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Export a BlueJet offer recipient as a TopTrans shipment JSON file")
    ap.add_argument("--bluejet-env-file", help="Optional .env file containing BlueJet API creds")
    ap.add_argument("--offer-code", required=True, help="BlueJet offer code (e.g. 52/2026)")
    ap.add_argument("--out", default="ops/_local/toptrans/shipments.json", help="Output JSON file")
    ap.add_argument("--kg", type=float, default=float(os.getenv("TOPTRANS_DEFAULT_KG", "10")), help="Shipment weight")
    ap.add_argument(
        "--pack-quantity",
        type=int,
        default=int(os.getenv("TOPTRANS_PACK_QUANTITY", "1")),
        help="Number of packages (labels) for this shipment",
    )
    args = ap.parse_args(argv)

    env: dict[str, str] = {}
    if args.bluejet_env_file:
        env.update(_load_dotenv(Path(args.bluejet_env_file)))

    creds = BlueJetCreds(
        base_url=_require_env("BLUEJET_BASE_URL", env),
        token_id=_require_env("BLUEJET_API_TOKEN_ID", env),
        token_hash=_require_env("BLUEJET_API_TOKEN_HASH", env),
    )
    bj = BlueJetClient(creds)

    offer_code = str(args.offer_code).strip()
    if not offer_code:
        raise BlueJetError("offer-code is required")

    offer_resp = bj.data(no=293, limit=1, offset=0, condition=f"kodnabidky|=|{offer_code}")
    rows = offer_resp.get("rows")
    if not isinstance(rows, list) or not rows:
        raise BlueJetError(f"Offer not found: {offer_code}")
    offer = bj.row_to_dict(rows[0])

    addr_id = _pick_shipping_address_id(offer)
    addr_resp = bj.data(no=243, limit=1, offset=0, condition=f"addressid|=|{addr_id}")
    addr_rows = addr_resp.get("rows")
    if not isinstance(addr_rows, list) or not addr_rows:
        raise BlueJetError(f"Address not found: {addr_id}")
    address = bj.row_to_dict(addr_rows[0])

    out = build_toptrans_shipments(
        offer_code=offer_code,
        address=address,
        kg=float(args.kg),
        pack_quantity=int(args.pack_quantity),
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(out_path))
    return 0


def main() -> None:
    try:
        raise SystemExit(run(sys.argv[1:]))
    except BlueJetError as e:
        print(f"ERROR: {e}")
        raise SystemExit(2)


if __name__ == "__main__":
    main()

