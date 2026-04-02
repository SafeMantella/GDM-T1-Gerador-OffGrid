// ============================================================
// ALGORITMO MPPT - Método Beta (β)
// T1 - Geração Distribuída e Microrredes - UFMS 2026
// Baseado no Tema 2 - Slide 25
// ============================================================
//
// Fórmula (do slide 25):
//   β = ln(I_pv / V_pv) - c × V_pv
//
// Onde:
//   c = q / (n × k × T × N_s)
//
// No MPP, β assume um valor de referência β* que é constante
// para uma dada temperatura (independe da irradiância).
//
// Um controlador PI ajusta a corrente de referência I_pv*
// para manter β = β*.
//
// NOTA: Este método DEPENDE dos parâmetros do painel (n, Ns, T)
// ao contrário do P&O que é independente.

function [Iref_new, integral_new] = mppt_beta_step(V_pv, I_pv, beta_ref, c_param, Kp, Ki, integral_prev, dt)
    // Executa um passo do algoritmo Beta com controlador PI
    //
    // Entradas:
    //   V_pv, I_pv    - Tensão e corrente atuais do painel
    //   beta_ref      - Valor de referência β* (calculado no MPP em STC)
    //   c_param       - Constante c = q/(n*k*T*Ns)
    //   Kp, Ki        - Ganhos do controlador PI
    //   integral_prev - Valor anterior do integrador
    //   dt            - Período de amostragem [s]
    //
    // Saídas:
    //   Iref_new     - Nova referência de corrente
    //   integral_new - Valor atualizado do integrador

    // Calcula β atual
    // Proteção contra divisão por zero ou log de número negativo
    if V_pv < 0.1 | I_pv < 0.01 then
        Iref_new = integral_prev;
        integral_new = integral_prev;
        return;
    end

    beta = log(I_pv / V_pv) - c_param * V_pv;

    // Erro: diferença entre β* e β atual
    erro = beta_ref - beta;

    // Controlador PI
    integral_new = integral_prev + Ki * erro * dt;

    // Anti-windup: limita o integrador
    integral_new = max(-5, min(integral_new, 10));

    Iref_new = Kp * erro + integral_new;

    // Limita a referência
    Iref_new = max(0.01, min(Iref_new, 10));

endfunction


function [beta_ref, c_param] = mppt_beta_init(params)
    // Calcula os parâmetros iniciais do método Beta
    //
    // Entrada:
    //   params - Estrutura de parâmetros do painel (de pv_init_params)
    //
    // Saídas:
    //   beta_ref - Valor de β no MPP em condições STC
    //   c_param  - Constante c = q/(n*k*T*Ns)

    k = 1.381e-23;    // Boltzmann [J/K]
    q = 1.602e-19;    // Carga do elétron [C]

    // Temperatura de referência em Kelvin
    T_ref_K = params.T_ref + 273.15;

    // Constante c (depende dos parâmetros do painel)
    c_param = q / (params.n * k * T_ref_K * params.Ns);

    // β no ponto de máxima potência (STC)
    // Usando Vmpp e Impp do datasheet
    beta_ref = log(params.Impp / params.Vmpp) - c_param * params.Vmpp;

endfunction
