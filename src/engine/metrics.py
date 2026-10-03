"""Metriche e formule finanziarie quantitative per l'analisi di portafoglio."""

from typing import Union

import numpy as np
import pandas as pd
from scipy import optimize



def calculate_cagr(start_value: float, end_value: float, years: float) -> float:
    """Calcola il tasso di crescita annuo composto (CAGR).

    Raises
    ------
    ValueError
        Se start_value <= 0, end_value < 0 o years <= 0.
    """
    if start_value <= 0:
        raise ValueError(
            "Il valore iniziale (start_value) deve essere maggiore di zero."
        )
    if end_value < 0:
        raise ValueError("Il valore finale (end_value) non può essere negativo.")
    if years <= 0:
        raise ValueError("L'orizzonte temporale (years) deve essere maggiore di zero.")
    return (end_value / start_value) ** (1.0 / years) - 1.0


def calculate_real_return_fisher(nominal_return: float, inflation_rate: float) -> float:
    """Calcola il rendimento reale esatto tramite l'equazione di Fisher:

    (1 + r_reale) = (1 + r_nominale) / (1 + inflazione)
    r_reale = (1 + r_nominale) / (1 + inflazione) - 1
    """
    return (1.0 + nominal_return) / (1.0 + inflation_rate) - 1.0


# Alias per retrocompatibilità
calculate_real_return = calculate_real_return_fisher


def calculate_drawdown_series(prices: pd.Series) -> pd.Series:
    """Calcola la serie dei drawdown percentuali rispetto ai massimi storici precedenti."""
    rolling_max = prices.cummax()
    return (prices - rolling_max) / rolling_max


def calculate_max_drawdown(prices: pd.Series) -> float:
    """Calcola il massimo drawdown percentuale (valore minimo negativo)."""
    dd = calculate_drawdown_series(prices)
    if dd.empty:
        return 0.0
    return float(dd.min())


def calculate_annualized_volatility(
    returns: pd.Series, periods_per_year: int = 12
) -> float:
    """Calcola la volatilità annualizzata data una serie di rendimenti periodici."""
    clean_returns = returns.dropna()
    if len(clean_returns) < 2:
        return 0.0
    return float(clean_returns.std() * np.sqrt(periods_per_year))


def calculate_xirr(
    cash_flows: Union[np.ndarray, pd.Series, list],
    dates: Union[pd.Series, pd.DatetimeIndex, list],
) -> float:
    """Calcola il Money-Weighted Return annualizzato (XIRR).

    Utilizza la convenzione standard a 365.0 giorni per anno.
    """
    cf = np.asarray(cash_flows, dtype=float)
    dt = pd.to_datetime(dates)

    if len(cf) != len(dt):
        raise ValueError("Lunghezza di flussi e date non coincidente.")
    if not (np.any(cf < 0) and np.any(cf > 0)):
        return 0.0

    t0 = dt[0]
    years_fraction = np.array([(d - t0).days / 365.0 for d in dt])

    def npv(rate: float) -> float:
        if rate <= -0.999999:
            return float("inf")
        return float(np.sum(cf / ((1.0 + rate) ** years_fraction)))

    try:
        rate = optimize.brentq(npv, -0.999, 10.0, maxiter=200)
        return float(rate)
    except (ValueError, RuntimeError):
        try:
            rate = optimize.newton(npv, 0.05, maxiter=200)
            return float(rate)
        except Exception:
            return 0.0


def apply_ter_to_prices(prices: pd.Series, ter_annual: float) -> pd.Series:
    """Simula la serie storica dei prezzi/NAV decurtata del TER annuo.

    Decurtazione su base geometrica mensile:
    drag_mensile = (1 + TER)^(1/12) - 1
    NAV_t = Prezzo_t * (1 - drag_mensile)^t

    Parameters
    ----------
    prices : pd.Series
        Serie delle quotazioni lorde dell'indice o benchmark.
    ter_annual : float
        Total Expense Ratio annuo (es. 0.0020 per lo 0.20%, 0.0200 per il 2.00%).

    Returns
    -------
    pd.Series
        Serie dei prezzi al netto dell'impatto cumulato del TER.

    Raises
    ------
    ValueError
        Se ter_annual < 0.
    """
    if ter_annual < 0.0:
        raise ValueError("Il TER non può essere negativo.")
    prices_s = pd.Series(prices, dtype=float)
    n_months = len(prices_s)
    if n_months == 0:
        return prices_s.copy()
    monthly_ter_drag = (1.0 + ter_annual) ** (1.0 / 12.0) - 1.0
    drag_factors = (1.0 - monthly_ter_drag) ** np.arange(n_months)
    return pd.Series(prices_s.values * drag_factors, index=prices_s.index)

