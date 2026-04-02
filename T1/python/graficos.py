"""
graficos.py - Geração de 7 figuras matplotlib (qualidade publicação)

Figuras produzidas:
  fig01_curvas_irradiancia.png  - Curvas I-V e P-V para 3 irradiâncias
  fig02_curvas_temperatura.png  - Curvas I-V e P-V para 3 temperaturas
  fig03_dados_inmet.png         - Irradiância e temperatura dos 7 dias
  fig04_potencia_mppt.png       - Potência P&O vs Beta vs Pmax
  fig05_soc_bateria.png         - SOC P&O vs Beta
  fig06_tensao_corrente.png     - Tensão e corrente do painel
  fig07_barras_comparacao.png   - FR% e Energia em barras
"""
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from pv_model import PVPanel
from leitor_inmet import InmetData
from simulacao import SimResult, Metrics

# ---------------------------------------------------------------------------
# Configuração global matplotlib
# ---------------------------------------------------------------------------
mpl.rcParams.update({
    'font.family'      : 'serif',
    'font.size'        : 11,
    'axes.labelsize'   : 12,
    'axes.titlesize'   : 13,
    'legend.fontsize'  : 10,
    'xtick.labelsize'  : 10,
    'ytick.labelsize'  : 10,
    'figure.dpi'       : 150,
    'savefig.dpi'      : 300,
    'savefig.bbox'     : 'tight',
    'axes.grid'        : True,
    'grid.alpha'       : 0.35,
    'grid.linestyle'   : '--',
    'lines.linewidth'  : 1.8,
})

COLORS = {
    'po'   : '#1f77b4',   # azul
    'beta' : '#d62728',   # vermelho
    'pmax' : '#2ca02c',   # verde
    'G'    : '#ff7f0e',   # laranja
    'T'    : '#9467bd',   # roxo
    'c500' : '#1f77b4',
    'c750' : '#ff7f0e',
    'c1000': '#2ca02c',
    'T25'  : '#2ca02c',
    'T41'  : '#ff7f0e',
    'T56'  : '#d62728',
}


def _x_dias(ax, n_horas, dia_inicio=60):
    """Configura eixo x em dias (ticks a cada 24 h)."""
    ticks = np.arange(0, n_horas + 1, 24)
    labels = [f'Dia {dia_inicio + i}' for i in range(len(ticks))]
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=9)


# ---------------------------------------------------------------------------
# Fig 1 - Curvas I-V e P-V para diferentes irradiâncias
# ---------------------------------------------------------------------------
def fig01_curvas_irradiancia(panel: PVPanel, fig_dir: str):
    irradiancias = [500, 750, 1000]
    cores = [COLORS['c500'], COLORS['c750'], COLORS['c1000']]
    Tc = 25.0
    V_arr = np.linspace(0.0, panel.Voc * 1.01, 300)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
    fig.suptitle('Curvas Características do Painel PV (Tc = 25°C)', fontsize=14, y=0.98)

    for G, cor in zip(irradiancias, cores):
        I_arr = panel.current_array(V_arr, G, Tc)
        P_arr = V_arr * I_arr
        mask  = I_arr >= 0
        label = f'{G} W/m²'
        ax1.plot(V_arr[mask], I_arr[mask], color=cor, label=label)
        ax2.plot(V_arr[mask], P_arr[mask], color=cor, label=label)

        # Marca MPP
        V_m, I_m, P_m = panel.find_mpp(G, Tc)
        ax1.plot(V_m, I_m, 'o', color=cor, markersize=7, zorder=5)
        ax2.plot(V_m, P_m, 'o', color=cor, markersize=7, zorder=5)

    ax1.set_ylabel('Corrente I [A]')
    ax1.set_ylim(bottom=0)
    ax1.legend(loc='upper right')
    ax1.set_title('Curva I-V')

    ax2.set_xlabel('Tensão V [V]')
    ax2.set_ylabel('Potência P [W]')
    ax2.set_ylim(bottom=0)
    ax2.legend(loc='upper left')
    ax2.set_title('Curva P-V')

    plt.tight_layout()
    _save(fig, fig_dir, 'fig01_curvas_irradiancia.png')


# ---------------------------------------------------------------------------
# Fig 2 - Curvas I-V e P-V para diferentes temperaturas
# ---------------------------------------------------------------------------
def fig02_curvas_temperatura(panel: PVPanel, fig_dir: str):
    temperaturas = [25, 41, 56]
    cores = [COLORS['T25'], COLORS['T41'], COLORS['T56']]
    G = 1000.0
    V_arr = np.linspace(0.0, panel.Voc * 1.15, 300)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
    fig.suptitle('Curvas Características do Painel PV (G = 1000 W/m²)', fontsize=14, y=0.98)

    for Tc, cor in zip(temperaturas, cores):
        I_arr = panel.current_array(V_arr, G, Tc)
        P_arr = V_arr * I_arr
        mask  = I_arr >= 0
        label = f'Tc = {Tc}°C'
        ax1.plot(V_arr[mask], I_arr[mask], color=cor, label=label)
        ax2.plot(V_arr[mask], P_arr[mask], color=cor, label=label)

        V_m, I_m, P_m = panel.find_mpp(G, Tc)
        ax1.plot(V_m, I_m, 'o', color=cor, markersize=7, zorder=5)
        ax2.plot(V_m, P_m, 'o', color=cor, markersize=7, zorder=5)

    ax1.set_ylabel('Corrente I [A]')
    ax1.set_ylim(bottom=0)
    ax1.legend(loc='upper right')
    ax1.set_title('Curva I-V')
    ax1.annotate('↓ Temperatura aumenta', xy=(28, 5), fontsize=9, color='gray')

    ax2.set_xlabel('Tensão V [V]')
    ax2.set_ylabel('Potência P [W]')
    ax2.set_ylim(bottom=0)
    ax2.legend(loc='upper left')
    ax2.set_title('Curva P-V')

    plt.tight_layout()
    _save(fig, fig_dir, 'fig02_curvas_temperatura.png')


# ---------------------------------------------------------------------------
# Fig 3 - Dados INMET: irradiância e temperatura (7 dias)
# ---------------------------------------------------------------------------
def fig03_dados_inmet(dados: InmetData, fig_dir: str):
    t = dados.time_h
    n = dados.n_hours
    dia_ini = dados.dia_inicio

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 6), sharex=True)
    fig.suptitle(
        f'Dados INMET - Estação A702, Campo Grande/MS\n'
        f'Dias {dia_ini}-{dia_ini + dados.n_dias - 1} de 2025 (~1-7 de março)',
        fontsize=13
    )

    ax1.fill_between(t, dados.G_wm2, alpha=0.35, color=COLORS['G'])
    ax1.plot(t, dados.G_wm2, color=COLORS['G'], linewidth=1.4)
    ax1.set_ylabel('Irradiância [W/m²]')
    ax1.set_ylim(bottom=0)
    ax1.set_title('Irradiância Global Horizontal')

    ax2.plot(t, dados.T_celsius, color=COLORS['T'], linewidth=1.4)
    ax2.fill_between(t, dados.T_celsius, min(dados.T_celsius) - 1,
                     alpha=0.2, color=COLORS['T'])
    ax2.set_ylabel('Temperatura [°C]')
    ax2.set_title('Temperatura do Ar')
    ax2.set_xlabel('Tempo')

    _x_dias(ax2, n, dia_ini)

    plt.tight_layout()
    _save(fig, fig_dir, 'fig03_dados_inmet.png')


# ---------------------------------------------------------------------------
# Fig 4 - Potência MPPT: P&O vs Beta vs Pmax
# ---------------------------------------------------------------------------
def fig04_potencia_mppt(res_po: SimResult, res_beta: SimResult,
                        dados: InmetData, fig_dir: str):
    t    = res_po.time_h
    n    = len(t)
    dia  = dados.dia_inicio

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True,
                                    gridspec_kw={'height_ratios': [3, 1]})
    fig.suptitle('Potência MPPT - P&O vs Método Beta', fontsize=14)

    # Potência máxima como referência
    ax1.plot(t, res_po.Pmax_hist, '--', color='gray', linewidth=1.2,
             label='$P_{max}$ (teórico)', alpha=0.7)
    ax1.plot(t, res_po.P_hist,  color=COLORS['po'],   label='P&O',  linewidth=1.6)
    ax1.plot(t, res_beta.P_hist, color=COLORS['beta'], label='Beta', linewidth=1.6)

    # Sombra mostrando ganho do Beta sobre P&O
    ax1.fill_between(t, res_po.P_hist, res_beta.P_hist,
                     where=res_beta.P_hist > res_po.P_hist,
                     alpha=0.15, color=COLORS['beta'], label='Ganho Beta')

    ax1.set_ylabel('Potência [W]')
    ax1.set_ylim(bottom=0)
    ax1.legend(loc='upper right', ncol=2)

    # Irradiância no painel inferior
    ax2.fill_between(t, dados.G_wm2, alpha=0.4, color=COLORS['G'])
    ax2.plot(t, dados.G_wm2, color=COLORS['G'], linewidth=1.0)
    ax2.set_ylabel('G [W/m²]')
    ax2.set_ylim(bottom=0)
    ax2.set_xlabel('Tempo')
    _x_dias(ax2, n, dia)

    plt.tight_layout()
    _save(fig, fig_dir, 'fig04_potencia_mppt.png')


# ---------------------------------------------------------------------------
# Fig 5 - SOC da bateria: P&O vs Beta
# ---------------------------------------------------------------------------
def fig05_soc_bateria(res_po: SimResult, res_beta: SimResult,
                      dados: InmetData, fig_dir: str):
    t   = res_po.time_h
    n   = len(t)
    dia = dados.dia_inicio

    fig, ax = plt.subplots(figsize=(13, 5))
    fig.suptitle('Estado de Carga do Banco de Baterias (48 V / 100 Ah)', fontsize=14)

    ax.plot(t, res_po.SOC_hist  * 100, color=COLORS['po'],   label='P&O',  linewidth=1.8)
    ax.plot(t, res_beta.SOC_hist * 100, color=COLORS['beta'], label='Beta', linewidth=1.8)

    ax.axhline(20,  color='red',   linestyle='--', linewidth=1.2, alpha=0.7,
               label='Limite mín. SOC (20%)')
    ax.axhline(100, color='green', linestyle='--', linewidth=1.2, alpha=0.7,
               label='SOC máximo (100%)')

    ax.set_ylabel('SOC [%]')
    ax.set_ylim(0, 115)
    ax.set_xlabel('Tempo')
    ax.legend(loc='lower right')
    _x_dias(ax, n, dia)

    plt.tight_layout()
    _save(fig, fig_dir, 'fig05_soc_bateria.png')


# ---------------------------------------------------------------------------
# Fig 6 - Tensão e corrente do painel
# ---------------------------------------------------------------------------
def fig06_tensao_corrente(res_po: SimResult, res_beta: SimResult,
                          panel: PVPanel, dados: InmetData, fig_dir: str):
    t   = res_po.time_h
    n   = len(t)
    dia = dados.dia_inicio

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), sharex=True)
    fig.suptitle('Tensão e Corrente do Painel PV - P&O vs Beta', fontsize=14)

    ax1.plot(t, res_po.V_hist,   color=COLORS['po'],   label='P&O',  linewidth=1.6)
    ax1.plot(t, res_beta.V_hist, color=COLORS['beta'],  label='Beta', linewidth=1.6)
    ax1.axhline(panel.Vmpp, color='gray', linestyle=':', linewidth=1.2,
                label=f'$V_{{mpp}}$ STC = {panel.Vmpp} V', alpha=0.8)
    ax1.set_ylabel('Tensão V [V]')
    ax1.set_ylim(bottom=0)
    ax1.legend(loc='upper right')

    ax2.plot(t, res_po.I_hist,   color=COLORS['po'],   label='P&O',  linewidth=1.6)
    ax2.plot(t, res_beta.I_hist, color=COLORS['beta'],  label='Beta', linewidth=1.6)
    ax2.axhline(panel.Impp, color='gray', linestyle=':', linewidth=1.2,
                label=f'$I_{{mpp}}$ STC = {panel.Impp} A', alpha=0.8)
    ax2.set_ylabel('Corrente I [A]')
    ax2.set_ylim(bottom=0)
    ax2.legend(loc='upper right')
    ax2.set_xlabel('Tempo')
    _x_dias(ax2, n, dia)

    plt.tight_layout()
    _save(fig, fig_dir, 'fig06_tensao_corrente.png')


# ---------------------------------------------------------------------------
# Fig 7 - Barras: FR% e Energia [kWh]
# ---------------------------------------------------------------------------
def fig07_barras_comparacao(met_po: Metrics, met_beta: Metrics, fig_dir: str):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6))
    fig.suptitle('Comparação de Desempenho - P&O vs Método Beta', fontsize=14)

    algoritmos = ['P&O', 'Beta']
    cores      = [COLORS['po'], COLORS['beta']]
    hatches    = ['/', '\\']

    # FR%
    frs = [met_po.FR_pct, met_beta.FR_pct]
    bars1 = ax1.bar(algoritmos, frs, color=cores, hatch=hatches,
                    edgecolor='black', linewidth=0.8, width=0.5)
    ax1.bar_label(bars1, fmt='%.1f%%', padding=3, fontsize=12, fontweight='bold')
    ax1.axhline(100, color='gray', linestyle='--', linewidth=1, alpha=0.6)
    ax1.set_ylabel('Fator de Rastreamento [%]')
    ax1.set_title('Fator de Rastreamento (FR)')
    ax1.set_ylim(0, 115)
    ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f%%'))

    # Energia
    energias = [met_po.E_kWh, met_beta.E_kWh]
    bars2 = ax2.bar(algoritmos, energias, color=cores, hatch=hatches,
                    edgecolor='black', linewidth=0.8, width=0.5)
    ax2.bar_label(bars2, fmt='%.2f kWh', padding=3, fontsize=12, fontweight='bold')
    ax2.set_ylabel('Energia Total [kWh]')
    ax2.set_title('Energia Total Gerada (7 dias)')
    ax2.set_ylim(0, max(energias) * 1.2)

    # Anotação: ganho relativo do Beta
    ganho = (met_beta.E_kWh - met_po.E_kWh) / met_po.E_kWh * 100
    ax2.annotate(
        f'Ganho Beta: +{ganho:.1f}%',
        xy=(1, met_beta.E_kWh), xytext=(0.5, met_beta.E_kWh * 1.1),
        fontsize=10, color=COLORS['beta'],
        arrowprops=dict(arrowstyle='->', color=COLORS['beta']),
    )

    plt.tight_layout()
    _save(fig, fig_dir, 'fig07_barras_comparacao.png')


# ---------------------------------------------------------------------------
# Utilitário de salvamento
# ---------------------------------------------------------------------------
def _save(fig, fig_dir: str, filename: str):
    os.makedirs(fig_dir, exist_ok=True)
    path = os.path.join(fig_dir, filename)
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f'  [salvo] {path}')


def gerar_todas_figuras(
    panel   : PVPanel,
    dados   : InmetData,
    res_po  : SimResult,
    res_beta: SimResult,
    met_po  : Metrics,
    met_beta: Metrics,
    fig_dir : str = '../figuras',
):
    """Gera e salva todas as 7 figuras."""
    print('\nGerando figuras...')
    fig01_curvas_irradiancia(panel, fig_dir)
    fig02_curvas_temperatura(panel, fig_dir)
    fig03_dados_inmet(dados, fig_dir)
    fig04_potencia_mppt(res_po, res_beta, dados, fig_dir)
    fig05_soc_bateria(res_po, res_beta, dados, fig_dir)
    fig06_tensao_corrente(res_po, res_beta, panel, dados, fig_dir)
    fig07_barras_comparacao(met_po, met_beta, fig_dir)
    print(f'Figuras salvas em: {os.path.abspath(fig_dir)}')
