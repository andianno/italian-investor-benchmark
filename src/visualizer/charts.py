"""Modulo di generazione grafici focalizzato sulla distribuzione statistica delle finestre mobili."""

from pathlib import Path
from typing import Dict
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import OUTPUT_DIR
from src.engine.statistics import RollingWindowStats

plt.style.use(
    "seaborn-v0_8-whitegrid"
    if "seaborn-v0_8-whitegrid" in plt.style.available
    else "default"
)
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#cccccc"
plt.rcParams["axes.linewidth"] = 0.8


def plot_rolling_cagr_distributions(
    all_rolling: Dict[str, Dict[int, RollingWindowStats]],
    output_path: Path = OUTPUT_DIR / "rolling_cagr_distribution.png",
) -> None:
    """Grafico 1: Distribuzione del CAGR Reale (Min, Mediana, Max, Quartili) per orizzonte."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)

    horizons = [5, 10, 15, 20]
    benchmarks = list(all_rolling.keys())
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    width = 0.25
    x_base = np.arange(len(horizons))

    for idx, (name, col) in enumerate(zip(benchmarks, colors)):
        pos = x_base + (idx - 1) * width
        data = [all_rolling[name][h].windows_df["real_cagr"] * 100.0 for h in horizons]

        ax.boxplot(
            data,
            positions=pos,
            widths=width * 0.85,
            patch_artist=True,
            showmeans=True,
            meanprops={
                "marker": "o",
                "markerfacecolor": "white",
                "markeredgecolor": col,
            },
            boxprops=dict(facecolor=col, color=col, alpha=0.5),
            whiskerprops=dict(color=col, linewidth=1.2),
            capprops=dict(color=col, linewidth=1.2),
            medianprops=dict(color="black", linewidth=1.5),
        )

    ax.axhline(0, color="red", linestyle="--", linewidth=1.0, alpha=0.8)
    ax.set_xticks(x_base)
    ax.set_xticklabels([f"{h} Anni" for h in horizons], fontsize=11)
    ax.set_ylabel("CAGR Reale Netto Inflazione (%)", fontsize=11)
    ax.set_title(
        "Distribuzione del CAGR Reale per Orizzonte Temporale (SWDA vs VWCE vs VALL)",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )

    handles = [
        plt.Line2D([0], [0], color=c, lw=4, label=name)
        for c, name in zip(colors, benchmarks)
    ]
    ax.legend(handles=handles, loc="upper right", frameon=True)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_rolling_loss_time(
    all_rolling: Dict[str, Dict[int, RollingWindowStats]],
    output_path: Path = OUTPUT_DIR / "rolling_real_loss_time.png",
) -> None:
    """Grafico 2: Percentuale di tempo trascorsa in perdita reale (Caso Peggiore e Mediano)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    horizons = [5, 10, 15, 20]
    benchmarks = list(all_rolling.keys())
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    x = np.arange(len(horizons))
    width = 0.25

    # Subplot 1: CASO PEGGIORE (% di tempo in perdita reale)
    for idx, (name, col) in enumerate(zip(benchmarks, colors)):
        worst_times = [all_rolling[name][h].loss_time_pct_max for h in horizons]
        ax1.bar(
            x + (idx - 1) * width,
            worst_times,
            width=width * 0.85,
            label=name,
            color=col,
            alpha=0.85,
        )

    ax1.set_title(
        "Scenario Peggiore: % Tempo Sott'Acqua rispetto all'Inflazione",
        fontweight="bold",
        fontsize=11,
    )
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"{h} Anni" for h in horizons])
    ax1.set_ylabel("% Mesi della Finestra con Potere d'Acquisto < Versato")
    ax1.set_ylim(0, 105)
    ax1.legend(loc="upper right")

    # Subplot 2: CASO MEDIANO (% di tempo in perdita reale)
    for idx, (name, col) in enumerate(zip(benchmarks, colors)):
        median_times = [all_rolling[name][h].loss_time_pct_median for h in horizons]
        ax2.bar(
            x + (idx - 1) * width,
            median_times,
            width=width * 0.85,
            label=name,
            color=col,
            alpha=0.85,
        )

    ax2.set_title(
        "Scenario Tipico (Mediana): % Tempo Sott'Acqua rispetto all'Inflazione",
        fontweight="bold",
        fontsize=11,
    )
    ax2.set_xticks(x)
    ax2.set_xticklabels([f"{h} Anni" for h in horizons])
    ax2.set_ylim(0, 105)
    ax2.legend(loc="upper right")

    fig.suptitle(
        "Permanenza in Perdita Reale per Orizzonte Temporale (Netto Inflazione"
        " Italiana)",
        fontsize=13,
        fontweight="bold",
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_etf_vs_bank_fund_growth(
    df_etf: "pd.DataFrame",
    df_bank: "pd.DataFrame",
    output_path: Path = OUTPUT_DIR / "etf_vs_bank_fund_growth.png",
    etf_label: str = "ETF Passivo (TER 0.20%)",
    bank_label: str = "Fondo Bancario Attivo (TER 2.00%)",
) -> None:
    """Grafico comparativo della crescita patrimoniale (Base 100) dal 2000 ad oggi.

    Mostra l'evoluzione temporale su scala lineare al netto di TER, imposta di bollo
    annuale (0,20% al 31/12) e tassazione capital gain (26% al realizzo):
    - ETF Nominale Netto (linea continua)
    - ETF Reale Netto (linea tratteggiata)
    - Fondo Bancario Nominale Netto (linea continua)
    - Fondo Bancario Reale Netto (linea tratteggiata)
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(13, 7), dpi=300)

    dates = pd.to_datetime(df_etf["date"])

    # Curve ETF
    etf_nom = df_etf["net_nominal_value"]
    etf_real = df_etf["net_real_value"]

    # Curve Fondo Bancario
    bank_nom = df_bank["net_nominal_value"]
    bank_real = df_bank["net_real_value"]

    # Valori finali per legenda
    etf_nom_end = etf_nom.iloc[-1]
    etf_real_end = etf_real.iloc[-1]
    bank_nom_end = bank_nom.iloc[-1]
    bank_real_end = bank_real.iloc[-1]

    # Tracciamento curve
    color_etf = "#1f77b4"  # Blu
    color_bank = "#d62728"  # Rosso

    ax.plot(
        dates,
        etf_nom,
        color=color_etf,
        linewidth=2.4,
        label=f"{etf_label} - Nominale (Fine: {etf_nom_end:.1f})",
    )
    ax.plot(
        dates,
        etf_real,
        color=color_etf,
        linewidth=2.0,
        linestyle="--",
        label=f"{etf_label} - Reale Netto Inflazione (Fine: {etf_real_end:.1f})",
    )
    ax.plot(
        dates,
        bank_nom,
        color=color_bank,
        linewidth=2.4,
        label=f"{bank_label} - Nominale (Fine: {bank_nom_end:.1f})",
    )
    ax.plot(
        dates,
        bank_real,
        color=color_bank,
        linewidth=2.0,
        linestyle="--",
        label=f"{bank_label} - Reale Netto Inflazione (Fine: {bank_real_end:.1f})",
    )

    # Linea orizzontale di pareggio (Capitale iniziale = 100)
    ax.axhline(
        100,
        color="#7f7f7f",
        linestyle=":",
        linewidth=1.2,
        alpha=0.8,
        label="Pareggio Capitale Iniziale (100)",
    )

    # Area di valore perso tra nominale ETF e nominale Fondo
    ax.fill_between(
        dates,
        bank_nom,
        etf_nom,
        color="#ff7f0e",
        alpha=0.12,
        label="Costi cumulati erosi dalla gestione attiva",
    )

    ax.set_title(
        "Confronto Performance Storica (2000-2025): ETF Passivo vs Fondo Bancario Attivo\n"
        "MSCI World Net Total Return | Base 100 | Netto TER, Bollo Dossier Titoli (0.20%/anno) e Capital Gain (26%)",
        fontsize=12,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("Anno", fontsize=11)
    ax.set_ylabel("Valore Netto di Realizzo (Base 100)", fontsize=11)
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper left", frameon=True, framealpha=0.9, fontsize=9.5)

    # Box statistico riassuntivo in basso a destra
    lost_nominal_pct = ((etf_nom_end - bank_nom_end) / etf_nom_end) * 100.0
    stats_text = (
        f"Impatto dei Costi Bancari:\n"
        f"• Capitale finale ETF Nominale: {etf_nom_end:.1f}\n"
        f"• Capitale finale Fondo Nominale: {bank_nom_end:.1f}\n"
        f"• Capitale eroso dal TER: -{lost_nominal_pct:.1f}%\n"
        f"• Potere d'acquisto reale Fondo: {bank_real_end:.1f} (vs {etf_real_end:.1f} ETF)"
    )
    ax.text(
        0.98,
        0.05,
        stats_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="bottom",
        horizontalalignment="right",
        bbox=dict(boxstyle="round,pad=0.6", facecolor="white", edgecolor="#cccccc", alpha=0.9),
    )

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_etf_vs_bank_rolling_cagr(
    all_rolling: Dict[str, Dict[int, RollingWindowStats]],
    output_path: Path = OUTPUT_DIR / "etf_vs_bank_fund_rolling_cagr.png",
) -> None:
    """Grafico Boxplot: Confronto distribuzione CAGR Reale Netto tra ETF Passivo e Fondo Bancario."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)

    horizons = [5, 10, 15, 20]
    benchmarks = list(all_rolling.keys())
    colors = ["#1f77b4", "#d62728"]  # Blu ETF, Rosso Fondo

    width = 0.32
    x_base = np.arange(len(horizons))

    for idx, (name, col) in enumerate(zip(benchmarks, colors)):
        pos = x_base + (idx - 0.5) * width
        data = [all_rolling[name][h].windows_df["real_cagr"] * 100.0 for h in horizons]

        ax.boxplot(
            data,
            positions=pos,
            widths=width * 0.85,
            patch_artist=True,
            showmeans=True,
            meanprops={
                "marker": "o",
                "markerfacecolor": "white",
                "markeredgecolor": col,
                "markersize": 6,
            },
            boxprops=dict(facecolor=col, color=col, alpha=0.45),
            whiskerprops=dict(color=col, linewidth=1.3),
            capprops=dict(color=col, linewidth=1.3),
            medianprops=dict(color="black", linewidth=1.6),
        )

    ax.axhline(0, color="red", linestyle="--", linewidth=1.0, alpha=0.7)
    ax.set_xticks(x_base)
    ax.set_xticklabels([f"{h} Anni" for h in horizons], fontsize=11)
    ax.set_ylabel("CAGR Reale Netto Tasse & TER (%)", fontsize=11)
    ax.set_title(
        "Distribuzione del CAGR Reale Netto per Orizzonte: ETF Passivo vs Fondo Bancario Attivo\n"
        "MSCI World (2000-2025) | Netto TER (0.20% vs 2.00%), Bollo (0,20%/anno) e Capital Gain (26%)",
        fontsize=12,
        fontweight="bold",
        pad=15,
    )

    handles = [
        plt.Line2D([0], [0], color=c, lw=4, label=name)
        for c, name in zip(colors, benchmarks)
    ]
    ax.legend(handles=handles, loc="upper right", frameon=True, fontsize=10)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_etf_vs_bank_rolling_loss_time(
    all_rolling: Dict[str, Dict[int, RollingWindowStats]],
    output_path: Path = OUTPUT_DIR / "etf_vs_bank_fund_rolling_loss_time.png",
) -> None:
    """Grafico a barre: Confronto % di tempo in perdita reale (Caso Peggiore e Mediano) ETF vs Banca."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), dpi=300)

    horizons = [5, 10, 15, 20]
    benchmarks = list(all_rolling.keys())
    colors = ["#1f77b4", "#d62728"]
    x = np.arange(len(horizons))
    width = 0.32

    # Subplot 1: CASO PEGGIORE
    for idx, (name, col) in enumerate(zip(benchmarks, colors)):
        worst_times = [all_rolling[name][h].loss_time_pct_max for h in horizons]
        ax1.bar(
            x + (idx - 0.5) * width,
            worst_times,
            width=width * 0.85,
            label=name,
            color=col,
            alpha=0.85,
        )

    ax1.set_title(
        "Scenario Peggiore: % Tempo Sott'Acqua rispetto all'Inflazione",
        fontweight="bold",
        fontsize=11,
    )
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"{h} Anni" for h in horizons])
    ax1.set_ylabel("% Mesi della Finestra con Potere d'Acquisto < Versato")
    ax1.set_ylim(0, 105)
    ax1.legend(loc="upper right", fontsize=9.5)

    # Subplot 2: CASO MEDIANO
    for idx, (name, col) in enumerate(zip(benchmarks, colors)):
        median_times = [all_rolling[name][h].loss_time_pct_median for h in horizons]
        ax2.bar(
            x + (idx - 0.5) * width,
            median_times,
            width=width * 0.85,
            label=name,
            color=col,
            alpha=0.85,
        )

    ax2.set_title(
        "Scenario Tipico (Mediana): % Tempo Sott'Acqua rispetto all'Inflazione",
        fontweight="bold",
        fontsize=11,
    )
    ax2.set_xticks(x)
    ax2.set_xticklabels([f"{h} Anni" for h in horizons])
    ax2.set_ylim(0, 105)
    ax2.legend(loc="upper right", fontsize=9.5)

    fig.suptitle(
        "Permanenza in Perdita Reale per Orizzonte Temporale: ETF vs Fondo Bancario\n"
        "(Netto Inflazione Italiana FOI, Bollo Dossier Titoli e Capital Gain)",
        fontsize=12,
        fontweight="bold",
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


