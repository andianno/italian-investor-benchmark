"""Modulo di generazione grafici focalizzato sulla distribuzione statistica delle finestre mobili."""

from pathlib import Path
from typing import Dict
import matplotlib.pyplot as plt
import numpy as np

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
