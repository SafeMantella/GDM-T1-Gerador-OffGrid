"""
pv_model.py - Modelo de painel fotovoltaico (diodo único)
Equação implícita resolvida por Newton-Raphson + bisseção

Referências: Slides Tema 2, Prof. Luigi Galotto Junior - UFMS 2026
"""
import math
import numpy as np
from scipy.optimize import brentq, minimize_scalar


# Constantes físicas
q  = 1.60218e-19   # Carga do elétron [C]
k  = 1.38065e-23   # Constante de Boltzmann [J/K]
Eg = 1.12          # Bandgap do silício [eV]


class PVPanel:
    """
    Modelo de painel PV de diodo único com parâmetros do slide 8 (Tema 2).

    Parâmetros nominais (STC: G=1000 W/m², Tc=25°C):
      Pmax=200 Wp, Vmpp=26.3 V, Impp=7.61 A, Voc=32.9 V, Isc=8.21 A
      Ns=54 células, n=1.2, α=3.18e-3 A/°C, Rs=0.221 Ω, Rp=415.405 Ω
    """

    def __init__(self):
        # Parâmetros elétricos (STC)
        self.Pmax  = 200.0 # Potência máxima [Wp]
        self.Vmpp  = 26.3  # Tensão no ponto de máxima potência [V]
        self.Impp  = 7.61  # Corrente no ponto de máxima potência [A]
        self.Voc   = 32.9  # Tensão de circuito aberto [V]
        self.Isc   = 8.21  # Corrente de curto-circuito [A]
        self.Ns    = 54    # Número de células em série    
        self.n     = 1.2   # Fator de idealidade
        self.alpha = 3.18e-3 # coef. temperatura Isc [A/°C]
        self.Rs    = 0.221 # resistência série [Ω]
        self.Rp    = 415.405 # resistência paralela [Ω]

        # Condições de referência
        self.G_ref   = 1000.0 # G é a irradiância em W/m²
        self.Tc_ref  = 25.0 # Tc é a temperatura em Celsius
        self.Tk_ref  = self.Tc_ref + 273.15 # Tk é a temperatura em Kelvin

        # Pré-computar I0_ref (à STC)
        Vt_ref = self._Vt(self.Tc_ref)
        self.I0_ref = self.Isc / (math.exp(self.Voc / Vt_ref) - 1.0)

    # ------------------------------------------------------------------
    # Funções auxiliares
    # ------------------------------------------------------------------

    def _Vt(self, Tc):
        """Tensão térmica [V] para temperatura Tc [°C]."""
        return self.Ns * self.n * k * (Tc + 273.15) / q

    def _Iph(self, G, Tc):
        """Fotocorrente [A]."""
        return (self.Isc + self.alpha * (Tc - self.Tc_ref)) * (G / self.G_ref)

    def _I0(self, Tc):
        """Corrente de saturação [A] - escalonada com temperatura."""
        Tk = Tc + 273.15
        exponent = (q * Eg) / (self.n * k) * (1.0 / self.Tk_ref - 1.0 / Tk)
        exponent = min(exponent, 500.0)
        return self.I0_ref * (Tk / self.Tk_ref) ** 3 * math.exp(exponent)

    def _f(self, I, V, G, Tc):
        """Resíduo da equação implícita f(I)=0."""
        Vt  = self._Vt(Tc)
        Iph = self._Iph(G, Tc)
        I0  = self._I0(Tc)
        x   = (V + I * self.Rs) / Vt
        x   = min(x, 500.0)
        return Iph - I0 * (math.exp(x) - 1.0) - (V + I * self.Rs) / self.Rp - I

    def _df(self, I, V, Tc):
        """Derivada df/dI."""
        Vt = self._Vt(Tc)
        I0 = self._I0(Tc)
        x  = (V + I * self.Rs) / Vt
        x  = min(x, 500.0)
        return -I0 * (self.Rs / Vt) * math.exp(x) - self.Rs / self.Rp - 1.0

    # ------------------------------------------------------------------
    # Interface pública
    # ------------------------------------------------------------------

    def current(self, V, G, Tc):
        """
        Calcula corrente I [A] para tensão V [V], irradiância G [W/m²],
        temperatura da célula Tc [°C].
        Resolve via Newton-Raphson (fallback: brentq).
        """
        if V < 0.0 or G < 1e-3:
            return 0.0
        Iph = self._Iph(G, Tc)
        if V > self.Voc * 1.1:
            return 0.0

        # Chute inicial
        I = Iph * 0.9
        for _ in range(50):
            f  = self._f(I, V, G, Tc)
            df = self._df(I, V, Tc)
            if abs(df) < 1e-15:
                break
            I_new = I - f / df
            I_new = max(0.0, min(I_new, Iph * 1.05))
            if abs(I_new - I) < 1e-8:
                return max(0.0, I_new)
            I = I_new

        # Fallback: brentq
        try:
            lo = max(0.0, Iph - 0.5)
            hi = Iph * 1.05
            return max(0.0, brentq(lambda i: self._f(i, V, G, Tc), lo, hi,
                                   xtol=1e-8, maxiter=100))
        except Exception:
            return max(0.0, I)

    def current_array(self, V_arr, G, Tc):
        """Versão vetorizada de current()."""
        return np.array([self.current(v, G, Tc) for v in V_arr])

    def voltage_for_current(self, Iref, G, Tc):
        """
        Dado Iref [A], encontra V [V] por bisseção.
        Usado no controle de corrente (MPPT define Iref → painel opera em V).
        """
        Iph = self._Iph(G, Tc)
        if Iref >= Iph * 0.999:
            return 0.01
        if Iref < 0.001:
            return self.Voc * 0.995

        # f_bis(V) = I(V) - Iref: busca zero
        # I(V) é monotonamente decrescente com V
        def f_bis(V):
            return self.current(V, G, Tc) - Iref

        lo, hi = 0.01, self.Voc * 1.05
        # Garante sinais opostos
        if f_bis(lo) * f_bis(hi) > 0:
            # Tenta encontrar bracket
            for v_try in np.linspace(0.01, self.Voc, 20):
                if f_bis(v_try) <= 0:
                    hi = v_try
                    break
        try:
            return brentq(f_bis, lo, hi, xtol=1e-6, maxiter=60)
        except Exception:
            # Fallback: bisseção manual
            for _ in range(60):
                mid = (lo + hi) / 2.0
                if f_bis(mid) > 0:
                    lo = mid
                else:
                    hi = mid
            return (lo + hi) / 2.0

    def find_mpp(self, G, Tc):
        """
        Encontra o ponto de máxima potência (MPP).
        Retorna (V_mpp, I_mpp, P_mpp).
        """
        if G < 1.0:
            return 0.0, 0.0, 0.0

        # Varredura grossa
        V_arr = np.linspace(0.5, self.Voc * 0.99, 500)
        I_arr = self.current_array(V_arr, G, Tc)
        P_arr = V_arr * I_arr
        idx   = np.argmax(P_arr)
        V0    = V_arr[idx]

        # Refinamento com scipy
        lo = max(0.5, V0 - 2.0)
        hi = min(self.Voc * 0.999, V0 + 2.0)
        try:
            res = minimize_scalar(
                lambda v: -self.current(v, G, Tc) * v,
                bounds=(lo, hi), method='bounded',
                options={'xatol': 1e-6}
            )
            V_mpp = res.x
        except Exception:
            V_mpp = V0

        I_mpp = self.current(V_mpp, G, Tc)
        P_mpp = V_mpp * I_mpp
        return V_mpp, I_mpp, P_mpp

    @staticmethod
    def noct_correction(T_amb, G):
        """Temperatura da célula com correção NOCT (NOCT=45°C)."""
        if G > 10.0:
            return T_amb + 25.0 * G / 800.0
        return T_amb
