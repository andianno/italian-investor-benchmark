"""Entry point principale dell'Italian Investor Benchmark.

Esegue la pipeline end-to-end:
1. Caricamento e caching dati storici (MSCI + FRED CPI).
2. Allineamento temporale (Inner Join).
3. Simulazione di portafoglio PIC e PAC (TER, Bollo 0.20%, Capital Gain 26%, Deflazione CPI).
4. Analisi a finestre mobili (Rolling Returns).
5. Simulazione Monte Carlo non parametrica (Block Bootstrapping).
6. Generazione prospetti comparativi a terminale ed esportazione grafici in output/.
"""

import sys
from pathlib import Path
import pandas as pd

from src.config import (
    CACHE_DATA_DIR,
    ETFConfig,
    OUTPUT_DIR,
    SimulationConfig,
    TaxConfig,
)
from src.data.fred_loader import load_italian_inflation
from src.data.msci_loader import build_benchmarks_parquet
from src.engine.portfolio import simulate_portfolio
from src.engine.statistics import (
    block_bootstrap_simulation,
    calculate_all_rolling_horizons,
)
from src.visualizer.charts import (
    plot_bootstrap_fan_chart,
    plot_equity_lines,
    plot_rolling_boxplots,
    plot_underwater,
)
from src.visualizer.tables import (
    print_bootstrap_table,
    print_portfolio_comparison,
    print_rolling_returns_table,
)


def run_pipeline() -> None:
    print("\n" + "=" * 80)
    print("       ITALIAN INVESTOR BENCHMARK: THE DEFINITIVE INDEX SIMULATOR")
    print("=" * 80)

    # 1. Ingestion Dati
    print("\n[1/5] Caricamento e normalizzazione dati storici...")
    df_benchmarks = build_benchmarks_parquet(force_reload=False)
    df_inflation = load_italian_inflation(force_download=False)

    # 2. Intersezione e allineamento temporale
    df_merged = df_benchmarks.merge(df_inflation, on="date", how="inner")
    df_merged = df_merged.sort_values("date").reset_index(drop=True)

    start_date = df_merged["date"].iloc[0].strftime("%m/%Y")
    end_date = df_merged["date"].iloc[-1].strftime("%m/%Y")
    n_months = len(df_merged)
    print(
        f"      Dataset unificato: {n_months} mesi comuni validati (dal {start_date} al {end_date})."
    )

    dates = df_merged["date"]
    cpi = df_merged["cpi_index"]

    benchmarks_to_simulate = [
        ("MSCI World (SWDA)", df_merged["msci_world"], ETFConfig.swda_ter),
        ("MSCI ACWI (VWCE)", df_merged["msci_acwi"], ETFConfig.vwce_ter),
        (
            "MSCI ACWI IMI (VALL)",
            df_merged["msci_acwi_imi"],
            ETFConfig.acwi_imi_ter,
        ),
    ]

    # 3. Simulazioni PIC
    print("\n[2/5] Esecuzione simulazioni PIC (Lump Sum 10.000 €)...")
    pic_results = []
    for name, prices, ter in benchmarks_to_simulate:
        res = simulate_portfolio(
            dates=dates,
            prices=prices,
            cpi=cpi,
            mode="PIC",
            initial_capital=SimulationConfig.pic_initial_capital,
            ter_annual=ter,
            bollo_rate=TaxConfig.bollo_annuo,
            capital_gain_rate=TaxConfig.capital_gain,
            benchmark_name=name,
        )
        pic_results.append(res)
    print_portfolio_comparison(
        pic_results, title="Simulazione PIC: 10.000 € Iniziali (2000-2026)"
    )

    # 4. Simulazioni PAC
    print("\n[3/5] Esecuzione simulazioni PAC (300 € / mese)...")
    pac_results = []
    for name, prices, ter in benchmarks_to_simulate:
        res = simulate_portfolio(
            dates=dates,
            prices=prices,
            cpi=cpi,
            mode="PAC",
            initial_capital=0.0,
            monthly_contribution=SimulationConfig.pac_monthly_contribution,
            ter_annual=ter,
            bollo_rate=TaxConfig.bollo_annuo,
            capital_gain_rate=TaxConfig.capital_gain,
            benchmark_name=name,
        )
        pac_results.append(res)
    print_portfolio_comparison(
        pac_results, title="Simulazione PAC: 300 € al mese (2000-2026)"
    )

    # 5. Analisi a Finestre Mobili (Rolling Returns)
    print("\n[4/5] Calcolo rendimenti a finestre mobili (Rolling Returns)...")
    all_rolling = {}
    for name, prices, _ in benchmarks_to_simulate:
        rolling_stats = calculate_all_rolling_horizons(
            dates=dates,
            prices=prices,
            cpi=cpi,
            horizons_years=SimulationConfig.rolling_horizons_years,
        )
        all_rolling[name] = rolling_stats
        print_rolling_returns_table(name, rolling_stats)

    # 6. Simulazione Monte Carlo Bootstrapping su MSCI World
    print(
        "\n[5/5] Esecuzione Block Bootstrapping Monte Carlo (MSCI World, 20 anni, 2.000 scenari)..."
    )
    msci_world_returns = df_merged["msci_world_return"]
    monthly_inflation = df_merged["monthly_inflation"]

    bs_world = block_bootstrap_simulation(
        returns=msci_world_returns,
        inflation=monthly_inflation,
        horizon_years=20,
        n_simulations=SimulationConfig.bootstrap_simulations,
        block_size_months=SimulationConfig.bootstrap_block_size_months,
        seed=SimulationConfig.bootstrap_seed,
    )
    print_bootstrap_table("MSCI World", bs_world)

    # 7. Esportazione Grafici
    print("\n>>> Generazione ed esportazione grafici in corso...")
    plot_equity_lines(
        pic_results, mode="PIC", output_path=OUTPUT_DIR / "equity_pic.png"
    )
    plot_equity_lines(
        pac_results, mode="PAC", output_path=OUTPUT_DIR / "equity_pac.png"
    )
    plot_underwater(pic_results, output_path=OUTPUT_DIR / "drawdowns.png")
    plot_rolling_boxplots(
        all_rolling, output_path=OUTPUT_DIR / "rolling_distributions.png"
    )
    plot_bootstrap_fan_chart(
        bs_world,
        benchmark_name="MSCI World",
        output_path=OUTPUT_DIR / "monte_carlo_world_20y.png",
    )

    print(f"\n[OK] Pipeline completata con successo!")
    print(f"     I grafici ad alta risoluzione sono disponibili in: {OUTPUT_DIR}/")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_pipeline()