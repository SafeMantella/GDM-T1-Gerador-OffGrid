// ============================================================
// MODELO DE BANCO DE BATERIAS (IDEAL)
// T1 - Geração Distribuída e Microrredes - UFMS 2026
//
// Modelo simplificado de bateria ideal:
//   - Tensão terminal constante (modelo ideal, como permitido no enunciado)
//   - Capacidade em Ah
//   - Estado de carga (SOC) variável
//   - Limites de SOC (não pode ultrapassar 100% nem ir abaixo de 20%)
//
// O banco de baterias recebe a potência gerada pelo painel PV
// através do conversor Buck-Boost com MPPT.
// ============================================================

function bat = bateria_init(V_nom, Cap_Ah, SOC_inicial)
    // Inicializa parâmetros do banco de baterias
    //
    // Entradas:
    //   V_nom       - Tensão nominal do banco [V]
    //   Cap_Ah      - Capacidade total [Ah]
    //   SOC_inicial - Estado de carga inicial [0 a 1] (ex: 0.5 = 50%)
    //
    // Saída:
    //   bat - Estrutura com parâmetros da bateria

    bat = struct('V_nom', 0);
    bat.V_nom = V_nom;           // Tensão nominal [V]
    bat.Cap_Ah = Cap_Ah;         // Capacidade [Ah]
    bat.Cap_Wh = V_nom * Cap_Ah; // Capacidade em [Wh]
    bat.SOC = SOC_inicial;       // Estado de carga [0-1]
    bat.SOC_min = 0.20;          // SOC mínimo (20%) - proteção
    bat.SOC_max = 1.00;          // SOC máximo (100%)
    bat.eta_carga = 0.95;        // Eficiência de carga (95%)

    disp('  Banco de baterias inicializado:');
    disp('    Tensão nominal: ' + string(V_nom) + ' V');
    disp('    Capacidade: ' + string(Cap_Ah) + ' Ah (' + string(bat.Cap_Wh) + ' Wh)');
    disp('    SOC inicial: ' + string(SOC_inicial * 100) + '%');
endfunction


function [SOC_new, I_bat, P_bat_real] = bateria_step(bat, P_in, dt_h)
    // Executa um passo de tempo na bateria
    //
    // Entradas:
    //   bat   - Estrutura da bateria (com SOC atual)
    //   P_in  - Potência de entrada (do PV via conversor) [W]
    //   dt_h  - Passo de tempo em horas [h]
    //
    // Saídas:
    //   SOC_new   - Novo estado de carga [0-1]
    //   I_bat     - Corrente na bateria [A]
    //   P_bat_real - Potência efetivamente absorvida [W]

    // Potência efetiva considerando eficiência de carga
    P_efetiva = P_in * bat.eta_carga;

    // Energia adicionada neste passo [Wh]
    E_add = P_efetiva * dt_h;

    // Novo SOC
    SOC_new = bat.SOC + E_add / bat.Cap_Wh;

    // Limita o SOC
    if SOC_new > bat.SOC_max then
        // Bateria cheia - não aceita mais carga
        E_add = (bat.SOC_max - bat.SOC) * bat.Cap_Wh;
        SOC_new = bat.SOC_max;
        P_bat_real = E_add / dt_h;
    elseif SOC_new < bat.SOC_min then
        // Proteção de descarga profunda (não aplicável aqui, só carregamos)
        SOC_new = bat.SOC_min;
        P_bat_real = 0;
    else
        P_bat_real = P_efetiva;
    end

    // Corrente na bateria
    if bat.V_nom > 0 then
        I_bat = P_bat_real / bat.V_nom;
    else
        I_bat = 0;
    end

endfunction
