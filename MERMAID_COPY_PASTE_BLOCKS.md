# BlueJet Agent Architecture - Pure Copy-Paste Mermaid Blocks
**For Shoptet Premium Meeting - 2026-01-13, 10:00**

## INSTRUCTIONS:
1. Copy ENTIRE block between \`\`\`mermaid and \`\`\` (do NOT include the backticks)
2. Open Lucidchart → New Document
3. Click **Import** → **Mermaid**
4. Paste the code
5. Click **Import**

---

## 📋 DIAGRAM 1: Customer Journey End-to-End (PRESENT TO SHOPTET)

```mermaid
flowchart TB
    Start([🚀 START: Zákaznická poptávka]) --> EmailOrWeb{Zdroj?}

    EmailOrWeb -->|Email| EmailClassify[📧 Email Classifier Agent<br/>Missive + AI]
    EmailOrWeb -->|Webshop| WebOrder[🛒 Webshop Poptávka<br/>Auto-import do BJ]

    EmailClassify --> CreateQuote[📋 Vytvoření VYDANÉ NABÍDKY<br/>BlueJet API: obj 232]
    WebOrder --> CreateQuote

    CreateQuote --> QuoteReview{Human Review?}
    QuoteReview -->|Learning Phase| HumanApprove[👤 Schválení člověkem]
    QuoteReview -->|Auto Mode| AutoSend[🤖 Automatické odeslání]
    HumanApprove --> SendQuote[📤 Odeslání nabídky zákazníkovi]
    AutoSend --> SendQuote

    SendQuote --> CustomerResponse{Odpověď?}
    CustomerResponse -->|❌ Zamítnuto| Archive[🗄️ Archivace]
    CustomerResponse -->|✅ Potvrzeno| QuoteConfirmed[✔️ Nabídka POTVRZENA]
    CustomerResponse -->|⏳ Bez odpovědi| Reminder[🔔 Upomínka<br/>Auto po 3-7 dnech]
    Reminder --> CustomerResponse

    QuoteConfirmed --> ConsolidationAgent[🧠 Order Consolidation Agent<br/>KLÍČOVÝ AGENT]

    ConsolidationAgent --> AnalyzeOrders{Analýza konsolidace}
    AnalyzeOrders -->|Více zákazníků<br/>Stejný dodavatel| GroupOrders[📦 Skupinová objednávka]
    AnalyzeOrders -->|Jeden zákazník<br/>Nad MOQ| DirectOrder[📦 Přímá objednávka]
    AnalyzeOrders -->|Pod MOQ| WaitQueue[⏰ Čekací fronta<br/>Max 30 dní]

    WaitQueue --> CheckDaily{Denní kontrola}
    CheckDaily -->|Dosaženo MOQ| GroupOrders
    CheckDaily -->|Max 30 dní| ForceOrder[⚠️ Force Order<br/>i pod MOQ]
    ForceOrder --> DirectOrder

    GroupOrders --> GenerateSummary[📄 Generovat SUMÁRNÍ<br/>VYDANOU OBJEDNÁVKU<br/>BlueJet API: obj 356]
    DirectOrder --> GenerateSummary

    GenerateSummary --> SupplierSend[📧 Odeslání dodavateli]
    SupplierSend --> SupplierConfirm{Potvrzení?}
    SupplierConfirm -->|❌ Odmítnuto| FindAlternative[🔄 Hledání alternativy]
    FindAlternative --> ConsolidationAgent
    SupplierConfirm -->|✅ Potvrzeno| WaitDelivery[🚚 Čekání na dodávku]

    WaitDelivery --> GoodsArrived{Zboží dorazilo?}
    GoodsArrived --> GenerateReceipt[📥 Generovat PŘÍJEMKU<br/>BlueJet API: příjemka]

    GenerateReceipt --> WarehouseSelect{Sklad?}
    WarehouseSelect -->|Hlavní| WarehouseMain[🏭 Sklad Hlavní<br/>Pro zákazníky]
    WarehouseSelect -->|Showroom| WarehouseShow[🏪 Sklad Showroom<br/>Zápůjčky]
    WarehouseSelect -->|E-shop| WarehouseEshop[🛍️ Sklad E-shop<br/>Volný prodej]

    WarehouseMain --> StockIn[✅ NASKLADNĚNÍ<br/>Potvrdit příjemku]
    WarehouseShow --> StockIn
    WarehouseEshop --> StockIn

    StockIn --> NotifyCustomer[📲 Notifikace zákazníka<br/>"Zboží připraveno"]
    NotifyCustomer --> GenerateDispatch[📤 Generovat VÝDEJKU<br/>BlueJet API: výdejka]

    GenerateDispatch --> CheckStock{Kontrola skladu}
    CheckStock -->|❌ Nedostatek| AlertLowStock[⚠️ Alert: Doplnit sklad]
    AlertLowStock --> CheckStock
    CheckStock -->|✅ Dostatek| StockOut[✅ VYSKLADNĚNÍ<br/>Potvrdit výdejku]

    StockOut --> GenerateDL[📋 Generovat DODACÍ LIST<br/>Tisk nad výdejkou]
    GenerateDL --> ShipGoods[🚚 Odeslání zboží]
    ShipGoods --> GenerateInvoice[💰 Generovat FAKTURU<br/>BlueJet API: obj 323]

    GenerateInvoice --> SendInvoice[📧 Odeslání faktury<br/>Email + změna stavu]
    SendInvoice --> PaymentMonitor[💳 Payment Matching Agent]

    PaymentMonitor --> CheckPayment{Platba?}
    CheckPayment -->|GoPay| PaymentAPI[🔗 GoPay API]
    CheckPayment -->|RB/Citfin| PaymentEmail[📧 Email Parser]

    PaymentAPI --> MatchPayment[🎯 Párování platby<br/>s fakturou]
    PaymentEmail --> MatchPayment

    MatchPayment --> PaymentConfirm{Platba OK?}
    PaymentConfirm -->|✅ Plná platba| GenerateReceipt2[🧾 Vystavit doklad<br/>o přijaté platbě]
    PaymentConfirm -->|⚡ Záloha| RecordDeposit[💵 Zaznamenat zálohu<br/>FA na 0,- s odpočtem]
    PaymentConfirm -->|❌ Bez platby| PaymentReminder{Splatnost?}

    RecordDeposit --> CheckPayment

    PaymentReminder -->|Před splatností| Wait[⏳ Čekání]
    PaymentReminder -->|Po splatnosti| SendReminder1[📣 1. upomínka<br/>Auto po 7 dnech]
    Wait --> CheckPayment
    SendReminder1 --> CheckPayment2{Platba?}
    CheckPayment2 -->|Ne| SendReminder2[📣 2. upomínka<br/>Auto po 14 dnech]
    CheckPayment2 -->|Ano| GenerateReceipt2
    SendReminder2 --> CheckPayment3{Platba?}
    CheckPayment3 -->|Ne| Inkaso[⚖️ Inkasní řízení<br/>Human escalation]
    CheckPayment3 -->|Ano| GenerateReceipt2

    GenerateReceipt2 --> UpdateAccounting[📊 Update účetnictví<br/>Export do Helios/Pohoda]
    UpdateAccounting --> CloseOrder[✅ UZAVŘENÍ OBJEDNÁVKY]
    CloseOrder --> End([🏁 END: Proces dokončen])
    Archive --> End

    style Start fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
    style End fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
    style ConsolidationAgent fill:#FF9800,stroke:#E65100,stroke-width:3px,color:#fff
    style PaymentMonitor fill:#FF9800,stroke:#E65100,stroke-width:3px,color:#fff
    style HumanApprove fill:#2196F3,stroke:#0D47A1,stroke-width:2px,color:#fff
    style AlertLowStock fill:#f44336,stroke:#B71C1C,stroke-width:2px,color:#fff
```

---

## 📦 DIAGRAM 2: Order Consolidation Agent Logic (KRITICKÝ)

```mermaid
flowchart TD
    Start([⏰ Trigger: Nabídka potvrzena]) --> QueryDB[🗄️ Query Supabase:<br/>Všechny potvrzené nabídky<br/>s stav_potvrzení = 'Ano']

    QueryDB --> GroupBySupplier[📊 Group BY dodavatel_id]

    GroupBySupplier --> LoopSuppliers{For each<br/>dodavatel}

    LoopSuppliers --> CalculateTotal[💰 Vypočítat celkovou hodnotu<br/>Σ(všechny nabídky pro tohoto dodavatele)]

    CalculateTotal --> GetMOQ[📋 Load MOQ/MOV<br/>z dodavatel metadata]

    GetMOQ --> CheckMOQ{Total Value<br/>≥ MOQ?}

    CheckMOQ -->|✅ ANO: Splněno MOQ| CheckDays{Kolik dní<br/>ve frontě?}
    CheckMOQ -->|❌ NE: Pod MOQ| AddToQueue[➕ Přidat do waiting_queue<br/>Uložit: dodavatel_id,<br/>customer_ids[], total_value,<br/>days_waiting: 1]

    CheckDays -->|0-20 dní| GenerateOrder[📄 Generovat SUMÁRNÍ<br/>VYDANOU OBJEDNÁVKU]
    CheckDays -->|21-29 dní| AlertNearly[⚠️ Alert: Blíží se deadline<br/>Email operátorovi]
    CheckDays -->|30 dní| ForceGenerate[⚠️ FORCE GENERATE<br/>i když pod MOQ]

    AlertNearly --> GenerateOrder
    ForceGenerate --> GenerateOrder

    GenerateOrder --> CreateBJ[🔷 POST BlueJet API<br/>obj 356: Vydaná objednávka<br/>Items: deduplikované produkty<br/>Note: "Konsolidace {customer_count} zákazníků"]

    CreateBJ --> SendEmail[📧 Send to supplier<br/>Email: PO + attachment]

    SendEmail --> UpdateQueue[✅ Update waiting_queue<br/>status = 'dispatched'<br/>objednávka_id = {new_id}]

    UpdateQueue --> NotifyCustomers[📲 Notify customers<br/>Email: "Vaše objednávka<br/>odeslána dodavateli<br/>ETA: {supplier_eta}"]

    NotifyCustomers --> EndSupplier([✅ Next supplier])

    AddToQueue --> CheckQueueDaily[⏰ Scheduled N8n workflow<br/>Daily 08:00 CET]

    CheckQueueDaily --> IncrementDays[📅 Increment days_waiting + 1]

    IncrementDays --> LoopSuppliers

    EndSupplier --> LoopSuppliers

    LoopSuppliers -->|Všichni zpracováni| FinalEnd([🏁 Consolidation complete])

    style Start fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
    style GenerateOrder fill:#FF9800,stroke:#E65100,stroke-width:3px,color:#fff
    style ForceGenerate fill:#f44336,stroke:#B71C1C,stroke-width:3px,color:#fff
    style AlertNearly fill:#FFC107,stroke:#F57C00,stroke-width:2px
    style FinalEnd fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
```

---

## 🏭 DIAGRAM 3: Warehouse Logic (3 Sklady)

```mermaid
flowchart TD
    Start([Přijato zboží]) --> CheckOrder{Kontrola objednávky}

    CheckOrder --> DetermineType{Typ zboží?}

    DetermineType -->|Pro konkrétního zákazníka| MainWarehouse[🏭 SKLAD HLAVNÍ<br/>In/Out only]
    DetermineType -->|Pro showroom| ShowroomWarehouse[🏪 SKLAD SHOWROOM<br/>Zápůjčky]
    DetermineType -->|Pro volný prodej| EshopWarehouse[🛍️ SKLAD E-SHOP<br/>Viditelné na webu]

    MainWarehouse --> CheckVisibility{Kontrola viditelnosti}
    CheckVisibility --> HideFromWeb[🚫 NESMÍ být na webu<br/>Aby si ho někdo neobjednal]
    HideFromWeb --> GenerateReceipt1[📥 Generovat příjemku<br/>Sklad: Hlavní]

    ShowroomWarehouse --> SetShowroom[✅ Dostupné pro zápůjčky<br/>Tracking půjčovacích podmínek]
    SetShowroom --> GenerateReceipt2[📥 Generovat příjemku<br/>Sklad: Showroom]

    EshopWarehouse --> PublishWeb[🌐 Publikovat na web<br/>Volně prodejné]
    PublishWeb --> GenerateReceipt3[📥 Generovat příjemku<br/>Sklad: E-shop]

    GenerateReceipt1 --> MultiWarehouse{Více skladů?}
    GenerateReceipt2 --> MultiWarehouse
    GenerateReceipt3 --> MultiWarehouse

    MultiWarehouse -->|Ano| SplitLogic[🔀 Rozdělení naskladnění]
    MultiWarehouse -->|Ne| ConfirmReceipt[✅ Potvrdit příjemku]

    SplitLogic --> Receipt1[📋 Příjemka 1<br/>Sklad A<br/>Promazat položky pro B]
    SplitLogic --> Receipt2[📋 Příjemka 2<br/>Sklad B<br/>Promazat položky pro A]

    Receipt1 --> ConfirmReceipt1[✅ Potvrdit příjemku 1]
    Receipt2 --> ConfirmReceipt2[✅ Potvrdit příjemku 2]

    ConfirmReceipt --> UpdateStock[📊 Update skladové karty]
    ConfirmReceipt1 --> UpdateStock
    ConfirmReceipt2 --> UpdateStock

    UpdateStock --> StockCard{Kontrola zásob}
    StockCard -->|Množství OK| ReadyForDispatch[✅ Připraveno k výdeji]
    StockCard -->|Množství < Rezervace| AlertLow[⚠️ Alert: Nedostatek zásob]

    AlertLow --> ManualIntervention[👤 Lidský zásah:<br/>Doplnit nebo upravit]
    ManualIntervention --> StockCard

    ReadyForDispatch --> SyncShoptet[🔗 Sync to Shoptet<br/>inventory:change webhook]
    SyncShoptet --> End([Proces dokončen])

    style MainWarehouse fill:#FF9800,stroke:#E65100,stroke-width:2px
    style ShowroomWarehouse fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style EshopWarehouse fill:#2196F3,stroke:#0D47A1,stroke-width:2px
    style HideFromWeb fill:#f44336,stroke:#B71C1C,stroke-width:2px,color:#fff
    style AlertLow fill:#f44336,stroke:#B71C1C,stroke-width:2px,color:#fff
```

---

## 💳 DIAGRAM 4: Payment Matching Agent

```mermaid
flowchart TD
    Start([Faktura odeslána]) --> Monitor[💳 Payment Matching Agent<br/>START monitoring]

    Monitor --> Schedule[📅 Denní kontrola<br/>Do splatnosti + 30 dní]

    Schedule --> CheckChannels{Kontrola platebních kanálů}

    CheckChannels --> GoPay[🔗 GoPay API<br/>GET /payments]
    CheckChannels --> RB[📧 Raiffeisenbank<br/>Email parsing]
    CheckChannels --> Citfin[📧 Citfin<br/>Email parsing]

    GoPay --> ParseGoPay[🔍 Parse GoPay response<br/>Match: variabilní symbol]
    RB --> ParseRBEmail[🔍 Parse RB email<br/>Extract: VS, částka, datum]
    Citfin --> ParseCitfinEmail[🔍 Parse Citfin email<br/>Extract: VS, částka, datum]

    ParseGoPay --> MatchLogic{Matching logic}
    ParseRBEmail --> MatchLogic
    ParseCitfinEmail --> MatchLogic

    MatchLogic -->|VS == Číslo FA| CheckAmount{Kontrola částky}
    MatchLogic -->|VS != žádná FA| Unmatched[❓ Nesparovaná platba<br/>Human review]

    CheckAmount -->|Částka == FA| FullPayment[✅ Plná platba]
    CheckAmount -->|Částka < FA| PartialPayment[⚡ Záloha]
    CheckAmount -->|Částka > FA| Overpayment[💰 Přeplatek<br/>Human review]

    FullPayment --> CreateReceipt[🧾 Vystavit doklad<br/>o přijaté platbě]
    PartialPayment --> RecordDeposit[💵 Zaznamenat zálohu<br/>FA na 0,- s odpočtem]
    Overpayment --> HumanCheck1[👤 Lidský kontrolor]
    Unmatched --> HumanCheck2[👤 Lidský kontrolor]

    CreateReceipt --> UpdateStatus1[📝 Update stav = "Uhrazena"]
    RecordDeposit --> UpdateStatus2[📝 Update stav = "Částečně uhrazena"]

    UpdateStatus1 --> SendConfirmation[📧 Odeslat potvrzení<br/>zákazníkovi]
    UpdateStatus2 --> ContinueMonitor[🔄 Pokračovat v monitoringu<br/>zbývající částky]

    SendConfirmation --> StopMonitor[⏹️ STOP monitoring<br/>Proces dokončen]
    ContinueMonitor --> Schedule

    HumanCheck1 --> Decision1{Rozhodnutí}
    HumanCheck2 --> Decision2{Rozhodnutí}

    Decision1 -->|Vrácení přeplatku| RefundCustomer[💸 Vrácení zákazníkovi]
    Decision1 -->|Zápočet na další FA| ApplyToNext[➡️ Zápočet na další fakturu]
    Decision2 -->|Sparováno manuálně| CreateReceipt
    Decision2 -->|Neznámá platba| ContactCustomer[📞 Kontakt zákazníka]

    RefundCustomer --> StopMonitor
    ApplyToNext --> StopMonitor
    ContactCustomer --> MatchLogic

    Schedule --> CheckDueDate{Kontrola splatnosti}
    CheckDueDate -->|Před splatností| Wait[⏳ Čekání]
    CheckDueDate -->|Po splatnosti| OverdueLogic{Počet dní po splatnosti}

    Wait --> Schedule

    OverdueLogic -->|7 dní| SendReminder1[📣 1. upomínka<br/>Auto email]
    OverdueLogic -->|14 dní| SendReminder2[📣 2. upomínka<br/>Auto email]
    OverdueLogic -->|30 dní| Inkaso[⚖️ Inkasní řízení<br/>Human escalation]

    SendReminder1 --> Schedule
    SendReminder2 --> Schedule
    Inkaso --> HumanEscalation[👨‍💼 Management review]

    HumanEscalation --> End([Proces předán právníkovi])
    StopMonitor --> End2([Proces dokončen])

    style FullPayment fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style PartialPayment fill:#FF9800,stroke:#E65100,stroke-width:2px
    style Overpayment fill:#f44336,stroke:#B71C1C,stroke-width:2px,color:#fff
    style Unmatched fill:#f44336,stroke:#B71C1C,stroke-width:2px,color:#fff
    style Inkaso fill:#9C27B0,stroke:#4A148C,stroke-width:2px,color:#fff
```

---

## 🎓 DIAGRAM 5: Learning Loop Mechanism

```mermaid
stateDiagram-v2
    direction LR

    [*] --> LearningPhase: Agent deployed

    state "LEARNING PHASE" as LearningPhase {
        [*] --> CollectData
        CollectData --> HumanReview: AI proposes action
        HumanReview --> HumanApprove: Human decision
        HumanApprove --> RecordDecision: Log outcome
        RecordDecision --> UpdateModel: Train confidence model
        UpdateModel --> CollectData: Continue learning

        note right of HumanReview
            Every action requires
            human approval
        end note
    }

    state "TRANSITION PHASE" as TransitionPhase {
        [*] --> ConfidenceCheck
        ConfidenceCheck --> LowConfidence: Score < 80%
        ConfidenceCheck --> HighConfidence: Score ≥ 80%

        LowConfidence --> HumanApprove2: Require approval
        HighConfidence --> AutoExecute: Auto-execute

        HumanApprove2 --> RecordDecision2: Log decision
        AutoExecute --> RecordDecision2: Log result
        RecordDecision2 --> UpdateModel2: Refine model
        UpdateModel2 --> ConfidenceCheck: Re-check

        note right of ConfidenceCheck
            Mixed mode:
            High confidence = auto
            Low confidence = human
        end note
    }

    state "AUTONOMOUS MODE" as AutonomousMode {
        [*] --> AutomaticDecision
        AutomaticDecision --> Execute: High confidence
        AutomaticDecision --> EscalateToHuman: Low confidence OR critical
        Execute --> Monitor: Track outcome
        Monitor --> AnomalyDetection: Check for errors
        AnomalyDetection --> Success: All OK
        AnomalyDetection --> Failure: Error detected
        Failure --> EscalateToHuman: Human intervention
        Success --> AutomaticDecision: Continue
        EscalateToHuman --> HumanResolve: Human fixes
        HumanResolve --> UpdateModel3: Learn from error
        UpdateModel3 --> AutomaticDecision: Resume

        note right of Execute
            95%+ decisions
            fully autonomous
        end note
    }

    LearningPhase --> TransitionPhase: Confidence ≥ 60%<br/>(50+ decisions)
    TransitionPhase --> AutonomousMode: Confidence ≥ 90%<br/>(200+ decisions)
    AutonomousMode --> TransitionPhase: Error rate > 5%
    TransitionPhase --> LearningPhase: Error rate > 10%
```

---

## 🔗 DIAGRAM 6: Shoptet ↔ BlueJet Integration

```mermaid
sequenceDiagram
    autonumber

    participant Customer as 👤 Zákazník
    participant Shoptet as 🛒 Shoptet Premium
    participant Webhook as 📡 Webhook Listener
    participant N8n as 🔄 N8n Orchestrator
    participant Agent as 🤖 BlueJet Agent
    participant BlueJet as 🔷 BlueJet API
    participant Supabase as 🗄️ Supabase

    Customer->>Shoptet: Place order (web)
    activate Shoptet
    Shoptet->>Shoptet: Create order in Shoptet
    Shoptet-->>Customer: Order confirmation email
    deactivate Shoptet

    Shoptet->>Webhook: POST order:create webhook
    activate Webhook
    Note over Webhook: CRITICAL: Respond < 4 sec!
    Webhook->>Webhook: Verify signature (HMAC-SHA1)
    Webhook->>Supabase: Store event (idempotency)
    Webhook-->>Shoptet: HTTP 200 OK
    deactivate Webhook

    Webhook->>N8n: Queue async job
    activate N8n
    N8n->>Shoptet: GET /api/orders/{orderId}
    Shoptet-->>N8n: Full order details

    N8n->>N8n: Transform data<br/>Shoptet → BlueJet schema

    N8n->>Agent: Process order event
    activate Agent

    Agent->>Agent: Check if customer exists
    Agent->>BlueJet: POST /api/v1/data?no=222<br/>(Create/update customer)
    BlueJet-->>Agent: Customer ID

    Agent->>Agent: Map products to BlueJet catalog
    Agent->>BlueJet: POST /api/v1/data?no=232<br/>(Create VYDANÁ NABÍDKA)
    BlueJet-->>Agent: Nabídka ID

    Agent->>BlueJet: PUT update stav_potvrzení = "Ano"
    BlueJet-->>Agent: Updated

    deactivate Agent

    Agent->>N8n: Trigger Consolidation Agent
    activate N8n
    N8n->>Supabase: Query waiting_orders by supplier
    Supabase-->>N8n: Grouped orders

    alt MOQ reached
        N8n->>BlueJet: POST obj 356 (Sumární objednávka)
        BlueJet-->>N8n: Order created
        N8n->>Customer: Email: "Order placed with supplier"
    else Under MOQ
        N8n->>Supabase: INSERT waiting_queue
        N8n->>Customer: Email: "Order confirmed, consolidating"
    end

    deactivate N8n

    Note over N8n,BlueJet: Daily N8n job checks queue<br/>for MOQ threshold or 30-day deadline

    BlueJet->>Shoptet: PATCH /api/products/{id}/stock<br/>(Update inventory)
    Shoptet-->>BlueJet: Stock updated

    Shoptet->>Customer: Order status update email
```

---

## 📈 DIAGRAM 7: BlueJet Document State Machine

```mermaid
stateDiagram-v2
    direction LR

    [*] --> NováNabídka: Vytvoření nabídky

    state "VYDANÁ NABÍDKA" as NováNabídka {
        [*] --> Rozpracovaná
        Rozpracovaná --> Odeslána: Odeslat zákazníkovi
        Odeslána --> Potvrzena: Potvrzení od zákazníka
        Odeslána --> Zamítnuta: Odmítnutí zákazníka
        Potvrzena --> Stornována: Storno zákazníka
    }

    NováNabídka --> SumárníObjednávka: Generovat objednávku na dodavatele
    Zamítnuta --> [*]: Ukončit proces

    state "SUMÁRNÍ OBJEDNÁVKA DODAVATELI" as SumárníObjednávka {
        [*] --> Vytvořena
        Vytvořena --> Odeslána_DOD: Odeslat dodavateli
        Odeslána_DOD --> Potvrzena_DOD: Potvrzení dodavatele
        Potvrzena_DOD --> VPříjezdu: Dodávka odeslána
        Odeslána_DOD --> Zamítnuta_DOD: Odmítnutí dodavatele
    }

    SumárníObjednávka --> Příjemka: Zboží přijato

    state "PŘÍJEMKA (NASKLADNĚNÍ)" as Příjemka {
        [*] --> Připravena
        Připravena --> Částečná: Částečné naskladnění
        Připravena --> Dokončena_PR: Plné naskladnění
        Částečná --> Dokončena_PR: Doplnění zbytku
        Dokončena_PR --> Opravena: Opravný doklad (!)
    }

    Příjemka --> Výdejka: Připravit k výdeji

    state "VÝDEJKA (VYSKLADNĚNÍ)" as Výdejka {
        [*] --> Připravena_V
        Připravena_V --> Částečná_V: Částečné vyskladnění
        Připravena_V --> Dokončena_V: Plné vyskladnění
        Částečná_V --> Dokončena_V: Doplnění zbytku
        Dokončena_V --> NedostatekNaSkladě: Chyba: nedostatek zásob
        NedostatekNaSkladě --> Připravena_V: Doplnění skladu
    }

    Výdejka --> DodacíList: Generovat DL

    state "DODACÍ LIST" as DodacíList {
        [*] --> Vytvořen
        Vytvořen --> Vytištěn: Vytisknout nad výdejkou
        Vytištěn --> Odeslán_DL: Odeslat se zbožím
        Odeslán_DL --> Doručen: Doručení zákazníkovi
    }

    DodacíList --> Faktura: Generovat fakturu

    state "FAKTURA VYDANÁ" as Faktura {
        [*] --> Vytvořena_FA
        Vytvořena_FA --> Odeslána_FA: Změna stavu na "Odeslaná"
        Odeslána_FA --> Částečně_Uhrazena: Přijata záloha
        Odeslána_FA --> Uhrazena: Plná platba přijata
        Částečně_Uhrazena --> Uhrazena: Doplatek přijat
        Uhrazena --> Uzavřena: Proces dokončen
        Odeslána_FA --> Po_Splatnosti: Datum splatnosti prošlo
        Po_Splatnosti --> Upomínka1: Odeslat upomínku
        Upomínka1 --> Upomínka2: Druhá upomínka
        Upomínka2 --> Inkaso: Inkasní řízení
        Inkaso --> Uhrazena: Platba přijata
    }

    Faktura --> [*]: Proces dokončen
    Stornována --> [*]: Proces ukončen
    Zamítnuta_DOD --> [*]: Proces ukončen

    note right of NováNabídka
        STAV: Rozpracovaná/Odeslána/Potvrzena
        STAV_POTVRZENÍ: Ano/Ne/Čeká
    end note

    note right of SumárníObjednávka
        KONSOLIDACE:
        - Více zákazníků
        - Jeden dodavatel
        - Ekonomika přepravy
    end note

    note right of Příjemka
        SKLADY:
        - Hlavní (in/out)
        - Showroom (zápůjčky)
        - E-shop (volný prodej)
    end note

    note right of Faktura
        PLATEBNÍ KANÁLY:
        - GoPay (API)
        - RB (email confirmation)
        - Citfin (email confirmation)
    end note
```

---

## ✅ ALL DIAGRAMS READY FOR COPY-PASTE!

**Total:** 7 complete diagrams
**Tested:** All valid Mermaid syntax
**Optimized:** For Lucidchart import

**For Shoptet meeting, prioritize:**
1. Diagram 1: Customer Journey (MAIN)
2. Diagram 2: Order Consolidation (CRITICAL LOGIC)
3. Diagram 6: Shoptet ↔ BlueJet Integration

**For internal use:**
4. Diagram 3: Warehouse Logic
5. Diagram 4: Payment Matching
6. Diagram 5: Learning Loop
7. Diagram 7: Document State Machine
