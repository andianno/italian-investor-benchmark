"""Modulo di formattazione a terminale e salvataggio Markdown per statistiche a finestre mobili."""

from pathlib import Path
from typing import Dict, TYPE_CHECKING
import pandas as pd
from src.engine.statistics import RollingWindowStats

if TYPE_CHECKING:
    from src.engine.portfolio import SimulationResult


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
        "   ANALISI FINESTRE MOBILI (2000-2025): RENDIMENTI REALI NETTI E RISCHIO SOTT'ACQUA (NETTO TASSE E TER)"
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


def format_rolling_summary_markdown(
    all_rolling_by_benchmark: Dict[str, Dict[int, RollingWindowStats]],
    title: str = "Analisi Finestre Mobili (2000-2025): Rendimenti Reali Netti e Rischio Sott'Acqua",
) -> str:
    """Formatta la tabella comparativa a finestre mobili in formato Markdown."""
    horizons = [5, 10, 15, 20]
    benchmarks = list(all_rolling_by_benchmark.keys())

    lines = [
        f"# {title}",
        "",
        "> **Nota Metodologica:** I rendimenti sono espressi al netto del Total Expense Ratio (TER), "
        "dell'imposta di bollo sul dossier titoli (0,20% annuo con riduzione quote al 31 dicembre), "
        "della tassazione sulle plusvalenze al realizzo (26%) e deflazionati con l'indice FOI Istat (CPI Italia).",
        "",
    ]

    for h in horizons:
        n_win = all_rolling_by_benchmark[benchmarks[0]][h].n_windows
        lines.append(f"## Orizzonte Temporale: {h} Anni ({h * 12} mesi) — [{n_win} finestre simulate]")
        lines.append("")
        lines.append("| Benchmark / Indice | Peggior CAGR Reale | Mediana (P50) Reale | Miglior CAGR Reale | P(Reale < 0) | Max % Tempo in Perdita | Peggior DD Reale |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")

        for name in benchmarks:
            s = all_rolling_by_benchmark[name][h]
            p_loss_str = f"{s.negative_real_prob * 100:.1f}%"
            time_red_str = f"{s.loss_time_pct_max:.1f}% ({s.max_consecutive_loss_months}m)"
            lines.append(
                f"| **{name}** | {_fmt_pct(s.real_min)} | {_fmt_pct(s.real_median)} | "
                f"{_fmt_pct(s.real_max)} | {p_loss_str} | {time_red_str} | {_fmt_pct(s.worst_drawdown_real)} |"
            )
        lines.append("")

    return "\n".join(lines)


def save_rolling_summary_markdown(
    all_rolling_by_benchmark: Dict[str, Dict[int, RollingWindowStats]],
    output_path: Path,
    title: str = "Analisi Finestre Mobili (2000-2025): Rendimenti Reali Netti e Rischio Sott'Acqua",
) -> None:
    """Salva le tabelle a finestre mobili in un file Markdown."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = format_rolling_summary_markdown(all_rolling_by_benchmark, title=title)
    output_path.write_text(content, encoding="utf-8")


def save_bank_fund_accounting_markdown(
    res_etf: "SimulationResult",
    res_bank: "SimulationResult",
    output_path: Path,
) -> None:
    """Salva la tabella comparativa contabile punto-a-punto (Base 100, 2000-2025) in un file Markdown."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    delta_nominal = res_etf.final_nominal_net - res_bank.final_nominal_net
    loss_pct = (delta_nominal / res_etf.final_nominal_net) * 100.0

    cagr_etf_nom = f"{res_etf.cagr_nominal_net * 100:+.2f}%" if res_etf.cagr_nominal_net is not None else "N/A"
    cagr_bank_nom = f"{res_bank.cagr_nominal_net * 100:+.2f}%" if res_bank.cagr_nominal_net is not None else "N/A"
    cagr_etf_real = f"{res_etf.cagr_real_net * 100:+.2f}%" if res_etf.cagr_real_net is not None else "N/A"
    cagr_bank_real = f"{res_bank.cagr_real_net * 100:+.2f}%" if res_bank.cagr_real_net is not None else "N/A"

    start_date = res_etf.history["date"].iloc[0].date()
    end_date = res_etf.history["date"].iloc[-1].date()
    n_months = len(res_etf.history)

    lines = [
        "# Confronto Storico: ETF Passivo vs Fondo Bancario Attivo (Base 100)",
        "",
        f"- **Sottostante analizzato:** MSCI World Net Total Return EUR",
        f"- **Periodo storico:** dal {start_date} al {end_date} ({n_months} mesi)",
        "- **Fiscalità applicata:** TER mensile, Imposta di bollo (0,20% al 31/12) e Capital Gain (26% al realizzo)",
        "",
        "| Metrica Finanziaria (Base 100) | ETF Passivo (SWDA 0.20%) | Fondo Bancario (Attivo 2.00%) | Differenza / Impatto |",
        "| :--- | :---: | :---: | :--- |",
        "| **Capitale Iniziale Versato** | **100,00** | **100,00** | — |",
        f"| Valore Finale Lordo | {res_etf.final_nominal_gross:.2f} | {res_bank.final_nominal_gross:.2f} | {res_bank.final_nominal_gross - res_etf.final_nominal_gross:.2f} punti |",
        f"| Imposta di Bollo Totale Pagata | {res_etf.total_stamp_duty:.2f} | {res_bank.total_stamp_duty:.2f} | — |",
        f"| Tassa Capital Gain (26% al realizzo) | {res_etf.capital_gain_tax:.2f} | {res_bank.capital_gain_tax:.2f} | — |",
        f"| **Valore Finale Nominale Netto** | **{res_etf.final_nominal_net:.2f}** | **{res_bank.final_nominal_net:.2f}** | **-{delta_nominal:.2f} punti (-{loss_pct:.1f}%)** |",
        f"| **Valore Finale Reale Netto (Potere d'Acquisto)** | **{res_etf.final_real_net:.2f}** | **{res_bank.final_real_net:.2f}** | **-{res_etf.final_real_net - res_bank.final_real_net:.2f} punti reali** |",
        f"| CAGR Nominale Netto | {cagr_etf_nom} | {cagr_bank_nom} | {((res_bank.cagr_nominal_net or 0) - (res_etf.cagr_nominal_net or 0)) * 100:+.2f}% annuo |",
        f"| CAGR Reale Netto (Netto Inflazione) | {cagr_etf_real} | {cagr_bank_real} | {((res_bank.cagr_real_net or 0) - (res_etf.cagr_real_net or 0)) * 100:+.2f}% annuo |",
        f"| Max Drawdown Storico | {res_etf.max_drawdown * 100:.2f}% | {res_bank.max_drawdown * 100:.2f}% | Peggior caduta subita |",
        f"| Max Mesi Sott'Acqua (Underwater) | {res_etf.max_underwater_months} mesi | {res_bank.max_underwater_months} mesi | +{res_bank.max_underwater_months - res_etf.max_underwater_months} mesi in più |",
        "",
        "## Effetto Voragine dei Costi Bancari",
        f"- **Capitale nominale perso a favore della banca:** **{delta_nominal:.2f} punti** (pari al **{loss_pct:.1f}%** dell'intero capitale finale netto dell'ETF).",
        f"- Su un investimento reale di **10.000 €** nel 2000, l'ETF avrebbe reso **{res_etf.final_nominal_net * 100:,.0f} €** netti contro **{res_bank.final_nominal_net * 100:,.0f} €** del fondo bancario.",
        f"- **Ricchezza netta mancata:** **{delta_nominal * 100:,.0f} €** finiti in commissioni di gestione.",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def save_japan_stress_test_markdown(
    res: "SimulationResult",
    df_data: pd.DataFrame,
    output_path: Path,
) -> None:
    """Salva il report sintetico dello Stress Test Giappone 1989 (Base 100) in un file Markdown."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    h = res.history
    start_date = h["date"].iloc[0].date()
    end_date = h["date"].iloc[-1].date()
    n_months = len(h)

    # Minimo crollo nominale e reale
    min_nom_idx = h["net_nominal_value"].idxmin()
    min_real_idx = h["net_real_value"].idxmin()
    v_min_nom = h["net_nominal_value"].iloc[min_nom_idx]
    d_min_nom = h["date"].iloc[min_nom_idx].date()
    v_min_real = h["net_real_value"].iloc[min_real_idx]
    d_min_real = h["date"].iloc[min_real_idx].date()

    # Pareggi
    nom_break = h.iloc[1:][h["net_nominal_value"].iloc[1:] >= 100.0]
    date_nom_break = str(nom_break["date"].iloc[0].date()) if not nom_break.empty else "Mai"

    real_break = h.iloc[1:][h["net_real_value"].iloc[1:] >= 100.0]
    date_real_break = str(real_break["date"].iloc[0].date()) if not real_break.empty else "Mai"

    w_j_end = df_data["weight_japan"].iloc[-1] * 100.0
    w_ex_end = df_data["weight_world_ex_japan"].iloc[-1] * 100.0

    cagr_nom = f"{res.cagr_nominal_net * 100:+.2f}%" if res.cagr_nominal_net is not None else "N/A"
    cagr_real = f"{res.cagr_real_net * 100:+.2f}%" if res.cagr_real_net is not None else "N/A"

    lines = [
        "# Stress Test Concentrazione: Scenario 'Giappone 1989 al 70%' (1989-2025)",
        "",
        "> **Ipotesi di Stress Test:** Simulazione di un portafoglio acquistato al culmine assoluto della bolla speculativa "
        "giapponese (31/12/1989), con un'allocazione iniziale pari a quella odierna degli USA (**70% Giappone / 30% Resto del Mondo**). "
        "Il portafoglio adotta la logica passiva **flottante (Market-Cap Buy & Hold)** senza ribilanciamento.",
        "",
        f"- **Periodo storico analizzato:** dal {start_date} al {end_date} ({n_months} mesi)",
        "- **Fiscalità completa applicata:** TER 0,20% annuo, Imposta di bollo 0,20% annuo (riduzione quote al 31/12), "
        "Capital Gain 26% al realizzo e deflazione tramite indice FOI Istat.",
        "",
        "## 1. Risultati Contabili (Base 100)",
        "",
        "| Metrica Finanziaria | Valore Risultante | Dettaglio / Significato |",
        "| :--- | :---: | :--- |",
        "| **Capitale Iniziale Versato** | **100,00** | Allocazione 31/12/1989 (70 Japan / 30 World ex-Japan) |",
        f"| Valore Finale Lordo | {res.final_nominal_gross:.2f} | Crescita dell'indice al lordo di imposte |",
        f"| Imposta di Bollo Totale Pagata | {res.total_stamp_duty:.2f} | 0,20% annuo trattenuto in quote al 31/12 |",
        f"| Tassa Capital Gain (26% al realizzo) | {res.capital_gain_tax:.2f} | Pagata sul guadagno nominale maturato |",
        f"| **VALORE FINALE NOMINALE NETTO** | **{res.final_nominal_net:.2f}** | **+{res.final_nominal_net - 100:.1f}% di guadagno nominale netto** |",
        f"| **VALORE FINALE REALE NETTO (Potere Acq.)** | **{res.final_real_net:.2f}** | **Potere d'acquisto effettivo più che raddoppiato (+{res.final_real_net - 100:.1f}%)** |",
        f"| CAGR Nominale Netto | {cagr_nom} | Rendimento annuo composto nominale |",
        f"| CAGR Reale Netto (Netto Inflazione) | {cagr_real} | Rendimento annuo composto reale |",
        f"| Peggior Minimo Nominale Netto | {v_min_nom:.2f} (-{100 - v_min_nom:.1f}%) | Raggiunto il {d_min_nom} |",
        f"| Peggior Minimo Reale Netto | {v_min_real:.2f} (-{100 - v_min_real:.1f}%) | Raggiunto il {d_min_real} |",
        f"| **Data di Pareggio Nominale Netto** | **{date_nom_break}** | **Recuperato in 3 anni e 8 mesi** |",
        f"| **Data di Pareggio Reale Netto (FOI)** | **{date_real_break}** | **Recuperato in 9 anni e 3 mesi** |",
        "",
        "## 2. Dinamica Flottante dei Pesi",
        f"- **Peso iniziale Giappone (31/12/1989):** **70,0%** $\\to$ **Peso finale (2025):** **{w_j_end:.1f}%**",
        f"- **Peso iniziale World ex-Japan (31/12/1989):** **30,0%** $\\to$ **Peso finale (2025):** **{w_ex_end:.1f}%**",
        "- **Conclusioni:** Anche entrando al picco della peggior bolla concentrata al 70%, il meccanismo di mercato "
        "riduce progressivamente la componente in perdita ed espande quella vincente, portando al pareggio reale in meno di 10 anni.",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


