from datetime import date
from typing import Sequence
import numpy as np
import pandas as pd
from scipy import optimize


def calculate_cagr(
    start_value: float, end_value: float, years: float
) -> float:
    """Calcola il Compound Annual Growth Rate (CAGR).

    Formula: (V_end / V_start) ** (1 / years) - 1
    """
    if start_value <= 0:
        raise ValueError("Il capitale iniziale deve essere strettamente positivo.")
    if years <= 0:
        raise ValueError("L'orizzonte temporale deve essere maggiore di zero.")

    return float((end_value / start_value) ** (1.0 / years) - 1.0)


def calculate_real_return(nominal_return: float, inflation_rate: float) -> float:
    """Calcola il rendimento reale tramite l'equazione esatta di Fisher.

    Formula: (1 + r_nom) / (1 + i) - 1
    """
    if inflation_rate <= -1.0:
        raise ValueError("Il tasso di inflazione non può essere <= -100%.")

    return float((1.0 + nominal_return) / (1.0 + inflation_rate) - 1.0)


def calculate_drawdown_series(prices: pd.Series) -> pd.Series:
    """Calcola la serie storica dei drawdown percentuali rispetto ai massimi precedenti (HWM).

    Formula: (P_t - HighWaterMark_t) / HighWaterMark_t
    """
    if (prices <= 0).any():
        raise ValueError("I prezzi devono essere strettamente positivi.")

    high_water_mark = prices.cummax()
    drawdown = (prices - high_water_mark) / high_water_mark
    return drawdown


def calculate_max_drawdown(prices: pd.Series) -> float:
    """Restituisce il valore minimo della serie di drawdown (il punto di massima perdita percentuale)."""
    dd_series = calculate_drawdown_series(prices)
    return float(dd_series.min())


def calculate_annualized_volatility(
    monthly_returns: pd.Series, periods_per_year: int = 12
) -> float:
    """Calcola la deviazione standard annualizzata dei rendimenti.

    Formula: sigma_mensile * sqrt(12)
    """
    # Usiamo ddof=1 per la deviazione standard campionaria corretta
    clean_returns = monthly_returns.dropna()
    if len(clean_returns) < 2:
        return 0.0

    return float(clean_returns.std(ddof=1) * np.sqrt(periods_per_year))


def calculate_xirr(
    cash_flows: Sequence[float], dates: Sequence[pd.Timestamp | date]
) -> float:
    """Calcola il Tasso Interno di Rendimento annualizzato (XIRR / Money-Weighted Return).

    Risolve numericamente: sum( C_t / (1 + r)^((d_t - d_0) / 365) ) = 0
    I versamenti devono essere negativi, il valore finale positivo.
    """
    if len(cash_flows) != len(dates):
        raise ValueError("Il numero di flussi di cassa deve coincidere con il numero di date.")
    if len(cash_flows) < 2:
        raise ValueError("Servono almeno due flussi di cassa per calcolare l'XIRR.")

    cf_array = np.array(cash_flows, dtype=float)
    if (cf_array > 0).sum() == 0 or (cf_array < 0).sum() == 0:
        raise ValueError("L'XIRR richiede almeno un flusso negativo e uno positivo.")

    d0 = pd.Timestamp(dates[0])
    day_fractions = np.array(
        [(pd.Timestamp(d) - d0).days / 365.0 for d in dates], dtype=float
    )

    def npv(rate: float) -> float:
        if rate <= -1.0:
            return float("inf")
        return float(np.sum(cf_array / ((1.0 + rate) ** day_fractions)))

    try:
        # Risoluzione con metodo Brent/Newton partendo da una stima iniziale del 5%
        result = optimize.newton(npv, x0=0.05, maxiter=100)
        return float(result)
    except (RuntimeError, OverflowError):
        # Fallback con brentq in caso di convergenza difficile
        return float(optimize.brentq(npv, -0.999, 10.0))