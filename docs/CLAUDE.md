# Geração Distribuída e Microrredes - UFMS 2026

## Contexto
Mestrado em Engenharia Elétrica - UFMS, Campo Grande/MS.
Disciplina ministrada pelo Prof. Luigi Galotto Junior (BATLAB).
Ferramenta de simulação: **Scilab** (substituto gratuito do MATLAB/Simulink, macOS arm64).

## Trabalho 1 (T1) - Em andamento
**Prazo:** 01/04/2026 | **Peso:** 20% da nota final

### Tema escolhido
Simulação de sistema de Geração Distribuída Fotovoltaica (200 Wp) com comparação de algoritmos MPPT: **P&O (Perturba & Observa)** vs **Método Beta (β)**.

### Requisitos do enunciado (Slide 51, Tema 2)
1. Fonte primária: PV 200 Wp
2. Dados reais do INMET - Estação A702, Campo Grande/MS, 2025
3. Conversor Buck-Boost + controle MPPT
4. Banco de baterias ideal (48V / 100Ah)
5. Otimização e comparação dos algoritmos

### Entregáveis
- Arquivos de simulação `.sce` (Scilab)
- Relatório PDF em **LaTeX** (máx. 5 páginas)
- Apresentação individual (slides opcionais)

## Arquivos do Projeto

```
T1/
├── simulacao_principal.sce   ← Script principal - executa tudo
├── pv_model.sce              ← Modelo painel PV (diodo único + Newton-Raphson)
├── mppt_po.sce               ← Algoritmo P&O
├── mppt_beta.sce             ← Algoritmo Beta com controlador PI
├── leitor_inmet.sce          ← Leitor CSV do INMET (função split_delim incluída)
├── modelo_bateria.sce        ← Banco de baterias ideal
├── fundamentacao_tecnica.md  ← Todos os valores e fórmulas com referência aos slides
├── LEIA_PRIMEIRO.md          ← Guia de execução
└── dataset/2025/
    └── INMET_CO_MS_A702_CAMPO GRANDE_01-01-2025_A_31-12-2025.CSV
```

## Parâmetros do Sistema

### Painel PV (Slide 8, Tema 2)
| Parâmetro | Valor |
|-----------|-------|
| Pmax | 200 Wp |
| Vmpp | 26.3 V |
| Impp | 7.61 A |
| Voc | 32.9 V |
| Isc | 8.21 A |
| Ns | 54 células |
| α (Isc) | 3.18×10⁻³ A/°C |
| n (idealidade) | 1.2 |

### Banco de Baterias (modelo ideal)
- 48 V / 100 Ah (4.8 kWh), SOC inicial 50%, eficiência 95%

### Dados INMET
- Estação A702, Campo Grande/MS, dados horários 2025
- Coluna 7: RADIACAO GLOBAL (kJ/m²) → dividir por 3.6 para obter W/m²
- Coluna 8: TEMPERATURA DO AR (°C)
- 9 linhas de cabeçalho para pular
- Separador `;`, decimal `,` → converter para `.`
- Período simulado: 7 dias a partir do dia 60 (≈ 1º de março)

## Algoritmos MPPT

### P&O (Slide 21)
- Lógica: `dP * dV < 0` → aumenta Iref; `> 0` → diminui Iref
- FR esperado: ~86.4% | Complexidade: baixa | Independe dos parâmetros do painel

### Beta - β (Slide 25)
- `β = ln(I_pv / V_pv) - c × V_pv`, onde `c = q / (n × k × T × Ns)`
- Controlador PI mantém β = β* (valor no MPP)
- FR esperado: ~96.9% | Complexidade: alta | Depende dos parâmetros do painel

## Compatibilidade Scilab - Regras Importantes
- **Nunca usar `~`** para ignorar saídas → usar variável dummy (`_dummy`)
- **`tokens()` pula campos vazios** → usar função `split_delim()` já implementada em `leitor_inmet.sce`
- **`['a', 'b']` concatena strings** → usar `['a'; 'b']` para vetor de strings
- **`struct()` vazio não funciona** → usar `struct('campo', valor_inicial)`
- **Funções não acessam workspace pai** → passar variáveis como argumentos (ver `mppt_params` em `simulacao_principal.sce`)
- **`'LineWidth'`** não é suportado diretamente em `plot()` do Scilab

## Métricas de Avaliação
- **Fator de Rastreamento (FR):** `∫P_mppt dt / ∫P_max dt × 100%` (Slides 28-29)
- Energia total gerada [Wh] em 7 dias
- SOC final da bateria
- Ganho do Beta sobre o P&O em %

## Próximos Passos
- [ ] Testar `simulacao_principal.sce` no Scilab e corrigir erros eventuais
- [ ] Criar template LaTeX do relatório (5 páginas, PDF)
- [ ] Exportar gráficos como PNG para o relatório (`xs2png`)
