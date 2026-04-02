"""
modelo_bateria.py - Banco de baterias ideal

Modelo simplificado: tensão constante (V_nom), sem sag de tensão.
A potência de entrada é convertida em energia com eficiência η.

Parâmetros: 48 V / 100 Ah (4.8 kWh), SOC₀=50%, η=95%, SOC∈[20%, 100%]
"""
import copy


class Battery:
    """
    Modelo ideal de banco de baterias (tensão constante).

    Parâmetros
    ----------
    V_nom    : tensão nominal [V]
    Cap_Ah   : capacidade [Ah]
    SOC_init : SOC inicial (0-1)
    eta      : eficiência de carga (0-1)
    SOC_min  : SOC mínimo permitido (0-1)
    SOC_max  : SOC máximo permitido (0-1)
    """

    def __init__(
        self,
        V_nom    : float = 48.0,
        Cap_Ah   : float = 100.0,
        SOC_init : float = 0.50,
        eta      : float = 0.95,
        SOC_min  : float = 0.20,
        SOC_max  : float = 1.00,
    ):
        self.V_nom   = V_nom
        self.Cap_Ah  = Cap_Ah
        self.Cap_Wh  = V_nom * Cap_Ah      # 4800 Wh
        self.eta     = eta
        self.SOC_min = SOC_min
        self.SOC_max = SOC_max
        self.SOC     = SOC_init

    def step(self, P_in_W: float, dt_h: float = 1.0) -> float:
        """
        Absorve potência P_in_W [W] por dt_h [h].

        Retorna o SOC após o passo (0-1).
        Energia em excesso (bateria cheia) é simplesmente rejeitada.
        """
        E_add = P_in_W * self.eta * dt_h   # [Wh]
        SOC_new = self.SOC + E_add / self.Cap_Wh

        # Limita ao intervalo físico
        SOC_new = max(self.SOC_min, min(self.SOC_max, SOC_new))
        self.SOC = SOC_new
        return SOC_new

    def copy(self) -> 'Battery':
        """Retorna uma cópia independente da bateria (para duas simulações)."""
        return copy.deepcopy(self)

    def __repr__(self):
        return (
            f"Battery(V={self.V_nom}V, Cap={self.Cap_Ah}Ah, "
            f"SOC={self.SOC*100:.1f}%, η={self.eta*100:.0f}%)"
        )
