"""
leitor_inmet.py - Leitura e pré-processamento dos dados do INMET

Estação A702 - Campo Grande/MS - 2025
Dados horários: irradiância global [W/m²] e temperatura do ar [°C]

Referências:
  - Arquivo: INMET_CO_MS_A702_CAMPO GRANDE_01-01-2025_A_31-12-2025.CSV
  - 8 linhas de metadados + 1 linha de cabeçalho = 9 linhas a pular nos dados
  - Coluna índice 6 (0-based): Radiação Global [kJ/m²] → dividir por 3.6 → [W/m²]
  - Coluna índice 7 (0-based): Temperatura do Ar [°C]
"""
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class InmetData:
    """Dados INMET para um período selecionado."""
    G_wm2    : np.ndarray   # Irradiância [W/m²]
    T_celsius: np.ndarray   # Temperatura do ar [°C]
    time_h   : np.ndarray   # Tempo relativo ao início do período [h]
    n_hours  : int
    dia_inicio: int
    n_dias   : int


def ler_inmet(caminho_csv: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """
    Lê o CSV completo da estação INMET e retorna arrays anuais.

    Retorna:
      G_anual [W/m²]   - 8760 valores (um por hora)
      T_anual [°C]     - 8760 valores
    """
    caminho = Path(caminho_csv)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    df = pd.read_csv(
        caminho,
        skiprows=8,          # pula 8 linhas de metadados
        sep=';',
        decimal=',',
        encoding='latin-1',
        header=0,            # linha 9 do arquivo é o cabeçalho
        on_bad_lines='skip',
    )

    # Extrair colunas por posição (mais robusto que por nome com acentos)
    # índice 6 = Radiação Global [kJ/m²], índice 7 = Temperatura [°C]
    G_raw = pd.to_numeric(df.iloc[:, 6], errors='coerce')
    T_raw = pd.to_numeric(df.iloc[:, 7], errors='coerce')

    # Limpeza: irradiância negativa → 0, NaN → 0
    G_clean = G_raw.fillna(0.0).clip(lower=0.0) / 3.6   # kJ/m² → W/m²

    # Temperatura: forward fill para preencher lacunas, default 25°C
    T_clean = T_raw.ffill().bfill().fillna(25.0)

    return G_clean.values.astype(float), T_clean.values.astype(float)


def selecionar_periodo(
    G_anual: np.ndarray,
    T_anual: np.ndarray,
    dia_inicio: int = 60,
    n_dias: int = 7
) -> InmetData:
    """
    Seleciona um período de n_dias a partir do dia dia_inicio (1-indexed).

    dia_inicio=60 → ~1° de março (7 dias: dias 60 a 66)
    """
    h_start = (dia_inicio - 1) * 24
    h_end   = h_start + n_dias * 24

    G = G_anual[h_start:h_end]
    T = T_anual[h_start:h_end]

    # Garante comprimento exato (trunca se necessário)
    n = min(len(G), len(T), n_dias * 24)
    G = G[:n]
    T = T[:n]

    return InmetData(
        G_wm2     = G,
        T_celsius = T,
        time_h    = np.arange(n, dtype=float),
        n_hours   = n,
        dia_inicio = dia_inicio,
        n_dias    = n_dias,
    )


def carregar_periodo(
    caminho_csv: str | Path,
    dia_inicio: int = 60,
    n_dias: int = 7
) -> InmetData:
    """Atalho: lê o CSV e seleciona o período em uma chamada."""
    G_anual, T_anual = ler_inmet(caminho_csv)
    return selecionar_periodo(G_anual, T_anual, dia_inicio, n_dias)
