"""
simulacao.py - Motor de simulação: loop hora × sub-passo MPPT

Cada ponto horário do INMET é subdividido em N_sub=100 sub-passos para
permitir que o algoritmo MPPT convirja dentro de cada hora.

Referência: Slides 28-29, Tema 2 - Prof. Luigi Galotto Junior - UFMS 2026
"""
from dataclasses import dataclass

import numpy as np

from pv_model import PVPanel
from modelo_bateria import Battery


@dataclass
class SimResult:
    """Resultados de uma simulação (P&O ou Beta)."""
    P_hist   : np.ndarray    # Potência média por hora [W]
    Pmax_hist: np.ndarray    # Potência máxima teórica por hora [W]
    SOC_hist : np.ndarray    # SOC da bateria ao final de cada hora [0-1]
    V_hist   : np.ndarray    # Tensão final do painel por hora [V]
    I_hist   : np.ndarray    # Corrente final do painel por hora [A]
    time_h   : np.ndarray    # Vetor de tempo [h, relativo ao início]
    label    : str           # Nome do algoritmo


@dataclass
class Metrics:
    """Métricas de desempenho calculadas a partir de SimResult."""
    FR_pct     : float   # Fator de Rastreamento [%]
    E_Wh       : float   # Energia total gerada [Wh]
    E_kWh      : float   # Energia total gerada [kWh]
    SOC_final  : float   # SOC final da bateria [%]
    label      : str


def simular(
    G_profile : np.ndarray,
    T_profile : np.ndarray,
    mppt,
    battery   : Battery,
    panel     : PVPanel,
    N_sub     : int = 100,
    label     : str = 'MPPT',
) -> SimResult:
    """
    Executa a simulação para um perfil de irradiância/temperatura.

    Parâmetros
    ----------
    G_profile : irradiância horária [W/m²], shape (N_hours,)
    T_profile : temperatura do ar horária [°C], shape (N_hours,)
    mppt      : instância de MPPT_PO ou MPPT_Beta (interface comum)
    battery   : instância de Battery (modificada in-place - passar .copy())
    panel     : instância de PVPanel
    N_sub     : número de sub-passos MPPT por hora
    label     : nome do algoritmo para exibição
    """
    N_hours  = len(G_profile)
    dt_sub_h = 1.0 / N_sub    # 0.01 h = 36 s

    P_hist    = np.zeros(N_hours)
    Pmax_hist = np.zeros(N_hours)
    SOC_hist  = np.zeros(N_hours)
    V_hist    = np.zeros(N_hours)
    I_hist    = np.zeros(N_hours)

    for h in range(N_hours):
        G    = float(G_profile[h])
        Tamb = float(T_profile[h])

        # Correção NOCT
        Tcell = PVPanel.noct_correction(Tamb, G)

        # Noite ou irradiância desprezível - sem geração
        if G < 10.0:
            SOC_hist[h] = battery.SOC
            # Pmax = 0, P = 0 - não conta para o FR
            continue

        # Ponto de máxima potência teórico (usado no FR e para reset do MPPT)
        V_mpp, I_mpp, P_mpp = panel.find_mpp(G, Tcell)
        Pmax_hist[h] = P_mpp
        Isc_now      = panel.Isc * G / panel.G_ref

        # Reinicia MPPT com estimativa próxima do MPP
        # Passa V_mpp e I_mpp para Beta calibrar beta_ref com as condições reais
        mppt.reset(Iref_init=I_mpp * 0.95, T_c=Tcell,
                   V_mpp_actual=V_mpp, I_mpp_actual=I_mpp)

        # --- Sub-loop MPPT ---
        P_acum = 0.0
        V_pv   = V_mpp    # valor inicial razoável
        I_pv   = I_mpp

        for _ in range(N_sub):
            # 1. Limita Iref ao intervalo físico
            mppt.clip_iref(Isc_now)
            Iref = mppt.get_iref()

            # 2. Painel encontra tensão para a corrente pedida
            V_pv = panel.voltage_for_current(Iref, G, Tcell)
            I_pv = panel.current(V_pv, G, Tcell)
            P_pv = V_pv * I_pv
            P_acum += P_pv

            # 3. Algoritmo MPPT atualiza Iref
            mppt.update(V_pv, I_pv, Tcell, dt_sub_h)

        P_hist[h] = P_acum / N_sub
        V_hist[h] = V_pv
        I_hist[h] = I_pv

        # Bateria absorve potência média da hora
        SOC_hist[h] = battery.step(P_hist[h], dt_h=1.0)

    return SimResult(
        P_hist    = P_hist,
        Pmax_hist = Pmax_hist,
        SOC_hist  = SOC_hist,
        V_hist    = V_hist,
        I_hist    = I_hist,
        time_h    = np.arange(N_hours, dtype=float),
        label     = label,
    )


def calcular_metricas(result: SimResult) -> Metrics:
    """Calcula FR, energia total e SOC final a partir de SimResult."""
    mask = result.Pmax_hist > 0
    FR   = 0.0
    if mask.sum() > 0:
        FR = result.P_hist[mask].sum() / result.Pmax_hist[mask].sum() * 100.0

    E_Wh = float(result.P_hist.sum())    # cada bin = 1 hora → [Wh]

    return Metrics(
        FR_pct    = FR,
        E_Wh      = E_Wh,
        E_kWh     = E_Wh / 1000.0,
        SOC_final = float(result.SOC_hist[-1]) * 100.0,
        label     = result.label,
    )
