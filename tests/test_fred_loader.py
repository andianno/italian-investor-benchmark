import pandas as pd
import pytest

from src.config import CACHE_DATA_DIR
from src.data.fred_loader import INFLATION_CACHE_FILE, load_italian_inflation


def test_load_italian_inflation_contract():
    df = load_italian_inflation(force_download=True)

    # 1. Integrità strutturale
    assert isinstance(df, pd.DataFrame)
    assert not df.empty, "Il DataFrame dell'inflazione è vuoto."

    expected_cols = {"date", "cpi_index", "monthly_inflation"}
    assert expected_cols.issubset(df.columns), (
        f"Colonne mancanti: {expected_cols - set(df.columns)}"
    )

    # 2. Tipi di dato
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert pd.api.types.is_float_dtype(df["cpi_index"])
    assert pd.api.types.is_float_dtype(df["monthly_inflation"])

    # 3. Assenza di valori nulli
    assert df["cpi_index"].isna().sum() == 0, "Ci sono NaN nell'indice CPI"
    assert df["monthly_inflation"].iloc[1:].isna().sum() == 0, (
        "Ci sono NaN imprevisti nell'inflazione mensile"
    )

    # 4. Copertura temporale
    # Deve coprire almeno dal 2000 a oggi per allinearsi con i dati MSCI
    assert df["date"].min() <= pd.Timestamp("2000-12-31"), (
        "Lo storico dell'inflazione non copre l'inizio del periodo (2000)"
    )

    # 5. Salvataggio su disco
    assert INFLATION_CACHE_FILE.exists(), (
        "Il file inflation_italy.parquet non è stato creato"
    )
