# Global Equity Benchmark Simulator: SWDA vs VWCE vs VALL

Simulatore quantitativo e probabilistico in Python per l'analisi comparativa a lungo termine (2000–2026) delle tre principali strategie passive su azionario globale:

1. **Solo Paesi Sviluppati (Large & Mid Cap)** — Proxy di **iShares Core MSCI World (SWDA)**.

2. **Tutto il Mondo (Sviluppati + Emergenti Large & Mid Cap)** — Proxy di **Vanguard FTSE All-World (VWCE)**.

3. **Tutto il Mondo All-Cap (Sviluppati + Emergenti + Small Cap)** — Proxy di **Vanguard FTSE Global All Cap (VALL)**.

Il progetto nasce per superare i limiti dei tipici backtest lineari a breve termine, applicando l'approccio analitico e didattico promosso dal prof. Paolo Coletti: **orizzonti profondi (oltre 25 anni), rendimenti reali deflazionati su inflazione italiana (CPI), tassazione reale (imposta di bollo e capital gain), analisi a finestre mobili (*Rolling Returns*) e simulazione stocastica tramite *Block Bootstrapping*.**

## 1. Il Problema Finanziario: Il "Dilemma dell'Investitore Globale"

L'investitore passivo che decide di allocare al 100% su azionario globale si trova tipicamente davanti a tre livelli di diversificazione:

| Strategia / ETF | Benchmark Replicato | Copertura Geografica | Segmento Capitalizzazione | Tesi di Investimento | 
 | ----- | ----- | ----- | ----- | ----- | 
| **SWDA** *(iShares Core MSCI World)* | MSCI World Net Total Return EUR | Paesi Sviluppati (\~23 nazioni) | Large & Mid Cap (\~85% mercato) | Massima efficienza, governance consolidata, nessun rischio politico/valutario tipico degli emergenti. | 
| **VWCE** *(Vanguard FTSE All-World)* | MSCI ACWI Net Total Return EUR *(proxy)* | Sviluppati + Emergenti (\~47 nazioni) | Large & Mid Cap (\~85-90% mercato) | Replica neutrale dell'intera economia globale quotata; esposizione alla crescita demografica ed economica dei paesi emergenti. | 
| **VALL** *(FTSE Global All Cap)* | MSCI ACWI IMI Net Total Return EUR *(proxy)* | Sviluppati + Emergenti (\~47 nazioni) | Large, Mid & **Small Cap** (\~99% mercato) | Massima diversificazione teorica; cattura del premio dimensionale (*Size Premium* del modello Fama-French). | 

### Le Domande di Ricerca a cui Risponde il Simulatore

1. **Emergenti:** L'inclusione dei mercati emergenti ha storicamente migliorato il profilo rendimento/rischio o ha introdotto solo volatilità superflua?

2. **Small Cap:** L'aggiunta di circa il 10% di Small Cap globali genera un extra-rendimento tangibile al netto dei maggiori costi di gestione (TER)?

3. **Resilienza al Rischio:** In caso di crash sistemici (crisi Dot-Com del 2000, Crisi Finanziaria del 2008, COVID del 2020), come divergono i tempi di recupero (*underwater duration*) e le perdite massime?

4. **Potere d'Acquisto Reale:** Quanto capitale reale resta in mano all'investitore italiano dopo aver scontato l'inflazione Istat/FRED, l'imposta di bollo dello 0,20% annuo e il 26% di capital gain?

## 2. Metodologia e Dati

### 2.1 Isolamento delle Variabili (*Ceteris Paribus*)

Per confrontare gli strumenti senza introdurre il rumore dovuto a metodologie di calcolo eterogenee di provider concorrenti (FTSE vs MSCI), l'analisi utilizza **l'intera famiglia di indici MSCI**:

* **MSCI World** $\rightarrow$ Benchmark per SWDA.

* **MSCI ACWI** (All Country World Index) $\rightarrow$ Proxy perfetto per FTSE All-World (VWCE).

* **MSCI ACWI IMI** (Investable Market Index) $\rightarrow$ Proxy perfetto per FTSE Global All Cap (VALL).

Tutte le serie storiche condividono gli stessi identici criteri contabili:

* **Frequenza:** Mensile (*Monthly End of Month*).

* **Valuta:** Euro (EUR) — nessun bisogno di modellare tassi di cambio sintetici.

* **Livello:** **Net Total Return (NTR)** — reinvestimento automatico dei dividendi al netto delle ritenute fiscali alla fonte, replicando fedelmente il funzionamento degli ETF ad accumulazione.

* **Periodo Comune:** **Dicembre 2000 – Agosto 2026** (309 mesi continui, oltre 25 anni e mezzo).

### 2.2 Inflazione Italiana (CPI)

I dati di inflazione sono estratti direttamente dalla **Federal Reserve Bank of St. Louis (FRED)** tramite la serie:

* **`ITACPIALLMINMEI`**: Consumer Price Index of All Items for Italy (frequenza mensile).

## 3. Specifiche delle Analisi e Formule Matematiche

Il motore del simulatore implementa quattro cluster analitici distinti:

### 3.1 Modalità di Investimento

1. **PIC (Lump Sum):** Investimento di un capitale $C_0$ all'istante iniziale $t_0$.

2. **PAC (Dollar-Cost Averaging):**

   * *Rata Costante:* Versamento di una quota fissa $R$ ogni fine mese.

   * *Rata Indicizzata:* La quota $R_t$ viene adeguata annualmente al tasso di inflazione storica, simulando la crescita dello stipendio.

### 3.2 Metriche di Rendimento

* **Compound Annual Growth Rate (CAGR):**

  $$
  \text{CAGR} = \left(\frac{V_f}{V_0}\right)^{\frac{1}{\Delta t}} - 1
  $$

  dove $\Delta t$ è la durata temporale in anni.

* **Rendimento Reale Netto (Equazione di Fisher esatta):**

  $$
  1 + r_{\text{reale}} = \frac{1 + r_{\text{nominale}}}{1 + i_{\text{cumulata}}}
  $$

* **Money-Weighted Return (MWR / XIRR) per il PAC:**
  Tasso interno di rendimento $r$ annualizzato che azzera il valore attuale netto dei flussi di cassa $C_t$:

  $$
  \sum_{t=0}^{N} \frac{C_t}{(1 + r)^{\frac{d_t - d_0}{365}}} = 0
  $$

### 3.3 Metriche di Rischio e Drawdown

* **High-Water Mark (HWM) e Drawdown Series:**

  $$
  \text{HWM}_t = \max_{0 \le s \le t} (V_s)
  $$

  $$
  \text{Drawdown}_t = \frac{V_t - \text{HWM}_t}{\text{HWM}_t}
  $$

* **Max Drawdown (MDD):** $\min_{t}(\text{Drawdown}_t)$.

* **Underwater Duration:** Il tempo massimo (in mesi/anni) trascorso dal portafoglio prima di eguagliare o superare un precedente picco.

* **Volatilità Annualizzata:**

  $$
  \sigma_{\text{annuale}} = \sigma_{\text{mensile}} \times \sqrt{12}
  $$

### 3.4 Fisco Italiano e Costi

* **TER (Total Expense Ratio):** Scalato mensilmente dal valore quota:

  $$
  r_{\text{net\_cost}} = r_{\text{index}} - \left[(1 + \text{TER})^{\frac{1}{12}} - 1\right]
  $$

  *Default:* SWDA = 0.20%, VWCE = 0.14%, VALL = 0.07%.

* **Imposta di Bollo (0,20% annuo):** Detratta al 31 dicembre di ciascun anno sul controvalore maturato del portafoglio:

  $$
  \text{Bollo}_y = 0.0020 \times V_{\text{31-Dec}}
  $$

* **Tassazione Capital Gain (26%):** Applicata in un'unica soluzione al termine del periodo solo sulle plusvalenze maturate:

  $$
  \text{Imposta Plusvalenza} = 0.26 \times \max(0, V_{\text{finale}} - C_{\text{totale\_versato}})
  $$

### 3.5 Analisi Statistica Avanzata (alla Coletti)

1. **Rolling Returns Analysis:**
   Valutazione delle distribuzioni di rendimento su finestre mobili a orizzonte fisso ($H \in \{5, 10, 15, 20\}$ anni):

   * Percentili calcolati: **5° percentile** (scenario peggiore), **50° percentile** (mediana), **95° percentile** (scenario ottimistico).

   * Probabilità storica di rendimento reale negativo: $P(r_{\text{reale}} < 0)$.

2. **Block Bootstrapping (Monte Carlo non parametrico):**
   Invece di ipotizzare una distribuzione normale teorica (che ignora crolli estremi e asimmetria), la serie storica dei rendimenti viene ricampionata a blocchi continui di $B = 12$ mesi per preservare la correlazione seriale e generare $N = 2.000$ percorsi stocastici sintetici.

## 4. Architettura Software del Repository

La struttura del progetto separa rigorosamente il data layer, la logica matematica pura e la visualizzazione:

```
etf-global-benchmark-sim/
│
├── data/
│   ├── raw/                   # File originali scaricati dal portale MSCI
│   │   ├── msci_world.xls
│   │   ├── msci_acwi.xls
│   │   └── msci_acwi_imi.xls
│   └── cache/                 # File Parquet preprocessati ad alta velocità
│       ├── benchmarks.parquet
│       └── inflation_italy.parquet
│
├── src/
│   ├── __init__.py
│   ├── config.py              # Parametri globali (TER, aliquote fiscali, orizzonti)
│   ├── data/
│   │   ├── __init__.py
│   │   ├── msci_loader.py     # Ingestion, parsing e allineamento join degli indici
│   │   └── fred_loader.py     # Download automatico e caching CPI Italia
│   │
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── metrics.py         # Funzioni pure: CAGR, XIRR, Drawdown, Volatilità
│   │   ├── portfolio.py       # Motore PIC & PAC (gestione quote, TER, bollo, tasse)
│   │   └── statistics.py      # Finestre mobili (rolling) e Block Bootstrapping
│   │
│   └── visualizer/
│       ├── __init__.py
│       ├── tables.py          # Tabelle riassuntive da terminale (Rich / Tabulate)
│       └── charts.py          # Generazione grafici (Matplotlib / Plotly)
│
├── tests/
│   ├── test_metrics.py        # Test di consistenza matematica sulle formule
│   └── test_portfolio.py      # Test contabile su flussi di cassa e imposte
│
├── .gitignore
├── requirements.txt
└── README.md


```

## 5. Output Attesi del Simulatore

All'esecuzione dell'analisi completa, il tool genera:

1. **Tabella Comparativa Riassuntiva:**

   * Capitale finale (nominale e reale).

   * CAGR e MWR/XIRR (lordo e netto da imposte).

   * Max Drawdown e mesi massimi di recupero.

   * Volatilità annualizzata.

2. **Grafico dell'Evoluzione Patrimoniale:**

   * Linea del valore nominale vs linea del potere d'acquisto reale (in Euro costanti).

3. **Underwater Plot:**

   * Grafico dell'intensità e durata dei drawdown a confronto nei tre scenari.

4. **Grafico delle Finestre Mobili (Rolling Boxplots):**

   * Dispersione dei rendimenti annui a 5, 10, 15 e 20 anni per ciascun indice.

5. **Ventaglio Monte Carlo / Percentili Bootstrap:**

   * Cono di probabilità (5°-50°-95°) del valore patrimoniale atteso nel tempo.

## 6. Requisiti e Riproducibilità

* **Python:** 3.10+

* **Librerie Principali:** `pandas`, `numpy`, `scipy`, `matplotlib`, `pyarrow`