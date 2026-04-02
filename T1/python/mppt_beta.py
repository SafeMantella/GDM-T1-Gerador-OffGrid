"""
mppt_beta.py - Algoritmo MPPT Método Beta (β) com controlador PI adaptativo

Lógica: Slide 25, Tema 2 - Prof. Luigi Galotto Junior - UFMS 2026

β = ln(I_pv / V_pv) - c(T) · V_pv
c(T) = q / (n · k · Tk · Ns)

O controlador PI mantém β = β_ref (constante para dado T, independe de G).

Nota de implementação - ganho do processo:
  ∂β/∂Iref ≈ (2 + c·V_mpp) / I_mpp
Esse ganho AUMENTA quando I_mpp diminui (baixa irradiância), tornando o
sistema instável com Kp fixo grande. Por isso usamos:
  Kp_efetivo = α / K_planta   onde K_planta = (2 + c·V_mpp) / I_mpp
O fator α (amortecimento) garante estabilidade em qualquer condição de
irradiância. O integrador é pré-semeado com I_mpp_actual para convergência
imediata sem transitório.
"""
import math
import numpy as np

from pv_model import q, k


class MPPT_Beta:
    """
    Controlador MPPT pelo Método Beta com PI adaptativo.

    Interface comum com MPPT_PO:
      reset(Iref_init, T_c, V_mpp_actual, I_mpp_actual)
      get_iref()
      update(V, I, T_c, dt)
      clip_iref(Isc_now)
    """

    def __init__(self, panel, alpha=0.5, Ki=2.0):
        """
        panel : instância de PVPanel
        alpha : fator de amortecimento (0 < α < 1). Define Kp_efetivo = α/K_planta.
                α=0.5 → amortecimento crítico. Garante estabilidade para qualquer G.
        Ki    : ganho integral [A/unidade-beta/h]
        """
        self.panel  = panel
        self.alpha  = alpha
        self.Ki     = Ki
        self.n      = panel.n
        self.Ns     = panel.Ns
        self.Isc    = panel.Isc

        self.Iref       = panel.Impp
        self.integral   = panel.Impp
        self.Kp_eff     = 0.09          # inicialização conservadora
        self.beta_ref   = None
        self._c_T       = None

        # Calcula beta_ref e Kp_eff iniciais à STC
        V0, I0, _ = panel.find_mpp(1000.0, 25.0)
        self._set_from_mpp(V0, I0, 25.0)

    # ------------------------------------------------------------------
    # Funções auxiliares
    # ------------------------------------------------------------------

    def _c(self, Tc):
        """Parâmetro c(T) = q/(n·k·Tk·Ns)."""
        return q / (self.n * k * (Tc + 273.15) * self.Ns)

    def _beta(self, V_pv, I_pv, Tc):
        """Calcula β para o ponto de operação atual."""
        if I_pv < 0.05 or V_pv < 0.5:
            return self.beta_ref   # evita log de valor inválido
        c_T = self._c(Tc)
        return math.log(I_pv / V_pv) - c_T * V_pv

    def _set_from_mpp(self, V_mpp, I_mpp, Tc):
        """
        Atualiza beta_ref e Kp_efetivo com os parâmetros do MPP atual.
        Deve ser chamado a cada reinicialização (nova hora).
        """
        c_T = self._c(Tc)
        self._c_T = c_T

        # beta_ref = β avaliado exatamente no MPP
        if I_mpp > 0.05 and V_mpp > 0.5:
            self.beta_ref = math.log(I_mpp / V_mpp) - c_T * V_mpp
        # else: mantém valor anterior

        # Ganho do processo: K_planta ≈ (2 + c·V_mpp) / I_mpp
        # Kp_efetivo = α / K_planta para loop gain = α (sub-crítico)
        if I_mpp > 0.01:
            K_planta   = (2.0 + c_T * V_mpp) / I_mpp
            self.Kp_eff = self.alpha / K_planta
        # else: mantém Kp_eff anterior

    # ------------------------------------------------------------------
    # Interface pública
    # ------------------------------------------------------------------

    def reset(self, Iref_init, T_c=25.0, V_mpp_actual=None, I_mpp_actual=None):
        """
        Reinicia o controlador para nova hora.

        Estratégia de inicialização do integrador:
        - integral pré-semeado com I_mpp_actual (ponto ótimo)
        - Iref começa em I_mpp_actual (sem transitório de convergência)
        - Kp_eff recalibrado para a irradiância atual
        """
        if (V_mpp_actual is not None and I_mpp_actual is not None
                and I_mpp_actual > 0.05 and V_mpp_actual > 0.5):
            self._set_from_mpp(V_mpp_actual, I_mpp_actual, T_c)
            # Inicia integrador diretamente no I_mpp (sem transitório)
            self.integral = I_mpp_actual
            self.Iref     = I_mpp_actual
        else:
            # Fallback: usa estimativa fornecida
            self._set_from_mpp_via_panel(T_c)
            self.integral = Iref_init
            self.Iref     = Iref_init

    def _set_from_mpp_via_panel(self, Tc):
        """Fallback: recalcula MPP via find_mpp quando V/I não são fornecidos."""
        V_mpp, I_mpp, _ = self.panel.find_mpp(1000.0, Tc)
        self._set_from_mpp(V_mpp, I_mpp, Tc)

    def get_iref(self):
        return self.Iref

    def update(self, V_pv, I_pv, T_c, dt_h):
        """
        Passo do controlador PI adaptativo.

        Iref = Kp_eff · error + integral
        integral += Ki · error · dt

        Kp_eff é adaptado ao ponto de operação (constante dentro de cada hora).
        """
        if I_pv < 0.05 or V_pv < 0.5:
            return

        beta  = self._beta(V_pv, I_pv, T_c)
        error = self.beta_ref - beta

        # Atualiza integrador com anti-windup (suave)
        self.integral += self.Ki * error * dt_h
        self.integral = float(np.clip(self.integral, 0.0, self.Isc * 1.05))

        # Saída: proporcional + integrador
        self.Iref = self.Kp_eff * error + self.integral

    def clip_iref(self, Isc_now):
        """Limita Iref ao intervalo físico."""
        self.Iref = float(np.clip(self.Iref, 0.01, Isc_now * 0.99))
        return self.Iref
