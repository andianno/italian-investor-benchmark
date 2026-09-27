from dataclasses import dataclass
from pathlib import Path

# Percorsi del progetto
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CACHE_DATA_DIR = DATA_DIR / "cache"


@dataclass(frozen=True)
class TaxConfig:
    """Configurazione fiscale italiana."""

    bollo_annuo: float = 0.0020  # 0.20% annuo sul controvalore
    capital_gain: float = 0.26  # 26% sulle plusvalenze realizzate


@dataclass(frozen=True)
class ETFConfig:
    """Parametri degli strumenti simulati."""

    # TER annuo di default per ciascun benchmark
    ter_world: float = 0.0020  # SWDA: 0.20%
    ter_acwi: float = 0.0014  # VWCE: 0.14%
    ter_allcap: float = 0.0007  # VALL: 0.07%


@dataclass(frozen=True)
class SimulationConfig:
    """Parametri generali di simulazione."""

    initial_capital_pic: float = 10_000.0
    monthly_pac: float = 300.0
    bootstrap_block_size_months: int = 12
    bootstrap_iterations: int = 2_000