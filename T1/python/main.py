"""
main.py - Ponto de entrada da simulação

T1 - Geração Distribuída e Microrredes - UFMS 2026
Disciplina: Prof. Luigi Galotto Junior (BATLAB)

Sistema:  PV 200 Wp + Conversor Buck-Boost + Bateria 48V/100Ah
MPPT:     P&O (Perturba & Observa) vs Método Beta (β)
Dados:    INMET A702 - Campo Grande/MS - 2025
Período:  7 dias a partir do dia 60 (~1° de março)
"""
import os
import sys
import time
from pathlib import Path

# Garante que o diretório do script está no path
sys.path.insert(0, str(Path(__file__).parent))

from pv_model      import PVPanel
from mppt_po       import MPPT_PO
from mppt_beta     import MPPT_Beta
from leitor_inmet  import carregar_periodo
from modelo_bateria import Battery
from simulacao     import simular, calcular_metricas
from graficos      import gerar_todas_figuras

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
BASE_DIR   = Path(__file__).parent.parent          # T1/
DATASET    = BASE_DIR / 'dataset' / '2025' / \
             'INMET_CO_MS_A702_CAMPO GRANDE_01-01-2025_A_31-12-2025.CSV'
FIG_DIR    = str(BASE_DIR / 'figuras')
RESULT_TXT = BASE_DIR / 'resultados_python.txt'

# ---------------------------------------------------------------------------
# Parâmetros de simulação
# ---------------------------------------------------------------------------
DIA_INICIO = 60      # ~1° de março
N_DIAS     = 7
N_SUB      = 100     # sub-passos MPPT por hora


def print_header():
    print('=' * 62)
    print('  T1 - Simulação GD Fotovoltaica com MPPT')
    print('  P&O vs Método Beta - UFMS 2026')
    print('  Dados: INMET A702, Campo Grande/MS, 2025')
    print(f'  Período: {N_DIAS} dias a partir do dia {DIA_INICIO} (~1°/mar)')
    print('=' * 62)


def print_metrics_table(met_po, met_beta):
    ganho_fr = met_beta.FR_pct - met_po.FR_pct
    ganho_e  = (met_beta.E_Wh - met_po.E_Wh)
    ganho_e_pct = ganho_e / met_po.E_Wh * 100 if met_po.E_Wh > 0 else 0

    print('\n' + '─' * 55)
    print(f'  {"Métrica":<30} {"P&O":>10} {"Beta":>10}')
    print('─' * 55)
    print(f'  {"Fator de Rastreamento [%]":<30} {met_po.FR_pct:>10.2f} {met_beta.FR_pct:>10.2f}')
    print(f'  {"Energia Total [Wh]":<30} {met_po.E_Wh:>10.1f} {met_beta.E_Wh:>10.1f}')
    print(f'  {"Energia Total [kWh]":<30} {met_po.E_kWh:>10.3f} {met_beta.E_kWh:>10.3f}')
    print(f'  {"SOC Final [%]":<30} {met_po.SOC_final:>10.1f} {met_beta.SOC_final:>10.1f}')
    print('─' * 55)
    print(f'  Ganho Beta sobre P&O:  ΔFR = {ganho_fr:+.2f}%  |  ΔE = {ganho_e:+.1f} Wh ({ganho_e_pct:+.1f}%)')
    print('─' * 55)


def salvar_resultados(met_po, met_beta, path: Path):
    ganho_fr  = met_beta.FR_pct - met_po.FR_pct
    ganho_e   = met_beta.E_Wh - met_po.E_Wh
    ganho_pct = ganho_e / met_po.E_Wh * 100 if met_po.E_Wh > 0 else 0

    with open(path, 'w', encoding='utf-8') as f:
        f.write('=' * 55 + '\n')
        f.write('T1 - GD Fotovoltaica - UFMS 2026\n')
        f.write(f'Dados: INMET A702, Campo Grande/MS, 2025\n')
        f.write(f'Período: {N_DIAS} dias a partir do dia {DIA_INICIO}\n')
        f.write('=' * 55 + '\n\n')
        f.write(f'{"Métrica":<32} {"P&O":>10} {"Beta":>10}\n')
        f.write('-' * 55 + '\n')
        f.write(f'{"Fator de Rastreamento [%]":<32} {met_po.FR_pct:>10.2f} {met_beta.FR_pct:>10.2f}\n')
        f.write(f'{"Energia Total [Wh]":<32} {met_po.E_Wh:>10.1f} {met_beta.E_Wh:>10.1f}\n')
        f.write(f'{"Energia Total [kWh]":<32} {met_po.E_kWh:>10.3f} {met_beta.E_kWh:>10.3f}\n')
        f.write(f'{"SOC Final [%]":<32} {met_po.SOC_final:>10.1f} {met_beta.SOC_final:>10.1f}\n')
        f.write('-' * 55 + '\n')
        f.write(f'Ganho Beta: ΔFR = {ganho_fr:+.2f}%  |  ΔE = {ganho_e:+.1f} Wh ({ganho_pct:+.1f}%)\n')
    print(f'\nResultados salvos em: {path}')


def main():
    print_header()

    # ------------------------------------------------------------------
    # 1. Carregar dados INMET
    # ------------------------------------------------------------------
    print(f'\n[1] Carregando dados INMET...')
    if not DATASET.exists():
        print(f'ERRO: arquivo não encontrado:\n  {DATASET}')
        sys.exit(1)

    dados = carregar_periodo(DATASET, dia_inicio=DIA_INICIO, n_dias=N_DIAS)
    print(f'    {dados.n_hours} horas carregadas  |  '
          f'G_max = {dados.G_wm2.max():.0f} W/m²  |  '
          f'T_med = {dados.T_celsius.mean():.1f}°C')

    # ------------------------------------------------------------------
    # 2. Inicializar painel e baterias
    # ------------------------------------------------------------------
    print('\n[2] Inicializando modelos...')
    panel    = PVPanel()
    bat_po   = Battery()
    bat_beta = Battery()

    V_mpp_stc, I_mpp_stc, P_mpp_stc = panel.find_mpp(1000.0, 25.0)
    print(f'    Painel STC: Vmpp={V_mpp_stc:.2f}V  Impp={I_mpp_stc:.3f}A  Pmax={P_mpp_stc:.1f}W')
    print(f'    Bateria: {bat_po.V_nom}V / {bat_po.Cap_Ah}Ah  SOC₀={bat_po.SOC*100:.0f}%')

    # ------------------------------------------------------------------
    # 3. Simulação P&O
    # ------------------------------------------------------------------
    print(f'\n[3] Simulando P&O ({N_SUB} sub-passos/hora × {dados.n_hours} horas)...')
    t0      = time.time()
    mppt_po = MPPT_PO(step=0.3)
    res_po  = simular(dados.G_wm2, dados.T_celsius, mppt_po, bat_po, panel,
                      N_sub=N_SUB, label='P&O')
    met_po  = calcular_metricas(res_po)
    print(f'    Concluído em {time.time()-t0:.1f}s  |  '
          f'FR = {met_po.FR_pct:.1f}%  |  E = {met_po.E_kWh:.2f} kWh')

    # ------------------------------------------------------------------
    # 4. Simulação Beta
    # ------------------------------------------------------------------
    print(f'\n[4] Simulando Método Beta (α=0.5, Ki=2.0)...')
    t0        = time.time()
    mppt_beta = MPPT_Beta(panel, alpha=0.5, Ki=2.0)
    res_beta  = simular(dados.G_wm2, dados.T_celsius, mppt_beta, bat_beta, panel,
                        N_sub=N_SUB, label='Beta')
    met_beta  = calcular_metricas(res_beta)
    print(f'    Concluído em {time.time()-t0:.1f}s  |  '
          f'FR = {met_beta.FR_pct:.1f}%  |  E = {met_beta.E_kWh:.2f} kWh')

    # ------------------------------------------------------------------
    # 5. Resultados
    # ------------------------------------------------------------------
    print_metrics_table(met_po, met_beta)
    salvar_resultados(met_po, met_beta, RESULT_TXT)

    # ------------------------------------------------------------------
    # 6. Figuras
    # ------------------------------------------------------------------
    # Precisa injetar dados completos para eixos de tempo
    res_po.time_h   = dados.time_h
    res_beta.time_h = dados.time_h

    gerar_todas_figuras(panel, dados, res_po, res_beta, met_po, met_beta,
                        fig_dir=FIG_DIR)

    print('\nSimulação concluída com sucesso.')


if __name__ == '__main__':
    main()
