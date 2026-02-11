from __future__ import annotations

import argparse
import base64
import datetime as _dt
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


@dataclass(frozen=True)
class Address:
    city: str
    street: str | None = None
    zip: str | None = None
    city_part: str | None = None
    house_num: str | None = None


@dataclass(frozen=True)
class Partner:
    name: str
    address: Address
    phone: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    registration_code: str | None = None
    vat_code: str | None = None


@dataclass(frozen=True)
class Shipment:
    external_id: str
    discharge: Partner
    kg: float
    pack_id: int
    pack_quantity: int
    discharge_aviso: bool = False
    note_discharge: str | None = None
    label: str | None = None


class TopTransError(RuntimeError):
    pass


class TopTransClient:
    def __init__(
        self,
        *,
        base_url: str,
        username: str,
        password: str,
        fmt: str = "json",
        timeout_seconds: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._fmt = fmt.strip().lower()
        if self._fmt not in {"json", "xml"}:
            raise ValueError("fmt must be json or xml")
        self._auth = (username, password)
        self._timeout_seconds = timeout_seconds

    def _post(self, path: str, payload: dict[str, Any] | None, *, accept: str) -> requests.Response:
        clean = path.strip().lstrip("/")
        if not clean:
            raise ValueError("path is required")

        url = f"{self._base_url}/api/{self._fmt}/{clean}/"
        return requests.post(
            url,
            json=payload or {},
            auth=self._auth,
            timeout=self._timeout_seconds,
            headers={"Accept": accept},
        )

    def call(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = self._post(path, payload, accept="application/json")

        # TopTrans returns JSON even on errors; keep body for debugging.
        try:
            data = resp.json()
        except Exception as e:
            raise TopTransError(f"Non-JSON response from TopTrans ({resp.status_code}): {e}") from e

        if resp.status_code >= 400:
            raise TopTransError(f"TopTrans HTTP {resp.status_code}: {json.dumps(data, ensure_ascii=False)[:2000]}")

        status = str(data.get("status") or "").lower()
        if status and status not in {"ok", "success"}:
            raise TopTransError(f"TopTrans status={status}: {json.dumps(data, ensure_ascii=False)[:2000]}")

        if data.get("errors"):
            raise TopTransError(f"TopTrans errors: {json.dumps(data.get('errors'), ensure_ascii=False)[:2000]}")

        return data

    def call_pdf(self, path: str, payload: dict[str, Any] | None = None) -> bytes:
        """Call an endpoint that returns a PDF file body (not JSON).

        Some TopTrans API methods return raw PDF bytes (e.g. `order/print-unsent-labels`).
        In error cases the API often still returns JSON, so we attempt to parse and raise.
        """

        resp = self._post(path, payload, accept="application/pdf")

        if resp.status_code >= 400:
            try:
                data = resp.json()
                raise TopTransError(
                    f"TopTrans HTTP {resp.status_code}: {json.dumps(data, ensure_ascii=False)[:2000]}"
                )
            except TopTransError:
                raise
            except Exception:
                raise TopTransError(f"TopTrans HTTP {resp.status_code}: {resp.text[:2000]}")

        ct = (resp.headers.get("content-type") or "").lower()
        if "application/pdf" in ct or resp.content.startswith(b"%PDF"):
            return resp.content

        # Unexpected: try JSON and raise a better error.
        try:
            data = resp.json()
        except Exception as e:
            raise TopTransError(f"Unexpected non-PDF response from TopTrans: {e}") from e
        status = str(data.get("status") or "").lower()
        raise TopTransError(f"TopTrans status={status}: {json.dumps(data, ensure_ascii=False)[:2000]}")

    def register_pack(self) -> dict[int, str]:
        data = self.call("register/pack")
        raw = data.get("data") or {}
        out: dict[int, str] = {}
        if isinstance(raw, dict):
            for k, v in raw.items():
                try:
                    out[int(k)] = str(v)
                except Exception:
                    continue
        return out


def _require_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise TopTransError(f"Missing env var: {name}")
    return v


def _clean_external_id(v: str) -> str:
    s = (v or "").strip()
    if not s:
        raise TopTransError("external_id is required")
    return s


def _to_float(v: Any, *, field: str) -> float:
    try:
        return float(v)
    except Exception as e:
        raise TopTransError(f"Invalid {field}: {v!r}") from e


def _to_int(v: Any, *, field: str) -> int:
    try:
        return int(v)
    except Exception as e:
        raise TopTransError(f"Invalid {field}: {v!r}") from e


def _bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    s = str(v or "").strip().lower()
    return s in {"1", "true", "yes", "y", "on"}


def _parse_partner(obj: dict[str, Any]) -> Partner:
    name = str(obj.get("name") or "").strip()
    if not name:
        raise TopTransError("partner.name is required")

    addr_obj = obj.get("address")
    if not isinstance(addr_obj, dict):
        raise TopTransError("partner.address is required")

    city = str(addr_obj.get("city") or "").strip()
    if not city:
        raise TopTransError("partner.address.city is required")

    address = Address(
        city=city,
        street=(str(addr_obj.get("street")).strip() if addr_obj.get("street") else None),
        zip=(str(addr_obj.get("zip")).strip() if addr_obj.get("zip") else None),
        city_part=(str(addr_obj.get("city_part")).strip() if addr_obj.get("city_part") else None),
        house_num=(str(addr_obj.get("house_num")).strip() if addr_obj.get("house_num") else None),
    )

    phone = (str(obj.get("phone")).strip() if obj.get("phone") else None)
    email = (str(obj.get("email")).strip() if obj.get("email") else None)
    first_name = (str(obj.get("first_name")).strip() if obj.get("first_name") else None)
    last_name = (str(obj.get("last_name")).strip() if obj.get("last_name") else None)

    registration_code = (str(obj.get("registration_code")).strip() if obj.get("registration_code") else None)
    vat_code = (str(obj.get("vat_code")).strip() if obj.get("vat_code") else None)

    return Partner(
        name=name,
        address=address,
        phone=phone,
        email=email,
        first_name=first_name,
        last_name=last_name,
        registration_code=registration_code,
        vat_code=vat_code,
    )


def _parse_shipment(obj: dict[str, Any], *, default_pack_id: int, default_term_id: int) -> tuple[Shipment, int]:
    external_id = _clean_external_id(str(obj.get("external_id") or ""))

    discharge_obj = obj.get("discharge")
    if not isinstance(discharge_obj, dict):
        raise TopTransError(f"{external_id}: discharge is required")

    discharge = _parse_partner(discharge_obj)

    kg = _to_float(obj.get("kg"), field=f"{external_id}.kg")
    if kg <= 0:
        raise TopTransError(f"{external_id}: kg must be > 0")

    pack_id = _to_int(obj.get("pack_id", default_pack_id), field=f"{external_id}.pack_id")
    pack_quantity = _to_int(obj.get("pack_quantity", 1), field=f"{external_id}.pack_quantity")
    if pack_quantity <= 0 or pack_quantity > 250:
        raise TopTransError(f"{external_id}: pack_quantity must be 1..250")

    discharge_aviso = _bool(obj.get("discharge_aviso", False))
    note_discharge = (str(obj.get("note_discharge")).strip() if obj.get("note_discharge") else None)

    # label is optional but very useful for idempotence and later lookup.
    label = str(obj.get("label") or external_id).strip()[:40]

    term_id = _to_int(obj.get("term_id", default_term_id), field=f"{external_id}.term_id")

    return (
        Shipment(
            external_id=external_id,
            discharge=discharge,
            kg=kg,
            pack_id=pack_id,
            pack_quantity=pack_quantity,
            discharge_aviso=discharge_aviso,
            note_discharge=note_discharge,
            label=label,
        ),
        term_id,
    )


def _shipments_from_json(path: Path, *, default_pack_id: int, default_term_id: int) -> list[tuple[Shipment, int]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("shipments"), list):
        raise TopTransError("Input JSON must be an object with key shipments as a list")

    out: list[tuple[Shipment, int]] = []
    for i, raw in enumerate(data.get("shipments") or []):
        if not isinstance(raw, dict):
            raise TopTransError(f"shipments[{i}] must be an object")
        out.append(_parse_shipment(raw, default_pack_id=default_pack_id, default_term_id=default_term_id))
    return out


def _load_sent_external_ids(audit_path: Path) -> set[str]:
    if not audit_path.exists():
        return set()
    sent: set[str] = set()
    for line in audit_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("event") != "sent":
            continue
        ext = obj.get("external_id")
        if isinstance(ext, str) and ext:
            sent.add(ext)
    return sent


def _write_audit(audit_path: Path, event: dict[str, Any]) -> None:
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def _load_completed_external_ids(audit_path: Path) -> set[str]:
    """Return external_ids that were successfully processed (draft labels or sent)."""

    if not audit_path.exists():
        return set()
    done: set[str] = set()
    for line in audit_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("event") not in {"sent", "printed_unsent"}:
            continue
        ext = obj.get("external_id")
        if isinstance(ext, str) and ext:
            done.add(ext)
    return done


def _now_slug() -> str:
    return _dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def _select_pack_id(pack_map: dict[int, str], preferred_names: list[str]) -> int | None:
    norm_pref = [p.strip().lower() for p in preferred_names if p.strip()]
    for pid, name in pack_map.items():
        n = str(name).strip().lower()
        if n in norm_pref:
            return pid
    # Best effort: some packs are like "BALIK"; prefer substring match.
    for pid, name in pack_map.items():
        n = str(name).strip().lower()
        for p in norm_pref:
            if p and p in n:
                return pid
    return None


def _decode_toptrans_files(resp_data: dict[str, Any], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)

    files = resp_data.get("files")
    if files is None:
        # Some deployments nest under data
        files = (resp_data.get("data") or {}).get("files")

    if not isinstance(files, list):
        return []

    written: list[Path] = []
    for i, fobj in enumerate(files):
        if not isinstance(fobj, dict):
            continue
        filename = str(fobj.get("filename") or f"labels_{i}.pdf").strip() or f"labels_{i}.pdf"
        b64 = str(fobj.get("data") or "").strip()
        if not b64:
            continue
        try:
            blob = base64.b64decode(b64)
        except Exception:
            continue

        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", filename)
        p = out_dir / safe_name
        p.write_bytes(blob)
        written.append(p)

    return written


def run(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Create TopTrans labels from a JSON shipment list")
    ap.add_argument("--input", required=True, help="Path to JSON file")
    ap.add_argument("--out", default="ops/_local/toptrans/out", help="Output directory for PDFs")
    ap.add_argument(
        "--audit",
        default="ops/_local/toptrans/toptrans_audit.jsonl",
        help="JSONL audit log (used for idempotence)",
    )
    ap.add_argument("--term-id", type=int, default=int(os.getenv("TOPTRANS_TERM_ID", "1")), help="Default term_id")
    ap.add_argument(
        "--pack-id",
        type=int,
        default=int(os.getenv("TOPTRANS_PACK_ID", "0") or "0"),
        help="Default pack_id (0 = auto-detect)",
    )
    ap.add_argument(
        "--prefer-pack",
        default=os.getenv("TOPTRANS_PREFER_PACK", "BALIK,KUS"),
        help="Comma-separated pack names to prefer when auto-detecting",
    )
    ap.add_argument(
        "--mode",
        choices=("draft", "send"),
        default=(os.getenv("TOPTRANS_MODE", "draft").strip().lower() or "draft"),
        help="draft: create unsent orders + print labels; send: send orders + get labels",
    )
    ap.add_argument(
        "--position",
        type=int,
        default=int(os.getenv("TOPTRANS_POSITION", "0")),
        help="Label start position on A4 sheet (0..13)",
    )
    ap.add_argument(
        "--skip-price",
        action="store_true",
        help="Skip `order/price` (not recommended if you need cost analytics).",
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=int(os.getenv("TOPTRANS_LIMIT", "0")),
        help="Process only first N shipments from input (0 = all).",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print planned API calls without creating orders",
    )

    args = ap.parse_args(argv)

    audit_path = Path(args.audit)
    already_done = _load_completed_external_ids(audit_path)

    pack_id_arg = int(args.pack_id)
    auto_pack = pack_id_arg <= 0

    shipments = _shipments_from_json(
        Path(args.input),
        default_pack_id=(1 if auto_pack else pack_id_arg),
        default_term_id=int(args.term_id),
    )

    to_process: list[tuple[Shipment, int]] = []
    for sh, term_id in shipments:
        if sh.external_id in already_done:
            continue
        to_process.append((sh, term_id))

    if args.limit and args.limit > 0:
        to_process = to_process[: int(args.limit)]

    if not to_process:
        print("NOTHING_TO_DO")
        return 0

    if args.dry_run:
        print(f"DRY_RUN count={len(to_process)}")
        for sh, term_id in to_process:
            print(f"- {sh.external_id} term_id={term_id} kg={sh.kg} pack_id={sh.pack_id} qty={sh.pack_quantity} city={sh.discharge.address.city}")
        return 0

    base_url = os.getenv("TOPTRANS_BASE_URL", "https://zp.toptrans.cz")
    username = os.getenv("TOPTRANS_USERNAME")
    password = os.getenv("TOPTRANS_PASSWORD")
    if not username or not password:
        raise TopTransError("Missing TOPTRANS_USERNAME/TOPTRANS_PASSWORD")

    client = TopTransClient(
        base_url=base_url,
        username=username,
        password=password,
        fmt=os.getenv("TOPTRANS_FORMAT", "json"),
        timeout_seconds=float(os.getenv("TOPTRANS_TIMEOUT_SECONDS", "30")),
    )

    pack_map = client.register_pack()
    preferred = [p.strip() for p in str(args.prefer_pack or "").split(",")]

    if auto_pack:
        picked = _select_pack_id(pack_map, preferred)
        default_pack_id = picked if picked is not None else 1
        shipments = _shipments_from_json(
            Path(args.input),
            default_pack_id=default_pack_id,
            default_term_id=int(args.term_id),
        )
        # Rebuild the processing list now that pack_id is known.
        to_process = [(sh, term_id) for (sh, term_id) in shipments if sh.external_id not in already_done]
        if args.limit and args.limit > 0:
            to_process = to_process[: int(args.limit)]
        if not to_process:
            print("NOTHING_TO_DO")
            return 0

    position = int(args.position)
    if position < 0 or position > 13:
        raise TopTransError("--position must be in range 0..13")

    loading_city = os.getenv("TOPTRANS_LOADING_CITY")
    loading_zip = os.getenv("TOPTRANS_LOADING_ZIP")

    saved_ids: list[int] = []
    ext_by_id: dict[int, str] = {}
    price_by_ext: dict[str, Any] = {}

    for sh, term_id in to_process:
        if not args.skip_price:
            if not loading_city or not loading_zip:
                raise TopTransError("Missing TOPTRANS_LOADING_CITY/TOPTRANS_LOADING_ZIP (required for order/price)")
            if not sh.discharge.address.zip:
                raise TopTransError(f"Missing discharge.address.zip for external_id={sh.external_id}")

            price_payload: dict[str, Any] = {
                "term_id": term_id,
                "loading_address_city": loading_city,
                "loading_address_zip": loading_zip,
                "discharge_address_city": sh.discharge.address.city,
                "discharge_address_zip": sh.discharge.address.zip,
                "kg": sh.kg,
                "discharge_aviso": 1 if sh.discharge_aviso else 0,
            }
            price_resp = client.call("order/price", price_payload)
            price_data = price_resp.get("data") if isinstance(price_resp, dict) else None
            price_by_ext[sh.external_id] = price_data
            _write_audit(
                audit_path,
                {
                    "event": "priced",
                    "external_id": sh.external_id,
                    "price": price_data,
                },
            )

        payload: dict[str, Any] = {
            "term_id": term_id,
            "loading_select": 1,
            "discharge": {
                "name": sh.discharge.name,
                "first_name": sh.discharge.first_name,
                "last_name": sh.discharge.last_name,
                "phone": sh.discharge.phone,
                "email": sh.discharge.email,
                "registration_code": sh.discharge.registration_code,
                "vat_code": sh.discharge.vat_code,
                "address": {
                    "city": sh.discharge.address.city,
                    "city_part": sh.discharge.address.city_part,
                    "street": sh.discharge.address.street,
                    "house_num": sh.discharge.address.house_num,
                    "zip": sh.discharge.address.zip,
                },
            },
            "kg": sh.kg,
            "packs": [
                {
                    "pack_id": sh.pack_id,
                    "quantity": sh.pack_quantity,
                    "description": sh.label,
                }
            ],
            "discharge_aviso": 1 if sh.discharge_aviso else 0,
            "note_discharge": sh.note_discharge,
            "label": sh.label,
        }

        # Remove None values for a cleaner payload.
        def _strip_nones(o: Any) -> Any:
            if isinstance(o, dict):
                return {k: _strip_nones(v) for k, v in o.items() if v is not None and _strip_nones(v) is not None}
            if isinstance(o, list):
                return [x for x in (_strip_nones(v) for v in o) if x is not None]
            return o

        payload = _strip_nones(payload)

        resp = client.call("order/save", payload)
        data = resp.get("data")

        if isinstance(data, dict) and "id" in data:
            order_id = _to_int(data.get("id"), field="order.save.id")
        else:
            order_id = _to_int(data, field="order.save.data")

        saved_ids.append(order_id)
        ext_by_id[order_id] = sh.external_id

        _write_audit(
            audit_path,
            {
                "event": "saved",
                "external_id": sh.external_id,
                "order_id": order_id,
            },
        )

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "draft":
        pdf_blob = client.call_pdf(
            "order/print-unsent-labels",
            {
                "ids": saved_ids,
                "position": position,
            },
        )
        pdf_path = out_dir / f"labels_unsent_{_now_slug()}.pdf"
        pdf_path.write_bytes(pdf_blob)

        for order_id in saved_ids:
            ext = ext_by_id.get(order_id)
            _write_audit(
                audit_path,
                {
                    "event": "printed_unsent",
                    "external_id": ext,
                    "order_id": order_id,
                    "pdf": str(pdf_path),
                    "price": price_by_ext.get(ext or ""),
                },
            )

        print(f"DRAFT count={len(saved_ids)} pdf=1 out={pdf_path}")
        return 0

    send_resp = client.call(
        "order/send",
        {
            "ids": saved_ids,
            "options": {
                "position": position,
            },
        },
    )

    data_obj = send_resp.get("data") if isinstance(send_resp, dict) else None
    if not isinstance(data_obj, dict):
        data_obj = {}

    pdfs = _decode_toptrans_files(data_obj, out_dir)

    batch_id = data_obj.get("orderListObj")

    order_numbers = data_obj.get("order_numbers") or data_obj.get("orderNumbers") or []
    item_numbers = data_obj.get("item_numbers") or data_obj.get("itemNumbers") or []
    if not isinstance(order_numbers, list):
        order_numbers = []
    if not isinstance(item_numbers, list):
        item_numbers = []

    for i, order_id in enumerate(saved_ids):
        ext = ext_by_id.get(order_id)
        order_number = order_numbers[i] if i < len(order_numbers) else None
        item_number = item_numbers[i] if i < len(item_numbers) else None
        _write_audit(
            audit_path,
            {
                "event": "sent",
                "external_id": ext,
                "order_id": order_id,
                "batch_id": batch_id,
                "order_number": order_number,
                "item_number": item_number,
                "price": price_by_ext.get(ext or ""),
                "pdfs": [str(p) for p in pdfs],
            },
        )

    print(f"SENT count={len(saved_ids)} batch_id={batch_id} pdfs={len(pdfs)}")
    return 0


def main() -> None:
    try:
        raise SystemExit(run(sys.argv[1:]))
    except TopTransError as e:
        print(f"ERROR: {e}")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
