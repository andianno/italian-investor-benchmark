"""Modulo di formattazione e rendering tabellare a terminale.

Genera prospetti comparativi puliti senza richiedere librerie esterne pesanti.
"""

from typing import Dict, List, Optional
from src.engine.portfolio import SimulationResult
from src.engine.statistics import BootstrapResult, RollingWindowStats


def _fmt_curr(val: Optional[float]) -> str:
    if val is None:
        return "N/D"
    return f"{val:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_pct(val: Optional[float]) -> str:
    if val is None:
        return "N/D"
    return f"{val * 100:+.2f}%".replace(".", ",")


def print_portfolio_comparison(
    results: List[SimulationResult], title: str
) -> None:
    """Stampa una tabella comparativa a colonne affiancate per le strategie simulate."""
    if not results:
        return

    col_w = 26
    lbl_w = 34

    print(f"\n{'=' * (lbl_w + col_w * len(results))}")
    print(f"  {title.upper()}")
    print(f"{'=' * (lbl_w + col_w * len(results))}")

    # Header
    header = f"{'Metrica Contabile / Finanziaria':<{lbl_w}}"
    for r in results:
        header += f"{r.benchmark_name:>{col_w}}"
    print(header)
    print(f"{'-' * (lbl_w + col_w * len(results))}")

    rows = [
        ("Orizzonte temporale (anni)", [f"{r.years:.2f}" for r in results]),
        (
            "Capitale Totale Versato",
            [_fmt_curr(r.total_invested) for r in results],
        ),
        (
            "Controvalore Nominale Lordo",
            [_fmt_curr(r.final_nominal_gross) for r in results],
        ),
        (
            "Imposta di Bollo Totale (0,20%)",
            [_fmt_curr(r.total_stamp_duty) for r in results],
        ),
        (
            "Imposta Capital Gain (26%)",
            [_fmt_curr(r.capital_gain_tax) for r in results],
        ),
        (
            "Controvalore Nominale Netto",
            [_fmt_curr(r.final_nominal_net) for r in results],
        ),
        (
            "Valore Reale Netto (Potere d'Acquisto)",
            [_fmt_curr(r.final_real_net) for r in results],
        ),
        (
            "CAGR Nominale Lordo",
            [_fmt_pct(r.cagr_nominal_gross) for r in results],
        ),
        (
            "CAGR Nominale Netto",
            [_fmt_pct(r.cagr_nominal_net) for r in results],
        ),
        ("CAGR Reale Netto", [_fmt_pct(r.cagr_real_net) for r in results]),
        (
            "XIRR (MWR) Nominale Lordo",
            [_fmt_pct(r.xirr_nominal_gross) for r in results],
        ),
        (
            "XIRR (MWR) Nominale Netto",
            [_fmt_pct(r.xirr_nominal_net) for r in results],
        ),
        ("XIRR (MWR) Reale Netto", [_fmt_pct(r.xirr_real_net) for r in results]),
        ("Max Drawdown della Quota", [_fmt_pct(r.max_drawdown) for r in results]),
        (
            "Max Underwater Quota (Asset)",
            [f"{r.max_underwater_months} mesi" for r in results],
        ),
        (
            "Max in Perdita Nominale (Conto)",
            [f"{r.max_nominal_loss_months} mesi" for r in results],
        ),
        (
            "Max in Perdita Reale (Inflazione)",
            [f"{r.max_real_loss_months} mesi" for r in results],
        ),
        (
            "Volatilità Annualizzata",
            [_fmt_pct(r.annualized_volatility) for r in results],
        ),
    ]

    for label, vals in rows:
        line = f"{label:<{lbl_w}}"
        for v in vals:
            line += f"{v:>{col_w}}"
        print(line)

    print(f"{'=' * (lbl_w + col_w * len(results))}\n")


def print_rolling_returns_table(
    benchmark_name: str, stats_dict: Dict[int, RollingWindowStats]
) -> None:
    """Stampa la distribuzione statistica dei rendimenti a finestre mobili."""
    print(f"\n>>> ANALISI FINESTRE MOBILI (ROLLING RETURNS): {benchmark_name}")
    header = (
        f"{'Orizzonte':<11} | {'Finestre':<8} | {'Min Reale':<11} | {'P05 Reale':<11} | "
        f"{'Mediana Reale':<14} | {'P95 Reale':<11} | {'Max Reale':<11} | {'P(Reale < 0)':<12}"
    )
    print("-" * len(header))
    print(header)
    print("-" * len(header))

    for h, s in sorted(stats_dict.items()):
        print(
            f"{f'{h} anni':<11} | "
            f"{s.n_windows:<8} | "
            f"{_fmt_pct(s.real_min):>11} | "
            f"{_fmt_pct(s.real_p05):>11} | "
            f"{_fmt_pct(s.real_median):>14} | "
            f"{_fmt_pct(s.real_p95):>11} | "
            f"{_fmt_pct(s.real_max):>11} | "
            f"{f'{s.negative_real_prob * 100:.1f}%':>12}"
        )
    print("-" * len(header))


def print_bootstrap_table(name: str, bs: BootstrapResult) -> None:
    """Stampa l'esito della simulazione Monte Carlo con Block Bootstrapping."""
    print(
        f"\n>>> MONTE CARLO BOOTSTRAP (12m blocks, {bs.n_simulations} sim, {bs.horizon_years}y): {name}"
    )
    print(f"  * CAGR Reale Mediano (P50):    {_fmt_pct(bs.terminal_real_cagr_p50)}")
    print(f"  * Scenario Negativo (P05):      {_fmt_pct(bs.terminal_real_cagr_p05)}")
    print(f"  * Scenario Positivo (P95):      {_fmt_pct(bs.terminal_real_cagr_p95)}")
    print(
        f"  * Probabilità di Perdita Nominale: {bs.loss_prob_nominal * 100:.2f}%"
    )
    print(
        f"  * Probabilità di Perdita Reale:    {bs.loss_prob_real * 100:.2f}%"
    )