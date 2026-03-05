# BlueJet -> Qdrant Mirror (Phase 1)

## Cíl

Zajistit hodinový mirror BlueJet CRM/ERP dat do Qdrantu bez destruktivních operací:

- firmy (`225`) -> `bluejet_companies`
- kontakty (`222`) -> `bluejet_contacts`
- produkty (`217`) -> `bluejet_products`
- nabídky (`293`) -> `bluejet_offers_out`
- objednávky (`356`) -> `bluejet_orders_out`
- faktury (`323`) -> `bluejet_invoices_out`

Priorita: správné promítání změn stavů (`statuscode`, `stavuhrady`, `datumpotvrzeni`, atd.).

## Skript

`tools/indexing/index_bluejet_qdrant.py`

Vlastnosti:

- pouze GET čtení z BlueJet API
- upsert do Qdrant (bez mazání bodů)
- zachování existujících vektorů tam, kde již existují
- fallback deterministic vector pro nové body (aby se neblokoval ingest)
- audit log + sqlite state DB

## Povinné ENV

```
BLUEJET_BASE_URL=https://czeco.bluejet.cz
BLUEJET_API_TOKEN_ID=...
BLUEJET_API_TOKEN_HASH=...
QDRANT_URL=http://192.168.1.129:6333
QDRANT_API_KEY=...   # pokud je zapnutá auth
```

Bezpečnější varianta (bez plaintext tokenů v `.env`):

```
BLUEJET_API_TOKEN_ID_OP_REF=op://AI/BlueJet API/token_id
BLUEJET_API_TOKEN_HASH_OP_REF=op://AI/BlueJet API/token_hash
```

Skript použije přímé `BLUEJET_API_TOKEN_*` pokud jsou vyplněné; jinak zkusí `op read` přes `*_OP_REF`.

Alternativně lze použít jen jeden přímý token:

```
BLUEJET_API_DIRECT_TOKEN=...
```

## Volitelné ENV

```
BLUEJET_PAGE_LIMIT=50
BLUEJET_API_MIN_INTERVAL_SECONDS=0.75
BLUEJET_API_MAX_RETRIES=6
BLUEJET_API_RETRY_BASE_SECONDS=2.0
BLUEJET_API_MAX_RETRY_SLEEP_SECONDS=60
BLUEJET_MAX_PAGES_PER_EVIDENCE=0
BLUEJET_MAX_ROWS_PER_EVIDENCE=0
BLUEJET_QDRANT_BATCH_SIZE=50
BLUEJET_QDRANT_BATCH_PAUSE_SECONDS=0.4
BLUEJET_EVIDENCE_PAUSE_SECONDS=3
BLUEJET_MAX_POINTS_PER_RUN=3000
BLUEJET_MIRROR_EVIDENCES=225,222,217,293,356,323
BLUEJET_MIRROR_STATE_DB=.cache/bluejet_mirror_state.sqlite
BLUEJET_MIRROR_AUDIT_PATH=/tmp/bluejet_qdrant_mirror_audit.jsonl
BLUEJET_MIRROR_LOG_PATH=/tmp/bluejet_qdrant_mirror.log
QDRANT_WAIT=1
QDRANT_ORDERING=weak
```

Bezpečný start (doporučeno):

- první 24h držet `BLUEJET_API_MIN_INTERVAL_SECONDS` aspoň `1.0`
- po ověření stability případně snížit na `0.75`
- pro extra ochranu prvních 24h nastav `BLUEJET_MAX_PAGES_PER_EVIDENCE=50` (pak vrať na `0` = bez limitu)
- na Synology 423+ bez RAM/SSD ponech `BLUEJET_PAGE_LIMIT=50`, `BLUEJET_QDRANT_BATCH_SIZE=50` a `BLUEJET_MAX_POINTS_PER_RUN=3000`

## Manuální spuštění

Nejdřív preflight:

```bash
tools/indexing/bluejet_mirror_preflight.sh --dry-run
```

```bash
python3 tools/indexing/index_bluejet_qdrant.py
```

Pouze vybrané evidence:

```bash
python3 tools/indexing/index_bluejet_qdrant.py --evidences 293,356,323
```

Bezpečný test bez zápisu do Qdrant:

```bash
python3 tools/indexing/index_bluejet_qdrant.py --dry-run --evidences 293
```

## Hourly plán

Viz template LaunchAgent:

`ops/launchagents/com.premiumgastro.qdrant.bluejet.hourly.plist`

Pro slabší NAS je doporučený split:

- hourly (každé 2h): jen kritické statusové evidence `293,356,323`
- nightly full (02:20): všechny evidence `225,222,217,293,356,323`

Template pro nightly:

`ops/launchagents/com.premiumgastro.qdrant.bluejet.nightly-full.plist`

## Poznámka k Fázi 2

Fáze 1 řeší provozní stabilitu mirroru a stavové změny.
Fáze 2 řeší modernizaci embeddingů (shadow index + alias cutover) bez výpadku.
