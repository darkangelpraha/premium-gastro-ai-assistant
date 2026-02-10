from __future__ import annotations

import base64
from pathlib import Path

import pytest

from tools.logistics.toptrans_labels import (
    TopTransError,
    _decode_toptrans_files,
    _parse_partner,
    _parse_shipment,
    _select_pack_id,
)


def test_parse_partner_requires_name_and_city() -> None:
    with pytest.raises(TopTransError):
        _parse_partner({"address": {"city": "Praha"}})

    with pytest.raises(TopTransError):
        _parse_partner({"name": "X", "address": {}})

    p = _parse_partner({"name": "X", "address": {"city": "Praha"}})
    assert p.name == "X"
    assert p.address.city == "Praha"


def test_parse_shipment_defaults_label_and_pack() -> None:
    sh, term_id = _parse_shipment(
        {
            "external_id": "BJ-1",
            "kg": 1,
            "discharge": {"name": "X", "address": {"city": "Praha"}},
        },
        default_pack_id=1,
        default_term_id=1,
    )

    assert sh.external_id == "BJ-1"
    assert sh.label == "BJ-1"
    assert sh.pack_id == 1
    assert sh.pack_quantity == 1
    assert term_id == 1


def test_select_pack_id_prefers_exact_then_substring() -> None:
    pack_map = {1: "KUS", 2: "KARTON", 99: "BALIK"}

    assert _select_pack_id(pack_map, ["BALIK"]) == 99
    assert _select_pack_id(pack_map, ["bal"]) == 99
    assert _select_pack_id(pack_map, ["unknown"]) is None


def test_decode_files_writes_pdf(tmp_path: Path) -> None:
    payload = {
        "files": [
            {
                "filename": "labels.pdf",
                "data": base64.b64encode(b"%PDF-1.4\n").decode("ascii"),
            }
        ]
    }

    written = _decode_toptrans_files(payload, tmp_path)
    assert len(written) == 1
    assert written[0].name == "labels.pdf"
    assert written[0].read_bytes().startswith(b"%PDF")
