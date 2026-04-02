# Simulação GD Fotovoltaica — Comparação MPPT: P&O vs. Método Beta

> Simulação de sistema fotovoltaico off-grid de 200 Wp com bateria 48 V/100 Ah, usando dados reais do INMET (Campo Grande/MS). Compara algoritmos MPPT — Perturba & Observa vs. Método Beta — implementados em Python. Beta alcança FR = 99,98% vs. 95,0% do P&O, gerando 348 Wh a mais em 7 dias.

**Disciplina:** Geração Distribuída e Microrredes — UFMS 2026  
**Prof.:** Luigi Galotto Junior (BATLAB)

---

## Sobre o projeto

Este trabalho simula um sistema de geração distribuída fotovoltaica (GD-FV) de 200 Wp integrado a um banco de baterias ideal de 48 V / 100 Ah, alimentado por dados climáticos reais da Estação Automática INMET A702 (Campo Grande/MS, sete dias — março de 2025).

Dois algoritmos MPPT são implementados e comparados:

- **P&O** (*Perturba & Observa*): algoritmo clássico, simples, com oscilação inerente em torno do MPP
- **Método Beta (β)**: usa a variável β invariante com irradiância e um controlador PI adaptativo para convergir sem oscilação

O modelo de painel usa o **circuito equivalente de diodo único** (Villalva, 2009), resolvido por Newton-Raphson. O conversor Buck-Boost opera em **modelo médio de corrente controlada** — adequado para comparação de algoritmos em escala de tempo horária.

---

## Estrutura do projeto

```
T1/
├── python/
│   ├── main.py           # ponto de entrada — roda a simulação completa
│   ├── pv_model.py       # modelo do painel FV (diodo único + Newton-Raphson)
│   ├── mppt_po.py        # algoritmo P&O
│   ├── mppt_beta.py      # algoritmo Beta com PI adaptativo
│   ├── modelo_bateria.py # banco de baterias ideal
│   ├── leitor_inmet.py   # leitura e pré-processamento do CSV do INMET
│   ├── simulacao.py      # loop principal de simulação + métricas
│   └── graficos.py       # geração das 7 figuras (matplotlib)
├── dataset/
│   └── 2025/
│       └── INMET_CO_MS_A702_CAMPO GRANDE_01-01-2025_A_31-12-2025.CSV
├── figuras/              # figuras geradas automaticamente pela simulação
└── README.md
```

---

## Requisitos

Python 3.11 ou superior.

### Instalar dependências

```bash
pip install numpy scipy matplotlib pandas
```

| Biblioteca   | Uso                                               |
|--------------|---------------------------------------------------|
| `numpy`      | arrays, operações vetoriais                       |
| `scipy`      | `brentq` (bisseção I-V), `minimize_scalar` (MPP) |
| `matplotlib` | geração das 7 figuras de resultado                |
| `pandas`     | leitura e limpeza do CSV do INMET                 |

---

## Como executar

```bash
cd T1/python
python main.py
```

A simulação vai:

1. Carregar os dados INMET (7 dias a partir do dia 60 ≈ 1° de março)
2. Inicializar o painel FV e os bancos de baterias
3. Rodar a simulação com P&O (100 sub-passos/hora × 168 horas)
4. Rodar a simulação com Método Beta
5. Imprimir a tabela de resultados no terminal
6. Salvar os resultados em `resultados_python.txt`
7. Gerar e salvar 7 figuras em `figuras/`

### Saída esperada no terminal

```
══════════════════════════════════════════════════════════════
  T1 - Simulação GD Fotovoltaica com MPPT
  P&O vs Método Beta - UFMS 2026
══════════════════════════════════════════════════════════════

  Métrica                        P&O        Beta
───────────────────────────────────────────────────────
  Fator de Rastreamento [%]    95.00      99.98
  Energia Total [kWh]           6.616      6.964
  SOC Final [%]               100.0      100.0
───────────────────────────────────────────────────────
  Ganho Beta sobre P&O:  ΔFR = +4.98%  |  ΔE = +348 Wh (+5.3%)
```

### Figuras geradas

| Arquivo                      | Conteúdo                                              |
|------------------------------|-------------------------------------------------------|
| `fig00_esquema_sistema.png`  | Diagrama de blocos do sistema                         |
| `fig01_curvas_irradiancia.png` | Curvas I-V e P-V para 3 irradiâncias               |
| `fig02_curvas_temperatura.png` | Curvas I-V e P-V para 3 temperaturas               |
| `fig03_dados_inmet.png`      | Irradiância e temperatura dos 7 dias                  |
| `fig04_potencia_mppt.png`    | Potência P&O vs Beta vs Pmax ao longo dos 7 dias      |
| `fig05_soc_bateria.png`      | Estado de carga da bateria (P&O vs Beta)              |
| `fig06_tensao_corrente.png`  | Tensão e corrente do painel                           |
| `fig07_barras_comparacao.png`| Comparação final: FR% e energia em barras             |

---

## Parâmetros principais

### Painel FV (STC: G = 1000 W/m², Tc = 25°C)

| Parâmetro | Valor |
|---|---|
| Potência máxima | 200 Wp |
| Tensão MPP (Vmpp) | 26,3 V |
| Corrente MPP (Impp) | 7,61 A |
| Tensão circuito aberto (Voc) | 32,9 V |
| Corrente curto-circuito (Isc) | 8,21 A |
| Células em série (Ns) | 54 |
| Fator de idealidade (n) | 1,2 |

### Algoritmos MPPT

| Parâmetro | P&O | Beta |
|---|---|---|
| Passo (ΔI) | 0,3 A | — |
| Amortecimento (α) | — | 0,5 |
| Ganho integral (Ki) | — | 2,0 |

### Simulação

| Parâmetro | Valor |
|---|---|
| Período | 7 dias (dia 60–66 de 2025, ~1–7 de março) |
| Sub-passos por hora | 100 (Δt = 36 s) |
| Dados climáticos | INMET A702, Campo Grande/MS |

---

## Resultados

| Métrica | P&O | Beta | Ganho Beta |
|---|---|---|---|
| Fator de Rastreamento | 95,0% | 99,98% | +5,0 pp |
| Energia em 7 dias | 6,62 kWh | 6,96 kWh | +348 Wh (+5,3%) |
| Extrapolação anual | — | — | ~+18 kWh/ano |
| SOC final | 100% | 100% | — |

---

## Referências

- Villalva, M. G. et al. "Comprehensive approach to modeling and simulation of photovoltaic arrays." *IEEE Trans. Power Electron.*, 2009.
- Esram, T. e Chapman, P. L. "Comparison of photovoltaic array maximum power point tracking techniques." *IEEE Trans. Energy Convers.*, 2007.
- Jain, S. e Agarwal, V. "A new algorithm for rapid tracking of approximate maximum power point in photovoltaic systems." *IEEE Power Electron. Lett.*, 2004.
- INMET — Estação A702, Campo Grande/MS. Dados horários 2025. [bdmep.inmet.gov.br](https://bdmep.inmet.gov.br)
