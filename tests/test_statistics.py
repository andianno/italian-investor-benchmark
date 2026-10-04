"""Test di validazione per le finestre mobili e il calcolo del rischio reale."""

import numpy as np
import pandas as pd
import pytest
from src.engine.statistics import (
    calculate_all_rolling_horizons,
    calculate_rolling_returns,
)


def test_calculate_rolling_returns_deterministic():
    dates = pd.date_range("2000-01-31", periods=120, freq="ME")
    prices = pd.Series([100.0 * (1.10 ** (i / 12)) for i in range(120)])
    cpi = pd.Series([100.0 * (1.02 ** (i / 12)) for i in range(120)])

    stats = calculate_rolling_returns(dates, prices, cpi, horizon_years=5)

    assert stats.n_windows == 60
    expected_real = 1.10 / 1.02 - 1.0
    assert pytest.approx(stats.real_median, rel=1e-3) == expected_real
    assert stats.negative_real_prob == 0.0
    assert stats.loss_time_pct_max == 0.0
    assert stats.max_consecutive_loss_months == 0


def test_rolling_returns_guaranteed_loss():
    dates = pd.date_range("2000-01-31", periods=70, freq="ME")
    prices = pd.Series([100.0 * (0.99**i) for i in range(70)])
    cpi = pd.Series([100.0 * (1.002**i) for i in range(70)])

    stats = calculate_rolling_returns(dates, prices, cpi, horizon_years=5)
    assert stats.loss_time_pct_max == 100.0
    assert stats.max_consecutive_loss_months == 60


def test_calculate_all_rolling_horizons():
    dates = pd.date_range("2000-01-31", periods=250, freq="ME")
    prices = pd.Series([100.0 * (1.05 ** (i / 12)) for i in range(250)])
    cpi = pd.Series([100.0 * (1.02 ** (i / 12)) for i in range(250)])

    res = calculate_all_rolling_horizons(dates, prices, cpi, horizons_years=(5, 10))
    assert set(res.keys()) == {5, 10}


def test_rolling_returns_with_ter():
    """Verifica che l'applicazione del TER riduca il CAGR reale del drag atteso."""
    dates = pd.date_range("2000-01-31", periods=120, freq="ME")
    prices = pd.Series([100.0 * (1.10 ** (i / 12)) for i in range(120)])
    cpi = pd.Series([100.0 * (1.02 ** (i / 12)) for i in range(120)])

    # Senza TER
    stats_gross = calculate_rolling_returns(dates, prices, cpi, horizon_years=5, ter_annual=0.0)
    # Con TER 2.0%
    stats_net = calculate_rolling_returns(dates, prices, cpi, horizon_years=5, ter_annual=0.02)

    assert stats_net.real_median < stats_gross.real_median
    # Drag teorico su base Fisher
    expected_real_net = (1.10 / 1.02) * (1.0 - ((1.02 ** (1/12) - 1.0) * 0 + 0.02 / 1.02)) # approx
    assert stats_gross.real_median - stats_net.real_median == pytest.approx(0.0196, abs=2e-3)


def test_rolling_returns_with_full_tax():
    """Verifica che bollo e capital gain riducano coerentemente il rendimento finale."""
    dates = pd.date_range("2000-01-31", periods=120, freq="ME")
    prices = pd.Series([100.0 * (1.10 ** (i / 12)) for i in range(120)])
    cpi = pd.Series([100.0 * (1.02 ** (i / 12)) for i in range(120)])

    stats_gross = calculate_rolling_returns(dates, prices, cpi, horizon_years=5)
    stats_taxed = calculate_rolling_returns(
        dates, prices, cpi, horizon_years=5, ter_annual=0.002, bollo_rate=0.002, capital_gain_rate=0.26
    )

    # Il rendimento netto con tasse deve essere inferiore al lordo
    assert stats_taxed.real_median < stats_gross.real_median
    assert stats_taxed.windows_df["nominal_cagr"].iloc[0] < stats_gross.windows_df["nominal_cagr"].iloc[0]

