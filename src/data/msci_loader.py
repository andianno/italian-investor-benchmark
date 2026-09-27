from pathlib import Path
import pandas as pd
from src.config import CACHE_DATA_DIR, RAW_DATA_DIR


def _parse_single_msci_xls(filepath: Path, col_name: str) -> pd.DataFrame:
    """Legge un singolo file XLS esportato da MSCI e restituisce date e prezzi puliti."""
    if not filepath.exists():
        raise FileNotFoundError(f"File non trovato: {filepath}")

    # Legge l'Excel saltando le prime righe di metadati fino all'header 'Date'
    df_raw = pd.read_excel(filepath, sheet_name=0)
    header_idx = df_raw[df_raw.iloc[:, 0] == "Date"].index[0]
    df = pd.read_excel(filepath, skiprows=header_idx)

    # Conserva solo le prime due colonne: Data e Prezzo
    df = df.iloc[:, :2].copy()
    df.columns = ["date", col_name]
    df = df.dropna()

    # Rimuove note legali finali controllando il pattern della data (es. 'Dec 29, 2000')
    df = df[df["date"].astype(str).str.match(r"^[A-Z][a-z]{2} \d{1,2}, \d{4}$")]

    # Normalizza la data all'ultimo giorno del mese
    df["date"] = pd.to_datetime(df["date"], format="%b %d, %Y")
    df["date"] = df["date"] + pd.offsets.MonthEnd(0)

    # Converte il prezzo in virgola mobile rimuovendo eventuali separatori delle migliaia
    df[col_name] = (
        df[col_name].astype(str).str.replace(",", "").astype(float)
    )

    return df.sort_values("date").reset_index(drop=True)


def build_benchmarks_parquet(force_reload: bool = False) -> pd.DataFrame:
    """Allinea i tre indici (World, ACWI, IMI) sulle date comuni e li salva in cache."""
    CACHE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DATA_DIR / "benchmarks.parquet"

    if cache_path.exists() and not force_reload:
        return pd.read_parquet(cache_path)

    # Lettura delle tre serie storiche
    df_world = _parse_single_msci_xls(
        RAW_DATA_DIR / "msci_world.xls", "msci_world"
    )
    df_acwi = _parse_single_msci_xls(
        RAW_DATA_DIR / "msci_acwi.xls", "msci_acwi"
    )
    df_imi = _parse_single_msci_xls(
        RAW_DATA_DIR / "msci_acwi_imi.xls", "msci_acwi_imi"
    )

    # Intersezione delle date (Inner Join)
    merged = df_world.merge(df_acwi, on="date").merge(df_imi, on="date")
    merged = merged.sort_values("date").reset_index(drop=True)

    # Calcolo dei rendimenti mensili percentuali per ciascuna serie
    for col in ["msci_world", "msci_acwi", "msci_acwi_imi"]:
        merged[f"{col}_return"] = merged[col].pct_change()

    # Salva in Parquet per accessi futuri istantanei
    merged.to_parquet(cache_path, index=False)
    return merged


if __name__ == "__main__":
    df = build_benchmarks_parquet(force_reload=True)
    print(f"Dataset caricato: {len(df)} mesi.")
    print(f"Intervallo: dal {df['date'].min().date()} al {df['date'].max().date()}")
    print("\nPrime 3 righe:")
    print(df[["date", "msci_world", "msci_acwi", "msci_acwi_imi"]].head(3))