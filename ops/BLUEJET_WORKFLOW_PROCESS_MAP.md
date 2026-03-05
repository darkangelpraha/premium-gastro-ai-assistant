# BlueJet — Kompletní procesní mapa obchodního workflow

**Vytvořeno**: 2026-02-16
**Zdroje**: BlueJet API (11 534 nabídek, 3 448 objednávek, 9 114 faktur), export skripty, CLAUDE.md
**Účel**: Referenční dokument pro ABJ agenta — přesné kroky, checklisty, návaznosti

---

## Stavový automat nabídky (evidence 293)

Pole `pole150219155621supl` = custom workflow stav nabídky.

```
┌─────────────────┐
│   (empty)       │  Nově vytvořená nabídka, zatím bez stavu
│   Probíhající   │
└────────┬────────┘
         │ Nabídka zpracována, odeslána klientovi
         ▼
┌─────────────────┐
│  1. v řešení    │  Nabídka odeslána klientovi, čeká se na odpověď
│  statuscode:    │
│  Odeslaná       │
└────────┬────────┘
         │ Klient potvrdil
         ▼
┌─────────────────────┐
│  4. objednat        │  Klient nabídku akceptoval → je třeba objednat u dodavatele
│  statuscode:        │
│  Potvrzená          │
└────────┬────────────┘
         │ Sumární objednávka vytvořena na dodavatele
         ▼
┌─────────────────────┐
│  5. objednaná       │  Objednávka (356) odeslána dodavateli, čeká se na dodání
│  statuscode:        │
│  Potvrzená          │
└────────┬────────────┘
         │ Zboží dorazilo → příjemka (naskladnění)
         ▼
┌───────────────────────────────────────────────┐
│  7. naskladněná - odeslat zákazníkovi         │  Zboží na skladě, ready k expedici
│  statuscode: Potvrzená                        │
│  ALTERNATIVA:                                 │
│  8. naskladněná - osobní odběr                │  Zákazník si vyzvedne osobně
└────────┬──────────────────────────────────────┘
         │ Výdejka + dodací list + faktura + TopTrans
         ▼
┌─────────────────────┐
│  9. vyřízená        │  Kompletně dokončená nabídka
│  statuscode:        │  (odesláno, fakturováno, zaplaceno)
│  Potvrzená          │
└─────────────────────┘

   VEDLEJŠÍ STAVY:
   ┌──────────────────┐
   │  10. Vrácená     │  Zákazník vrátil zboží / reklamace
   │  statuscode:     │
   │  Odeslaná        │
   └──────────────────┘
   ┌──────────────────┐
   │  ..              │  Stornovaná / zamítnutá / neaktivní
   │  statuscode:     │
   │  Stornovaná /    │
   │  Zamítnutá       │
   └──────────────────┘
```

---

## Hlavní flow — od nabídky po expedici

### KROK 1: Vytvoření nabídky

**Kde**: Evidence 293 (Nabídky)
**Stav**: `(empty)` / `Probíhající`

**Checklist**:

- [ ] Vybrat zákazníka (`customerid` → evidence 225)
- [ ] Zadat dodací adresu (`prijemcezboziadsupl` → evidence 243)
- [ ] Přidat položky nabídky (evidence 291)
- [ ] Pro každou položku: produkt (`productid` → 217), množství, cena nákup/prodej
- [ ] Ověřit ceníkové ceny vs. zadané ceny
- [ ] Nastavit měnu a kurz
- [ ] Nastavit platební podmínky
- [ ] Nastavit způsob dopravy

**Výstup**: Nabídka s kódem `kodnabidky` (např. `692/2025`)

---

### KROK 2: Odeslání nabídky klientovi

**Stav**: `(empty)` → `1. v řešení`
**statuscode**: → `Odeslaná`

**Checklist**:

- [ ] Zkontrolovat kombinovaný náhled (preview nabídky)
- [ ] Ověřit správnost cen, položek, adres
- [ ] Vygenerovat PDF nabídky (šablona)
- [ ] Odeslat email klientovi s PDF přílohou
- [ ] Nastavit stav na `1. v řešení`

**Poznámky**:

- Email jde na adresu z firmy (`emailaddress1`) nebo kontaktu
- Příloha = PDF z BlueJet šablony

---

### KROK 3: Klient potvrdil → objednat u dodavatele

**Stav**: `1. v řešení` → `4. objednat`
**statuscode**: → `Potvrzená`

**Checklist**:

- [ ] Klient potvrdil nabídku (email/telefon)
- [ ] Zkontrolovat dostupnost položek
- [ ] Nastavit stav na `4. objednat`

---

### KROK 4: Vytvoření sumární objednávky na dodavatele

**Kde**: Evidence 356 (Objednávky)
**Stav nabídky**: `4. objednat` → `5. objednaná`

**Checklist**:

- [ ] Vytvořit sumární objednávku (356) z nabídky (293)
  - Agregace položek na dodavatele
  - Název: `Sumární objednávka {Dodavatel}`
  - `kodobjednavky`: auto-generováno (např. `ORDER13/2025`)
- [ ] Přenést položky do evidence 354 (Položky objednávek)
  - `productid`, `mnozstvi`, `cenanakup`, `cenaprodej`
- [ ] Odeslat objednávku dodavateli
- [ ] Nastavit stav nabídky na `5. objednaná`
- [ ] Na objednávce: `datumpotvrzeni` = datum potvrzení dodavatelem

**Vazby**:

- Objednávka (356) → `customerid` = dodavatel (225)
- Objednávka (356) → `opportunityid` = příležitost (209), pokud existuje
- Položky objednávky (354) → `productid` = produkt (217)

---

### KROK 5: Příjemka — naskladnění

**Kde**: Evidence 437 (Sklady) + 441 (Skladové karty)
**Stav nabídky**: `5. objednaná` → `7. naskladněná - odeslat zákazníkovi`

**Checklist**:

- [ ] Zboží fyzicky dorazilo od dodavatele
- [ ] Zkontrolovat kompletnost dodávky vs. objednávka
- [ ] Vytvořit příjemku v BlueJet
  - Zvýšení `mnozstvi` na skladové kartě (441) pro každý produkt
  - Aktualizace `mnozstvidisponibilni`
  - Záznam FIFO ceny (`cenajednotkova`)
- [ ] Ověřit shodu množství příjemka vs. objednávka
- [ ] Nastavit stav nabídky:
  - `7. naskladněná - odeslat zákazníkovi` (doprava)
  - `8. naskladněná - osobní odběr` (osobní odběr)

**Skladové karty (441) — klíčová pole**:

- `skladkartaid`: ID karty
- `productid`: vazba na produkt (217)
- `skladid`: vazba na sklad (437)
- `mnozstvi`: aktuální stav
- `mnozstvirezervovane`: rezervováno pro nabídky
- `mnozstviobjednane`: objednáno od dodavatele
- `mnoszstvidisponibilni`: dostupné (mnozstvi - rezervovane)

---

### KROK 6: Výdejka + dodací list (DL) + faktura

**Kde**: Nabídka (293), Faktura (323), Skladové karty (441)
**Stav nabídky**: `7. naskladněná - odeslat zákazníkovi` → `9. vyřízená`

**Trigger**: Změna stavu na "odeslat zákazníkovi" / manuální akce

#### 6a: Výdejka (vyskladnění)

**Checklist**:

- [ ] Vytvořit výdejku v BlueJet
  - Snížení `mnozstvi` na skladové kartě (441) pro každý produkt
  - Kontrola, že `mnoszstvidisponibilni` >= požadované množství
- [ ] Ověřit shodu vyskladněných položek vs. nabídka

#### 6b: Dodací list (DL)

**Checklist**:

- [ ] Vygenerovat dodací list (PDF) z BlueJet šablony
- [ ] DL obsahuje:
  - Příjemce (adresa z cascade: `prijemcezboziadsupl` → `mainprijemcezboziadsupl` → `prijemadd` → `prijemfakturyadd`)
  - Položky: název, množství, jednotka
  - Kód nabídky jako reference
- [ ] Přiložit DL ke zásilce

#### 6c: Faktura

**Kde**: Evidence 323 (Vydané faktury) + 324 (Položky faktur)
**Checklist**:

- [ ] Vytvořit fakturu (323) z nabídky/výdejky
  - Přenést položky do evidence 324
  - `cenaprodej`, `cenadphprodej`, `mena`, `kurz`
  - Fakturační adresa: `prijemfakturyadd` (243)
- [ ] Ověřit DPH (pole `paytaxes`, `rozpisdphsupl`)
- [ ] Vygenerovat PDF faktury
- [ ] Odeslat fakturu emailem zákazníkovi
  - Email: `emailaddress1` z firmy (225) nebo kontaktu (222)
- [ ] Statuscode faktury: `Potvrzená`

---

### KROK 7: Expedice přes TopTrans

**Kdy**: Denně v 10:00 — nabídky se stavem `7. naskladněná - odeslat zákazníkovi`

**Automatizovaný flow (existující skripty)**:

#### 7a: Export z BlueJet do TopTrans JSON

**Skript**: `tools/logistics/bluejet_export_toptrans.py`

```bash
python3 tools/logistics/bluejet_export_toptrans.py \
  --offer-code "692/2025" \
  --kg 10 \
  --pack-quantity 1 \
  --avizo
```

**Co skript dělá**:

1. Najde nabídku (293) podle `kodnabidky`
2. Vezme shipping adresu (cascade: `prijemcezboziadsupl` → `mainprijemcezboziadsupl` → `prijemadd` → `prijemfakturyadd`)
3. Načte detaily adresy (243): `recipient`, `town`, `street1`, `zipcode`
4. Načte firmu (225): `contactperson1`, `mobilephone`, `emailaddress1`, `ico`, `dic`
5. Vytvoří `shipments.json` s TopTrans-kompatibilním payloadem

**Checklist**:

- [ ] Ověřit, že nabídka má vyplněnou dodací adresu
- [ ] Ověřit, že zákazník má telefon a email (pro avízo)
- [ ] Zadat váhu (`--kg`)
- [ ] Zadat počet balíků (`--pack-quantity`)

#### 7b: Vytvoření TopTrans zásilky

**Skript**: `tools/logistics/toptrans_labels.py`

```bash
# Dry-run (kontrola bez odeslání):
python3 tools/logistics/toptrans_labels.py \
  --input ops/_local/toptrans/shipments.json \
  --mode draft --dry-run

# Draft (vytvoří neodeslaný order + tiskne štítky):
python3 tools/logistics/toptrans_labels.py \
  --input ops/_local/toptrans/shipments.json \
  --mode draft

# Send (odešle order do TOPIS = reálné odeslání):
python3 tools/logistics/toptrans_labels.py \
  --input ops/_local/toptrans/shipments.json \
  --mode send
```

**Co skript dělá**:

1. `order/price` — cenová kalkulace dopravy
2. `order/save` — vytvoří draft zásilku v TopTrans
3. `order/send` (mode=send) — odešle do TOPIS systému
4. Stáhne štítkové PDF
5. Zapisuje audit log (`toptrans_audit.jsonl`) pro idempotenci

**Checklist**:

- [ ] Spustit `--dry-run` jako kontrolu
- [ ] Zkontrolovat adresy a kontakty ve výstupu
- [ ] Spustit `--mode draft` pro štítky
- [ ] Vytisknout štítky (PDF z `ops/_local/toptrans/out/`)
- [ ] Nalepit štítky na balíky
- [ ] Spustit `--mode send` pro odeslání do TOPIS
- [ ] Ověřit tracking kódy v TopTrans ZP portálu

#### 7c: Kontrola tracking kódů

**Checklist**:

- [ ] Zkontrolovat `toptrans_audit.jsonl` — `event: sent`, `order_number`, `item_number`
- [ ] Ověřit v TopTrans ZP portálu, že zásilky mají status "Odesláno"
- [ ] Zaslat tracking kódy zákazníkům (email)
- [ ] Nastavit stav nabídky na `9. vyřízená`

---

### KROK 8: Stav "Vyřízená"

**Stav**: `9. vyřízená`

**Co to znamená**:

- Zboží odesláno zákazníkovi ✅
- Dodací list přiložen ✅
- Faktura vystavena a odeslána ✅
- Tracking kód zaslán ✅
- Platba (dle platebních podmínek — sledovat splatnost)

---

## Denní rutina (10:00 ráno)

### Ranní expedice workflow

```
10:00  Zkontrolovat nabídky se stavem "7. naskladněná - odeslat zákazníkovi"
         │
         ├─ Pro každou nabídku:
         │    1. Výdejka (vyskladnění)
         │    2. Dodací list (PDF)
         │    3. Faktura (PDF) → email zákazníkovi
         │    4. Export → TopTrans JSON (bluejet_export_toptrans.py)
         │
         ├─ Batch: Všechny zásilky do jednoho shipments.json
         │    5. toptrans_labels.py --dry-run (kontrola)
         │    6. toptrans_labels.py --mode draft (štítky)
         │    7. Tisk štítků
         │    8. toptrans_labels.py --mode send (odeslání do TOPIS)
         │
         └─ Po odeslání:
              9. Ověřit tracking kódy (audit log + ZP portál)
              10. Zaslat tracking kódy zákazníkům
              11. Nastavit stav nabídek na "9. vyřízená"
```

---

## Osobní odběr workflow

Pro nabídky se stavem `8. naskladněná - osobní odběr`:

1. Kontaktovat zákazníka — domluvit termín odběru
2. Při odběru:
   - [ ] Výdejka (vyskladnění)
   - [ ] Dodací list (podpis zákazníka)
   - [ ] Faktura (vytisknout nebo email)
3. Nastavit stav na `9. vyřízená`

---

## Vrácení zboží (stav 10)

**Stav**: `10. Vrácená`

1. Zákazník nahlásí vrácení/reklamaci
2. Domluvit způsob vrácení (doprava zpět / osobní)
3. Příjemka vráceného zboží → naskladnění
4. Dobropis faktury (evidence 323, statuscode: `Dobropisovaná`)
5. Nastavit stav na `10. Vrácená`

---

## Mapa evidencí a jejich vazeb

```
Firmy (225) ◄────────────────── Kontakty (222)
  │ customerid                    │ contactid
  │                               │
  ▼                               ▼
Nabídky (293) ◄─── Produkty (217)
  │ nabidkaid       productid │
  │                           │
  ├─► Položky nabídek (291)   │
  │     productid ────────────┘
  │
  ├─► Adresy (243)
  │     prijemcezboziadsupl → addressid
  │
  ├─► Objednávky (356) ◄─── na dodavatele
  │     │ objednavkaid
  │     └─► Položky objednávek (354)
  │
  ├─► Sklady (437) / Skladové karty (441)
  │     příjemka / výdejka
  │
  ├─► Faktury (323)
  │     │ fakturaid
  │     └─► Položky faktur (324)
  │
  └─► Přílohy (341)
        soubory, PDFka, šablony
```

---

## Shipping address cascade (priorita)

Při určování dodací adresy se použije **první neprázdná** z:

1. `prijemcezboziadsupl` — explicitní dodací adresa
2. `mainprijemcezboziadsupl` — hlavní dodací adresa
3. `prijemadd` — adresa příjemce
4. `prijemfakturyadd` — fakturační adresa (fallback)

Každá z těchto hodnot je GUID → evidence 243 (Adresy): `recipient`, `town`, `street1`, `zipcode`

---

## Statusy napříč evidencemi

### Nabídky (293) — `statuscode`

| Status | Význam |
|--------|--------|
| Probíhající | Rozpracovaná |
| Odeslaná | Odeslána klientovi |
| Potvrzená | Klient akceptoval |
| Stornovaná | Zrušená |
| Zamítnutá | Klient odmítl |
| Vzor | Šablona/vzor |

### Nabídky (293) — `pole150219155621supl` (custom)

| Stav | Význam | Další akce |
|------|--------|------------|
| (empty) | Nová / rozpracovaná | Dokončit a odeslat |
| 1. v řešení | Odeslána klientovi | Čekat na odpověď |
| 4. objednat | Potvrzená klientem | Vytvořit objednávku na dodavatele |
| 5. objednaná | Objednáno u dodavatele | Čekat na dodání |
| 7. naskladněná - odeslat zákazníkovi | Na skladě | Výdejka + DL + FA + TopTrans |
| 8. naskladněná - osobní odběr | Na skladě | Kontaktovat zákazníka, osobní odběr |
| 9. vyřízená | Dokončeno | Sledovat platbu |
| 10. Vrácená | Vrácení/reklamace | Dobropis, naskladnit zpět |
| .. | Neaktivní/stornovaná | — |

### Objednávky (356) — `statuscode`

| Status | Význam |
|--------|--------|
| Odeslaná | Odeslána dodavateli |
| Potvrzená | Dodavatel potvrdil |

### Faktury (323) — `statuscode`

| Status | Význam |
|--------|--------|
| Potvrzená | Platná faktura |
| Dobropisovaná | Vystavený dobropis |
| Stornovaná | Zrušená |

---

## ABJ automatizace — co lze automatizovat

### Již implementováno

- ✅ Export nabídky → TopTrans JSON (`bluejet_export_toptrans.py`)
- ✅ Vytvoření TopTrans zásilky + štítky (`toptrans_labels.py`)
- ✅ Idempotence přes audit log
- ✅ Dry-run režim pro bezpečnost
- ✅ BlueJet MCP server pro API přístup

### K implementaci (ABJ agent)

- [ ] **Denní ranní batch**: v 10:00 vzít všechny nabídky se stavem `7` → provést celý export+send flow
- [ ] **Automatická změna stavů**: po úspěšném odeslání → `9. vyřízená`
- [ ] **Email s tracking kódy**: po `order/send` → extrahovat tracking → email zákazníkovi
- [ ] **Monitoring**: kontrola, že všechny zásilky z rána mají tracking
- [ ] **Výdejka + DL + FA**: automatizace vytvoření těchto dokumentů v BlueJet
- [ ] **Upozornění**: nabídky ve stavu `5. objednaná` > 7 dní → upozornit na zpožděnou dodávku

---

## Poznámky

- Čísla stavů (1, 4, 5, 7, 8, 9, 10) nejsou sekvenční — chybí 2, 3, 6 (možná dříve existovaly nebo jsou nepoužívané)
- Pole `..` v custom stavu odpovídá stornovaným/zamítnutým nabídkám
- `statuscode` je BJ nativní stav, `pole150219155621supl` je business workflow stav — oba se musí správně nastavit
- BlueJet API `fields` parametr nefunguje u všech evidencí (293 vrací 400)
- MCP server má 200k char limit na response — pro velké dotazy použít menší `limit`
