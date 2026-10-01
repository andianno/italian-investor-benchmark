"""Modulo di formattazione a terminale per statistiche a finestre mobili."""

from typing import Dict
from src.engine.statistics import RollingWindowStats


def _fmt_pct(val: float) -> str:
    return f"{val * 100:+.2f}%".replace(".", ",")


def print_rolling_comprehensive_summary(
    all_rolling_by_benchmark: Dict[str, Dict[int, RollingWindowStats]],
) -> None:
    """Stampa la tabella comparativa definitiva su rendimenti e permanenza in perdita reale."""
    horizons = [5, 10, 15, 20]
    benchmarks = list(all_rolling_by_benchmark.keys())

    print("\n" + "=" * 115)
    print(
        "         ANALISI FINESTRE MOBILI (2000-2025): RENDIMENTI REALI E RISCHIO SOTT'ACQUA"
    )
    print("=" * 115)

    for h in horizons:
        n_win = all_rolling_by_benchmark[benchmarks[0]][h].n_windows
        print(
            f"\n>>> ORIZZONTE TEMPORALE: {h} ANNI ({h * 12} mesi) [Finestre simulate: {n_win}]"
        )

        col_names = [
            f"{'Benchmark / Indice':<24}",
            f"{'Peggior CAGR':<13}",
            f"{'Mediana (P50)':<13}",
            f"{'Miglior CAGR':<13}",
            f"{'P(Reale < 0)':<12}",
            f"{'Max % Tempo Rosso':<17}",
            f"{'Peggior DD Reale':<14}",
        ]
        header = " | ".join(col_names)
        divider = "-" * len(header)

        print(divider)
        print(header)
        print(divider)

        for name in benchmarks:
            s = all_rolling_by_benchmark[name][h]
            p_loss_str = f"{s.negative_real_prob * 100:.1f}%"
            time_red_str = (
                f"{s.loss_time_pct_max:.1f}% ({s.max_consecutive_loss_months}m)"
            )
            row = [
                f"{name:<24}",
                f"{_fmt_pct(s.real_min):>13}",
                f"{_fmt_pct(s.real_median):>13}",
                f"{_fmt_pct(s.real_max):>13}",
                f"{p_loss_str:>12}",
                f"{time_red_str:>17}",
                f"{_fmt_pct(s.worst_drawdown_real):>14}",
            ]
            print(" | ".join(row))
        print(divider)
    print("=" * 115 + "\n")
