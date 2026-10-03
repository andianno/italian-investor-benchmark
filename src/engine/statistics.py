"""Modulo per l'analisi statistica a finestre mobili, distribuzioni empiriche e asimmetria del rischio."""

from dataclasses import dataclass
from typing import Dict, Tuple
import numpy as np
import pandas as pd

from src.engine.metrics import (
    apply_ter_to_prices,
    calculate_cagr,
    calculate_drawdown_series,
    calculate_real_return_fisher,
)


@dataclass(frozen=True)
class UnderwaterPainStats:
    """Metriche di sofferenza psicologica e tempo di recupero (Underwater Analysis)."""

    max_drawdown: float  # Massimo drawdown storico subito (es. -0.55 per -55%)
    max_underwater_months: int  # Mesi consecutivi peggiori sotto il picco precedente
    max_underwater_years: float  # Durata massima consecutiva in anni (mesi / 12)
    underwater_months_pct: float  # % dei mesi totali trascorsi sott'acqua (drawdown < 0)
    total_months: int
    drawdown_series: pd.Series


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
    # Metriche Rendimento Nominale (CAGR)
    nominal_min: float = 0.0
    nominal_p05: float = 0.0
    nominal_median: float = 0.0
    nominal_p95: float = 0.0
    nominal_max: float = 0.0
    nominal_std: float = 0.0
    negative_nominal_prob: float = 0.0
    # Peggior Drawdown Nominale all'interno delle finestre
    worst_drawdown_nominal: float = 0.0
    # Statistiche Inflazione Cumulata di Periodo
    inflation_cum_min: float = 0.0
    inflation_cum_median: float = 0.0
    inflation_cum_max: float = 0.0


def calculate_underwater_pain(prices: pd.Series) -> UnderwaterPainStats:
    """Calcola le metriche di sofferenza psicologica e tempo di recupero dal picco precedente.

    Parameters
    ----------
    prices : pd.Series
        Serie storica delle quotazioni o valore patrimoniale.

    Returns
    -------
    UnderwaterPainStats
        Statistiche su drawdown, durata massima sott'acqua e % mesi trascorsi in perdita.

    Raises
    ------
    ValueError
        Se la serie contiene meno di 2 osservazioni.
    """
    clean_prices = pd.Series(prices, dtype=float).dropna().reset_index(drop=True)
    n_obs = len(clean_prices)
    if n_obs < 2:
        raise ValueError(
            f"Dati insufficienti: servono almeno 2 osservazioni per l'underwater analysis (trovate {n_obs})."
        )

    dd_series = calculate_drawdown_series(clean_prices)
    max_dd = float(dd_series.min())

    underwater_mask = (dd_series < -1e-9).values
    total_underwater_months = int(np.sum(underwater_mask))
    underwater_pct = (total_underwater_months / n_obs) * 100.0

    max_consec = 0
    curr_consec = 0
    for is_underwater in underwater_mask:
        if is_underwater:
            curr_consec += 1
            if curr_consec > max_consec:
                max_consec = curr_consec
        else:
            curr_consec = 0

    return UnderwaterPainStats(
        max_drawdown=max_dd,
        max_underwater_months=max_consec,
        max_underwater_years=max_consec / 12.0,
        underwater_months_pct=underwater_pct,
        total_months=n_obs,
        drawdown_series=dd_series,
    )


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

        # Traiettoria nominale e calcolo drawdown nominale nella finestra
        window_prices = prices_arr[start_idx : end_idx + 1]
        nom_peaks = np.maximum.accumulate(window_prices)
        nom_dd = (window_prices - nom_peaks) / nom_peaks
        max_nom_dd_in_window = float(np.min(nom_dd))

        # Traiettoria reale normalizzata mese per mese (t0 = 1.0)
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
                "cumulative_inflation": cpi_growth,
                "annualized_inflation": cpi_annual,
                "real_cagr": real_cagr,
                "worst_nominal_dd": max_nom_dd_in_window,
                "worst_real_dd": max_dd_in_window,
                "pct_time_in_loss": pct_time_in_loss,
                "loss_months_total": loss_months_total,
                "max_consecutive_loss_months": max_consec,
            }
        )

    df_w = pd.DataFrame(records)
    real_vals = df_w["real_cagr"].values
    nom_vals = df_w["nominal_cagr"].values
    inf_cum_vals = df_w["cumulative_inflation"].values
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
        nominal_min=float(np.min(nom_vals)),
        nominal_p05=float(np.percentile(nom_vals, 5)),
        nominal_median=float(np.median(nom_vals)),
        nominal_p95=float(np.percentile(nom_vals, 95)),
        nominal_max=float(np.max(nom_vals)),
        nominal_std=float(np.std(nom_vals)),
        negative_nominal_prob=float(np.mean(nom_vals < 0.0)),
        worst_drawdown_nominal=float(np.min(df_w["worst_nominal_dd"])),
        inflation_cum_min=float(np.min(inf_cum_vals)),
        inflation_cum_median=float(np.median(inf_cum_vals)),
        inflation_cum_max=float(np.max(inf_cum_vals)),
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


@dataclass(frozen=True)
class RiskAsymmetryComparison:
    """Risultato del confronto di asimmetria tra ETF a basso costo e Fondo Bancario attivo."""

    etf_name: str
    bank_fund_name: str
    etf_ter: float
    bank_fund_ter: float
    etf_underwater: UnderwaterPainStats
    bank_underwater: UnderwaterPainStats
    etf_rolling: Dict[int, RollingWindowStats]
    bank_rolling: Dict[int, RollingWindowStats]
    horizons_years: Tuple[int, ...]


def compare_etf_vs_bank_fund(
    dates: pd.Series,
    benchmark_prices: pd.Series,
    cpi: pd.Series,
    etf_ter: float = 0.0020,
    bank_fund_ter: float = 0.0200,
    horizons_years: Tuple[int, ...] = (5, 10, 15, 20),
    etf_name: str = "ETF Passivo (SWDA - TER 0.20%)",
    bank_fund_name: str = "Fondo Bancario (TER 2.00%)",
) -> RiskAsymmetryComparison:
    """Esegue l'analisi comparativa dell'asimmetria del rischio tra ETF e Fondo Bancario.

    Simula entrambi gli strumenti sullo stesso benchmark e calcola:
    1. Metriche storiche di sofferenza psicologica (Drawdown massimo, mesi sott'acqua, % tempo in perdita).
    2. Rendimenti e rischio di perdita reale a finestre mobili (5, 10, 15, 20 anni).
    """
    etf_prices = apply_ter_to_prices(benchmark_prices, etf_ter)
    bank_prices = apply_ter_to_prices(benchmark_prices, bank_fund_ter)

    etf_pain = calculate_underwater_pain(etf_prices)
    bank_pain = calculate_underwater_pain(bank_prices)

    etf_rolling = calculate_all_rolling_horizons(dates, etf_prices, cpi, horizons_years)
    bank_rolling = calculate_all_rolling_horizons(dates, bank_prices, cpi, horizons_years)

    return RiskAsymmetryComparison(
        etf_name=etf_name,
        bank_fund_name=bank_fund_name,
        etf_ter=etf_ter,
        bank_fund_ter=bank_fund_ter,
        etf_underwater=etf_pain,
        bank_underwater=bank_pain,
        etf_rolling=etf_rolling,
        bank_rolling=bank_rolling,
        horizons_years=horizons_years,
    )

