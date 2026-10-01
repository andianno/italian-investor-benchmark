import numpy as np
import pandas as pd
import pytest

from src.engine.metrics import (
    calculate_annualized_volatility,
    calculate_cagr,
    calculate_drawdown_series,
    calculate_max_drawdown,
    calculate_real_return,
    calculate_xirr,
)


def test_calculate_cagr():
    # Raddoppio esatto in 10 anni: (2)^(1/10) - 1 ≈ 7.177%
    cagr = calculate_cagr(100.0, 200.0, 10.0)
    assert pytest.approx(cagr, rel=1e-4) == 0.07177

    # Nessuna variazione
    assert calculate_cagr(100.0, 100.0, 5.0) == 0.0

    # Errori su input non validi
    with pytest.raises(ValueError):
        calculate_cagr(0, 100.0, 10.0)
    with pytest.raises(ValueError):
        calculate_cagr(100.0, 200.0, 0)


def test_calculate_real_return_fisher():
    # Rendimento nominale 10%, inflazione 10% -> rendimento reale = 0%
    assert pytest.approx(calculate_real_return(0.10, 0.10)) == 0.0

    # Rendimento nominale 8%, inflazione 2% -> (1.08 / 1.02) - 1 ≈ 5.882%
    # (l'approssimazione rozza 8 - 2 = 6% sovrastima)
    real_ret = calculate_real_return(0.08, 0.02)
    assert pytest.approx(real_ret, rel=1e-4) == 0.05882


def test_drawdown_and_max_drawdown():
    # Prezzi: 100 -> 150 (nuovo picco) -> 75 (-50% dal picco) -> 120
    prices = pd.Series([100.0, 150.0, 75.0, 120.0])
    dd_series = calculate_drawdown_series(prices)

    expected_dd = [0.0, 0.0, -0.50, -0.20]
    np.testing.assert_allclose(dd_series.values, expected_dd)

    mdd = calculate_max_drawdown(prices)
    assert mdd == -0.50


def test_annualized_volatility():
    # Serie di rendimenti mensili alternati
    returns = pd.Series([0.02, -0.01, 0.03, -0.02])
    vol = calculate_annualized_volatility(returns)
    assert vol > 0
    # Deviazione std mensile * sqrt(12)
    assert pytest.approx(vol) == float(returns.std(ddof=1) * np.sqrt(12))


def test_calculate_xirr():
    # Test 1: Esattamente 365 giorni (anno non bisestile 2021 -> 2022)
    # Un guadagno del 10% in esattamente 365 giorni deve restituire rate = 0.10
    dates = [pd.Timestamp("2021-01-01"), pd.Timestamp("2022-01-01")]
    cash_flows = [-1000.0, 1100.0]

    rate = calculate_xirr(cash_flows, dates)
    assert pytest.approx(rate, rel=1e-4) == 0.10

    # Test 2: Anno bisestile (2020 -> 2021, 366 giorni)
    # Poiché il capitale ha impiegato 366 giorni per fare il 10%,
    # il tasso annualizzato su base 365 è leggermente inferiore: (1.10)^(365/366) - 1 ≈ 9.971%
    leap_dates = [pd.Timestamp("2020-01-01"), pd.Timestamp("2021-01-01")]
    leap_rate = calculate_xirr(cash_flows, leap_dates)
    expected_leap_rate = (1100.0 / 1000.0) ** (365.0 / 366.0) - 1.0
    assert pytest.approx(leap_rate, rel=1e-4) == expected_leap_rate


def calculate_real_return_fisher(nominal_return: float, inflation_rate: float) -> float:
    """Calcola il rendimento reale esatto tramite l'equazione di Fisher:

    (1 + r_reale) = (1 + r_nominale) / (1 + inflazione)
    r_reale = (1 + r_nominale) / (1 + inflazione) - 1
    """
    return (1.0 + nominal_return) / (1.0 + inflation_rate) - 1.0


# Alias per retrocompatibilità
calculate_real_return = calculate_real_return_fisher
