"""Modulo di visualizzazione grafica con Matplotlib.

Esporta in output/ i 4 grafici analitici del benchmark.
"""

from pathlib import Path
from typing import Dict, List
import matplotlib.pyplot as plt
import numpy as np

from src.config import OUTPUT_DIR
from src.engine.portfolio import SimulationResult
from src.engine.statistics import BootstrapResult, RollingWindowStats

# Impostazione stile scuro ed elegante per grafici finanziari
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#cccccc"
plt.rcParams["axes.linewidth"] = 0.8


def plot_equity_lines(
    results: List[SimulationResult],
    mode: str,
    output_path: Path = OUTPUT_DIR / "equity_lines.png",
) -> None:
    """Grafico 1: Traiettoria Patrimoniale Nominale vs Reale (Potere d'Acquisto)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    # Linea del capitale investito (uguale per tutti nella stessa modalità)
    first_hist = results[0].history
    ax.plot(
        first_hist["date"],
        first_hist["invested_capital"],
        label="Capitale Versato",
        color="#7f7f7f",
        linestyle="--",
        linewidth=1.5,
    )

    for r, col in zip(results, colors):
        ax.plot(
            r.history["date"],
            r.history["gross_value"],
            label=f"{r.benchmark_name} (Nominale)",
            color=col,
            linewidth=1.8,
        )
        ax.plot(
            r.history["date"],
            r.history["real_value"],
            label=f"{r.benchmark_name} (Reale Deflazionato)",
            color=col,
            linestyle=":",
            linewidth=1.2,
            alpha=0.8,
        )

    ax.set_title(
        f"Evoluzione Patrimoniale {mode} (2000-2026): Nominale vs Potere d'Acquisto Reale",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )
    ax.set_ylabel("Controvalore (€)", fontsize=11)
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, p: f"{int(x):,} €".replace(",", "."))
    )
    ax.legend(loc="upper left", frameon=True)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_underwater(
    results: List[SimulationResult],
    output_path: Path = OUTPUT_DIR / "underwater_plot.png",
) -> None:
    """Grafico 2: Underwater Plot (Discesa e recupero dai Drawdown)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 5), dpi=300)

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    for r, col in zip(results, colors):
        dd_pct = r.history["drawdown"] * 100.0
        ax.plot(
            r.history["date"],
            dd_pct,
            label=f"{r.benchmark_name} (Max: {r.max_drawdown*100:.1f}%)",
            color=col,
            linewidth=1.2,
        )
        ax.fill_between(r.history["date"], dd_pct, 0, color=col, alpha=0.1)

    ax.set_title(
        "Underwater Plot: Drawdown Storici dal Massimo Precedente (2000-2026)",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )
    ax.set_ylabel("Calo dal Massimo (%)", fontsize=11)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x)}%"))
    ax.axhline(0, color="black", linewidth=0.8)
    ax.legend(loc="lower left", frameon=True)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_rolling_boxplots(
    all_rolling: Dict[str, Dict[int, RollingWindowStats]],
    output_path: Path = OUTPUT_DIR / "rolling_returns.png",
) -> None:
    """Grafico 3: Dispersione dei CAGR Reali a 5, 10, 15 e 20 anni."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)

    horizons = [5, 10, 15, 20]
    bench_names = list(all_rolling.keys())
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    width = 0.25
    positions_base = np.arange(len(horizons))

    for idx, (name, col) in enumerate(zip(bench_names, colors)):
        pos = positions_base + (idx - 1) * width
        cagr_data = [
            all_rolling[name][h].windows_df["real_cagr"] * 100.0
            for h in horizons
            if h in all_rolling[name]
        ]
        bp = ax.boxplot(
            cagr_data,
            positions=pos[: len(cagr_data)],
            widths=width * 0.85,
            patch_artist=True,
            showmeans=True,
            meanprops={
                "marker": "o",
                "markerfacecolor": "white",
                "markeredgecolor": col,
            },
            boxprops=dict(facecolor=col, color=col, alpha=0.6),
            whiskerprops=dict(color=col),
            capprops=dict(color=col),
            medianprops=dict(color="black", linewidth=1.5),
        )

    ax.axhline(0, color="red", linestyle="--", linewidth=1.0, alpha=0.7)
    ax.set_xticks(positions_base)
    ax.set_xticklabels([f"{h} Anni" for h in horizons], fontsize=11)
    ax.set_ylabel("CAGR Reale Annuo Netto Inflazione (%)", fontsize=11)
    ax.set_title(
        "Distribuzione Storica dei Rendimenti Reali a Finestre Mobili (Rolling CAGR)",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )
    # Dummy legend
    handles = [
        plt.Line2D([0], [0], color=c, lw=4, label=name)
        for c, name in zip(colors, bench_names)
    ]
    ax.legend(handles=handles, loc="upper right", frameon=True)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_bootstrap_fan_chart(
    bs: BootstrapResult,
    benchmark_name: str,
    output_path: Path = OUTPUT_DIR / "bootstrap_fan_chart.png",
) -> None:
    """Grafico 4: Fan Chart Monte Carlo con intervalli percentilari."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)

    months = np.arange(bs.horizon_years * 12 + 1)
    years_axis = months / 12.0

    p = bs.real_percentile_paths

    ax.fill_between(
        years_axis,
        p[5],
        p[95],
        color="#1f77b4",
        alpha=0.15,
        label="Intervallo 5° - 95° percentile",
    )
    ax.fill_between(
        years_axis,
        p[25],
        p[75],
        color="#1f77b4",
        alpha=0.30,
        label="Intervallo Interquartile (25° - 75°)",
    )
    ax.plot(
        years_axis,
        p[50],
        color="#0b4070",
        linewidth=2.2,
        label=f"Traiettoria Mediana (CAGR Reale: {bs.terminal_real_cagr_p50*100:+.2f}%)",
    )

    ax.axhline(
        1.0,
        color="red",
        linestyle="--",
        linewidth=1.2,
        label=f"Capitale Reale Invariato (Loss prob: {bs.loss_prob_real*100:.1f}%)",
    )

    ax.set_title(
        f"Simulazione Monte Carlo Block Bootstrap ({bs.horizon_years} Anni) - {benchmark_name}\n"
        f"Moltiplicatore del Potere d'Acquisto Reale ({bs.n_simulations} scenari a blocchi di 12m)",
        fontsize=12,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("Anni di Investimento", fontsize=11)
    ax.set_ylabel("Moltiplicatore del Capitale Reale (Base = 1.0)", fontsize=11)
    ax.legend(loc="upper left", frameon=True)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)