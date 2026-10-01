import numpy as np
import pandas as pd
import pytest

from src.engine.statistics import (
    block_bootstrap_simulation,
    calculate_all_rolling_horizons,
    calculate_rolling_returns,
)


def test_calculate_rolling_returns_deterministic():
    """Verifica che su una crescita deterministica (10% nominale, 2% inflazione),

    tutte le finestre mobili restituiscano esattamente i CAGR teorici attesi.
    """
    # 120 mesi (10 anni)
    dates = pd.date_range("2000-01-31", periods=120, freq="ME")
    prices = pd.Series([100.0 * (1.10 ** (i / 12)) for i in range(120)])
    cpi = pd.Series([100.0 * (1.02 ** (i / 12)) for i in range(120)])

    stats = calculate_rolling_returns(dates, prices, cpi, horizon_years=5)

    # 120 mesi - 60 mesi = 60 finestre quinquennali
    assert stats.n_windows == 60
    assert pytest.approx(stats.nominal_median, rel=1e-3) == 0.10
    assert pytest.approx(stats.nominal_min, rel=1e-3) == 0.10
    assert pytest.approx(stats.nominal_max, rel=1e-3) == 0.10
    assert stats.nominal_std == 0.0

    # Fisher: (1.10 / 1.02) - 1 ≈ 0.07843 (7.84%)
    expected_real = 1.10 / 1.02 - 1.0
    assert pytest.approx(stats.real_median, rel=1e-3) == expected_real
    assert stats.negative_real_prob == 0.0


def test_calculate_rolling_returns_insufficient_data():
    """Verifica che venga sollevato ValueError se i mesi sono insufficienti."""
    dates = pd.date_range("2000-01-31", periods=30, freq="ME")
    prices = pd.Series([100.0] * 30)
    cpi = pd.Series([100.0] * 30)

    # 5 anni richiedono almeno 61 osservazioni
    with pytest.raises(ValueError):
        calculate_rolling_returns(dates, prices, cpi, horizon_years=5)


def test_calculate_all_rolling_horizons():
    """Verifica il calcolo aggregato su orizzonti multipli."""
    # 250 mesi (~20.8 anni)
    dates = pd.date_range("2000-01-31", periods=250, freq="ME")
    prices = pd.Series([100.0 * (1.05 ** (i / 12)) for i in range(250)])
    cpi = pd.Series([100.0 * (1.02 ** (i / 12)) for i in range(250)])

    horizons_dict = calculate_all_rolling_horizons(
        dates, prices, cpi, horizons_years=(5, 10, 15, 20)
    )

    # Tutti gli orizzonti devono essere stati calcolati
    assert set(horizons_dict.keys()) == {5, 10, 15, 20}
    assert horizons_dict[5].n_windows == 250 - 60
    assert horizons_dict[20].n_windows == 250 - 240


def test_block_bootstrap_reproducibility():
    """Verifica che a parità di seed la simulazione restituisca gli stessi percentili."""
    returns = pd.Series(np.linspace(-0.03, 0.04, 150))
    inflation = pd.Series([0.002] * 150)

    res1 = block_bootstrap_simulation(
        returns, inflation, horizon_years=5, n_simulations=200, seed=123
    )
    res2 = block_bootstrap_simulation(
        returns, inflation, horizon_years=5, n_simulations=200, seed=123
    )

    assert (
        res1.terminal_nominal_cagr_p50 == res2.terminal_nominal_cagr_p50
    )
    assert res1.loss_prob_real == res2.loss_prob_real
    assert np.allclose(
        res1.nominal_percentile_paths[50], res2.nominal_percentile_paths[50]
    )


def test_block_bootstrap_flat_market():
    """Su rendimenti e inflazione rigorosamente a zero, il capitale non varia."""
    returns = pd.Series([0.0] * 60)
    inflation = pd.Series([0.0] * 60)

    res = block_bootstrap_simulation(
        returns, inflation, horizon_years=2, n_simulations=100, seed=42
    )

    assert res.terminal_nominal_cagr_p50 == 0.0
    assert res.terminal_real_cagr_p50 == 0.0
    assert res.loss_prob_nominal == 0.0
    assert res.loss_prob_real == 0.0