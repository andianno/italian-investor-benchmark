# Italian Investor Benchmark: SWDA vs VWCE vs VALL

> ⚠️ **DISCLAIMER**: Questo progetto nasce esclusivamente per **scopo didattico e curiosità personale**.  
> **Non sono un consulente finanziario** e nessuna informazione, dato, metrica o tabella presente in questo repository costituisce o intende costituire una consulenza finanziaria, un consiglio di investimento o una sollecitazione al pubblico risparmio.  
> Investire sui mercati finanziari comporta il rischio concreto di perdita totale o parziale del capitale. L'autore declina espressamente ogni responsabilità per qualsiasi decisione o perdita economica derivante dall'uso o dall'interpretazione dei dati e del codice qui contenuti. I rendimenti passati non sono in alcun modo garanzia di rendimenti futuri.

---

Simulatore e strumento di esplorazione quantitativa in Python per analizzare il comportamento storico (2000–2025) di tre tipiche strategie azionarie globali ad accumulazione:

1. **Sviluppati Large & Mid Cap** (approssimazione di strumenti come **SWDA** / iShares Core MSCI World).
2. **Tutto il Mondo Large & Mid Cap** (approssimazione di strumenti come **VWCE** / Vanguard FTSE All-World).
3. **Tutto il Mondo All-Cap con Small Cap** (approssimazione di strumenti come **VALL** / Vanguard FTSE Global All Cap).

Il focus del progetto non è il classico backtest lineare da punto a punto, ma l'analisi empirica a **finestre mobili (*Rolling Windows*)** per osservare la dispersione dei rendimenti e stimare **per quanti mesi consecutivi il potere d'acquisto dell'investitore italiano è rimasto inferiore al capitale versato**, tenendo conto dell'inflazione italiana (CPI).

---

## 1. I Tre Livelli di Diversificazione Analizzati

| Indice Simulato | Benchmark Reale Usato | ETF di Mercato Tipici | Copertura e Caratteristiche |
| :--- | :--- | :--- | :--- |
| **World** | MSCI World Net Total Return EUR | SWDA, LCWD | Paesi Sviluppati (~23 nazioni), Large & Mid Cap. |
| **ACWI** | MSCI ACWI Net Total Return EUR | VWCE, SPYI, IUSQ | Sviluppati + Emergenti (~47 nazioni), Large & Mid Cap. |
| **ACWI IMI** | MSCI ACWI IMI Net Total Return EUR | VALL, V3AA, IMIE | Sviluppati + Emergenti + **Small Cap** (~99% del mercato quotato). |

### Nota sui Provider (MSCI vs FTSE)
Gli ETF di Vanguard (come VWCE o VALL) replicano benchmark dell'emittente FTSE. In questa simulazione viene utilizzata l'intera famiglia **MSCI Net Total Return** esclusivamente per garantire uniformità e coerenza metodologica nei dati (stessi criteri di reinvestimento dividendi e stesse metodologie di calcolo).  
*Non si tratta di repliche identiche*: ad esempio, la Corea del Sud è considerata paese sviluppato per FTSE ed emergente per MSCI. Gli indici usati vanno intesi come **proxy comparativi indicativi** e non come cloni perfetti degli ETF commerciali.

---

## 2. Metodologia, Dati e Limiti del Modello

### 2.1 Fonte Dati
* **Serie Azionarie:** Serie mensili ufficiali MSCI Net Total Return (NTR) in Euro (periodo validato: **Dicembre 2000 – Marzo 2025**, 292 mesi).
* **Inflazione Italiana:** Indice mensile dei prezzi al consumo per l'Italia (CPI All Items) ricavato da FRED St. Louis (`ITACPIALLMINMEI`).

### 2.2 Costi e Tassazione (Approssimazioni adottate)
* **TER:** Decurtato mensilmente sul valore quota (valori indicativi di riferimento impostabili in `config.py`, es. 0.20% per World, 0.14% per ACWI, 0.07% per IMI).
* **Imposta di Bollo (0,20% annuo):** Detratta al 31 dicembre di ogni anno direttamente tramite **riduzione proporzionale del numero di quote**, simulando l'assenza di liquidità libera sul conto titoli.
* **Capital Gain (26%):** Considerato a titolo indicativo al momento della liquidazione finale sul guadagno nominale maturato.
* **Equazione di Fisher:** Il CAGR reale è calcolato deflazionando il rendimento nominale con l'inflazione cumulata del periodo:
  $$1 + r_{\text{reale}} = \frac{1 + r_{\text{nominale}}}{1 + i_{\text{inflazione}}}$$

### 2.3 Limiti Statistici da Tenere a Mente
* **Orizzonte temporale limitato:** 24 anni di dati (292 mesi) rappresentano un campione storico ridotto. Le finestre mobili a 15 e 20 anni sono fortemente sovrapposte tra loro (condividono quasi tutti i mesi) e riflettono essenzialmente **le peculiarità di quel singolo ciclo storico**, non una verità asintotica o universale.
* I calcoli qui riportati non pretendono di avere significatività econometrica formale, ma offrono una fotografia di ciò che è accaduto empiricamente in quello specifico intervallo.

---

## 3. Risultati Empirici (Finestre Mobili 2000–2025)

Simulando tutte le finestre mobili storiche disponibili (a 5, 10, 15 e 20 anni), questi sono i numeri prodotti dal motore di calcolo:

| Orizzonte | Benchmark / Indice | Peggior CAGR Reale | Mediana (P50) Reale | Miglior CAGR Reale | P(Reale < 0) | Max % Tempo in Perdita Reale | Peggior DD Reale |
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

### Spunti di Riflessione
1. **La mediana storica è quasi coincidente:** Su 15 e 20 anni, il rendimento reale mediano dei tre indici si colloca stabilmente attorno al **+6,0% – +6,2% annuo**. Aggiungere emergenti e small cap non ha cambiato significativamente il rendimento tipico centrale in questo periodo.
2. **Comportamento nelle code:**
   * **Nello scenario peggiore (drawdown severi):** L'indice ACWI IMI ha contenuto meglio i minimi (a 10 anni -2,19% vs -3,61% di World; a 15 anni +1,19% vs +0,63%).
   * **Nello scenario migliore (fasi di boom):** L'MSCI World ha registrato i massimi più alti nei decenni favorevoli ai titoli occidentali e alle mega-cap.
3. **Il fattore psicologico del tempo sott'acqua:** Anche a 15 anni, dove tutte le finestre si sono chiuse con un guadagno reale finale ($P(\text{Reale} < 0) = 0\%$), nel caso peggiore (ingresso fine 2000) si è passati circa il **90% del tempo (oltre 13 anni)** con un potere d'acquisto inferiore a quello iniziale prima di tornare stabilmente in attivo.

---

## 4. Struttura del Progetto

```
italian-investor-benchmark/
│
├── data/
│   ├── raw/                   # File originali scaricati da MSCI (esclusi da git)
│   └── cache/                 # File Parquet generati ad accesso rapido
│
├── src/
│   ├── config.py              # Costanti contabili, parametri simulazione e percorsi
│   ├── data/
│   │   ├── msci_loader.py     # Parser e allineamento date delle serie MSCI
│   │   └── fred_loader.py     # Scaricamento e caching CPI Italia da FRED
│   ├── engine/
│   │   ├── metrics.py         # Formule finanziarie pure (CAGR, Fisher, Drawdown, XIRR)
│   │   ├── portfolio.py       # Logica contabile di simulazione PIC/PAC con costi e bollo
│   │   └── statistics.py      # Calcolo metriche su finestre mobili e permanenza in perdita
│   └── visualizer/
│       ├── tables.py          # Formattazione tabelle a terminale
│       └── charts.py          # Esportazione grafici ad alta risoluzione (cartella output/)
│
├── tests/                     # Suite di test unitari con pytest
│   ├── test_fred_loader.py
│   ├── test_metrics.py
│   ├── test_msci_loader.py
│   ├── test_portfolio.py
│   └── test_statistics.py
│
├── output/                    # Grafici salvati a fine esecuzione
│   ├── rolling_cagr_distribution.png
│   └── rolling_real_loss_time.png
│
├── pyproject.toml
├── requirements.txt
├── main.py                    # Script di avvio
└── README.md
```

---

## 5. Installazione ed Utilizzo

### Prerequisiti
* Python **3.10+**
* Un ambiente virtuale raccomandato (`venv`).

### Setup Rapido

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

### Esecuzione dei Test
Per verificare la coerenza matematica e contabile delle funzioni:
```bash
pytest -v
```

### Avvio del Simulatore
Per calcolare le finestre mobili e generare i grafici:
```bash
python main.py
```

I grafici ad alta risoluzione verranno salvati automaticamente nella cartella `output/`:
* `output/rolling_cagr_distribution.png` (Boxplot della distribuzione dei rendimenti reali)
* `output/rolling_real_loss_time.png` (Confronto sulla percentuale di tempo trascorsa in perdita reale)

---

## 6. Dati e Licenze

* **Dati Indici:** Proprietà di MSCI Inc. I file grezzi non sono ridistribuiti nel repository per rispetto delle condizioni d'uso del fornitore.
* **Dati Inflazione:** Istat / FRED (Federal Reserve Bank of St. Louis).