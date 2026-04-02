"""
mppt_po.py - Algoritmo MPPT Perturba & Observa (P&O)

Lógica: Slide 21, Tema 2 - Prof. Luigi Galotto Junior - UFMS 2026

O P&O pertuba a referência de corrente a cada sub-passo e observa
se a potência aumentou ou diminuiu, ajustando a direção do próximo passo.
"""


class MPPT_PO:
    """
    Controlador MPPT por Perturba & Observa.

    Interface comum com MPPT_Beta:
      reset(Iref_init, T_c)  - reinicia estado
      get_iref()             - retorna Iref atual
      update(V, I, T_c, dt)  - atualiza estado com novo ponto de operação
    """

    def __init__(self, step=0.3, Iref_init=7.61):
        self.step       = step        # passo de perturbação [A]
        self.Iref       = Iref_init
        self._V_prev    = None
        self._P_prev    = None

    def reset(self, Iref_init, T_c=None, V_mpp_actual=None, I_mpp_actual=None):
        """
        Reinicia o controlador para nova hora / nova condição.
        Iref_init: estimativa do I_mpp para a condição atual.
        (V_mpp_actual, I_mpp_actual aceitos mas ignorados - interface comum com Beta)
        """
        self.Iref    = Iref_init
        self._V_prev = None
        self._P_prev = None

    def get_iref(self):
        return self.Iref

    def update(self, V_pv, I_pv, T_c=None, dt_h=None):
        """
        Atualiza Iref com base no novo ponto de operação (V_pv, I_pv).
        Deve ser chamado APÓS usar get_iref() e medir o ponto resultante.
        """
        P_pv = V_pv * I_pv

        if self._V_prev is None:
            # Primeiro passo - sem histórico, apenas pertuba
            self._V_prev = V_pv
            self._P_prev = P_pv
            self.Iref += self.step
            return

        dP = P_pv - self._P_prev
        dV = V_pv - self._V_prev

        if abs(dP) < 1e-6:
            # Sem variação de potência - pertuba para explorar
            self.Iref += self.step
        elif dP * dV < 0:
            # Estamos à direita do MPP - aumenta corrente (move para esquerda)
            self.Iref += self.step
        else:
            # Estamos à esquerda do MPP - diminui corrente (move para direita)
            self.Iref -= self.step

        self._V_prev = V_pv
        self._P_prev = P_pv

    def clip_iref(self, Isc_now):
        """Limita Iref ao intervalo físico [0.01, 0.99*Isc]."""
        self.Iref = max(0.01, min(self.Iref, Isc_now * 0.99))
        return self.Iref
