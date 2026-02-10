# Depoto Support Email Draft (API + STP + BlueJet)

Subject: Depoto API integration for Premium Gastro (BlueJet now, Shoptet Premium later)

Dobrý den,

jmenuji se Petr Svejkovský (Premium Gastro). V současnosti běží BlueJet (BJ) + custom web, stavíme Shoptet Premium (STP) jako náhradu custom webu a části BJ.

Potřebujeme zavést lean integraci Depoto pro expedici a sklad, s minimem ruční práce.

Co jsme ověřili z veřejných zdrojů:
- Depoto API je GraphQL + OAuth2 (repo `TomAtomCZ/depotoPhpClient`).
- Depoto má webhooks na události (nastavení přes checkout `eventUrl`).
- `paymentItems.isPaid` je potřeba posílat explicitně, jinak se objednávky mohou chovat jako zaplacené.

Prosím o potvrzení a doplnění konkrétních detailů pro produkční nasazení:

1) Přístup a prostředí
- Jaké je správné base URL pro náš tenant a doporučené test/stage prostředí?
- Jak získat produkční přihlašovací údaje pro API (uživatel/heslo nebo jiný typ)?
- Máme použít stejné OAuth client ID/secret jako ve `depotoPhpClient`, nebo poskytnete vlastní?

2) Nejbezpečnější integrační postup pro náš use-case
- Doporučujete využít STP integraci, pokud existuje, nebo přímé API?
- Pokud STP integrace existuje, prosím o přesný seznam synchronizovaných dat a limitů.

3) BJ -> Depoto (expedice)
- Cíl: v BJ bude tlačítko, které odešle objednávku do Depota, podobně jako dnes "tisk" a "email".
- Cíl: možnost automatického odeslání, jakmile je splněn předchozí krok.
- Kapacitní plánování: je možné posílat objednávky dopředu tak, aby byly viditelné, ale nezačaly se vyskladňovat (typicky gate přes `isPaid=false`)? Potvrďte prosím správnou a doporučenou metodu.

4) Depoto -> BJ (tracking a stavy)
- Cíl: po předání dopravci vrátit trackovací kódy a stav objednávky zpět do BJ.
- Prosím potvrďte nejlepší eventy a doporučené timeouty/retry chování webhooků.

5) Sklad a příjemky
- Depoto předpokládá, že sklad je správně a aktuálně veden.
- Potřebujeme dohodnout, kde má být "zdroj pravdy" pro sklad během přechodu.
- Prosím potvrďte doporučený model a případně jak nejlépe řešit příjemky a skladové pohyby přes API.

Jakmile tyto body potvrdíme, navrhneme konkrétní datový model a harmonogram nasazení.

Děkuji,
Petr Svejkovský
Premium Gastro
