from pathlib import Path
import pandas as pd
import pytest

from src.config import CACHE_DATA_DIR, RAW_DATA_DIR
from src.data.msci_loader import build_benchmarks_parquet


def test_raw_files_exist():
    """Verifica preliminare:

    i tre file XLS grezzi devono essere presenti in data/raw.
    """
    assert (RAW_DATA_DIR / "msci_world.xls").exists(), "Manca msci_world.xls"
    assert (RAW_DATA_DIR / "msci_acwi.xls").exists(), "Manca msci_acwi.xls"
    assert (
        RAW_DATA_DIR / "msci_acwi_imi.xls"
    ).exists(), "Manca msci_acwi_imi.xls"


def test_build_benchmarks_parquet_contract():
    """Verifica gli invarianti del DataFrame normalizzato."""
    # Forziamo la rigenerazione per testare l'intera pipeline di parsing
    df = build_benchmarks_parquet(force_reload=True)

    # 1. Verifica esistenza e non vuotezza
    assert isinstance(df, pd.DataFrame)
    assert not df.empty, "Il DataFrame generato è vuoto."
    assert (
        len(df) >= 300
    ), f"Attesi almeno 300 mesi di storico comune, trovati {len(df)}"

    # 2. Verifica colonne obbligatorie
    expected_columns = {
        "date",
        "msci_world",
        "msci_acwi",
        "msci_acwi_imi",
        "msci_world_return",
        "msci_acwi_return",
        "msci_acwi_imi_return",
    }
    assert expected_columns.issubset(
        df.columns
    ), f"Colonne mancanti: {expected_columns - set(df.columns)}"

    # 3. Verifica tipi di dato
    assert pd.api.types.is_datetime64_any_dtype(
        df["date"]
    ), "La colonna 'date' non è in formato datetime"
    for col in ["msci_world", "msci_acwi", "msci_acwi_imi"]:
        assert pd.api.types.is_float_dtype(
            df[col]
        ), f"La colonna {col} non è di tipo float"

    # 4. Verifica assenza di valori nulli sui prezzi
    assert df["msci_world"].isna().sum() == 0, "Ci sono NaN in msci_world"
    assert df["msci_acwi"].isna().sum() == 0, "Ci sono NaN in msci_acwi"
    assert df["msci_acwi_imi"].isna().sum() == 0, "Ci sono NaN in msci_acwi_imi"

    # Nota: la prima riga dei rendimenti sarà fisiologicamente NaN per pct_change()
    assert (
        df["msci_world_return"].iloc[1:].isna().sum() == 0
    ), "Ci sono NaN imprevisti nei rendimenti"

    # 5. Verifica ordinamento temporale strettamente crescente
    assert (
        df["date"].is_monotonic_increasing
    ), "Le date non sono ordinate cronologicamente in modo crescente"
    assert df["date"].duplicated().sum() == 0, "Sono presenti date duplicate"

    # 6. Verifica cache su disco
    parquet_file = CACHE_DATA_DIR / "benchmarks.parquet"
    assert (
        parquet_file.exists()
    ), "Il file benchmarks.parquet non è stato salvato in cache"