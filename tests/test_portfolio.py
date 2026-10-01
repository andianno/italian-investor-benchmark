import numpy as np
import pandas as pd
import pytest

from src.engine.portfolio import simulate_portfolio


def test_pic_flat_market_only_costs():
    """Su un mercato piatto (rendimento indice 0%):

    non ci devono essere plusvalenze (tax = 0), ma il portafoglio deve subire
    solo l'attrito del TER e del bollo titoli al 31 dicembre.
    """
    # 13 mesi: da fine Dicembre 2021 a fine Gennaio 2023 (un passaggio al 31 Dicembre 2022)
    dates = pd.date_range("2021-12-31", "2023-01-31", freq="ME")
    prices = pd.Series(100.0, index=np.arange(len(dates)))
    cpi = pd.Series(100.0, index=np.arange(len(dates)))

    res = simulate_portfolio(
        dates=dates,
        prices=prices,
        cpi=cpi,
        mode="PIC",
        initial_capital=10_000.0,
        ter_annual=0.0020,  # 0.20%
        bollo_rate=0.0020,  # 0.20%
        capital_gain_rate=0.26,
    )

    # 1. Nessun guadagno, quindi zero capital gain
    assert res.capital_gain_tax == 0.0
    assert res.final_nominal_net == res.final_nominal_gross

    # 2. Il bollo pagato al 31/12/2022 deve essere circa 20€ (0.20% di ~10.000€)
    assert pytest.approx(res.total_stamp_duty, rel=1e-2) == 20.0

    # 3. Capitale finale leggermente inferiore a 10.000€ a causa di TER e bollo
    assert res.final_nominal_gross < 10_000.0
    assert res.final_nominal_gross > 9_900.0


def test_pic_capital_gain_tax_exactness():
    """Verifica che la tassazione sulle plusvalenze venga applicata solo al termine

    ed esattamente al 26% del guadagno nominale maturato.
    """
    dates = pd.Series(
        [
            pd.Timestamp("2021-01-31"),
            pd.Timestamp("2021-06-30"),  # Nessun dicembre attraversato
        ]
    )
    # Prezzo raddoppia: da 100 a 200
    prices = pd.Series([100.0, 200.0])
    cpi = pd.Series([100.0, 100.0])

    res = simulate_portfolio(
        dates=dates,
        prices=prices,
        cpi=cpi,
        mode="PIC",
        initial_capital=10_000.0,
        ter_annual=0.0,  # Zero TER per isolare la tassa
        bollo_rate=0.0,  # Zero bollo
        capital_gain_rate=0.26,
    )

    # Raddoppio: 10.000 -> 20.000 lordi. Plusvalenza = 10.000.
    # Tassa 26% = 2.600€. Netto = 17.400€.
    assert pytest.approx(res.final_nominal_gross) == 20_000.0
    assert pytest.approx(res.capital_gain_tax) == 2_600.0
    assert pytest.approx(res.final_nominal_net) == 17_400.0


def test_pac_share_accumulation():
    """Verifica che il PAC accumuli correttamente quote e capitale investito."""
    dates = pd.date_range("2021-01-31", periods=12, freq="ME")
    # Prezzi costanti a 100€
    prices = pd.Series(100.0, index=np.arange(len(dates)))
    cpi = pd.Series(100.0, index=np.arange(len(dates)))

    res = simulate_portfolio(
        dates=dates,
        prices=prices,
        cpi=cpi,
        mode="PAC",
        initial_capital=0.0,
        monthly_contribution=300.0,
        ter_annual=0.0,
        bollo_rate=0.0,
    )

    # 12 versamenti da 300€ = 3.600€ investiti
    assert res.total_invested == 3_600.0
    assert pytest.approx(res.final_nominal_gross) == 3_600.0
    assert res.cagr_nominal_gross is None  # CAGR non applicabile a PAC
    assert pytest.approx(res.xirr_nominal_gross, abs=1e-3) == 0.0


def test_invalid_parameters():
    """Verifica che input non validi sollevino eccezioni appropriate."""
    dates = pd.date_range("2021-01-31", periods=5, freq="ME")
    prices = pd.Series([100.0] * 5)
    cpi = pd.Series([100.0] * 5)

    with pytest.raises(ValueError):
        simulate_portfolio(dates, prices, cpi, mode="INVALID_MODE")

    with pytest.raises(ValueError):
        # Meno di 2 mesi
        simulate_portfolio(dates[:1], prices[:1], cpi[:1])
