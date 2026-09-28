from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import requests

from src.config import CACHE_DATA_DIR

FRED_CPI_URL = (
    "https://fred.stlouisfed.org/graph/fredgraph.csv?id=ITACPIALLMINMEI"
)
INFLATION_CACHE_FILE = CACHE_DATA_DIR / "inflation_italy.parquet"


def load_italian_inflation(
    force_download: bool = False, max_cache_age_days: int = 30
) -> pd.DataFrame:
    """Scarica, normalizza e memorizza in cache l'indice CPI mensile italiano da FRED."""
    CACHE_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Controlla se la cache esiste ed è ancora fresca
    if INFLATION_CACHE_FILE.exists() and not force_download:
        mtime = datetime.fromtimestamp(INFLATION_CACHE_FILE.stat().st_mtime)
        if datetime.now() - mtime < timedelta(days=max_cache_age_days):
            return pd.read_parquet(INFLATION_CACHE_FILE)

    # 2. Download da FRED
    try:
        df_raw = pd.read_csv(FRED_CPI_URL)
    except Exception as exc:
        if INFLATION_CACHE_FILE.exists():
            # Fallback resiliente: usiamo la cache anche se scaduta
            return pd.read_parquet(INFLATION_CACHE_FILE)
        raise ConnectionError(
            f"Impossibile scaricare l'inflazione da FRED e nessuna cache disponibile: {exc}"
        ) from exc

    # 3. Pulizia e normalizzazione del Data Contract
    df = df_raw.copy()
    df.columns = ["date", "cpi_index"]

    # Gestisce eventuali valori mancanti o formati non numerici rappresentati da '.'
    df["cpi_index"] = pd.to_numeric(df["cpi_index"], errors="coerce")
    df = df.dropna().reset_index(drop=True)

    df["date"] = pd.to_datetime(df["date"]) + pd.offsets.MonthEnd(0)
    df = df.sort_values("date").drop_duplicates("date").reset_index(drop=True)

    # 4. Calcolo variazione mensile dell'inflazione
    df["monthly_inflation"] = df["cpi_index"].pct_change()

    # 5. Salvataggio su Parquet
    df.to_parquet(INFLATION_CACHE_FILE, index=False)
    return df


if __name__ == "__main__":
    df_inf = load_italian_inflation(force_download=True)
    print(f"Inflazione caricata: {len(df_inf)} mesi.")
    print(
        f"Intervallo: dal {df_inf['date'].min().date()} al {df_inf['date'].max().date()}"
    )
    print("\nUltime 5 osservazioni:")
    print(df_inf.tail(5))