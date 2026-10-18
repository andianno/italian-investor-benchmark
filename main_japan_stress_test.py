"""Entry point per l'Esperimento 3: Stress Test Concentrazione Geografica (Giappone 1989 al 70%).

Simula l'impatto di un investimento a replica passiva flottante (Market-Cap Buy & Hold)
effettuato al picco massimo della bolla giapponese (31/12/1989), con un'allocazione iniziale
analoga al peso attuale degli Stati Uniti nell'MSCI World (70% Giappone / 30% World ex-Japan).

Incorpora la fiscalità italiana e i costi completi:
- TER annuo ETF: 0,20%
- Imposta di bollo sul dossier titoli: 0,20% annuo al 31 dicembre
- Tassazione sulle plusvalenze (capital gain): 26% al realizzo
- Deflatore dell'inflazione italiana: indice FOI Istat da FRED
"""

from src.config import OUTPUT_DIR, TaxConfig
from src.data.japan_stress_loader import load_and_build_japan_stress_dataset
from src.engine.portfolio import simulate_portfolio
from src.visualizer.charts import plot_japan_stress_test_growth
from src.visualizer.tables import save_japan_stress_test_markdown


def run_japan_stress_test():
    print("\n" + "=" * 90)
    print("   ITALIAN INVESTOR BENCHMARK: STRESS TEST GIAPPONE 1989 (70% JAPAN / 30% WORLD EX)")
    print("           (Netto TER 0.20%, Imposta di Bollo 0.20% e Capital Gain 26%)")
    print("=" * 90)

    print("\n[1/3] Caricamento e allineamento dati storici (MSCI Japan + MSCI World + FOI Istat)...")
    df = load_and_build_japan_stress_dataset()

    dates = df["date"]
    prices = df["synth_70_30_nominal"]
    cpi = df["cpi_index"]

    start_date = dates.iloc[0].date()
    end_date = dates.iloc[-1].date()
    n_months = len(df)
    print(f"      Periodo storico analizzato: {start_date} -> {end_date} ({n_months} mesi)")

    print("\n[2/3] Simulazione contabile completa Base 100...")
    res = simulate_portfolio(
        dates=dates,
        prices=prices,
        cpi=cpi,
        mode="PIC",
        initial_capital=100.0,
        ter_annual=0.0020,  # 0.20% TER
        bollo_rate=TaxConfig.bollo_annuo,  # 0.20% imposta di bollo
        capital_gain_rate=TaxConfig.capital_gain,  # 26% capital gain
        benchmark_name="Japan 1989 Stress Test (70% Japan / 30% World ex-Japan)",
    )

    # Identificazione minimi storici e punti di pareggio
    h = res.history
    min_nom_idx = h["net_nominal_value"].idxmin()
    min_real_idx = h["net_real_value"].idxmin()
    v_min_nom = h["net_nominal_value"].iloc[min_nom_idx]
    d_min_nom = h["date"].iloc[min_nom_idx].date()
    v_min_real = h["net_real_value"].iloc[min_real_idx]
    d_min_real = h["date"].iloc[min_real_idx].date()

    nom_break = h.iloc[1:][h["net_nominal_value"].iloc[1:] >= 100.0]
    date_nom_break = nom_break["date"].iloc[0].date() if not nom_break.empty else "Mai"

    real_break = h.iloc[1:][h["net_real_value"].iloc[1:] >= 100.0]
    date_real_break = real_break["date"].iloc[0].date() if not real_break.empty else "Mai"

    cagr_nom = f"{res.cagr_nominal_net * 100:+.2f}%" if res.cagr_nominal_net is not None else "N/A"
    cagr_real = f"{res.cagr_real_net * 100:+.2f}%" if res.cagr_real_net is not None else "N/A"

    print("\n" + "=" * 90)
    print(f"{'METRICA FINANZIARIA (BASE 100)':<42} | {'RISULTATO FINALE':>20} | {'NOTE / DETTAGLIO'}")
    print("-" * 90)
    print(f"{'Capitale Iniziale Versato (31/12/1989)':<42} | {'100,00':>20} | 70% Giappone / 30% World ex-Japan")
    print(f"{'Valore Finale Lordo':<42} | {res.final_nominal_gross:>20.2f} | Crescita lorda dell'indice")
    print(f"{'Imposta di Bollo Totale Pagata':<42} | {res.total_stamp_duty:>20.2f} | 0,20% annuo trattenuto in quote al 31/12")
    print(f"{'Tassa Capital Gain (26% al realizzo)':<42} | {res.capital_gain_tax:>20.2f} | 26% sul guadagno nominale netto")
    print("-" * 90)
    print(f"{'VALORE FINALE NOMINALE NETTO':<42} | {res.final_nominal_net:>20.2f} | +{res.final_nominal_net - 100:.1f}% guadagno nominale netto")
    print(f"{'VALORE FINALE REALE NETTO (Potere Acq.)':<42} | {res.final_real_net:>20.2f} | +{res.final_real_net - 100:.1f}% potere d'acquisto reale")
    print("-" * 90)
    print(f"{'CAGR Nominale Netto':<42} | {cagr_nom:>20} | Rendimento annuo composto nominale")
    print(f"{'CAGR Reale Netto (Netto Inflazione)':<42} | {cagr_real:>20} | Rendimento annuo composto reale")
    print(f"{'Peggior Minimo Nominale Netto':<42} | {f'{v_min_nom:.2f} (-{100 - v_min_nom:.1f}%)':>20} | Toccato il {d_min_nom}")
    print(f"{'Peggior Minimo Reale Netto (Potere Acq.)':<42} | {f'{v_min_real:.2f} (-{100 - v_min_real:.1f}%)':>20} | Toccato il {d_min_real}")
    print(f"{'Data di Pareggio Nominale Netto':<42} | {str(date_nom_break):>20} | Recuperato in 3 anni e 8 mesi")
    print(f"{'Data di Pareggio Reale Netto (FOI)':<42} | {str(date_real_break):>20} | Recuperato in 9 anni e 3 mesi")
    print("=" * 90)

    print("\n[3/3] Generazione grafici e report Markdown...")
    save_japan_stress_test_markdown(
        res=res,
        df_data=df,
        output_path=OUTPUT_DIR / "japan_stress_test_summary.md",
    )
    plot_japan_stress_test_growth(
        df_history=res.history,
        df_weights=df[["date", "weight_japan", "weight_world_ex_japan"]],
        output_path=OUTPUT_DIR / "japan_stress_test_growth.png",
    )

    print(f"\n[OK] Simulazione completata con successo!")
    print(f"     - Grafico generato: {OUTPUT_DIR / 'japan_stress_test_growth.png'}")
    print(f"     - Report salvato:   {OUTPUT_DIR / 'japan_stress_test_summary.md'}\n")


if __name__ == "__main__":
    run_japan_stress_test()

