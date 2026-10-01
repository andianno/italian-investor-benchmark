# Italian Investor Benchmark: SWDA vs VWCE vs VALL

Simulatore quantitativo e probabilistico in Python per l'analisi del rischio e dei rendimenti reali a lungo termine (2000–2025) delle tre principali strategie passive ad accumulazione su azionario globale:

1. **Sviluppati Large & Mid Cap** — Proxy di **iShares Core MSCI World (SWDA)**.
2. **Globale Large & Mid Cap (Sviluppati + Emergenti)** — Proxy di **Vanguard FTSE All-World (VWCE)**.
3. **Globale All-Cap (Sviluppati + Emergenti + Small Cap)** — Proxy di **Vanguard FTSE Global All Cap (VALL)**.

Il progetto supera l'arbitrarietà dei tradizionali backtest su singolo percorso (*starting point bias* del 2000), focalizzandosi interamente sulla **distribuzione empirica a finestre mobili (*Rolling Windows*)** al netto dell'**inflazione italiana reale (CPI FOI)** e misurando non solo il rendimento a scadenza, ma il **tempo effettivo trascorso con un potere d'acquisto inferiore al capitale versato**.

---

## 1. Il Dilemma dell'Investitore Globale

Chi alloca il proprio patrimonio sull'azionario globale si trova tipicamente davanti a tre livelli di diversificazione:

| Strategia / Proxy | Benchmark di Riferimento | Copertura Geografica | Segmento di Capitalizzazione | Tesi di Investimento |
| :--- | :--- | :--- | :--- | :--- |
| **SWDA** *(MSCI World)* | MSCI World Net Total Return EUR | Paesi Sviluppati (~23 paesi) | Large & Mid Cap (~85% mercato) | Massima efficienza, governance consolidata, zero rischio giurisdizionale e di controllo dei capitali degli emergenti. |
| **VWCE** *(FTSE All-World)* | MSCI ACWI Net Total Return EUR *(proxy)* | Sviluppati + Emergenti (~47 paesi) | Large & Mid Cap (~85-90% mercato) | Neutralità geografica globale; esposizione alla crescita economica e demografica dei mercati emergenti. |
| **VALL** *(FTSE All Cap)* | MSCI ACWI IMI Net Total Return EUR *(proxy)* | Sviluppati + Emergenti (~47 paesi) | Large, Mid & **Small Cap** (~99% mercato) | Massima diversificazione teorica; cattura del premio dimensionale (*Size Premium* del modello Fama-French). |

---

## 2. Metodologia e Dati

### 2.1 Isolamento delle Variabili (*Ceteris Paribus*)
Per evitare discrepanze dovute a metodologie di calcolo eterogenee di provider concorrenti (FTSE vs MSCI):
* Tutti e tre i panieri appartengono alla medesima famiglia **MSCI Net Total Return (NTR)** in **EUR** con dividendi netti reinvestiti.
* **Periodo Comune Validato:** **Dicembre 2000 – Marzo 2025** (292 mesi sequenziali senza discontinuità).
* **Inflazione Italiana:** Serie storica mensile CPI All Items da FRED St. Louis (`ITACPIALLMINMEI`).

### 2.2 Il Superamento dello *Starting Point Bias*
Un singolo backtest dal 2000 al 2025 misura solo la fortuna o la sfortuna di aver investito in quel dato mese. Il simulatore analizza invece l'**intera popolazione di finestre mobili sovrapposte**:
* **5 Anni (60 mesi):** 232 finestre storiche simulate.
* **10 Anni (120 mesi):** 172 finestre storiche simulate.
* **15 Anni (180 mesi):** 112 finestre storiche simulate.
* **20 Anni (240 mesi):** 52 finestre storiche simulate.

### 2.3 Metriche di Rischio Reale
Per ogni finestra mobile $H$, oltre al **CAGR Reale** (calcolato tramite l'equazione esatta di Fisher), il motore traccia mese per mese la traiettoria del capitale reale:

$$V_k^{\text{reale}} = \frac{P_{t_0 + k}}{P_{t_0}} \times \frac{\text{CPI}_{t_0}}{\text{CPI}_{t_0 + k}} \quad \text{con } k \in [1, H]$$

* **% Tempo in Perdita Reale:** percentuale di mesi della finestra trascorsi con $V_k^{\text{reale}} < 1.0$ (potere d'acquisto intaccato rispetto al carrello della spesa di partenza).
* **Max Striscia Consecutiva Sott'Acqua:** durata massima continua (in mesi) trascorsa in perdita reale prima di un recupero.
* **Peggior Drawdown Reale:** calo percentuale massimo calcolato sui picchi reali all'interno dell'orizzonte.

---

## 3. Risultati Empirici e Conclusioni

Dalla simulazione su tutte le finestre storiche disponibili (2000–2025) emergono i seguenti risultati aggregati:

| Orizzonte Temporale | Benchmark / Indice | Peggior CAGR | Mediana (P50) | Miglior CAGR | P(Reale < 0) | Max % Tempo Rosso | Peggior DD Reale |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **5 Anni** (60 mesi) | **MSCI World (SWDA)** | -7,36% | +7,51% | +15,86% | 27,2% | 100,0% (60m) | -50,95% |
| *232 finestre* | **MSCI ACWI (VWCE)** | -6,85% | +7,62% | +15,47% | 24,6% | 100,0% (60m) | -50,75% |
| | **MSCI ACWI IMI (VALL)** | -6,74% | +7,66% | +16,22% | 23,3% | 100,0% (60m) | -51,19% |
| **10 Anni** (120 mesi) | **MSCI World (SWDA)** | -3,61% | +6,91% | +13,36% | 10,5% | 100,0% (120m) | -57,44% |
| *172 finestre* | **MSCI ACWI (VWCE)** | -2,89% | +6,64% | +12,64% | 10,5% | 100,0% (120m) | -55,48% |
| | **MSCI ACWI IMI (VALL)** | -2,19% | +6,91% | +12,96% | 10,5% | 100,0% (120m) | -53,34% |
| **15 Anni** (180 mesi) | **MSCI World (SWDA)** | +0,63% | +6,17% | +11,76% | 0,0% | 91,1% (164m) | -57,44% |
| *112 finestre* | **MSCI ACWI (VWCE)** | +0,70% | +6,06% | +11,12% | 0,0% | 90,0% (162m) | -55,48% |
| | **MSCI ACWI IMI (VALL)** | +1,19% | +6,20% | +11,19% | 0,0% | 88,3% (159m) | -53,34% |
| **20 Anni** (240 mesi) | **MSCI World (SWDA)** | +2,89% | +6,17% | +7,54% | 0,0% | 68,3% (164m) | -57,44% |
| *52 finestre* | **MSCI ACWI (VWCE)** | +2,98% | +6,00% | +7,21% | 0,0% | 67,5% (162m) | -55,48% |
| | **MSCI ACWI IMI (VALL)** | +3,36% | +6,19% | +7,26% | 0,0% | 66,2% (159m) | -53,34% |

### Lezioni Chiave per l'Investitore

1. **La Mediana Converge (~6,1% Reale Annuo):**  
   Su orizzonti di 15 e 20 anni, le mediane storiche dei tre strumenti sono essenzialmente indistinguibili. L'aggiunta di emergenti e small cap non incrementa il rendimento atteso tipico.
2. **La Diversificazione Globale (VALL) Alza il Pavimento nei Periodi Bui:**  
   Nei peggiori scenari storici, VALL sovraperforma sensibilmente l'MSCI World:
   * A 10 anni attenua il caso peggiore da **-3,61%** a **-2,19% annuo** (+1,42% all'anno di protezione reale).
   * A 15 anni quasi raddoppia il rendimento minimo (**+1,19%** vs **+0,63% reale**).
   * Il peggior calo reale dal picco si ferma al **-53,34%** rispetto al **-57,44%** di World.
3. **MSCI World Ha la Coda Destra Più Spinta (Massimizza i Cicli Favorevoli):**  
   Nei cicli in cui dominano le grandi società americane e i monopoli tecnologici consolidati, l'assenza di mercati periferici spinge maggiormente verso l'alto (miglior CAGR decennale a +13,36% vs +12,96%).
4. **Il Paradosso dei 15 Anni:**  
   Sebbene la probabilità di perdita reale a 15 anni sia storicamente dello **0,0%**, nello scenario peggiore l'investitore ha trascorso il **91,1% del tempo (164 mesi su 180, oltre 13 anni e mezzo)** con un potere d'acquisto inferiore ai soldi versati, tornando in guadagno reale solo in prossimità della scadenza.

---

## 4. Architettura del Repository

La struttura del progetto separa nettamente caricamento dati, logica finanziaria e visualizzazione:

```
italian-investor-benchmark/
│
├── data/
│   ├── raw/                   # Dataset originali MSCI (.xls)
│   └── cache/                 # File Parquet compressi e preprocessati
│
├── src/
│   ├── config.py              # Costanti globali, aliquote fiscali e parametri orizzonti
│   ├── data/
│   │   ├── msci_loader.py     # Ingestion, parsing e inner-join delle serie storiche MSCI
│   │   └── fred_loader.py     # Download e caching dell'inflazione CPI Italia da FRED
│   ├── engine/
│   │   ├── metrics.py         # Funzioni pure: CAGR, equazione di Fisher, Drawdown, XIRR
│   │   ├── portfolio.py       # Motore contabile PIC & PAC con fiscalità italiana (bollo e capital gain)
│   │   └── statistics.py      # Motore statistico a finestre mobili (rendimenti e durata perdite)
│   └── visualizer/
│       ├── tables.py          # Formattazione tabelle comparative a terminale
│       └── charts.py          # Generazione grafici ad alta risoluzione (output/)
│
├── tests/                     # Suite di unit test automatizzati (pytest)
│   ├── test_fred_loader.py
│   ├── test_metrics.py
│   ├── test_msci_loader.py
│   ├── test_portfolio.py
│   └── test_statistics.py
│
├── output/                    # Grafici PNG generati a runtime (300 DPI)
│   ├── rolling_cagr_distribution.png
│   └── rolling_real_loss_time.png
│
├── pyproject.toml
├── requirements.txt
├── main.py                    # Entrypoint dell'applicazione
└── README.md
```

---

## 5. Installazione ed Utilizzo

### Prerequisiti
* Python **3.10** o superiore (sviluppato e testato su Python 3.12).
* Un ambiente virtuale raccomandato (`venv`).

### Setup

```bash
# 1. Clona il repository
git clone [https://github.com/tuo-username/italian-investor-benchmark.git](https://github.com/tuo-username/italian-investor-benchmark.git)
cd italian-investor-benchmark

# 2. Crea e attiva l'ambiente virtuale
python3 -m venv .venv
source .venv/bin/activate

# 3. Installa le dipendenze
pip install -r requirements.txt
```

### Esecuzione della Suite di Test

Per verificare l'integrità delle funzioni matematiche, contabili e statistiche:

```bash
pytest -v
```

### Esecuzione del Simulatore

Per eseguire l'analisi completa a finestre mobili e generare i grafici:

```bash
python main.py
```

I grafici esportati in `output/` comprendono:
* `rolling_cagr_distribution.png`: Boxplot della distribuzione dei rendimenti reali netti per orizzonte (5, 10, 15, 20 anni).
* `rolling_real_loss_time.png`: Istogramma della percentuale di tempo trascorsa in perdita reale rispetto all'inflazione (Scenario Peggiore vs Mediana).

---

## 6. Licenza

Distribuito sotto licenza MIT. I dati delle serie storiche degli indici appartengono a MSCI Inc.; i dati sull'indice dei prezzi al consumo (CPI) appartengono a Istat / FRED St. Louis.