"""Entry point secondario: Confronto Storico ETF Passivo vs Fondo Bancario Attivo (2000-2025).

Simula e confronta le performance di un investimento Base 100 su MSCI World:
1. ETF Passivo (SWDA - TER 0.20%)
2. Fondo Bancario Attivo di sportello (TER 2.00%)

Entrambi incorporano la fiscalità italiana completa:
- Imposta di bollo sul dossier titoli (0,20% annuo al 31 dicembre)
- Tassazione capital gain (26% al realizzo)
- Deflazione per l'inflazione reale italiana (indice FOI Istat da FRED)
"""

from src.config import BankFundConfig, ETFConfig, OUTPUT_DIR, TaxConfig
from src.data.fred_loader import load_italian_inflation
from src.data.msci_loader import build_benchmarks_parquet
from src.engine.portfolio import simulate_portfolio
from src.visualizer.charts import plot_etf_vs_bank_fund_growth


def run_bank_fund_comparison():
    print("\n" + "=" * 90)
    print("   ITALIAN INVESTOR BENCHMARK: ETF PASSIVO vs FONDO BANCARIO ATTIVO (BASE 100)")
    print("=" * 90)

    print("\n[1/3] Caricamento dati storici MSCI World e allineamento all'inflazione FOI...")
    df_bench = build_benchmarks_parquet()
    df_inf = load_italian_inflation()
    df = df_bench.merge(df_inf, on="date", how="inner").sort_values("date").reset_index(drop=True)

    dates = df["date"]
    prices = df["msci_world"]
    cpi = df["cpi_index"]

    print(f"      Periodo storico analizzato: {dates.iloc[0].date()} -> {dates.iloc[-1].date()} ({len(df)} mesi)")

    print("\n[2/3] Simulazione contabile completa (Base 100, TER, Bollo 0.20% e Capital Gain 26%)...")
    # 1. Simulazione ETF Passivo
    res_etf = simulate_portfolio(
        dates=dates,
        prices=prices,
        cpi=cpi,
        mode="PIC",
        initial_capital=100.0,
        ter_annual=ETFConfig.swda_ter,
        bollo_rate=TaxConfig.bollo_annuo,
        capital_gain_rate=TaxConfig.capital_gain,
        benchmark_name="ETF Passivo (MSCI World - TER 0.20%)",
    )

    # 2. Simulazione Fondo Bancario Attivo
    res_bank = simulate_portfolio(
        dates=dates,
        prices=prices,
        cpi=cpi,
        mode="PIC",
        initial_capital=100.0,
        ter_annual=BankFundConfig.active_fund_ter,
        bollo_rate=TaxConfig.bollo_annuo,
        capital_gain_rate=TaxConfig.capital_gain,
        benchmark_name="Fondo Bancario Attivo (MSCI World - TER 2.00%)",
    )

    # Output tabellare a terminale
    print("\n" + "=" * 90)
    print(f"{'METRICA FINANZIARIA (BASE 100)':<36} | {'ETF PASSIVO (0.20%)':>22} | {'FONDO BANCA (2.00%)':>24}")
    print("-" * 90)
    print(f"{'Capitale Iniziale Versato':<36} | {'100,00':>22} | {'100,00':>24}")
    print(f"{'Valore Finale Lordo':<36} | {res_etf.final_nominal_gross:>22.2f} | {res_bank.final_nominal_gross:>24.2f}")
    print(f"{'Imposta di Bollo Totale Pagata':<36} | {res_etf.total_stamp_duty:>22.2f} | {res_bank.total_stamp_duty:>24.2f}")
    print(f"{'Tassa Capital Gain (26% al realizzo)':<36} | {res_etf.capital_gain_tax:>22.2f} | {res_bank.capital_gain_tax:>24.2f}")
    print("-" * 90)
    print(f"{'VALORE FINALE NOMINALE NETTO':<36} | {res_etf.final_nominal_net:>22.2f} | {res_bank.final_nominal_net:>24.2f}")
    print(f"{'VALORE FINALE REALE NETTO (Potere Acq.)':<36} | {res_etf.final_real_net:>22.2f} | {res_bank.final_real_net:>24.2f}")
    print("-" * 90)
    cagr_etf_nom = f"{res_etf.cagr_nominal_net * 100:+.2f}%" if res_etf.cagr_nominal_net is not None else "N/A"
    cagr_bank_nom = f"{res_bank.cagr_nominal_net * 100:+.2f}%" if res_bank.cagr_nominal_net is not None else "N/A"
    cagr_etf_real = f"{res_etf.cagr_real_net * 100:+.2f}%" if res_etf.cagr_real_net is not None else "N/A"
    cagr_bank_real = f"{res_bank.cagr_real_net * 100:+.2f}%" if res_bank.cagr_real_net is not None else "N/A"

    print(f"{'CAGR Nominale Netto':<36} | {cagr_etf_nom:>22} | {cagr_bank_nom:>24}")
    print(f"{'CAGR Reale Netto (Netto Inflazione)':<36} | {cagr_etf_real:>22} | {cagr_bank_real:>24}")
    print(f"{'Max Drawdown Storico':<36} | {res_etf.max_drawdown * 100:>21.2f}% | {res_bank.max_drawdown * 100:>23.2f}%")
    print(f"{'Max Mesi Sott\'Acqua (Underwater)':<36} | {f'{res_etf.max_underwater_months} mesi':>22} | {f'{res_bank.max_underwater_months} mesi':>24}")
    print("=" * 90)

    # Analisi della voragine dei costi
    delta_nominal = res_etf.final_nominal_net - res_bank.final_nominal_net
    loss_pct = (delta_nominal / res_etf.final_nominal_net) * 100.0
    print(f"\n[!] EFFETTO VORAGINE DELLE COMMISSIONI BANCARIE (1.80% di differenza annua):")
    print(f"    - Capitale nominale netto perso a favore della banca: {delta_nominal:.2f} punti ({loss_pct:.1f}% del capitale finale dell'ETF)")
    print(f"    - Su un investimento iniziale reale di 10.000€, l'ETF avrebbe reso {res_etf.final_nominal_net * 100:,.0f}€ netti contro {res_bank.final_nominal_net * 100:,.0f}€ netti del fondo.")
    print(f"    - Ricchezza mancata: {delta_nominal * 100:,.0f}€ finiti in costi di intermediazione.")

    print("\n[3/3] Generazione ed esportazione del grafico ad alta risoluzione...")
    chart_path = OUTPUT_DIR / "etf_vs_bank_fund_growth.png"
    plot_etf_vs_bank_fund_growth(
        df_etf=res_etf.history,
        df_bank=res_bank.history,
        output_path=chart_path,
        etf_label="ETF Passivo (SWDA - TER 0.20%)",
        bank_label="Fondo Bancario Attivo (TER 2.00%)",
    )
    print(f"[OK] Grafico salvato con successo in: {chart_path}")


if __name__ == "__main__":
    run_bank_fund_comparison()
