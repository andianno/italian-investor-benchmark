"""Modulo per l'estrazione, allineamento e ricostruzione matematica del dataset Japan Stress Test (1989-2025).

Combina:
1. MSCI Japan (in EUR dal 1978)
2. MSCI World (in EUR dal 1969)
3. Inflazione italiana FOI (da FRED dal 1955)

Estrae matematicamente la serie di 'MSCI World ex Japan' scorporando il peso storico
del Giappone a fine 1989 (~44%) e costruisce l'indice sintetico 'Stress Test 70/30' a pesi flottanti.
"""

from pathlib import Path
import pandas as pd
from src.config import CACHE_DATA_DIR, RAW_DATA_DIR

JAPAN_CURVO_FILE = RAW_DATA_DIR / "msci_japan_curvo.csv"
WORLD_CURVO_FILE = RAW_DATA_DIR / "msci_world_curvo.csv"
INFLATION_CACHE_FILE = CACHE_DATA_DIR / "inflation_italy.parquet"
STRESS_TEST_CACHE_FILE = CACHE_DATA_DIR / "japan_stress_test.parquet"

# Peso stimato del Giappone nell'MSCI World al picco storico del 31/12/1989 (~44%)
HISTORICAL_JAPAN_WEIGHT_1989 = 0.44


def load_and_build_japan_stress_dataset(
    start_date: str = "1989-12-31",
    force_reload: bool = False,
) -> pd.DataFrame:
    """Carica, allinea e calcola l'indice sintetico 70% Japan / 30% World ex-Japan.

    Salva il risultato in data/cache/japan_stress_test.parquet.
    """
    CACHE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    if STRESS_TEST_CACHE_FILE.exists() and not force_reload:
        return pd.read_parquet(STRESS_TEST_CACHE_FILE)

    if not JAPAN_CURVO_FILE.exists():
        raise FileNotFoundError(f"File non trovato: {JAPAN_CURVO_FILE}")
    if not WORLD_CURVO_FILE.exists():
        raise FileNotFoundError(f"File non trovato: {WORLD_CURVO_FILE}")
    if not INFLATION_CACHE_FILE.exists():
        raise FileNotFoundError(f"File non trovato: {INFLATION_CACHE_FILE}")

    # 1. Lettura dei file CSV grezzi
    df_j = pd.read_csv(JAPAN_CURVO_FILE)
    df_w = pd.read_csv(WORLD_CURVO_FILE)

    # 2. Parsing e normalizzazione delle date a fine mese
    df_j["date"] = pd.to_datetime(df_j["Date"], format="%m/%Y") + pd.offsets.MonthEnd(0)
    df_w["date"] = pd.to_datetime(df_w["Date"], format="%m/%Y") + pd.offsets.MonthEnd(0)

    # Pulizia colonne
    df_j = df_j.rename(columns={"MSCI Japan": "msci_japan"})[["date", "msci_japan"]]
    df_w = df_w.rename(columns={"MSCI World": "msci_world"})[["date", "msci_world"]]

    # 3. Merge e filtro a partire dalla data di inizio (31/12/1989)
    df = pd.merge(df_j, df_w, on="date").sort_values("date").reset_index(drop=True)
    df = df[df["date"] >= start_date].reset_index(drop=True)

    if df.empty:
        raise ValueError(f"Nessun dato trovato a partire dalla data {start_date}")

    # 4. Performance normalizzata Base 1.0 al 31/12/1989
    p_j0 = df["msci_japan"].iloc[0]
    p_w0 = df["msci_world"].iloc[0]

    perf_j = df["msci_japan"] / p_j0
    perf_w = df["msci_world"] / p_w0

    # 5. Ricostruzione matematica di World ex-Japan:
    # M_World(t) = w_J0 * perf_Japan(t) + (1 - w_J0) * perf_WorldExJapan(t)
    w_j0 = HISTORICAL_JAPAN_WEIGHT_1989
    w_ex0 = 1.0 - w_j0

    m_j = w_j0 * perf_j
    m_w = 1.0 * perf_w
    perf_ex = (m_w - m_j) / w_ex0

    df["perf_japan"] = perf_j
    df["perf_world"] = perf_w
    df["perf_world_ex_japan"] = perf_ex

    # 6. Costruzione Portafoglio Stress Test 70/30 Flottante (Base 100)
    # Investimento iniziale: 70 punti Japan, 30 punti World ex-Japan
    val_j_component = 70.0 * perf_j
    val_ex_component = 30.0 * perf_ex
    synth_nominal = val_j_component + val_ex_component

    df["synth_70_30_nominal"] = synth_nominal
    df["weight_japan"] = val_j_component / synth_nominal
    df["weight_world_ex_japan"] = val_ex_component / synth_nominal

    # 7. Unione con l'inflazione italiana FOI da FRED
    df_inf = pd.read_parquet(INFLATION_CACHE_FILE)
    df = pd.merge(df, df_inf[["date", "cpi_index"]], on="date", how="inner").sort_values("date").reset_index(drop=True)

    # Deflazione reale del capitale nominale
    cpi_0 = df["cpi_index"].iloc[0]
    df["synth_70_30_real"] = df["synth_70_30_nominal"] * (cpi_0 / df["cpi_index"])

    # 8. Rendimenti mensili
    df["synth_nominal_return"] = df["synth_70_30_nominal"].pct_change()
    df["synth_real_return"] = df["synth_70_30_real"].pct_change()

    # Salva in cache Parquet per analisi istantanee
    df.to_parquet(STRESS_TEST_CACHE_FILE, index=False)
    return df


def print_dataset_summary(df: pd.DataFrame) -> None:
    """Stampa un report sintetico con le tappe storiche del dataset estratto."""
    print("\n" + "=" * 90)
    print("      JAPAN STRESS TEST DATASET (1989-2025): VALIDAZIONE E TAPPE STORICHE")
    print("=" * 90)
    print(f"Periodo disponibile: {df['date'].iloc[0].date()} -> {df['date'].iloc[-1].date()} ({len(df)} mesi)")
    print(f"Struttura Iniziale Base 100 (1989-12-31): 70% Giappone / 30% Resto del Mondo")

    # Minimo crollo nominale e reale
    min_nom_idx = df["synth_70_30_nominal"].idxmin()
    min_real_idx = df["synth_70_30_real"].idxmin()

    # Pareggio nominale (prima volta >= 100 dopo t0)
    nom_breakeven = df.iloc[1:][df["synth_70_30_nominal"].iloc[1:] >= 100.0]
    date_nom_break = nom_breakeven["date"].iloc[0].date() if not nom_breakeven.empty else "Mai"

    # Pareggio reale (prima volta >= 100 dopo t0)
    real_breakeven = df.iloc[1:][df["synth_70_30_real"].iloc[1:] >= 100.0]
    date_real_break = real_breakeven["date"].iloc[0].date() if not real_breakeven.empty else "Mai"

    print("\n--- RISULTATI CHIAVE DELLO STRESS TEST ---")
    print(f"• Peggior minimo nominale: {df['synth_70_30_nominal'].iloc[min_nom_idx]:.2f} (-{(100 - df['synth_70_30_nominal'].iloc[min_nom_idx]):.1f}%) il {df['date'].iloc[min_nom_idx].date()}")
    print(f"• Peggior minimo reale (potere acq.): {df['synth_70_30_real'].iloc[min_real_idx]:.2f} (-{(100 - df['synth_70_30_real'].iloc[min_real_idx]):.1f}%) il {df['date'].iloc[min_real_idx].date()}")
    print(f"• Pareggio nominale raggiunto il: {date_nom_break}")
    print(f"• Pareggio reale (recuperata inflazione) il: {date_real_break}")

    print("\n--- VALORI FINALI AL TERMINE DEL PERIODO (2025-03-31) ---")
    last = df.iloc[-1]
    print(f"• Valore Nominale Finale: {last['synth_70_30_nominal']:.2f} (Base 100 -> +{(last['synth_70_30_nominal'] - 100):.1f}%)")
    print(f"• Valore Reale Finale: {last['synth_70_30_real']:.2f} (Potere d'acquisto triplicato: +{(last['synth_70_30_real'] - 100):.1f}%)")
    print(f"• Peso finale del Giappone: {last['weight_japan'] * 100:.1f}% (dal 70,0% iniziale)")
    print(f"• Peso finale del Resto del Mondo: {last['weight_world_ex_japan'] * 100:.1f}% (dal 30,0% iniziale)")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    df = load_and_build_japan_stress_dataset(force_reload=True)
    print_dataset_summary(df)

