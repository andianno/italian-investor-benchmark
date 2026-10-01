"""Modulo per l'analisi statistica a finestre mobili e distribuzioni empiriche."""

from dataclasses import dataclass
from typing import Dict, Tuple
import numpy as np
import pandas as pd

from src.engine.metrics import (
    calculate_cagr,
    calculate_real_return_fisher,
)


@dataclass(frozen=True)
class RollingWindowStats:
    """Statistiche aggregate sulle distribuzioni a finestre mobili."""

    horizon_years: int
    n_windows: int
    # Metriche Rendimento Reale (CAGR)
    real_min: float
    real_p05: float
    real_median: float
    real_p95: float
    real_max: float
    real_std: float
    negative_real_prob: float
    # Metriche Tempo Sott'Acqua / Perdita Reale (% della durata finestra)
    loss_time_pct_min: float
    loss_time_pct_median: float
    loss_time_pct_max: float
    # Mesi consecutivi peggiori in perdita reale
    max_consecutive_loss_months: int
    # Peggior Drawdown Reale visto all'interno delle finestre
    worst_drawdown_real: float
    # DataFrame con tutte le singole finestre per i grafici
    windows_df: pd.DataFrame


def calculate_rolling_returns(
    dates: pd.Series,
    prices: pd.Series,
    cpi: pd.Series,
    horizon_years: int = 5,
) -> RollingWindowStats:
    """Calcola rendimenti e durata della perdita reale su tutte le finestre mobili di ampiezza H."""
    window_months = horizon_years * 12
    n_observations = len(prices)

    if n_observations < window_months + 1:
        raise ValueError(
            f"Dati insufficienti: servono almeno {window_months + 1} mesi per "
            f"l'orizzonte di {horizon_years} anni."
        )

    prices_arr = np.asarray(prices, dtype=float)
    cpi_arr = np.asarray(cpi, dtype=float)
    dates_arr = pd.to_datetime(dates).values

    records = []
    n_windows = n_observations - window_months

    for start_idx in range(n_windows):
        end_idx = start_idx + window_months

        p_start = prices_arr[start_idx]
        p_end = prices_arr[end_idx]
        cpi_start = cpi_arr[start_idx]
        cpi_end = cpi_arr[end_idx]

        # CAGR Nominale e Reale a scadenza
        nom_cagr = calculate_cagr(p_start, p_end, horizon_years)
        cpi_growth = cpi_end / cpi_start - 1.0
        cpi_annual = (1.0 + cpi_growth) ** (1.0 / horizon_years) - 1.0
        real_cagr = calculate_real_return_fisher(nom_cagr, cpi_annual)

        # Traiettoria reale normalizzata mese per mese (t0 = 1.0)
        window_prices = prices_arr[start_idx : end_idx + 1]
        window_cpi = cpi_arr[start_idx : end_idx + 1]
        real_path = (window_prices / p_start) * (cpi_start / window_cpi)

        # Analisi perdita reale (escludendo t=0)
        in_loss_path = real_path[1:] < 1.0
        loss_months_total = int(np.sum(in_loss_path))
        pct_time_in_loss = (loss_months_total / window_months) * 100.0

        # Calcolo striscia consecutiva massima in perdita reale
        max_consec = 0
        curr_consec = 0
        for is_loss in in_loss_path:
            if is_loss:
                curr_consec += 1
                if curr_consec > max_consec:
                    max_consec = curr_consec
            else:
                curr_consec = 0

        # Drawdown reale all'interno della finestra
        real_peaks = np.maximum.accumulate(real_path)
        real_dd = (real_path - real_peaks) / real_peaks
        max_dd_in_window = float(np.min(real_dd))

        records.append(
            {
                "start_date": dates_arr[start_idx],
                "end_date": dates_arr[end_idx],
                "nominal_cagr": nom_cagr,
                "real_cagr": real_cagr,
                "pct_time_in_loss": pct_time_in_loss,
                "loss_months_total": loss_months_total,
                "max_consecutive_loss_months": max_consec,
                "worst_real_dd": max_dd_in_window,
            }
        )

    df_w = pd.DataFrame(records)
    real_vals = df_w["real_cagr"].values
    loss_pct_vals = df_w["pct_time_in_loss"].values

    return RollingWindowStats(
        horizon_years=horizon_years,
        n_windows=len(df_w),
        real_min=float(np.min(real_vals)),
        real_p05=float(np.percentile(real_vals, 5)),
        real_median=float(np.median(real_vals)),
        real_p95=float(np.percentile(real_vals, 95)),
        real_max=float(np.max(real_vals)),
        real_std=float(np.std(real_vals)),
        negative_real_prob=float(np.mean(real_vals < 0.0)),
        loss_time_pct_min=float(np.min(loss_pct_vals)),
        loss_time_pct_median=float(np.median(loss_pct_vals)),
        loss_time_pct_max=float(np.max(loss_pct_vals)),
        max_consecutive_loss_months=int(np.max(df_w["max_consecutive_loss_months"])),
        worst_drawdown_real=float(np.min(df_w["worst_real_dd"])),
        windows_df=df_w,
    )


def calculate_all_rolling_horizons(
    dates: pd.Series,
    prices: pd.Series,
    cpi: pd.Series,
    horizons_years: Tuple[int, ...] = (5, 10, 15, 20),
) -> Dict[int, RollingWindowStats]:
    """Calcola le statistiche mobili per tutti gli orizzonti temporali indicati."""
    return {
        h: calculate_rolling_returns(dates, prices, cpi, horizon_years=h)
        for h in horizons_years
    }
