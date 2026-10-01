"""Modulo di statistica avanzata per benchmark finanziari.

Fornisce analisi a finestre mobili (Rolling Returns) e simulazioni Monte Carlo
non parametriche tramite Moving Block Bootstrapping.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Sequence
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RollingWindowStats:
    """Statistiche aggregate su finestre mobili di durata fissa."""

    horizon_years: int
    n_windows: int
    # CAGR Nominale
    nominal_min: float
    nominal_p05: float
    nominal_median: float
    nominal_mean: float
    nominal_p95: float
    nominal_max: float
    nominal_std: float
    # CAGR Reale (deflazionato con serie CPI)
    real_min: float
    real_p05: float
    real_median: float
    real_mean: float
    real_p95: float
    real_max: float
    real_std: float
    # Probabilità empirica di rendimento reale < 0%
    negative_real_prob: float
    # Tabella dettagliata di ogni singola finestra
    windows_df: pd.DataFrame


@dataclass(frozen=True)
class BootstrapResult:
    """Risultati della simulazione Monte Carlo con Block Bootstrapping."""

    horizon_years: int
    n_simulations: int
    block_size_months: int
    # Percentili del CAGR Nominale terminale
    terminal_nominal_cagr_p05: float
    terminal_nominal_cagr_p25: float
    terminal_nominal_cagr_p50: float
    terminal_nominal_cagr_p75: float
    terminal_nominal_cagr_p95: float
    # Percentili del CAGR Reale terminale
    terminal_real_cagr_p05: float
    terminal_real_cagr_p25: float
    terminal_real_cagr_p50: float
    terminal_real_cagr_p75: float
    terminal_real_cagr_p95: float
    # Probabilità di perdita terminale (Capitale Finale < Capitale Iniziale)
    loss_prob_nominal: float
    loss_prob_real: float
    # Traiettorie percentilari del montante nel tempo (per grafici a ventaglio)
    nominal_percentile_paths: Dict[int, np.ndarray]
    real_percentile_paths: Dict[int, np.ndarray]


def calculate_rolling_returns(
    dates: pd.Series,
    prices: pd.Series,
    cpi: pd.Series,
    horizon_years: int,
) -> RollingWindowStats:
    """Calcola la distribuzione dei rendimenti su finestre mobili di ampiezza fissa.

    Parameters
    ----------
    dates : pd.Series
        Date mensili della serie storica.
    prices : pd.Series
        Prezzi storici Net Total Return dell'indice o NAV dell'ETF.
    cpi : pd.Series
        Indice CPI allineato alle date.
    horizon_years : int
        Ampiezza dell'orizzonte in anni (es. 5, 10, 15, 20).
    """
    if horizon_years <= 0:
        raise ValueError("L'orizzonte temporale deve essere strettamente positivo.")

    window_months = horizon_years * 12
    n_obs = min(len(dates), len(prices), len(cpi))

    if n_obs <= window_months:
        raise ValueError(
            f"Dati insufficienti: orizzonte {horizon_years} anni richiede almeno "
            f"{window_months + 1} mesi, trovati {n_obs}."
        )

    p = pd.Series(prices[:n_obs], dtype=float).values
    c = pd.Series(cpi[:n_obs], dtype=float).values
    d = pd.Series(pd.to_datetime(dates[:n_obs])).reset_index(drop=True)

    # Calcolo vettoriale di tutti gli estremi delle finestre mobili
    p_start = p[:-window_months]
    p_end = p[window_months:]
    c_start = c[:-window_months]
    c_end = c[window_months:]

    # CAGR nominale su ogni finestra
    nom_cagr = (p_end / p_start) ** (1.0 / horizon_years) - 1.0

    # CAGR reale esatto tramite prezzi deflazionati (Fisher): P_real = P / CPI
    real_cagr = (
        (p_end / c_end) / (p_start / c_start)
    ) ** (1.0 / horizon_years) - 1.0

    n_windows = len(nom_cagr)
    neg_real_prob = float(np.mean(real_cagr < 0.0))

    windows_df = pd.DataFrame(
        {
            "start_date": d.iloc[:-window_months].values,
            "end_date": d.iloc[window_months:].values,
            "nominal_cagr": nom_cagr,
            "real_cagr": real_cagr,
        }
    )

    return RollingWindowStats(
        horizon_years=horizon_years,
        n_windows=n_windows,
        nominal_min=round(float(np.min(nom_cagr)), 4),
        nominal_p05=round(float(np.percentile(nom_cagr, 5)), 4),
        nominal_median=round(float(np.median(nom_cagr)), 4),
        nominal_mean=round(float(np.mean(nom_cagr)), 4),
        nominal_p95=round(float(np.percentile(nom_cagr, 95)), 4),
        nominal_max=round(float(np.max(nom_cagr)), 4),
        nominal_std=round(float(np.std(nom_cagr, ddof=1)), 4),
        real_min=round(float(np.min(real_cagr)), 4),
        real_p05=round(float(np.percentile(real_cagr, 5)), 4),
        real_median=round(float(np.median(real_cagr)), 4),
        real_mean=round(float(np.mean(real_cagr)), 4),
        real_p95=round(float(np.percentile(real_cagr, 95)), 4),
        real_max=round(float(np.max(real_cagr)), 4),
        real_std=round(float(np.std(real_cagr, ddof=1)), 4),
        negative_real_prob=round(neg_real_prob, 4),
        windows_df=windows_df,
    )


def calculate_all_rolling_horizons(
    dates: pd.Series,
    prices: pd.Series,
    cpi: pd.Series,
    horizons_years: Sequence[int] = (5, 10, 15, 20),
) -> Dict[int, RollingWindowStats]:
    """Esegue l'analisi a finestre mobili su tutti gli orizzonti compatibili con la serie storica."""
    results: Dict[int, RollingWindowStats] = {}
    n_obs = len(prices)

    for h in horizons_years:
        if n_obs > h * 12:
            results[h] = calculate_rolling_returns(dates, prices, cpi, h)

    return results


def block_bootstrap_simulation(
    returns: pd.Series,
    inflation: pd.Series,
    horizon_years: int = 10,
    n_simulations: int = 2000,
    block_size_months: int = 12,
    seed: Optional[int] = 42,
) -> BootstrapResult:
    """Esegue una simulazione Monte Carlo con Moving Block Bootstrap.

    Campiona blocchi temporali contigui di 12 mesi per conservare la correlazione
    tra rendimenti azionari e inflazione, oltre che i cluster di volatilità storici.
    """
    if horizon_years <= 0:
        raise ValueError("L'orizzonte temporale deve essere maggiore di zero.")
    if n_simulations <= 0:
        raise ValueError("Il numero di simulazioni deve essere positivo.")
    if block_size_months <= 0:
        raise ValueError("La dimensione del blocco deve essere positiva.")

    ret_clean = pd.Series(returns).dropna().values
    inf_clean = pd.Series(inflation).dropna().values
    n_obs = min(len(ret_clean), len(inf_clean))

    if n_obs < block_size_months:
        raise ValueError(
            f"Dati insufficienti: servono almeno {block_size_months} mesi di storico comune."
        )

    ret_arr = ret_clean[:n_obs]
    inf_arr = inf_clean[:n_obs]

    n_months = horizon_years * 12
    n_blocks = int(np.ceil(n_months / block_size_months))
    max_start = n_obs - block_size_months + 1

    rng = np.random.default_rng(seed)

    # Estrazione di tutti i blocchi sovrapposti disponibili
    ret_blocks = np.array(
        [ret_arr[i : i + block_size_months] for i in range(max_start)]
    )
    inf_blocks = np.array(
        [inf_arr[i : i + block_size_months] for i in range(max_start)]
    )

    # Matrice di indici casuali con reinserimento: (n_simulations, n_blocks)
    idx_matrix = rng.integers(0, max_start, size=(n_simulations, n_blocks))

    # Assemblaggio dei percorsi simulati: (n_simulations, n_months)
    sim_ret = ret_blocks[idx_matrix].reshape(n_simulations, -1)[:, :n_months]
    sim_inf = inf_blocks[idx_matrix].reshape(n_simulations, -1)[:, :n_months]

    # Rendimento mensile reale tramite equazione di Fisher: (1 + r) / (1 + i) - 1
    sim_real_ret = (1.0 + sim_ret) / (1.0 + sim_inf) - 1.0

    # Evoluzione temporale del patrimonio (base 1.0)
    wealth_nom = np.empty((n_simulations, n_months + 1), dtype=float)
    wealth_real = np.empty((n_simulations, n_months + 1), dtype=float)
    wealth_nom[:, 0] = 1.0
    wealth_real[:, 0] = 1.0

    np.cumprod(1.0 + sim_ret, axis=1, out=wealth_nom[:, 1:])
    np.cumprod(1.0 + sim_real_ret, axis=1, out=wealth_real[:, 1:])

    terminal_nom = wealth_nom[:, -1]
    terminal_real = wealth_real[:, -1]

    # Calcolo CAGR terminale per ogni percorso
    nom_cagr = np.sign(terminal_nom) * (
        np.abs(terminal_nom) ** (1.0 / horizon_years)
    ) - 1.0
    real_cagr = np.sign(terminal_real) * (
        np.abs(terminal_real) ** (1.0 / horizon_years)
    ) - 1.0

    percentiles = [5, 25, 50, 75, 95]
    nom_cagr_pcts = {p: float(np.percentile(nom_cagr, p)) for p in percentiles}
    real_cagr_pcts = {
        p: float(np.percentile(real_cagr, p)) for p in percentiles
    }

    loss_nom = float(np.mean(terminal_nom < 1.0))
    loss_real = float(np.mean(terminal_real < 1.0))

    nom_paths = {p: np.percentile(wealth_nom, p, axis=0) for p in percentiles}
    real_paths = {p: np.percentile(wealth_real, p, axis=0) for p in percentiles}

    return BootstrapResult(
        horizon_years=horizon_years,
        n_simulations=n_simulations,
        block_size_months=block_size_months,
        terminal_nominal_cagr_p05=round(nom_cagr_pcts[5], 4),
        terminal_nominal_cagr_p25=round(nom_cagr_pcts[25], 4),
        terminal_nominal_cagr_p50=round(nom_cagr_pcts[50], 4),
        terminal_nominal_cagr_p75=round(nom_cagr_pcts[75], 4),
        terminal_nominal_cagr_p95=round(nom_cagr_pcts[95], 4),
        terminal_real_cagr_p05=round(real_cagr_pcts[5], 4),
        terminal_real_cagr_p25=round(real_cagr_pcts[25], 4),
        terminal_real_cagr_p50=round(real_cagr_pcts[50], 4),
        terminal_real_cagr_p75=round(real_cagr_pcts[75], 4),
        terminal_real_cagr_p95=round(real_cagr_pcts[95], 4),
        loss_prob_nominal=round(loss_nom, 4),
        loss_prob_real=round(loss_real, 4),
        nominal_percentile_paths=nom_paths,
        real_percentile_paths=real_paths,
    )