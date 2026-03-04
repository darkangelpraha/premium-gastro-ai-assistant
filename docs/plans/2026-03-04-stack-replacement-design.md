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
| **Twenty CRM** | Apache 2.0 | ~24k | Postgres-native | ✅ 4 services | GraphQL + REST | ★★★★☆ | 2/5 | **✅ DOPORUČENO** |
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

### Finální doporučení: Twenty CRM

**Důvody:**
1. **Postgres-native** — splňuje constraint, nativní integrace s existující infrastrukturou
2. **Apache 2.0** — nejvolnější licence (vs AGPL/GPL), žádné copyleft komplikace
3. **Moderní stack** — React/TypeScript frontend, Node.js backend
4. **Extensible data model** — custom objects (jako BlueJet evidence)
5. **n8n community node** — `n8n-nodes-twenty-dynamic` na npm, snazší integrace
6. **Docker compose** — 4 services (server, worker, postgres:16, redis) — moderate complexity
7. **Aktivní vývoj** — 24k stars, pravidelné releases

**Nevýhody Twenty CRM:**
- Nativně chybí: quotes/RFQ modul, supplier PO, inventář — nutné custom objects nebo integrace s Medusa
- GraphQL API vyžaduje adaptér pro n8n (community node řeší základy)

**Alternativa pro plný ERP:** Frappe CRM + ERPNext (pokud je akceptovatelný MariaDB a AGPL)
- Má quotes, invoicing, inventory nativně
- Ale: komplexní deployment, MariaDB dependency, AGPL licence

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
┌───────▼───────┐   ┌─────────▼────────┐
│   Twenty CRM   │   │    Medusa v2     │
│  (Apache 2.0)  │   │    (MIT)         │
│  Postgres-16   │   │  Postgres + Redis│
│                │   │                  │
│ Firmy + kontakty│  │ Produkty+ceníky  │
│ Deals/pipeline │   │ B2B objednávky   │
│ Nabídky*       │   │ Sklad / expedice │
│ Custom objects │   │                  │
└───────┬────────┘   └────────┬─────────┘
        │                     │
        └──────────┬──────────┘
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
  Twenty CRM   → 2/5 effort (community node)
  Medusa v2    → 2/5 effort (clean REST)
  Missive      → 2/5 effort (clean REST API)
  Pohoda       → 4-5/5 effort (XML mServer, custom)
```

### Infrastruktura (zachovat stávající)

- **NAS 192.168.1.129**: Qdrant v1.15.5, PostgreSQL (port 5433)
- **Workstation Docker**: n8n (5678), BlueJet MCP (8741), 1Password Connect (8082)
- **Nové kontejnery na NAS**: Twenty CRM, Medusa v2

### Klíčové designové rozhodnutí

1. **Pohoda zůstává SoR pro účetnictví** — žádná náhrada
2. **Twenty CRM = CRM + pipeline + quotes** (custom objects pro nabídky)
3. **Medusa = ordering portal + product catalog** (pro B2B zákazníky)
4. **n8n = integrace všeho** (Pohoda XML bridge, notifikace, workflow)
5. **Qdrant = knowledge SSoT** (AI asistent, retrieval)

---

## E) Migrační plán — Fáze 0–3

### Phase 0: Příprava (1–2 týdny) — BEZ VÝPADKU

**Cíl:** Paralelní prostředí, datová mapa, go/no-go gate

| Akce | Výstup |
|------|--------|
| Nainstalovat Twenty CRM (Docker na NAS) | Instance running |
| Nainstalovat Medusa v2 (Docker na NAS) | Instance running |
| Exportovat všechna data z BlueJet (JSON) | Data backup |
| Vytvořit mapping: BlueJet evidence → Twenty objects | Data mapping doc |
| Definovat custom objects v Twenty (nabídky, objednávky) | Schema doc |
| Otestovat Pohoda XML API (mServer connection) | Connection verified |
| n8n: první webhook test (Twenty → Missive) | Proof of concept |

**Go/No-Go Gate 0:**
- [ ] Twenty CRM je dostupný a stabilní
- [ ] Data mapping je kompletní (všechny klíčové fieldy)
- [ ] Pohoda mServer endpoint je dosažitelný
- [ ] n8n může číst z Twenty a psát do Pohody

---

### Phase 1: CRM Core (2–3 týdny) — PARALELNÍ PROVOZ

**Cíl:** Firmy, kontakty, deals — production ready v Twenty

| Akce | Výstup |
|------|--------|
| Migrace firem (BlueJet 225 → Twenty Companies) | Data in Twenty |
| Migrace kontaktů (BlueJet 222 → Twenty People) | Data in Twenty |
| Nastavit custom objects: Příležitosti, pipeline stages | Objects defined |
| n8n: sync new contacts BlueJet → Twenty (read-only) | Live sync |
| Missive ↔ Twenty CRM kontext integrace | Comms enriched |
| Training uživatele na Twenty UI | User ready |

**Go/No-Go Gate 1:**
- [ ] 100% firem a kontaktů v Twenty (verified row count)
- [ ] Nové záznamy v BlueJet se synchronizují do Twenty
- [ ] Uživatel zvládá denní CRM workflow v Twenty

---

### Phase 2: Obchodní flow (3–4 týdny) — CUTOVER READY

**Cíl:** Nabídky + objednávky + produkty — bez BlueJet pro nové záznamy

| Akce | Výstup |
|------|--------|
| Custom object: Nabídka (ekvivalent BlueJet 293) | Object + fields |
| Custom object: Objednávka (ekvivalent BlueJet 356) | Object + fields |
| Medusa: migrace produktů (BlueJet 217 → Medusa) | Products in Medusa |
| Medusa: nastavit B2B ceníky pro zákazníky | Price lists |
| Medusa: warehouse setup (sklady 437 → Medusa locations) | Warehouses |
| n8n: objednávka Medusa → faktura Pohoda (XML) | XML bridge live |
| n8n: Twenty CRM nabídka → Pohoda (XML) | Quote sync |
| Pilot: 5 reálných objednávek přes nový stack | Validation |

**Go/No-Go Gate 2:**
- [ ] 5 objednávek zpracováno end-to-end bez BlueJet
- [ ] Pohoda přijímá faktury ze stacku (XML)
- [ ] Medusa warehouse tracking reflektuje realitu
- [ ] Žádná ztráta dat (audit log OK)

---

### Phase 3: Decommission BlueJet (1–2 týdny)

**Cíl:** BlueJet = read-only archiv, nový stack je primary

| Akce | Výstup |
|------|--------|
| Nastavit BlueJet na BLUEJET_READ_ONLY=1 | Read-only mode |
| Přesunout všechny aktivní záznamy do Twenty/Medusa | Data complete |
| Qdrant: spustit nightly mirror z Twenty (místo BlueJet) | New mirror |
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

1. **Pohoda verze a mServer endpoint**
   - Jaká verze Pohody je v produkci?
   - Je mServer aktivní a dostupný na síti?
   - Je dostupný REST addon (Pohoda REST API) nebo pouze XML mServer?

2. **Hosting rozhodnutí**
   - Bude Twenty CRM + Medusa na NAS nebo na VPS?
   - NAS Synology 423+ má dostatek RAM pro +2 Docker stacks?
   - Alternativa: Cloudflare tunnel pro Twenty (jako n8n)?

3. **Zákaznická data v Meduse**
   - Mají zákazníci dostat self-service B2B portál (Medusa storefront)?
   - Nebo Medusa slouží pouze jako internal catalog + warehouse (bez zákaznického UI)?

### Důležité (blokují Phase 2)

4. **Quotes custom object nebo Frappe CRM?**
   - Twenty CRM nemá nativní quotes — custom object je dostačující pro objem Premium Gastro?
   - Alternativa: Frappe CRM (nativní quotes, ale AGPL + MariaDB)

5. **Czech invoicing**
   - Má Pohoda přijímat faktury přímo (XML mServer)?
   - Nebo je potřeba ISDOC formát pro někoho dalšího?
   - Pokud jen Pohoda: n8n XML bridge stačí

6. **BlueJet Qdrant mirror — kdy zastavit?**
   - Fáze 1-2 aktuálně buduje `index_bluejet_qdrant.py` mirror
   - Po Phase 3 cutover: přejít na Twenty CRM mirror
   - Kdy je OK zastavit BlueJet mirror? (Phase 3 gate?)

### Nízká priorita (post-cutover)

7. **FIFO costing** — Medusa nemá FIFO nativně; bude to potřeba nebo stačí average cost?
8. **Reporting** — Zůstane analytics v Postgres DWH nebo bude potřeba BI tool (Metabase)?
9. **Cloudflare tunnel** — Twenty CRM bude exposed přes tunnel nebo VPN only?

---

## Příloha: Stack souhrn

| Vrstva | Nástroj | Licence | DB |
|--------|---------|---------|-----|
| CRM + pipeline | Twenty CRM | Apache 2.0 | Postgres 16 |
| B2B ordering + catalog | Medusa v2 | MIT | Postgres + Redis |
| Orchestrace | n8n (stávající) | Sustainable (self-host free) | Postgres |
| Účetnictví SoR | Pohoda | Proprietary | — |
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
- Twenty CRM (NAS Docker)
- Medusa v2 (NAS Docker)
- n8n Pohoda XML connector (new workflow)
- n8n Twenty CRM connector (community node setup)
