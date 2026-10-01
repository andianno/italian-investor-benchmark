"""Configurazione globale e costanti di progetto per Italian Investor Benchmark."""

from pathlib import Path

# Percorsi assoluti di progetto
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CACHE_DATA_DIR = DATA_DIR / "cache"
OUTPUT_DIR = BASE_DIR / "output"


class TaxConfig:
  """Parametri fiscali italiani su investimenti finanziari."""

  bollo_annuo: float = (
      0.0020  # 0.20% annuo sul dossier titoli (DPR 642/1972)
  )
  capital_gain: float = 0.26  # 26% sulle plusvalenze al realizzo


class ETFConfig:
  """Costi annui di gestione (TER) per gli ETF di riferimento."""

  swda_ter: float = 0.0020  # iShares Core MSCI World (0.20%)
  vwce_ter: float = 0.0014  # Vanguard FTSE All-World (0.14%)
  acwi_imi_ter: float = 0.0007  # Vanguard FTSE Global All Cap (0.07%)


class SimulationConfig:
  """Parametri per simulazioni di portafoglio e analisi quantitative."""

  pic_initial_capital: float = 10_000.0
  pac_monthly_contribution: float = 300.0
  rolling_horizons_years: tuple = (5, 10, 15, 20)
  bootstrap_simulations: int = 2000
  bootstrap_block_size_months: int = 12
  bootstrap_seed: int = 42