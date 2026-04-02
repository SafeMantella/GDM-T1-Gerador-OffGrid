# Roteiro de Apresentação - T1: GD Fotovoltaica com MPPT
**Geração Distribuída e Microrredes - UFMS 2026**

> Este roteiro é um **guia de tópicos**, não um script para ler palavra por palavra.
> Use suas próprias palavras - o objetivo é você entender o que está falando,
> não decorar. Os símbolos e siglas estão explicados em linguagem simples.

---

## 🎯 Slide 1 - Título / Apresentação

**O que dizer:**
"O meu trabalho simula um sistema de geração de energia solar de 200 watts,
aqui em Campo Grande, usando dados reais de clima do INMET.
A ideia central é comparar dois métodos diferentes de extrair o máximo de energia
possível do painel solar ao longo do dia."

---

## 💡 Slide 2 - Contexto: Por que isso importa?

**O que dizer:**
"Um painel solar não gera sempre a mesma potência - ela muda conforme o sol muda.
Para aproveitar ao máximo essa energia, existe um controlador chamado MPPT,
que fica ajustando o sistema em tempo real para sempre operar no ponto mais eficiente.

O problema é que existem vários algoritmos MPPT, e alguns são melhores que outros.
O meu trabalho compara dois deles: o **Perturba & Observa** (o mais simples e popular)
e o **Método Beta** (mais sofisticado)."

> **Sigla:** MPPT = *Maximum Power Point Tracking* = rastreamento do ponto de máxima potência.
> É o nome dado ao controlador que fica procurando onde o painel gera mais energia.

---

## ⚡ Slide 3 - O Sistema Simulado (mostre o diagrama de blocos)

```
  ┌──────────────┐              ┌─────────────┐   V·I do painel   ┌─────────────────┐
  │  INMET A702  │  G · T_amb   │  Painel FV  │──────────────────►│    Conversor    │
  │ Campo Grande │─────────────►│   200 Wp    │                   │   Buck-Boost    │
  └──────────────┘              └─────────────┘        ┌──────────└────────┬────────┘
                                                        │ medição           │ V_dc
                                                        │    V, I           ▼
                                                        │           ┌────────────────────┐
                                              ┌─────────┴────────┐  │  Barramento CC     │
                                              │  Controlador     │  │      48 V          │
                                              │     MPPT         │  └───────────┬────────┘
                                              │  P&O  /  Beta    │          ____│____
                                              └───────┬──────────┘         │         │
                                                      │ I_ref          P_bat│     P_load│
                                                      └────────────────►    ▼         ▼
                                                     ◄──── SOC ────── ┌──────────┐ ┌──────────┐
                                                                       │ Baterias │ │ Carga DC │
                                                                       │48V/100Ah │ │  (n/m*)  │
                                                                       └──────────┘ └──────────┘
                                                              * n/m = não modelada na simulação
```

**O que dizer:**
"Esse é o diagrama de blocos do sistema que montamos. Vou descrever cada componente,
o que ele faz e por que ele foi incluído dessa forma.

**Fonte climática - INMET A702:**
A entrada do sistema são dados reais de clima: irradiância solar (G, em W/m²)
e temperatura do ar (T_amb, em °C), coletados hora a hora pela estação meteorológica
A702 do INMET em Campo Grande. Usamos 7 dias de março de 2025.
Por que dados reais? Para que a comparação entre algoritmos reflita condições que
realmente acontecem - sol variando, dias nublados, temperatura oscilando ao longo do dia.

**Painel Fotovoltaico - 200 Wp (1 painel):**
É a fonte de energia do sistema. Converte a luz solar em corrente elétrica.
**Simulamos 1 único painel** — não há array, strings em série nem paralelo.
Modelo de diodo único, parâmetros do slide 8 do Tema 2 (Villalva 2009):
Voc(tensão de circuito aberto) = 32,9 V, Isc(corrente de curto-circuito) = 8,21 A, 54 células em série.
A tensão e corrente geradas dependem de G e da temperatura da célula.
A curva I-V é calculada a cada passo por Newton-Raphson.

**Conversor Buck-Boost (DC-DC):**
Fica entre o painel e o barramento de 48 V. Permite que o painel opere em qualquer
tensão, independente da tensão da bateria.
Na simulação, usamos modelo médio: o conversor simplesmente impõe a corrente de
referência I_ref que o MPPT manda. Não modelamos duty cycle, indutor nem capacitor.
I_ref = V_mpp / R_load , V_mpp = 26,3 V, R_load = 48 V / 7,61 A = 6,31 Ω

**Controlador MPPT - P&O e Beta:**
É o algoritmo que estamos comparando. Ele recebe a medição de tensão e corrente do
painel, calcula onde está o ponto de máxima potência, e manda uma corrente de
referência I_ref para o conversor.
Rodamos dois algoritmos separadamente: P&O e Beta.
O feedback do SOC da bateria vai para o MPPT - quando a bateria está cheia, o MPPT
para de injetar energia.

**Barramento CC - 48 V:**
É o ponto de conexão central. O conversor entrega energia aqui, a bateria absorve daqui.
48 V é tensão padrão para sistemas off-grid de pequeno/médio porte.

**Banco de Baterias - 48 V / 100 Ah:**
Armazena a energia gerada pelo painel. Capacidade de 4,8 kWh, eficiência de 95%.
SOC inicial de 50%, mínimo de 20% (proteção contra descarga profunda).
Modelo ideal: tensão constante em 48 V, só o SOC varia.

**Carga DC:**
Aparece no diagrama porque num sistema real ela existiria - iluminação, bomba d'água,
pequenos equipamentos. Mas na simulação ela não foi modelada.
Por quê? Porque o objetivo era comparar os algoritmos MPPT, não simular o consumo.
Incluir uma carga adicionaria uma variável extra que não influencia a comparação."

> **Resumo do fluxo de energia no diagrama:**
> INMET → Painel → Conversor → Barramento 48V → Bateria
> (o MPPT controla o conversor; o SOC da bateria realimenta o MPPT)
>
> | Componente | Por que foi incluído assim |
> |---|---|
> | Painel 200 Wp | escala residencial/rural, parâmetros do Villalva |
> | Conversor (modelo médio) | foco é o algoritmo, não o projeto do conversor |
> | MPPT P&O e Beta | os dois algoritmos que estamos comparando |
> | Bateria 48V/100Ah | armazena a energia; padrão off-grid |
> | Carga DC | presente no diagrama, mas não modelada na simulação |

---

## 🌞 Slide 4 - O Painel Solar: como ele funciona

**O que dizer:**
"Um painel solar gera corrente elétrica quando a luz bate nas células de silício.
Mas a relação entre tensão e corrente não é linear - depende muito de quanto sol
está fazendo e da temperatura."

**Explique as curvas I-V e P-V (mostre a figura 1 e 2):**
"Nesse gráfico, o eixo horizontal é a **tensão** (em volts) e o eixo vertical é
a **corrente** (em ampères). Repara que existe um ponto onde a potência -
que é tensão vezes corrente - é máxima. Esse ponto se chama MPP."

> **Glossário dos símbolos do painel:**
>
> - **Voc** (*Voltage open-circuit*) = tensão de circuito aberto.
>   É a tensão máxima que o painel gera quando nada está conectado a ele.
>   No nosso painel: **32,9 volts**.
>
> - **Isc** (*Current short-circuit*) = corrente de curto-circuito.
>   É a corrente máxima que o painel gera quando os terminais são curto-circuitados.
>   No nosso painel: **8,21 ampères**.
>
> - **Vmpp** = tensão no ponto de máxima potência. **26,3 volts**.
>
> - **Impp** = corrente no ponto de máxima potência. **7,61 ampères**.
>
> - **Pmax** = potência máxima = Vmpp × Impp = **200 watts**.
>   É o ponto que o MPPT tenta alcançar o tempo todo.
>
> - **G** = irradiância = quantidade de energia solar que chega por metro quadrado.
>   Medida em **W/m²** (watts por metro quadrado).
>   Dia ensolarado em Campo Grande: até ~1000 W/m².
>   Dia nublado: pode cair para 100-200 W/m².
>
> - **Tc** = temperatura da célula solar. Quanto mais quente, menor a tensão gerada.
>   Por isso painel quente rende menos, mesmo com muito sol.

---

## 📊 Slide 5 - Dados Reais do INMET (mostre a figura 3)

**O que dizer:**
"Em vez de inventar condições de sol e temperatura, usei dados horários reais
da Estação Meteorológica A702 do INMET aqui em Campo Grande,
para 7 dias em março de 2025.

Repara que o perfil varia bastante: tem dias com sol forte (pico de 1027 W/m²)
e dias nublados onde a irradiância cai pela metade. A temperatura do ar
ficou entre 18°C e 34°C - o que significa que a célula solar chegou a ~56°C
durante os horários de pico."

> **INMET** = Instituto Nacional de Meteorologia. Rede de estações automáticas
> espalhadas pelo Brasil que gravam temperatura, pressão, chuva, vento e irradiância
> de hora em hora.

---

## 🔁 Slide 6 - Algoritmo P&O: Perturba & Observa

**O que dizer:**
"O P&O é o algoritmo mais simples. A lógica é:
'Mexe um pouquinho na corrente, vê se a potência aumentou ou diminuiu,
e continua mexendo na mesma direção se melhorou, ou inverte se piorou.'

É como tentar encontrar o pico de uma colina no escuro - você dá um passo,
sente se subiu ou desceu, e decide o próximo passo."

**Como o loop de controle funciona (ciclo a cada sub-passo):**
"A cada iteração o algoritmo faz exatamente isso:
1. Lê V e I atuais do painel
2. Calcula P = V × I
3. Compara com P da iteração anterior:
   - P aumentou e V aumentou → diminui I_ref (move para a direita na curva)
   - P aumentou e V diminuiu → aumenta I_ref (move para a esquerda)
   - P diminuiu → inverte a direção do passo anterior
4. Conversor impõe o novo I_ref no painel
5. Volta ao passo 1"

**Problemas do P&O:**
"O ponto fraco é que ele **nunca para de perturbar**. Mesmo quando já chegou
no ponto máximo, continua dando passinhos para um lado e para o outro.
Isso causa uma pequena perda de energia o tempo todo - o sistema fica
oscilando em volta do ótimo, nunca exatamente nele."

> **P&O** = *Perturb & Observe* = Perturba & Observa.
> **Passo** (Δl = 0,3 A): o quanto a corrente é alterada a cada iteração.
> Passo grande → converge rápido, mas oscila muito.
> Passo pequeno → oscila pouco, mas pode ser lento para acompanhar mudanças de sol.

---

## β Slide 7 - Algoritmo Beta (Método β)

**O que dizer:**
"O Método Beta é mais sofisticado. Ele usa uma propriedade matemática
interessante dos painéis solares: existe uma combinação de corrente e tensão -
chamada de β (beta) - que tem um valor fixo quando o painel está no ponto ótimo,
e esse valor depende apenas da temperatura, não de quanto sol está fazendo.

temperatura aumenta -> beta diminui
temperatura diminui -> beta aumenta

Então em vez de ficar chutando e observando como o P&O, o Beta calcula
onde deveria estar e manda o controlador ir direto para lá.

É como ter um GPS em vez de ficar virando à esquerda e à direita aleatoriamente."

**Como o loop de controle funciona (ciclo a cada sub-passo):**
"A cada iteração o algoritmo faz:
1. Lê V e I atuais do painel
2. Calcula β atual:  β = ln(I / V) − c(T) × V
3. Calcula o erro:   erro = β* − β   (β* é o alvo calculado do MPP real)
4. Controlador PI ajusta I_ref:
   I_ref = Kp × erro + Ki × ∫erro dt
5. Conversor impõe o novo I_ref no painel
6. Quando erro = 0 → β = β* → painel está no MPP → I_ref para de mudar"

**Como funciona na prática:**
"O controlador calcula a diferença entre o β atual e o β ideal, e usa um
**controlador PI** para corrigir a corrente de referência. O PI é um controlador
clássico da engenharia: uma parte reage imediatamente ao erro (proporcional)
e outra parte acumula o erro ao longo do tempo para eliminar qualquer desvio residual (integral)."

> **β (beta)**: variável auxiliar calculada como:
> β = ln(I / V) − c × V
> onde **ln** é logaritmo natural, **I** é corrente, **V** é tensão e
> **c** é uma constante que depende da temperatura e dos parâmetros do painel.
>
> **Controlador PI** = Proporcional-Integral. É um algoritmo de controle automático
> muito usado na indústria. O P reage ao erro atual, o I corrige erros acumulados.
>
> **β* (beta estrela)** = valor de β quando o painel está exatamente no MPP.
> É o alvo do controlador.

**Diferença fundamental entre os dois:**

| | P&O | Beta |
|---|---|---|
| Estratégia | perturbação cega | controle por erro calculado |
| No MPP | continua oscilando | para (erro = 0) |
| Com sol variando | lento para reagir | recalcula β* imediatamente |
| Precisa calcular MPP? | não | sim (Newton-Raphson) |
| Parâmetros | step = 0,3 A | α = 0,5, Ki = 2,0 |

---

## 🖥️ Slide 8 - Como foi feita a simulação

**O que dizer:**
"A simulação foi implementada em Python. Para cada hora dos 7 dias -
168 horas no total - o programa:

1. Lê a irradiância e temperatura do arquivo do INMET
2. Calcula onde fica o ponto de máxima potência teoricamente
3. Roda 100 iterações do algoritmo MPPT dentro daquela hora (aqui eu troco de algoritmo)
4. Registra quanta potência foi gerada na média
5. Atualiza o estado de carga da bateria

No final, calcula o **Fator de Rastreamento** dos dois algoritmos."

> **Fator de Rastreamento (FR)** = a métrica principal de comparação.
> Mede quanto da energia máxima possível o algoritmo conseguiu capturar, em percentual.
> FR = (energia que o MPPT extraiu) ÷ (energia máxima teórica) × 100%
>
> FR = 100%: algoritmo perfeito, sempre no ponto ótimo.
> FR = 86%: 14% da energia disponível foi desperdiçada.

> ⚠️ **Nota técnica - o que fizemos (e não fizemos) no conversor:**
>
> O conversor Buck-Boost está **implícito** no modelo, mas seus detalhes de chaveamento
> foram abstraídos. O que a simulação assume é:
> - O MPPT define uma referência de corrente **I_ref**
> - O conversor consegue **instantaneamente** forçar o painel a operar nessa corrente
> - A tensão V_pv resultante vem da curva I-V do painel (calculada pelo Newton-Raphson)
>
> **Não há** duty cycle, PWM, frequência de chaveamento, dinâmica do indutor/capacitor,
> ripple de corrente nem perdas de chaveamento.
>
> | Elemento | O que modelaria se incluído |
> |---|---|
> | Duty cycle D | relação V_entrada / V_saída = f(D) |
> | Indutor L | corrente oscilando em torno da média |
> | Capacitor C | tensão oscilando (ripple) |
> | Passo de tempo | microsegundos (não horas) |
> | Perdas | resistência do MOSFET, perdas no núcleo |
>
> **Por que essa escolha está correta para o trabalho:**
> O objetivo era comparar algoritmos MPPT, não projetar o conversor.
> O **modelo médio de corrente controlada** é o padrão na literatura para esse tipo de análise -
> o próprio Villalva (2009), que usamos como referência, usa essa abordagem.
> Isola o efeito do algoritmo sem contaminar os resultados com dinâmicas de chaveamento.
>
> **Se o professor perguntar:** *"usamos modelo médio de corrente controlada,
> que é adequado para comparação de algoritmos MPPT em escala de tempo horária."*

---

## 📈 Slide 9 - Resultados: Potência ao longo dos 7 dias (figura 4)

**O que dizer:**
"Nesse gráfico a linha cinza tracejada é a potência máxima teórica - o teto.
O azul é o P&O e o vermelho é o Beta.

Repara que o Beta praticamente cobre a linha cinza - está quase sempre no teto.
O P&O fica um pouco abaixo, especialmente nos horários de irradiância baixa,
que são o amanhecer e o entardecer de cada dia.

Isso acontece porque nesses horários a corrente disponível é pequena,
e os passinhos de 0,3A do P&O representam uma perturbação proporcionalmente maior."

---

## 🔋 Slide 10 - Resultados: Bateria (figura 5)

**O que dizer:**
"Ambos os algoritmos carregam a bateria completamente - ela satura em 100% de SOC
já no segundo dia. Isso mostra que o sistema está superdimensionado para essa bateria,
ou que o painel de 200W é suficiente para manter a bateria cheia mesmo em março.

A diferença entre os dois aparece mais cedo: o Beta carrega a bateria mais rápido
porque gera mais energia."

> **SOC** = *State of Charge* = Estado de Carga.
> É simplesmente o quanto a bateria está carregada, de 0% a 100%.
> Nosso sistema não deixa a bateria cair abaixo de 20% (proteção contra descarga profunda).

---

## 📊 Slide 11 - Comparação Final (figura 7 - barras)

**O que dizer:**
"Em números: o Beta alcançou Fator de Rastreamento de praticamente 100%,
enquanto o P&O ficou em 95%. Em 7 dias, isso representa 348 Wh a mais com o Beta -
cerca de 5% de ganho de energia.

Extrapolando para um ano inteiro, seriam cerca de 18 kWh a mais,
sem nenhum custo de hardware adicional - só mudando o algoritmo."

| Métrica | P&O | Beta |
|---|---|---|
| Fator de Rastreamento | 95,0% | 100,0% |
| Energia em 7 dias | 6,62 kWh | 6,96 kWh |
| Ganho do Beta | - | +348 Wh (+5,3%) |

---

## 🏁 Slide 12 - Conclusões

**O que dizer:**
"Três pontos principais para fechar:

**Primeiro:** o Método Beta supera o P&O porque elimina a oscilação.
O P&O nunca para de perturbar o sistema - o Beta converge e fica parado no ótimo.

**Segundo:** um detalhe importante que corrigi na implementação -
o parâmetro de temperatura precisa ser atualizado em tempo real.
Se você usar os parâmetros de temperatura padrão de laboratório (25°C fixo)
no campo, onde a célula chega a 56°C, o algoritmo erra o ponto ótimo.

**Terceiro:** mesmo com o Beta sendo melhor, o P&O ainda é muito usado na prática
porque é simples, barato de implementar e suficientemente bom para a maioria dos casos.
O Beta faz sentido quando se quer extrair o máximo possível, como em instalações maiores."

---

## ❓ Possíveis perguntas da banca

**"Por que o FR do P&O foi 95% e não os 86% que a literatura cita?"**
> "Porque na nossa simulação, o algoritmo roda 100 vezes por hora com irradiância constante -
> ele consegue convergir dentro de cada hora. Na prática real, o sol muda a cada segundo,
> e o P&O perde mais energia tentando acompanhar essas variações rápidas."

**"O que é o conversor Buck-Boost?"**
> "É um circuito eletrônico que regula tensão - pode tanto abaixar quanto elevar.
> Ele fica entre o painel e a bateria, e permite que o painel opere na tensão ideal
> enquanto a bateria recebe a tensão que ela precisa."

**"Você modelou o conversor de verdade? Duty cycle, indutor, capacitor?"**
> "Não, usamos o modelo médio de corrente controlada. O MPPT define uma corrente de
> referência I_ref e o conversor a impõe instantaneamente no painel. Não há duty cycle
> nem dinâmica de chaveamento. Esse é o modelo padrão da literatura para comparação
> de algoritmos MPPT - o próprio Villalva (2009) usa essa abordagem. Se modelássemos
> o chaveamento real, precisaríamos de passo de tempo na casa dos microsegundos
> e o foco passaria a ser o projeto do conversor, não o algoritmo."

**"Por que usar bateria ideal?"**
> "Para isolar o efeito do algoritmo MPPT. Se modelasse uma bateria real com variação
> de tensão, os resultados refletiriam também as imperfeições da bateria, não só do MPPT.
> O foco do trabalho é comparar os algoritmos."

**"Quantos painéis vocês usaram?"**
> "Um único painel de 200 Wp. O objetivo era comparar algoritmos MPPT, não dimensionar
> um sistema real. Escalar para múltiplos painéis é uma implementação futura — o modelo
> de diodo único se aplica igualmente a um painel ou a uma string inteira, ajustando Voc, Isc
> e o número de células em série."

**"O sistema seria viável na prática?"**
> "Para uma pequena instalação residencial ou rural em Campo Grande, sim.
> 200W de painel gerando ~7 kWh por semana, com bateria de 4,8 kWh,
> é suficiente para iluminação e pequenos equipamentos fora da rede elétrica."

---

## 📌 Números que vale ter na ponta da língua

| O que é | Valor |
|---|---|
| Potência do painel | 200 W (watts-pico) |
| Tensão no ponto ótimo (Vmpp) | 26,3 V |
| Corrente no ponto ótimo (Impp) | 7,61 A |
| Tensão máxima do painel (Voc) | 32,9 V |
| Corrente máxima do painel (Isc) | 8,21 A |
| Banco de baterias | 48 V / 100 Ah = 4,8 kWh |
| Período simulado | 7 dias, março/2025, Campo Grande |
| FR do P&O | 95,0% |
| FR do Beta | ~100% |
| Energia extra com o Beta | 348 Wh em 7 dias (~18 kWh/ano) |

---

## 🔧 Implementações Futuras do Simulador

> Esta seção lista o que foi **deliberadamente simplificado** no trabalho e o que poderia
> ser implementado em versões futuras da ferramenta.

### 🟢 Simples — baixo esforço de implementação

**Modelar a carga DC**
- O que é: incluir um perfil de consumo horário (ex: 50 W constante ou curva diária típica)
- Por que não fizemos: adicionaria uma variável a mais, desviando o foco da comparação MPPT
- Como fazer: subtrair `P_load` antes de calcular `P_bat` no passo da bateria

**Mais algoritmos MPPT**
- Incremento de Condutância (INC) — mais preciso que o P&O, sem oscilação residual
- MPPT com lógica fuzzy — adapta o passo de perturbação automaticamente
- Redes neurais — aprende o ponto ótimo a partir de G e T sem curva I-V

**Período simulado configurável**
- Hoje fixo em 7 dias. Trivial tornar N_DIAS e DIA_INICIO parâmetros de linha de comando

---

### 🟡 Médio — requer modelagem adicional

**Bateria realista**
- Hoje: tensão constante em 48 V, SOC linear, eficiência fixa de 95%
- O que falta: modelo de Thevenin (V varia com SOC e corrente), resistência interna,
  efeito de temperatura, autossimulação e degradação por ciclagem
- Impacto: o MPPT entregaria energia diferente dependendo do estado atual da bateria

**Conversor Buck-Boost detalhado**
- Hoje: modelo médio (I_ref imposta instantaneamente)
- O que falta: duty cycle D, indutor L, capacitor C, ripple de corrente/tensão,
  perdas no MOSFET e no núcleo magnético
- Impacto: passo de tempo precisaria ser na ordem de microsegundos (hoje: 1 hora)

**Temperatura da célula mais precisa**
- Hoje: correção NOCT simplificada (`Tc = T_amb + 25 × G/800`)
- O que falta: modelo térmico RC com massa térmica, irradiância traseira, vento
- Impacto: especialmente relevante para horas de pico de verão em Campo Grande

---

### 🔴 Complexo — projeto adicional significativo

**Sombreamento parcial (partial shading)**
- Quando parte do painel fica na sombra, a curva I-V passa a ter **múltiplos picos locais**
- O P&O pode ficar preso num pico local, desperdiçando muita energia
- Requer modelo de strings com bypass diodes e algoritmos MPPT global (PSO, GA)

**Sistema conectado à rede (grid-tied)**
- Incluir inversor DC/AC, sincronismo com a rede, injeção de potência ativa/reativa
- Totalmente diferente do sistema off-grid — nova topologia, novos controladores

**Múltiplos painéis e strings**
- Escalar de 1 painel de 200 W para um array (ex: 10 painéis em série × 3 strings)
- Potências na ordem de kW, mais realista para instalações residenciais completas

**BMS (Battery Management System)**
- Lógica de proteção de célula, balanceamento de carga, estimador de SOH (saúde)
- Estado de saúde (SOH) degradando ao longo de anos de operação

**Simupy**
- Simulação dinâmica

---

| O que foi simplificado | Impacto na comparação P&O vs Beta |
|---|---|
| Carga DC = zero | nenhum (ambos sofrem igualmente) |
| Conversor = modelo médio | favorece ambos igualmente; isola o algoritmo |
| Bateria = tensão constante | nenhum (comparação relativa é preservada) |
| Passo de tempo = 1 hora | subestima a perda do P&O (que oscila em escala de segundos) |
| Sem sombreamento parcial | subestima a vantagem de algoritmos globais |
