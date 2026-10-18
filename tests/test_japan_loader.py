from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.config import CACHE_DATA_DIR, RAW_DATA_DIR
from src.data.japan_stress_loader import (
    load_and_build_japan_stress_dataset,
    JAPAN_CURVO_FILE,
    WORLD_CURVO_FILE,
    STRESS_TEST_CACHE_FILE,
)


def test_japan_raw_files_exist():
    """Verifica che i file CSV scaricati siano presenti in data/raw."""
    assert JAPAN_CURVO_FILE.exists(), f"Manca {JAPAN_CURVO_FILE}"
    assert WORLD_CURVO_FILE.exists(), f"Manca {WORLD_CURVO_FILE}"


def test_japan_stress_dataset_contract():
    """Verifica la coerenza del dataset estratto per il Japan Stress Test."""
    df = load_and_build_japan_stress_dataset(force_reload=True)

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert len(df) >= 400, f"Attesi almeno 400 mesi dal 1989, trovati {len(df)}"

    expected_cols = {
        "date",
        "msci_japan",
        "msci_world",
        "perf_japan",
        "perf_world",
        "perf_world_ex_japan",
        "synth_70_30_nominal",
        "weight_japan",
        "weight_world_ex_japan",
        "cpi_index",
        "synth_70_30_real",
    }
    assert expected_cols.issubset(df.columns)

    # Invarianti matematici
    # Al tempo t0, i pesi devono essere esattamente 70% e 30%
    assert pytest.approx(df["weight_japan"].iloc[0], 0.001) == 0.70
    assert pytest.approx(df["weight_world_ex_japan"].iloc[0], 0.001) == 0.30
    assert pytest.approx(df["synth_70_30_nominal"].iloc[0], 0.001) == 100.0

    # I pesi sommano sempre a 1.0
    weight_sum = df["weight_japan"] + df["weight_world_ex_japan"]
    assert np.allclose(weight_sum.values, 1.0, atol=1e-5)

    # Prezzi sempre positivi
    assert (df["perf_world_ex_japan"] > 0).all()
    assert (df["synth_70_30_nominal"] > 0).all()
    assert (df["synth_70_30_real"] > 0).all()

