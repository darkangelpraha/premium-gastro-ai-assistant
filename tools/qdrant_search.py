#!/usr/bin/env python3
"""
Unified cross-reference search across all BlueJet Qdrant collections.

Usage:
    python3 tools/qdrant_search.py "Infinity"
    python3 tools/qdrant_search.py "Infinity" --emails
    python3 tools/qdrant_search.py --product "781053"
    python3 tools/qdrant_search.py --firmaid "uuid-..."

Cross-reference chain:
    Company (firmaid) → Contacts, Offers, Orders, Invoices, Emails
    Product (code)    → Orders (via productid in BJ line items)
"""

import sys
import json
import argparse
import urllib.request
from typing import Optional

QDRANT = "http://192.168.1.129:6333"


def qdrant_scroll(collection: str, filt: dict, limit: int = 50) -> list:
    url = f"{QDRANT}/collections/{collection}/points/scroll"
    payload = json.dumps({"filter": filt, "limit": limit, "with_payload": True}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())["result"]["points"]
    except Exception as e:
        print(f"  [ERR {collection}]: {e}", file=sys.stderr)
        return []


def qdrant_text_search(collection: str, field: str, text: str, limit: int = 20) -> list:
    return qdrant_scroll(collection, {
        "must": [{"key": field, "match": {"text": text}}]
    }, limit)


def qdrant_keyword(collection: str, field: str, value: str, limit: int = 100) -> list:
    return qdrant_scroll(collection, {
        "must": [{"key": field, "match": {"value": value}}]
    }, limit)


def p(payload: dict, *keys):
    for k in keys:
        v = payload.get(k)
        if v:
            return v
    return None


def fmt_money(v) -> str:
    if v is None:
        return ""
    try:
        return f"{float(v):,.0f} Kč"
    except Exception:
        return str(v)


def search_company(query: str) -> Optional[dict]:
    """Find company by name (text search)."""
    pts = qdrant_text_search("bluejet_companies", "name", query, 5)
    if not pts:
        pts = qdrant_text_search("bluejet_companies", "searchable_text", query, 5)
    if not pts:
        return None
    # pick best match
    pay = pts[0]["payload"]
    print(f"\n{'='*60}")
    print(f"FIRMA:  {pay.get('name')}")
    print(f"IČO:    {pay.get('ico')}  DIČ: {pay.get('dic')}")
    print(f"Email:  {pay.get('emailaddress1')}")
    print(f"Tel:    {pay.get('telephone1') or pay.get('mobilephone')}")
    print(f"Město:  {pay.get('town')}")
    print(f"firmaid: {pay.get('firmaid')}")
    print(f"{'='*60}")
    return pay


def show_contacts(firmaid: str):
    pts = qdrant_keyword("bluejet_contacts", "firmaid", firmaid, 20)
    if not pts:
        return
    print(f"\nKONTAKTY ({len(pts)}):")
    for pt in pts:
        pay = pt["payload"]
        name = f"{pay.get('firstname','')} {pay.get('lastname','')}".strip()
        print(f"  • {name} | {pay.get('emailaddress1','')} | {pay.get('mobilephone','')}")


def show_offers(firmaid: str):
    pts = qdrant_keyword("bluejet_offers_out", "firmaid", firmaid, 50)
    if not pts:
        return
    pts.sort(key=lambda x: x["payload"].get("datumplatnosti", ""), reverse=True)
    print(f"\nNABÍDKY ({len(pts)}):")
    for pt in pts[:10]:
        pay = pt["payload"]
        print(f"  • {pay.get('kodnabidky','?'):25s} {str(pay.get('datumplatnosti',''))[:10]}  {fmt_money(pay.get('cenaprodej'))}  stav:{pay.get('statuscode','?')}")
    if len(pts) > 10:
        print(f"  ... a {len(pts)-10} dalších")


def show_orders(firmaid: str):
    pts = qdrant_keyword("bluejet_orders_out", "firmaid", firmaid, 50)
    if not pts:
        return
    pts.sort(key=lambda x: x["payload"].get("datumvystaveni", ""), reverse=True)
    print(f"\nOBJEDNÁVKY ({len(pts)}):")
    for pt in pts[:10]:
        pay = pt["payload"]
        print(f"  • {pay.get('kodobjednavky','?'):25s} {str(pay.get('datumvystaveni',''))[:10]}  {fmt_money(pay.get('cenaprodej'))}  stav:{pay.get('statuscode','?')}")
    if len(pts) > 10:
        print(f"  ... a {len(pts)-10} dalších")


def show_invoices(firmaid: str):
    pts = qdrant_keyword("bluejet_invoices_out", "firmaid", firmaid, 50)
    if not pts:
        return
    pts.sort(key=lambda x: x["payload"].get("datumvystaveni", ""), reverse=True)
    print(f"\nFAKTURY ({len(pts)}):")
    for pt in pts[:10]:
        pay = pt["payload"]
        uhrada = pay.get("stavuhrady", "?")
        print(f"  • {pay.get('kodfaktury','?'):25s} {str(pay.get('datumvystaveni',''))[:10]}  {fmt_money(pay.get('cenaprodej'))}  úhrada:{uhrada}")
    if len(pts) > 10:
        print(f"  ... a {len(pts)-10} dalších")


def show_emails(query: str, email_addr: Optional[str] = None):
    pts = []
    if email_addr:
        pts = qdrant_keyword("email_history", "from", email_addr, 20)
        pts += qdrant_keyword("email_history", "to", email_addr, 20)
    if not pts:
        pts = qdrant_text_search("email_history", "subject", query, 20)
    if not pts:
        return
    # deduplicate by message_id
    seen = set()
    unique = []
    for pt in pts:
        mid = pt["payload"].get("message_id", pt["id"])
        if mid not in seen:
            seen.add(mid)
            unique.append(pt)
    unique.sort(key=lambda x: x["payload"].get("date", ""), reverse=True)
    print(f"\nEMAILY ({len(unique)}):")
    for pt in unique[:10]:
        pay = pt["payload"]
        print(f"  • {str(pay.get('date',''))[:16]}  {pay.get('subject','')[:50]}")
        print(f"    od: {pay.get('from','')}  komu: {pay.get('to','')[:50]}")
    if len(unique) > 10:
        print(f"  ... a {len(unique)-10} dalších")


def search_product(code: str):
    pts = qdrant_keyword("bluejet_products", "code", code, 5)
    if not pts:
        pts = qdrant_text_search("bluejet_products", "name", code, 5)
    if not pts:
        print(f"Produkt '{code}' nenalezen.")
        return
    pay = pts[0]["payload"]
    print(f"\n{'='*60}")
    print(f"PRODUKT: {pay.get('code')}  {pay.get('name')}")
    print(f"Dodavatel: {pay.get('supplier')}  Kategorie: {pay.get('category')}")
    print(f"Cena: {fmt_money(pay.get('price'))}")
    print(f"{'='*60}")
    # NOTE: productid cross-ref to orders requires productid field (not yet in collection)
    print("  [INFO] Cross-ref na objednávky vyžaduje productid (re-import needed)")


def main():
    parser = argparse.ArgumentParser(description="Unified BlueJet Qdrant search")
    parser.add_argument("query", nargs="?", help="Název firmy / hledaný text")
    parser.add_argument("--firmaid", help="Přímé vyhledání podle firmaid UUID")
    parser.add_argument("--product", help="Hledat produkt podle kódu nebo názvu")
    parser.add_argument("--emails", action="store_true", help="Prohledat i emaily")
    parser.add_argument("--no-emails", action="store_true", help="Vynechat emaily")
    args = parser.parse_args()

    if args.product:
        search_product(args.product)
        return

    if args.firmaid:
        firmaid = args.firmaid
        company_email = None
        print(f"Hledám podle firmaid: {firmaid}")
    elif args.query:
        pay = search_company(args.query)
        if not pay:
            print(f"Firma '{args.query}' nenalezena v Qdrant.")
            sys.exit(1)
        firmaid = pay.get("firmaid")
        company_email = pay.get("emailaddress1")
    else:
        parser.print_help()
        sys.exit(1)

    show_contacts(firmaid)
    show_offers(firmaid)
    show_orders(firmaid)
    show_invoices(firmaid)

    if not args.no_emails:
        show_emails(args.query or "", company_email)

    print()


if __name__ == "__main__":
    main()
