# Technical Due Diligence: BlueJet Stack Replacement

**Datum:** 2026-03-04
**Autor:** Premium Gastro AI Ops (due diligence agent)
**Scope:** Open-source náhrada BlueJet CRM/ERP pro solo-operátora
**Status:** DRAFT — čeká na rozhodnutí o otevřených otázkách (viz sekce F)

---

## A) Identifikace „Atom" CRM

### Závěr

**„Atom" = marmelab/atomic-crm** (GitHub: github.com/marmelab/atomic-crm)

- **Typ:** Developer starter kit / demo šablona, NIKOLIv produkční CRM
- **Stack:** React + shadcn/ui + Supabase (Postgres)
- **Licence:** MIT
- **Demo:** marmelab.com/atomic-crm-demo
- **Funkce:** Contacts, Companies, Deals, Notes, Tasks — pouze základní CRM pipeline
- **Chybí:** Quotes, supplier PO, order management, inventář, ceníky, invoicing

### Alternativní kandidáti (pro případ záměny)

| Název | Proč by mohl být „Atom" |
|-------|------------------------|
| **Twenty CRM** | Moderní OSS CRM, může být zaměněn názvem |
| **Attio** | Fonetická podobnost, ale proprietary SaaS |
| **Atomic CRM** | Přesná shoda — nejpravděpodobnější |

### Hodnocení pro Premium Gastro

**Atomic CRM je nevhodný** jako přímý BlueJet náhrada:
- Chybí kompletní obchodní flow (nabídky → objednávky → faktury)
- Bez supply-chain funkcí (supplier management, skladové karty)
- Je to starter kit — vyžadoval by rozsáhlý custom vývoj
- Vhodný maximálně jako UI vrstva pokud by byl celý business layer postaven na zakázku

---

## B) CRM Shortlist — Srovnávací tabulka

### Hodnocená kritéria
Licence | Maintenance | Docker | Postgres | API | Data model | n8n effort | Rizika

### Tabulka kandidátů

| Produkt | Licence | Stars | DB | Docker | API | B2B datamodel | n8n | Doporučení |
|---------|---------|-------|----|--------|-----|---------------|-----|------------|
| **Odoo Community 17.0** | LGPL-3.0 core | ~49.3k | Postgres-native | ✅ moderate | REST + XML-RPC | ★★★★★ | 1/5 | **✅ #1 DOPORUČENO** |
| **Twenty CRM** | AGPL-3.0 + Enterprise | ~40.2k | Postgres-native | ✅ 4 services | GraphQL + REST | ★★★★☆ | 2/5 | ✅ #2 záloha |
| **Frappe CRM** | AGPL-3.0 | ~5k | MariaDB (Postgres beta) | ✅ complex | REST + Frappe API | ★★★★★ | 2/5 | ⚠️ Zvážit s ERPNext |
| **ERPNext** | GPL-3.0 | ~32k | MariaDB (Postgres expmt.) | ✅ heavy | REST + Frappe API | ★★★★★ | 2/5 | ⚠️ Přetížený pro solo |
| **Corteza CRM** | Apache 2.0 | ~2k | Postgres | ✅ moderate | REST | ★★★☆☆ | 3/5 | ⚠️ Nízká komunita |
| **SuiteCRM** | AGPL-3.0 | ~5.3k | MySQL/MariaDB | ⚠️ neoficiální | REST | ★★★★☆ | 3/5 | ❌ Bez Postgres |
| **Atomic CRM** | MIT | ~1k | Postgres (Supabase) | ✅ minimal | REST via Supabase | ★★☆☆☆ | — | ❌ Starter kit |
| **Monica** | AGPL-3.0 | ~24k | MySQL/Postgres | ✅ | REST | ☆☆☆☆☆ | — | ❌ Personal CRM |

### Eliminace

- **SuiteCRM** → DISQUALIFIED: MySQL/MariaDB only, bez Postgres, legacy PHP stack
- **Monica** → DISQUALIFIED: explicitně personal CRM, bez B2B
- **Atomic CRM** → DISQUALIFIED: starter kit, chybí business flow
- **ERPNext** → PODMÍNĚNO: MariaDB primární, Postgres je experimentální (porušuje constraint)

### Finální doporučení: Odoo Community 17.0 (#1) / Twenty CRM (#2 záloha)

#### #1 — Odoo Community 17.0

**Důvody:**
1. **Postgres-native** — splňuje constraint, nativní integrace s existující infrastrukturou
2. **LGPL-3.0 core** — moduly CRM, Sales, Purchase, Inventory jsou LGPL (výhodnější než AGPL)
3. **Má VŠE nativně** — quotes (`sale.order`), supplier PO (`purchase.order`), contacts (`res.partner`), ceníky, sklad
4. **Nativní n8n node** — bez custom HTTP Request adaptérů
5. **49,300 stars** — největší OSS ERP komunita, stabilní dlouhodobý vývoj
6. **Žádné custom objects nutné** — BlueJet evidence mapují přímo na Odoo moduly

**Nevýhody Odoo:**
- Komplexnější deployment (více services než Twenty)
- UI je „ERP styl" — složitější než moderní CRM-only tools
- Czech lokalizace (`l10n_cz`) dostupná, ale je třeba ověřit Pohoda sync

#### #2 záloha — Twenty CRM

**Kdy použít Twenty místo Odoo:**
- Pokud priorita je moderní minimalistické UI a jednoduchý deployment
- Pokud Medusa přebírá kompletně product catalog + orders (Twenty řeší jen CRM pipeline)
- ⚠️ **OPRAVA oproti původní verzi doc:** Licence je **AGPL-3.0 + Enterprise** (NE Apache 2.0)
- ⚠️ **OPRAVA:** Stars je **~40,200** (NE ~24k)

**Nevýhody Twenty jako #1:**
- AGPL-3.0 licence má copyleft implikace
- Nativně chybí: quotes, supplier PO, inventář — nutné custom objects nebo Medusa
- GraphQL API vyžaduje adaptér pro n8n

#### Eliminace
- **SuiteCRM** → DISQUALIFIED: MySQL/MariaDB only
- **Monica** → DISQUALIFIED: personal CRM
- **Atomic CRM** → DISQUALIFIED: starter kit
- **ERPNext/Frappe** → PODMÍNĚNO: MariaDB primární (porušuje Postgres constraint)

---

## C) Medusa v2 — Capability Map

### Co Medusa v2 zvládá nativně (MIT licence)

| Funkce | Status | Poznámka |
|--------|--------|----------|
| Produktový katalog | ✅ Nativní | varianty, SKU, kategorie |
| B2B ceníky | ✅ Nativní | customer group price lists |
| Zákaznické skupiny | ✅ Nativní | B2B customer tiers |
| Draft orders | ✅ Nativní | „nabídka" ekvivalent pro B2B |
| Multi-warehouse | ✅ Nativní | inventory locations |
| Fulfillment workflow | ✅ Nativní | shipping, tracking |
| Payment methods | ✅ Nativní | pro B2B: invoice payment method |
| Webhooks | ✅ Nativní | event-driven, n8n friendly |
| REST API | ✅ Nativní | admin + store API |
| Docker deployment | ✅ Nativní | compose: server, postgres, redis |
| Czech ISDOC invoicing | ❌ Chybí | HIGH effort plugin |
| RFQ / Quote workflow | ❌ Chybí | HIGH effort custom flow |
| Supplier PO management | ❌ Mimo scope | není commerce funkce |
| FIFO costing | ❌ Chybí | HIGH effort |
| Pohoda sync | ❌ Chybí | custom n8n connector |

### Závěr: Role Medusy v stack

**Medusa v2 = B2B ordering portal + product catalog + warehouse management**

**NENÍ** přímý BlueJet náhrada pro:
- Supplier objednávky (to je BlueJet 356 → dodavatel; Medusa řeší zákazník → firma)
- Pohoda sync / česká fakturace
- CRM (firma-kontakt-příležitost)

**JE** vhodná jako:
- Self-service B2B portál pro zákazníky (objednávají sami)
- Správa produktů + ceníků
- Warehouse tracking pro expedici

---

## D) Navrhovaná architektura

```
┌─────────────────────────────────────────────────────────┐
│                    KOMUNIKACE                           │
│  Missive (email/chat) ←→ n8n (orchestrace) ←→ Qdrant   │
└──────────────────┬──────────────────────────────────────┘
                   │ webhooks / API
        ┌──────────┴──────────┐
        │                     │
┌───────▼──────────┐  ┌───────▼──────────┐
│  Odoo Community  │  │    Medusa v2     │
│  17.0 (LGPL-3)   │  │    (MIT)         │
│  Postgres-native │  │  Postgres + Redis│
│                  │  │                  │
│ Firmy + kontakty │  │ B2B zákaznický   │
│ Deals / pipeline │  │ portál (opt.)    │
│ Nabídky nativní  │  │ Produkty + ceníky│
│ Supplier PO      │  │ Sklad / expedice │
│ Sklad nativní    │  │                  │
└───────┬──────────┘  └────────┬─────────┘
        │                      │
        └──────────┬───────────┘
                   │ ETL via n8n
        ┌──────────▼──────────┐
        │  Pohoda mServer      │
        │  (XML bridge via n8n)│
        │  Účetnictví SoR      │
        │  Faktury, DPH, účty  │
        └──────────┬───────────┘
                   │
        ┌──────────▼──────────┐
        │   Postgres DWH       │
        │   Analytics + BI     │
        │   (existující NAS)   │
        └──────────────────────┘

n8n integrace (HTTP Request + Webhook):
  Odoo Community → 1/5 effort (nativní n8n node)
  Medusa v2      → 2/5 effort (clean REST)
  Missive        → 2/5 effort (clean REST API)
  Pohoda         → 4-5/5 effort (XML mServer, custom)

Poznámka: Medusa v2 je volitelná komponenta. Pokud Odoo zvládá
vše nativně (quotes, orders, sklad), Medusa slouží jen jako
self-service B2B portál pro zákazníky — nebo se vynechá.
```

### Infrastruktura (zachovat stávající)

- **NAS 192.168.1.129**: Qdrant v1.15.5, PostgreSQL (port 5433)
- **Workstation Docker**: n8n (5678), BlueJet MCP (8741), 1Password Connect (8082)
- **Nové kontejnery na NAS** (po HW upgradu NAS): Odoo Community, Medusa v2

### Klíčové designové rozhodnutí

1. **Fakturoid = SoR pro účetnictví** (nahrazuje/doplňuje Pohodu) — REST API, snadnější integrace
2. **Odoo Community = CRM + pipeline + quotes + supplier PO + sklad** (vše nativní)
3. **Medusa v2 = B2B ecommerce backend** — product catalog, self-service objednávky pro zákazníky
4. **n8n = integrace všeho** (Fakturoid REST bridge, notifikace, workflow)
5. **Qdrant = knowledge SSoT** (AI asistent, retrieval)
6. **Hosting: NAS po HW upgradu** — Odoo + Medusa nasadit na NAS až po upgradu RAM/CPU

---

## E) Migrační plán — Fáze 0–3

### Phase 0: Příprava (1–2 týdny) — BEZ VÝPADKU

**Cíl:** Paralelní prostředí, datová mapa, go/no-go gate
**⚠️ Prerekvizita:** NAS HW upgrade dokončen před instalací Odoo + Medusa

| Akce | Výstup |
|------|--------|
| NAS HW upgrade (RAM/CPU) | NAS připraven |
| Nainstalovat Odoo Community 17.0 (Docker na NAS) | Instance running |
| Nainstalovat Medusa v2 (Docker na NAS) | Instance running |
| Exportovat všechna data z BlueJet (JSON) | Data backup |
| Vytvořit mapping: BlueJet evidence → Odoo moduly | Data mapping doc |
| Ověřit Fakturoid REST API credentials + sandbox | Connection verified |
| n8n: první webhook test (Odoo → Missive) | Proof of concept |
| n8n: Fakturoid test (create invoice draft) | Fakturoid PoC |

**Go/No-Go Gate 0:**
- [ ] NAS HW upgrade dokončen
- [ ] Odoo Community je dostupný a stabilní
- [ ] Data mapping je kompletní (všechny klíčové fieldy)
- [ ] Fakturoid REST API je dosažitelný, sandbox faktura vytvořena
- [ ] n8n může číst z Odoo a vytvořit draft fakturu v Fakturoid

---

### Phase 1: CRM Core (2–3 týdny) — PARALELNÍ PROVOZ

**Cíl:** Firmy, kontakty, deals — production ready v Odoo

| Akce | Výstup |
|------|--------|
| Migrace firem (BlueJet 225 → Odoo res.partner companies) | Data in Odoo |
| Migrace kontaktů (BlueJet 222 → Odoo res.partner persons) | Data in Odoo |
| Nastavit CRM pipeline stages v Odoo | Pipeline ready |
| n8n: sync nových záznamů BlueJet → Odoo (read-only) | Live sync |
| Missive ↔ Odoo CRM kontext integrace | Comms enriched |
| Training uživatele na Odoo UI | User ready |

**Go/No-Go Gate 1:**
- [ ] 100% firem a kontaktů v Odoo (verified row count)
- [ ] Nové záznamy v BlueJet se synchronizují do Odoo
- [ ] Uživatel zvládá denní CRM workflow v Odoo

---

### Phase 2: Obchodní flow (3–4 týdny) — CUTOVER READY

**Cíl:** Nabídky + objednávky + produkty — bez BlueJet pro nové záznamy

| Akce | Výstup |
|------|--------|
| Migrace produktů (BlueJet 217 → Odoo product.template) | Products in Odoo |
| Migrace ceníků (BlueJet → Odoo pricelists) | Price lists |
| Migrace skladů (BlueJet 437/441 → Odoo stock.warehouse) | Warehouses |
| Odoo: aktivovat Sale + Purchase + Inventory moduly | Full ERP live |
| Medusa: setup B2B ecommerce portal (product catalog sync z Odoo) | B2B portal |
| n8n: Odoo sale.order → faktura Fakturoid (REST) | Fakturoid bridge live |
| n8n: Odoo purchase.order → supplier workflow | PO workflow |
| Pilot: 5 reálných objednávek přes nový stack | Validation |

**Go/No-Go Gate 2:**
- [ ] 5 objednávek zpracováno end-to-end bez BlueJet
- [ ] Fakturoid přijímá faktury ze stacku (REST API)
- [ ] Medusa B2B portál zobrazuje produkty z Odoo
- [ ] Odoo sklad reflektuje reálné pohyby zboží
- [ ] Žádná ztráta dat (audit log OK)

---

### Phase 3: Decommission BlueJet (1–2 týdny)

**Cíl:** BlueJet = read-only archiv, nový stack je primary

| Akce | Výstup |
|------|--------|
| Nastavit BlueJet na BLUEJET_READ_ONLY=1 | Read-only mode |
| Přesunout všechny aktivní záznamy do Twenty/Medusa | Data complete |
| Qdrant: spustit nightly mirror z Odoo (místo BlueJet) | New mirror |
| Zrušit BlueJet LaunchAgenty | Clean cron |
| Archivovat BlueJet data (full export + Qdrant snapshot) | Archive done |
| Deaktivovat BlueJet MCP server | Container stopped |
| Dokumentovat nový stack | Ops runbook |

**Go/No-Go Gate 3 (Definition of Done):**
- [ ] 30 dní bez přístupu do BlueJet UI pro operační práci
- [ ] Nový stack zpracoval min. 20 objednávek bez incidentu
- [ ] Pohoda sync funguje bez manuálních oprav
- [ ] Qdrant mirror přechod na Twenty (freshness ≤ 2h)
- [ ] Ops runbook dokončen

---

### Časový odhad

```
Týden 1-2:   Phase 0 — Setup + data mapping
Týden 3-5:   Phase 1 — CRM core live
Týden 6-9:   Phase 2 — Obchodní flow + pilot
Týden 10-11: Phase 3 — Decommission
─────────────────────────────────────────
Celkem: 11 týdnů (optimisticky), 16 týdnů (realisticky pro solo-operátora)
```

---

## F) Otevřené otázky

### Kritické (blokují Phase 0)

1. **Fakturoid napojení** ✅ ROZHODUTO
   - Fakturoid = nový SoR pro fakturaci (místo Pohoda XML mServer)
   - REST API: `https://app.fakturoid.cz/api/v2/accounts/{slug}/invoices.json`
   - Integrace přes n8n HTTP Request node — nativní OAuth nebo API key

2. **NAS HW upgrade** ✅ ROZHODUTO
   - Odoo Community + Medusa v2 nasadit na NAS **po HW upgradu**
   - Workstation Docker zůstává pro n8n + BlueJet MCP (přechodné období)
   - Cloudflare tunnel pro Odoo (jako stávající n8n tunnel)

3. **Medusa jako B2B ecommerce backend** ✅ ROZHODUTO
   - Medusa = B2B ecommerce backend (product catalog + self-service objednávky)
   - Zákazníci objednávají přes Medusa storefront
   - Product sync: Odoo product.template → Medusa (via n8n)

### Důležité (blokují Phase 2)

4. **Czech invoicing přes Fakturoid**
   - Fakturoid podporuje českou fakturaci nativně (DPH, ISDOC, QR platby)
   - n8n: Odoo sale.order → Fakturoid REST API → faktura zákazníkovi
   - Ověřit: Fakturoid plan (Start/Pohoda/Business) pro objem Premium Gastro

5. **BlueJet Qdrant mirror — kdy zastavit?**
   - Fáze 1-2 aktuálně buduje `index_bluejet_qdrant.py` mirror
   - Po Phase 3 cutover: přejít na Odoo mirror
   - Kdy je OK zastavit BlueJet mirror? (Phase 3 gate?)

### Nízká priorita (post-cutover)

6. **FIFO costing** — Odoo má FIFO nativně (stock valuation); ověřit nastavení pro Premium Gastro
7. **Reporting** — Zůstane analytics v Postgres DWH nebo bude potřeba BI tool (Metabase)?
8. **Cloudflare tunnel** — Odoo bude exposed přes tunnel nebo VPN only?
9. **Pohoda** — zůstává v provozu souběžně, nebo se decommissionuje? Rozhodnutí post Phase 2.

---

## Příloha: Stack souhrn

| Vrstva | Nástroj | Licence | DB |
|--------|---------|---------|-----|
| CRM + ERP (quotes, PO, sklad) | Odoo Community 17.0 | LGPL-3.0 core | Postgres-native |
| B2B ecommerce backend | Medusa v2 | MIT | Postgres + Redis |
| Orchestrace | n8n (stávající) | Sustainable (self-host free) | Postgres |
| Účetnictví SoR | Fakturoid | Proprietary SaaS | — |
| Komunikace | Missive | Proprietary SaaS | — |
| Vektorová paměť | Qdrant (stávající) | Apache 2.0 | — |
| AI asistent | Claude + Ollama | Mixed | — |

**Zachovávané stávající komponenty:**
- n8n (workstation Docker, port 5678)
- Qdrant (NAS, port 6333)
- Postgres NAS (port 5433)
- Cloudflare tunnel
- 1Password Connect

**Nové komponenty:**
- Odoo Community 17.0 (NAS Docker — po HW upgradu)
- Medusa v2 (NAS Docker — B2B ecommerce backend)
- n8n Fakturoid REST connector (new workflow)
- n8n Odoo connector (nativní node)
