"""Entry point principale: Analisi Statistica Comparativa a Finestre Mobili."""

from src.config import OUTPUT_DIR, SimulationConfig
from src.data.fred_loader import load_italian_inflation
from src.data.msci_loader import build_benchmarks_parquet
from src.engine.statistics import calculate_all_rolling_horizons
from src.visualizer.charts import (
    plot_rolling_cagr_distributions,
    plot_rolling_loss_time,
)
from src.visualizer.tables import print_rolling_comprehensive_summary


def run_benchmark():
    print("\n" + "=" * 80)
    print("     ITALIAN INVESTOR BENCHMARK: ROLLING RISK & RETURN ENGINE (2000-2025)")
    print("=" * 80)

    print("\n[1/3] Caricamento dati storici e allineamento all'inflazione FOI...")
    df_bench = build_benchmarks_parquet()
    df_inf = load_italian_inflation()
    df = df_bench.merge(df_inf, on="date", how="inner").sort_values("date")

    dates = df["date"]
    cpi = df["cpi_index"]

    benchmarks = [
        ("MSCI World (SWDA)", df["msci_world"]),
        ("MSCI ACWI (VWCE)", df["msci_acwi"]),
        ("MSCI ACWI IMI (VALL)", df["msci_acwi_imi"]),
    ]

    print(
        "\n[2/3] Calcolo delle metriche di rendimento e perdita reale su tutte"
        " le finestre..."
    )
    all_rolling = {}
    for name, prices in benchmarks:
        all_rolling[name] = calculate_all_rolling_horizons(
            dates, prices, cpi, SimulationConfig.rolling_horizons_years
        )

    # Output tabellare
    print_rolling_comprehensive_summary(all_rolling)

    print("[3/3] Esportazione grafici statistici in output/...")
    plot_rolling_cagr_distributions(
        all_rolling, OUTPUT_DIR / "rolling_cagr_distribution.png"
    )
    plot_rolling_loss_time(all_rolling, OUTPUT_DIR / "rolling_real_loss_time.png")

    print(f"[OK] Fatto! Grafici esportati in {OUTPUT_DIR}/")
    print("     - rolling_cagr_distribution.png (Boxplot rendimenti)")
    print("     - rolling_real_loss_time.png (Confronto % tempo in perdita reale)")


if __name__ == "__main__":
    run_benchmark()
