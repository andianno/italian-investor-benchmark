"""Engine di simulazione di portafoglio per investimenti passivi (PIC e PAC).

Modella l'evoluzione patrimoniale mensile incorporando il Total Expense Ratio (TER),
l'imposta di bollo italiana sul dossier titoli (0,20% annuo al 31 dicembre),
la tassazione sul capital gain (26% al realizzo) e la deflazione per il potere
d'acquisto reale tramite serie CPI.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
import numpy as np
import pandas as pd

from src.config import TaxConfig
from src.engine.metrics import (
    calculate_annualized_volatility,
    calculate_cagr,
    calculate_drawdown_series,
    calculate_xirr,
)


@dataclass(frozen=True)
class SimulationResult:
    """Contenitore immutabile dei risultati di una simulazione temporale."""

    benchmark_name: str
    mode: str
    years: float
    total_invested: float
    final_nominal_gross: float
    final_nominal_net: float
    capital_gain_tax: float
    total_stamp_duty: float
    final_real_gross: float
    final_real_net: float
    cagr_nominal_gross: Optional[float]
    cagr_nominal_net: Optional[float]
    cagr_real_net: Optional[float]
    xirr_nominal_gross: float
    xirr_nominal_net: float
    xirr_real_net: float
    max_drawdown: float
    max_underwater_months: int
    max_nominal_loss_months: int  # <-- Perdita sul capitale nominale versato
    max_real_loss_months: int  # <-- Perdita sul potere d'acquisto reale versato
    annualized_volatility: float
    history: pd.DataFrame

    def to_dict(self) -> Dict[str, Any]:
        """Restituisce un dizionario serializzabile con tutti i KPI di sintesi."""
        return {
            "benchmark_name": self.benchmark_name,
            "mode": self.mode,
            "years": self.years,
            "total_invested": self.total_invested,
            "final_nominal_gross": self.final_nominal_gross,
            "final_nominal_net": self.final_nominal_net,
            "capital_gain_tax": self.capital_gain_tax,
            "total_stamp_duty": self.total_stamp_duty,
            "final_real_gross": self.final_real_gross,
            "final_real_net": self.final_real_net,
            "cagr_nominal_gross": self.cagr_nominal_gross,
            "cagr_nominal_net": self.cagr_nominal_net,
            "cagr_real_net": self.cagr_real_net,
            "xirr_nominal_gross": self.xirr_nominal_gross,
            "xirr_nominal_net": self.xirr_nominal_net,
            "xirr_real_net": self.xirr_real_net,
            "max_drawdown": self.max_drawdown,
            "max_underwater_months": self.max_underwater_months,
            "max_nominal_loss_months": self.max_nominal_loss_months,
            "max_real_loss_months": self.max_real_loss_months,
            "annualized_volatility": self.annualized_volatility,
        }


def _calculate_underwater_duration(drawdown_series: pd.Series) -> int:
    """Calcola la massima durata (in mesi consecutivi) trascorsa dal portafoglio sotto il picco precedente."""
    max_duration = 0
    current_duration = 0
    for dd in drawdown_series:
        if dd < 0:
            current_duration += 1
            if current_duration > max_duration:
                max_duration = current_duration
        else:
            current_duration = 0
    return max_duration


def _calculate_loss_duration(values: np.ndarray, thresholds: np.ndarray) -> int:
    """Calcola la massima sequenza di mesi consecutivi in cui il portafoglio

    è rimasto al di sotto del capitale totale versato fino a quel mese.
    """
    max_duration = 0
    current_duration = 0

    for val, thresh in zip(values, thresholds):
        # Condizione di perdita sul capitale versato
        if val < thresh:
            current_duration += 1
            if current_duration > max_duration:
                max_duration = current_duration
        else:
            current_duration = 0

    return max_duration


def simulate_portfolio(
    dates: pd.Series,
    prices: pd.Series,
    cpi: pd.Series,
    mode: str = "PIC",
    initial_capital: float = 10_000.0,
    monthly_contribution: float = 300.0,
    indexed_to_inflation: bool = False,
    ter_annual: float = 0.0020,
    bollo_rate: float = TaxConfig.bollo_annuo,
    capital_gain_rate: float = TaxConfig.capital_gain,
    benchmark_name: str = "Benchmark",
) -> SimulationResult:
    """Esegue la simulazione contabile dell'investimento passivo mese per mese.

    Parameters
    ----------
    dates : pd.Series
        Serie delle date mensili (normalizzate a fine mese).
    prices : pd.Series
        Serie storica delle quotazioni Net Total Return dell'indice.
    cpi : pd.Series
        Indice dei prezzi al consumo (es. CPI Italia da FRED) allineato alle date.
    mode : str
        Modalità di investimento: 'PIC' (Lump Sum) o 'PAC' (DCA).
    initial_capital : float
        Capitale investito al tempo t=0.
    monthly_contribution : float
        Quota fissa versata ogni fine mese (per modalità PAC).
    indexed_to_inflation : bool
        Se True, adegua la rata mensile del PAC all'inflazione cumulata (CPI_t / CPI_0).
    ter_annual : float
        Total Expense Ratio annuo dello strumento (es. 0.0020 per lo 0.20%).
    bollo_rate : float
        Aliquota annuale dell'imposta di bollo (default 0.0020).
    capital_gain_rate : float
        Aliquota di tassazione sulle plusvalenze (default 0.26).
    benchmark_name : str
        Nome identificativo della strategia/indice simulato.

    Returns
    -------
    SimulationResult
        Oggetto contenente serie temporale dettagliata e metriche finanziarie riassuntive.
    """
    mode_clean = mode.strip().upper()
    if mode_clean not in ("PIC", "PAC"):
        raise ValueError(f"Modalità '{mode}' non valida. Selezionare 'PIC' o 'PAC'.")

    dates_clean = pd.Series(pd.to_datetime(dates)).reset_index(drop=True)
    prices_clean = pd.Series(prices, dtype=float).reset_index(drop=True)
    cpi_clean = pd.Series(cpi, dtype=float).reset_index(drop=True)

    n_months = len(dates_clean)
    if n_months < 2:
        raise ValueError("La serie temporale deve contenere almeno 2 mesi.")

    # 1. Modello del TER: decurtazione geometrica mensile sul valore quota
    # drag_mensile = (1 + TER)^(1/12) - 1
    monthly_ter_drag = (1.0 + ter_annual) ** (1.0 / 12.0) - 1.0
    nav_per_share = prices_clean * ((1.0 - monthly_ter_drag) ** np.arange(n_months))

    # 2. Strutture dati contabili
    shares = np.zeros(n_months, dtype=float)
    contributions = np.zeros(n_months, dtype=float)
    cumulative_invested = np.zeros(n_months, dtype=float)
    gross_values = np.zeros(n_months, dtype=float)
    real_values = np.zeros(n_months, dtype=float)
    stamp_duty_paid = np.zeros(n_months, dtype=float)

    cpi_0 = cpi_clean.iloc[0]
    current_shares = 0.0
    current_invested = 0.0

    # 3. Ciclo contabile mensile
    for t in range(n_months):
        d = dates_clean.iloc[t]
        p_t = nav_per_share.iloc[t]
        cpi_t = cpi_clean.iloc[t]

        # Iniezione di liquidità
        c_t = 0.0
        if t == 0:
            if mode_clean == "PIC":
                c_t = initial_capital
            else:
                c_t = (
                    initial_capital + monthly_contribution
                    if initial_capital > 0
                    else monthly_contribution
                )
        else:
            if mode_clean == "PAC":
                if indexed_to_inflation:
                    c_t = monthly_contribution * (cpi_t / cpi_0)
                else:
                    c_t = monthly_contribution

        # Acquisto di quote frazionarie
        if c_t > 0:
            current_invested += c_t
            contributions[t] = c_t
            current_shares += c_t / p_t

        # Controvalore lordo corrente
        val = current_shares * p_t

        # 4. Imposta di bollo (31 dicembre, applicata per gli anni maturati t > 0)
        # La trattenuta avviene riducendo le quote in portafoglio (vendita per assolvimento imposta)
        bollo = 0.0
        if t > 0 and d.month == 12:
            bollo = val * bollo_rate
            current_shares *= 1.0 - bollo_rate
            val = current_shares * p_t
            stamp_duty_paid[t] = bollo

        shares[t] = current_shares
        cumulative_invested[t] = current_invested
        gross_values[t] = val
        real_values[t] = val * (cpi_0 / cpi_t)

    # 5. Metriche di rischio e drawdown sulla quota della strategia
    dd_series = calculate_drawdown_series(nav_per_share)
    max_dd = float(dd_series.min())
    max_underwater = _calculate_underwater_duration(dd_series)

    # 5.1 Durata in perdita nominale (V_t < Somma contanti versati)
    max_nom_loss = _calculate_loss_duration(gross_values, cumulative_invested)

    # 5.2 Durata in perdita reale (V_reale_t < Somma potere d'acquisto versato in base t0)
    real_contributions = contributions * (cpi_0 / cpi_clean.values)
    cumulative_real_invested = np.cumsum(real_contributions)
    max_real_loss = _calculate_loss_duration(real_values, cumulative_real_invested)

    # Volatilità annualizzata della strategia al netto del TER
    nav_returns = nav_per_share.pct_change()
    ann_vol = calculate_annualized_volatility(nav_returns)

    # 6. Liquidazione finale e tassazione plusvalenze (capital gain al realizzo)
    final_gross = gross_values[-1]
    final_real_gross = real_values[-1]
    total_invested = current_invested

    profit = max(0.0, final_gross - total_invested)
    tax = profit * capital_gain_rate
    final_net = final_gross - tax
    final_real_net = final_net * (cpi_0 / cpi_clean.iloc[-1])

    years = (dates_clean.iloc[-1] - dates_clean.iloc[0]).days / 365.25

    # CAGR (calcolato per il PIC sul capitale unico investito)
    cagr_gross = None
    cagr_net = None
    cagr_real_net = None
    if mode_clean == "PIC" and total_invested > 0:
        cagr_gross = calculate_cagr(total_invested, final_gross, years)
        cagr_net = calculate_cagr(total_invested, final_net, years)
        cagr_real_net = calculate_cagr(total_invested, final_real_net, years)

    # 7. Money-Weighted Return (XIRR)
    # Contributi: flussi in uscita (segno negativo)
    # Liquidazione finale: flusso in entrata (segno positivo)
    cf_gross = -contributions.copy()
    cf_gross[-1] += final_gross

    cf_net = -contributions.copy()
    cf_net[-1] += final_net

    # Flussi reali deflazionati rispetto a t0
    cpi_deflators = cpi_0 / cpi_clean.values
    cf_real = (-contributions * cpi_deflators).copy()
    cf_real[-1] += final_real_net

    active_mask = contributions > 0
    active_mask[-1] = True  # Include sempre la data di chiusura

    xirr_gross = calculate_xirr(cf_gross[active_mask], dates_clean[active_mask])
    xirr_net = calculate_xirr(cf_net[active_mask], dates_clean[active_mask])
    xirr_real = calculate_xirr(cf_real[active_mask], dates_clean[active_mask])

    # Valore netto di realizzo mensile comprensivo di eventuale capital gain maturato
    profits_series = np.maximum(0.0, gross_values - cumulative_invested)
    taxes_series = profits_series * capital_gain_rate
    net_values = gross_values - taxes_series
    net_real_values = net_values * (cpi_0 / cpi_clean.values)

    history_df = pd.DataFrame(
        {
            "date": dates_clean,
            "contribution": contributions,
            "invested_capital": cumulative_invested,
            "shares": shares,
            "nav_per_share": nav_per_share,
            "gross_value": gross_values,
            "real_value": real_values,
            "net_nominal_value": net_values,
            "net_real_value": net_real_values,
            "stamp_duty_paid": stamp_duty_paid,
            "drawdown": dd_series.values,
        }
    )

    return SimulationResult(
        benchmark_name=benchmark_name,
        mode=mode_clean,
        years=round(years, 2),
        total_invested=round(total_invested, 2),
        final_nominal_gross=round(final_gross, 2),
        final_nominal_net=round(final_net, 2),
        capital_gain_tax=round(tax, 2),
        total_stamp_duty=round(float(stamp_duty_paid.sum()), 2),
        final_real_gross=round(final_real_gross, 2),
        final_real_net=round(final_real_net, 2),
        cagr_nominal_gross=(round(cagr_gross, 4) if cagr_gross is not None else None),
        cagr_nominal_net=(round(cagr_net, 4) if cagr_net is not None else None),
        cagr_real_net=(round(cagr_real_net, 4) if cagr_real_net is not None else None),
        xirr_nominal_gross=round(xirr_gross, 4),
        xirr_nominal_net=round(xirr_net, 4),
        xirr_real_net=round(xirr_real, 4),
        max_drawdown=round(max_dd, 4),
        max_underwater_months=max_underwater,
        max_nominal_loss_months=max_nom_loss,
        max_real_loss_months=max_real_loss,
        annualized_volatility=round(ann_vol, 4),
        history=history_df,
    )
