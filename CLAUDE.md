# CLAUDE.md — Premium Gastro AI Assistant

## Jazyk a komunikace

- Uživatel komunikuje **česky**, odpovídej česky
- Uživatel je "roztržitý" — minimalizuj manuální práci, proaktivně navrhuj řešení
- **VŽDY se ZEPTEJ před velkými autonomními akcemi** — nespouštěj rozsáhlé operace bez souhlasu
- Stručné dotazy na souhlas: "Potřebuji udělat X. OK?"

---

## BlueJet CRM — Kompletní referenční příručka

### Připojení

- **Base URL**: `https://czeco.bluejet.cz`
- **Autentizace**: POST `/api/v1/users/authenticate` s `{tokenID, tokenHash}` → `{succeeded, token}`
- **Token TTL**: 23 hodin, automatický refresh při 401
- **Header**: `X-Token: <token>`
- **Read-only mode**: `BLUEJET_READ_ONLY=1` (bezpečný výchozí stav)

### MCP Server

- **Tool**: `bluejet_request(method, endpoint, payload, params)`
- **Docker kontejner**: `docker_configs-bluejet-mcp-1` na `127.0.0.1:8741` → port 8000
- **Projekt .mcp.json**: `{"mcpServers": {"bluejet": {"type": "url", "url": "http://127.0.0.1:8741/mcp/"}}}`
- **Claude Code tool name**: `mcp__bluejet__bluejet_request` (vyžaduje aktivní session s URL MCP)
- **Transport**: FastMCP v2.14.5 Streamable HTTP (`POST /mcp/` s JSON-RPC)
- **Env vars**: `BLUEJET_BASE_URL`, `BLUEJET_API_TOKEN_ID`, `BLUEJET_API_TOKEN_HASH`, `BLUEJET_READ_ONLY`, `BLUEJET_TOKEN_TTL_SECONDS`, `BLUEJET_MAX_RESPONSE_CHARS` (200k default)

### REST API — klíčové endpointy

| Metoda | Endpoint | Popis |
|--------|----------|-------|
| GET | `/api/v1/Data?no=<ev>&limit=N&offset=N` | Čtení záznamů z evidence |
| POST | `/api/v1/Data` | Vytvoření záznamu (dataObject + innerObjects) |
| PUT | `/api/v1/Data` | Aktualizace záznamu |
| DELETE | `/api/v1/data` | Smazání záznamu (by no + id) |
| POST | `/api/v1/data/remove` | Hromadné smazání |

### Query parametry

| Parametr | Popis | Příklad |
|----------|-------|---------|
| `no` | Číslo evidence (povinné) | `no=293` |
| `limit` | Max záznamů | `limit=100` |
| `offset` | Stránkování | `offset=200` |
| `sort` | Řazení (+asc, -desc) | `sort=+datumvystaveni` |
| `fields` | Konkrétní sloupce | `fields=kodnabidky,customerid` |
| `condition` | Filtr | `condition=kodnabidky\|=\|NAB-2024-001` |

**Operátory condition**: `=`, `!=`, `contains`, `starts`, `<`, `>`, `<=`, `>=`

**Response header**: `X-Total-Count` — celkový počet záznamů

### Row formát

```json
{"rows": [{"columns": [{"name": "fieldname", "value": "fieldvalue"}, ...]}]}
```

Pro práci v kódu: transformovat pomocí `row_to_dict()`:

```python
def row_to_dict(row):
    return {col["name"]: col["value"] for col in row["columns"]}
```

---

## Evidence — Kompletní mapa

| No | Název (CZ) | Název (EN) | Záznamy | Poznámka |
|----|-----------|-----------|---------|----------|
| 209 | Příležitosti | Opportunities | — | CRM pipeline |
| 217 | Produkty | Products | — | Katalog |
| 222 | Kontakty | Contacts | — | Osoby |
| 225 | Firmy | Companies | — | Organizace |
| 243 | Adresy | Addresses | — | Dodací/fakturační |
| 291 | Položky nabídek | Offer Line Items | 67 708 | Detail řádků nabídky |
| 293 | Nabídky | Offers/Quotes | — | Hlavní obchodní doklad |
| 323 | Vydané faktury | Issued Invoices | — | Fakturace |
| 324 | Položky faktur | Invoice Line Items | — | Detail řádků faktury |
| 341 | Přílohy | Attachments | — | Soubory |
| 354 | Položky objednávek | Order Line Items | 7 455 | Detail řádků objednávky |
| 356 | Objednávky | Orders/POs | 3 448 | Nákupní objednávky (na dodavatele) |
| 437 | Sklady | Warehouses | 3 | Eshop, hlavní, ... |
| 441 | Skladové karty | Stock Cards | 13 820 | Stav zásob per produkt/sklad |

### Klíčové pole dle evidence

**293 Nabídky**: `kodnabidky`, `customerid`, `prijemcezboziadsupl`, `mainprijemcezboziadsupl`, `prijemadd`, `prijemfakturyadd`, `datumvystaveni`, `cenanakup`, `cenaprodej`, `stav`

**291 Položky nabídek**: `productid`, `cenanakup`, `cenaprodej`, `mnozstvi`, `cenikcenanakup`, `cenikcenaprodej`, `finalnicenanakup`, `finalnicenaprodej`, `nazev` (= název produktu)

**356 Objednávky**: `kodobjednavky`, `customerid`, `datumvystaveni`, `datumpotvrzeni`, `cenanakup`, `cenaprodej`, `formauhrady`, `mena`, `kurz`, `prijemfakturyadd`, `firmaid`, `opportunityid`, `parentobjednavka`

**354 Položky objednávek**: `cenanakup`, `cenaprodej`, `productid`, `mnozstvi`, `cenikcenanakup`, `cenikcenaprodej`, `finalnicenanakup`, `finalnicenaprodej`, `grouppacket`, `jcenanakup`, `jcenaprodej`

**437 Sklady**: `skladid`, `kodskladu`, `nazev`, `typskladu`, `zasoba`, `inventura`, `mj`, `pouzivat`

**441 Skladové karty**: `skladkartaid`, `productid`, `skladid`, `mnozstvi`, `mnozstvirezervovane`, `mnozstviobjednane`, `mnoszstvidisponibilni`, `cenajednotkova`, `cenacelkem`, `fifo`

**225 Firmy**: `name`, `contactperson1`, `mobilephone`, `telephone1`, `emailaddress1`, `ico`, `dic`

**243 Adresy**: `recipient`, `town`, `street1`, `zipcode`, `addressid`

---

## Obchodní flow — od nabídky po fakturu

```
Vydaná nabídka (293)
    ↓
Kombinovaný náhled (kontrola před objednávkou)
    ↓
Sumární objednávka na dodavatele (356)
    ↓
Příjemka — naskladnění (437/441)
    ↓
Výdejka + dodací list (DL) — vyskladnění
    ↓
Faktura (323) — vystavení
    ↓
Odeslání emailem
```

### Klíčové procesy

1. **Sumární objednávka**: Vytvořena z nabídky, agreguje položky na dodavatele
2. **Příjemka**: Zboží dorazilo → zvýšení `mnozstvi` na skladové kartě (441)
3. **Výdejka + DL**: Expedice zákazníkovi → snížení `mnozstvi`, vytvoření dodacího listu
4. **Faktura**: Generována z výdejky, odesílána emailem

### Shipping address cascade (z kódu toptrans exportu)

```
prijemcezboziadsupl → mainprijemcezboziadsupl → prijemadd → prijemfakturyadd
```

Priorita: první neprázdná adresa z tohoto pořadí se použije pro dopravu.

---

## Ceníky (Price Lists)

### Typy ceníků

| Typ | Popis |
|-----|-------|
| Prodejní | Cena pro zákazníka |
| Nákupní | Cena od dodavatele |
| Vzorový | Šablona/template |
| Akční | Časově omezená akce |

### Priorita cen (od nejvyšší)

1. **Akční ceníková cena** (pokud platná)
2. **Ceníková cena** (standardní ceník)
3. **Cena z produktu** (fallback z evidence 217)
4. **Položková sleva** (aplikuje se na výslednou cenu)

### Ceníkové operace

- Generování zákazníků do ceníku
- Generování produktů do ceníku
- Akce nad ceníky (hromadné úpravy)

---

## Logistika

### TopTrans integrace

- **Export skript**: `tools/logistics/bluejet_export_toptrans.py`
- Flow: BlueJet nabídka (293) → adresy (243) → firmy (225) → TopTrans JSON
- Podporuje draft mode, cenové vstupy, tracking metadata
- **Labels**: `tools/logistics/toptrans_labels.py` (TopTrans API klient)
- Dokumentace: `tools/logistics/ARCHITECTURE.md`, `ops/TOPTRANS_INTEGRATION.md`

### Depoto integrace (plánovaná)

- Dokumentace: `ops/DEPOTO_LOGISTICS_INTEGRATION.md`, `ops/BLUEJET_MCP_DEPOTO_REPORT_2026-02-10.md`

---

## Infrastruktura

### Docker (lokální workstation)

- BlueJet MCP: `docker_configs-bluejet-mcp-1` (127.0.0.1:8741)
- n8n: kontejner `n8n` (port 5678, exposed via Cloudflare tunnel) — **jediný aktivní** (missicw-n8n-1 a docker_configs-n8n-1 smazány 2026-02-19)
- n8n API key: v PostgreSQL tabulce `user_api_keys`
- Health check: `docker ps --filter "name=bluejet"` / `docker ps --filter "name=n8n"`

### Docker (NAS 192.168.1.129)

- **Qdrant**: `http://192.168.1.129:6333` (v1.15.5, bez auth)
- **PostgreSQL**: port 5433
- DŮLEŽITÉ: NAS Docker ≠ lokální Docker!

### Cloudflare

- Tunnel: `n8n.premium-gastro.com` → `localhost:5678`
- Account ID: `300e0b3816bf67ea00d543f41e501b1e`
- Zone: `premium-gastro.com`

---

## Agent architektura (PLÁNOVANÁ)

| Agent | Role |
|-------|------|
| 01_CAgent-Office | Veškerá komunikace (email, Beeper, tel) kromě MKT |
| 02_CAgent-BlueJet | CRM expert, BlueJet API, dev ops |
| 03_CAgent-MKT | Sociální sítě, grafika, kalendář, MKT komunikace |

Cíl: Missive dropdown menu se všemi 3 agenty, n8n orchestrace.

---

## API dokumentace

- **Oficiální API docs**: <https://public.bluejet.cz/public/api/bluejet-api.html>
- **Layers no-code**: <https://www.bluejet.cz/layers-api/>
- **Formáty**: REST + SOAP, JSON + XML, HTTPS
- **Batch insert**: POST s `dataObject` a `innerObjects`, reference-based binding

---

## Známé problémy a workaroundy

- **406 na plain GET `/mcp/`**: Očekávané — MCP používá POST
- **MCP tool nedostupný po session continuation**: URL-type MCP servery se nemusí reinicializovat. Řešení: restart Claude Code.
- **Gmail těla emailů**: Nepřístupná přes Chrome extension kvůli URL omezení
- **Google Docs čtení**: Export URL vrací 401, DOM selektory prázdné. Workaround: screenshoty.
- **n8n webhook oprava**: PUT přes API neregistruje webhook — nutný přímý DB UPDATE na `webhook_entity` tabulce + deactivate/activate cycle
- **n8n API activate/deactivate**: `POST /api/v1/workflows/{id}/activate` (ne PATCH s `active` field)
- **Missive AI Reply webhook URL**: `https://n8n.premium-gastro.com/webhook/missive-webhook`
- **NAS Qdrant**: TCP port 6333 open ale HTTP může resetovat spojení při startu — počkat nebo zkontrolovat Container Manager
- **pg-pipeline na NAS**: Metabase port 3001 (ne 3000 — kolize), pgAdmin 5050, PostgreSQL 5434
