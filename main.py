"""Entry point principale: Analisi Statistica Comparativa a Finestre Mobili."""

from src.config import ETFConfig, OUTPUT_DIR, SimulationConfig, TaxConfig
from src.data.fred_loader import load_italian_inflation
from src.data.msci_loader import build_benchmarks_parquet
from src.engine.statistics import calculate_all_rolling_horizons
from src.visualizer.charts import (
    plot_rolling_cagr_distributions,
    plot_rolling_loss_time,
)
from src.visualizer.tables import (
    print_rolling_comprehensive_summary,
    save_rolling_summary_markdown,
)


def run_benchmark():
    print("\n" + "=" * 80)
    print("     ITALIAN INVESTOR BENCHMARK: ROLLING RISK & RETURN ENGINE (2000-2025)")
    print("        (Netto TER ETF, Imposta di Bollo 0.20% e Capital Gain 26%)")
    print("=" * 80)

    print("\n[1/3] Caricamento dati storici e allineamento all'inflazione FOI...")
    df_bench = build_benchmarks_parquet()
    df_inf = load_italian_inflation()
    df = df_bench.merge(df_inf, on="date", how="inner").sort_values("date")

    dates = df["date"]
    cpi = df["cpi_index"]

    benchmarks = [
        ("MSCI World (SWDA)", df["msci_world"], ETFConfig.swda_ter),
        ("MSCI ACWI (VWCE)", df["msci_acwi"], ETFConfig.vwce_ter),
        ("MSCI ACWI IMI (VALL)", df["msci_acwi_imi"], ETFConfig.acwi_imi_ter),
    ]

    print(
        "\n[2/3] Calcolo delle metriche di rendimento e perdita reale su tutte"
        " le finestre (Netto TER, Bollo 0.20% e Capital Gain 26%)..."
    )
    all_rolling = {}
    for name, prices, ter in benchmarks:
        all_rolling[name] = calculate_all_rolling_horizons(
            dates=dates,
            prices=prices,
            cpi=cpi,
            horizons_years=SimulationConfig.rolling_horizons_years,
            ter_annual=ter,
            bollo_rate=TaxConfig.bollo_annuo,
            capital_gain_rate=TaxConfig.capital_gain,
        )

    # Output tabellare a terminale e salvataggio Markdown
    print_rolling_comprehensive_summary(all_rolling)
    save_rolling_summary_markdown(
        all_rolling,
        OUTPUT_DIR / "rolling_etf_summary.md",
        title="Analisi Finestre Mobili (2000-2025): SWDA vs VWCE vs VALL (Netto TER e Tasse)",
    )

    print("[3/3] Esportazione grafici statistici in output/...")
    plot_rolling_cagr_distributions(
        all_rolling, OUTPUT_DIR / "rolling_cagr_distribution.png"
    )
    plot_rolling_loss_time(all_rolling, OUTPUT_DIR / "rolling_real_loss_time.png")

    print(f"[OK] Fatto! Risultati esportati in {OUTPUT_DIR}/")
    print("     - rolling_etf_summary.md (Tabella riassuntiva Markdown)")
    print("     - rolling_cagr_distribution.png (Boxplot rendimenti)")
    print("     - rolling_real_loss_time.png (Confronto % tempo in perdita reale)")


if __name__ == "__main__":
    run_benchmark()

