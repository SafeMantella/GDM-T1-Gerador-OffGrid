// ============================================================
// ALGORITMO MPPT - P&O (Perturba & Observa) / Escalada
// T1 - Geração Distribuída e Microrredes - UFMS 2026
// Baseado no Tema 2 - Slide 21
// ============================================================
//
// Lógica (do slide 21):
//   1. Calcula dP/dt e dV/dt
//   2. Se dP/dt × dV/dt < 0 → Aumenta corrente (move para direita na curva P-V)
//   3. Se dP/dt × dV/dt > 0 → Diminui corrente (move para esquerda na curva P-V)
//   4. O passo (ΔI) é fixo
//
// Na implementação discreta:
//   - Em vez de derivadas contínuas, usamos diferenças entre amostras
//   - dP = P(k) - P(k-1)
//   - dV = V(k) - V(k-1)

function Iref_new = mppt_po_step(V_pv, I_pv, V_prev, I_prev, Iref_prev, passo)
    // Executa um passo do algoritmo P&O
    //
    // Entradas:
    //   V_pv, I_pv     - Tensão e corrente atuais do painel
    //   V_prev, I_prev - Tensão e corrente da amostra anterior
    //   Iref_prev      - Referência de corrente anterior
    //   passo          - Tamanho do passo ΔI [A]
    //
    // Saída:
    //   Iref_new - Nova referência de corrente

    // Potências
    P_atual = V_pv * I_pv;
    P_prev  = V_prev * I_prev;

    // Diferenças
    dP = P_atual - P_prev;
    dV = V_pv - V_prev;

    // Lógica P&O (tabela do slide 21)
    if dP * dV < 0 then
        // dP e dV têm sinais opostos → aumenta corrente
        Iref_new = Iref_prev + passo;
    elseif dP * dV > 0 then
        // dP e dV têm mesmo sinal → diminui corrente
        Iref_new = Iref_prev - passo;
    else
        // Sem variação → perturba para explorar
        // (P&O SEMPRE perturba; sem isso, fica parado após reset)
        Iref_new = Iref_prev + passo;
    end

    // Limita a referência (não pode ser negativa nem maior que Isc)
    Iref_new = max(0.01, min(Iref_new, 10));

endfunction
