// ============================================================
// SIMULAÇÃO PRINCIPAL - GD Fotovoltaica com MPPT + Bateria
// T1 - Geração Distribuída e Microrredes - UFMS 2026
//
// Conforme enunciado do Trabalho 1 (Slide 51, Tema 2):
//   1. Fonte primária: Fotovoltaica 200Wp
//   2. Dados reais do INMET (Estação A702, Campo Grande/MS)
//   3. Conversor Buck-Boost + MPPT (P&O e Beta)
//   4. Banco de baterias ideal
//   5. Otimização: comparação P&O vs Beta
//
// COMO EXECUTAR:
//   1. Abra o Scilab
//   2. cd('caminho/para/T1/Scripts')
//   3. exec('simulacao_principal.sce', -1)
// ============================================================

clear; clc;

disp('=========================================================');
disp('  T1 - Simulação de GD Fotovoltaica com MPPT');
disp('  Dados Reais INMET + Banco de Baterias');
disp('  P&O (Escalada) vs. Método Beta');
disp('  Geração Distribuída e Microrredes - UFMS 2026');
disp('=========================================================');
disp('');

// --- Carrega módulos ---
disp('[1/6] Carregando módulos...');
exec('pv_model.sce', -1);
exec('mppt_po.sce', -1);
exec('mppt_beta.sce', -1);
exec('leitor_inmet.sce', -1);
exec('modelo_bateria.sce', -1);
disp('  OK');
disp('');

// --- Parâmetros do painel ---
params = pv_init_params();

// --- Parâmetros do MPPT (ambos algoritmos) ---
mppt_params = struct('passo_po', 0.3);         // Passo fixo do P&O [A] (maior → mais oscilação → menor FR)
[mppt_params.beta_ref, mppt_params.c_param] = mppt_beta_init(params);
mppt_params.Kp_beta = 0.5;                    // Ganho proporcional PI do Beta (reduzido p/ estabilidade)
mppt_params.Ki_beta = 2.0;                    // Ganho integral PI do Beta (reduzido p/ estabilidade)

// --- Banco de baterias ---
// Bateria 48V, 100Ah (4.8 kWh), SOC inicial 50%
// Compatível com sistemas PV residenciais de 200Wp
disp('[2/6] Inicializando banco de baterias...');
bat_params = bateria_init(48, 100, 0.5);
disp('');


// ============================================================
// LEITURA DOS DADOS INMET
// ============================================================
disp('[3/6] Lendo dados do INMET...');

// Caminho para o CSV da estação A702
csv_path = '../dataset/2025/INMET_CO_MS_A702_CAMPO GRANDE_01-01-2025_A_31-12-2025.CSV';

[tempo_total, G_total, T_total, datas, horas] = ler_inmet(csv_path);

// --- Seleciona período para simulação ---
// Escolhemos uma semana em março (outono, boa irradiância em CG)
// Dia 60 = ~1º de março
dia_inicio = 60;
n_dias = 7;

[G_semana, T_semana, tempo_semana] = selecionar_periodo(tempo_total, G_total, T_total, dia_inicio, n_dias);

disp('');

// --- Plota dados brutos do INMET ---
disp('  Plotando dados meteorológicos...');
plot_dados_inmet(tempo_semana, G_semana, T_semana, 'INMET A702 - Campo Grande/MS');


// ============================================================
// FUNÇÃO DE SIMULAÇÃO COM DADOS REAIS + BATERIA
// ============================================================

function [P_hist, Pmax_hist, SOC_hist, E_total, FR, V_hist, I_hist] = ...
    simular_gd(G_perfil, T_perfil, params, metodo, bat_init_params, mppt_params)
    // Simula o sistema GD completo com dados reais hora a hora
    //
    // Entradas:
    //   G_perfil, T_perfil - Vetores de irradiância [W/m²] e temperatura [°C]
    //   params             - Parâmetros do painel PV
    //   metodo             - 'po' ou 'beta'
    //   bat_init_params    - Estrutura de bateria inicializada
    //   mppt_params        - Estrutura com parâmetros do MPPT:
    //     .passo_po, .beta_ref, .c_param, .Kp_beta, .Ki_beta
    //
    // O loop externo é por hora (dados INMET).
    // Dentro de cada hora, o MPPT opera em sub-passos para convergir.

    N_horas = length(G_perfil);
    dt_h = 1;  // Cada passo = 1 hora

    // Sub-passos do MPPT dentro de cada hora
    N_sub = 100;          // 100 iterações por hora para o MPPT convergir
    dt_sub = dt_h / N_sub;

    // Alocação
    P_hist    = zeros(1, N_horas);
    Pmax_hist = zeros(1, N_horas);
    SOC_hist  = zeros(1, N_horas);
    V_hist    = zeros(1, N_horas);
    I_hist    = zeros(1, N_horas);

    // Estado da bateria
    bat = bat_init_params;

    // Estado do MPPT
    V_pv = params.Vmpp;
    I_pv = params.Impp;
    V_prev = V_pv;
    I_prev = I_pv;
    Iref = params.Impp;
    Iref_prev = Iref;
    integral_beta = params.Impp;
    primeiro_dia = %t;  // Flag para indicar primeira hora diurna

    for h = 1:N_horas
        G = G_perfil(h);
        T_amb = T_perfil(h);

        // Correção NOCT: temperatura da célula > temperatura do ar
        // T_cel = T_amb + (NOCT - 20) × G / 800, NOCT ≈ 45°C
        if G > 10 then
            T_cel = T_amb + 25 * G / 800;
        else
            T_cel = T_amb;
        end

        // Se não há irradiância (noite), potência = 0
        if G < 10 then
            P_hist(h) = 0;
            Pmax_hist(h) = 0;
            SOC_hist(h) = bat.SOC;
            V_hist(h) = 0;
            I_hist(h) = 0;
            primeiro_dia = %t;  // Próxima hora diurna será "primeira"
            continue;
        end

        // --- Calcula potência máxima real (MPP) via sweep ---
        V_sweep = linspace(0.1, params.Voc * 1.1, 500);
        [I_sweep, P_sweep] = pv_panel(V_sweep, G, T_cel, params);
        [Pmax_hist(h), idx_mpp] = max(P_sweep);
        V_mpp_real = V_sweep(idx_mpp);
        I_mpp_real = I_sweep(idx_mpp);

        // --- Ajusta Iref para ser factível ---
        Isc_hora = params.Isc * (G / 1000);
        if Iref > Isc_hora * 0.95 | Iref < 0.05 | primeiro_dia then
            // Reinicializa próximo ao MPP estimado
            Iref = I_mpp_real;
            integral_beta = I_mpp_real;
            Iref_prev = Iref;
            primeiro_dia = %f;
        end

        // --- Encontra ponto de operação ATUAL para Iref via bisseção ---
        // (robusto: não depende de dI/dV como o Newton-Raphson)
        V_lo = 0.1;
        V_hi = params.Voc * 1.1;
        for iter = 1:40
            V_mid = (V_lo + V_hi) / 2;
            [I_mid, _dummy] = pv_panel(V_mid, G, T_cel, params);
            if I_mid > Iref then
                V_lo = V_mid;
            else
                V_hi = V_mid;
            end
        end
        V_pv = (V_lo + V_hi) / 2;
        [I_pv, _dummy] = pv_panel(V_pv, G, T_cel, params);

        // Reset V_prev/I_prev para condições ATUAIS (evita confusão entre horas)
        V_prev = V_pv;
        I_prev = I_pv;

        // --- Sub-loop: MPPT converge dentro da hora ---
        P_soma = 0;

        for s = 1:N_sub
            // Atualiza MPPT
            select metodo
            case 'po'
                Iref = mppt_po_step(V_pv, I_pv, V_prev, I_prev, ...
                    Iref_prev, mppt_params.passo_po);
                V_prev = V_pv;
                I_prev = I_pv;
                Iref_prev = Iref;

            case 'beta'
                [Iref, integral_beta] = mppt_beta_step(V_pv, I_pv, ...
                    mppt_params.beta_ref, mppt_params.c_param, ...
                    mppt_params.Kp_beta, mppt_params.Ki_beta, ...
                    integral_beta, dt_sub);
            end

            // Limita Iref ao factível
            Iref = max(0.01, min(Iref, Isc_hora * 0.99));

            // Encontra ponto de operação via bisseção (V tal que I(V) ≈ Iref)
            V_lo = 0.1;
            V_hi = params.Voc * 1.1;
            for iter = 1:40
                V_mid = (V_lo + V_hi) / 2;
                [I_mid, _dummy] = pv_panel(V_mid, G, T_cel, params);
                if I_mid > Iref then
                    V_lo = V_mid;
                else
                    V_hi = V_mid;
                end
            end
            V_pv = (V_lo + V_hi) / 2;
            [I_pv, P_pv] = pv_panel(V_pv, G, T_cel, params);
            P_soma = P_soma + P_pv;
        end

        P_hist(h) = P_soma / N_sub;
        V_hist(h) = V_pv;
        I_hist(h) = I_pv;

        // --- Carrega bateria ---
        [SOC_new, I_bat, P_bat] = bateria_step(bat, P_hist(h), dt_h);
        bat.SOC = SOC_new;
        SOC_hist(h) = SOC_new;
    end

    // Energia total gerada [Wh]
    E_total = sum(P_hist);  // Cada amostra = 1h, então P[W] × 1h = Wh

    // Fator de Rastreamento
    idx_dia = find(Pmax_hist > 0);
    if length(idx_dia) > 0 then
        FR = sum(P_hist(idx_dia)) / sum(Pmax_hist(idx_dia)) * 100;
    else
        FR = 0;
    end

endfunction


// ============================================================
// EXECUÇÃO DAS SIMULAÇÕES
// ============================================================

disp('[4/6] Simulando com P&O...');
bat_po = bateria_init(48, 100, 0.5);
[P_po, Pmax, SOC_po, E_po, FR_po, V_po, I_po] = ...
    simular_gd(G_semana, T_semana, params, 'po', bat_po, mppt_params);
disp('  FR (P&O)  = ' + string(FR_po) + '%');
disp('  Energia total (P&O): ' + string(E_po) + ' Wh');
disp('');

disp('[5/6] Simulando com Beta...');
bat_beta = bateria_init(48, 100, 0.5);
[P_beta, Pmax_dummy, SOC_beta, E_beta, FR_beta, V_beta, I_beta] = ...
    simular_gd(G_semana, T_semana, params, 'beta', bat_beta, mppt_params);
disp('  FR (Beta) = ' + string(FR_beta) + '%');
disp('  Energia total (Beta): ' + string(E_beta) + ' Wh');
disp('');


// ============================================================
// GRÁFICOS
// ============================================================

disp('[6/6] Gerando gráficos...');

// --- Curvas I-V e P-V do painel ---
plot_pv_curves(params);

// --- Potência gerada: P&O vs Beta ---
scf(10); clf();
subplot(2,1,1);
plot(tempo_semana, Pmax, 'r--');
plot(tempo_semana, P_po, 'b');
plot(tempo_semana, P_beta, 'g');
xlabel('Tempo [h]');
ylabel('Potência [W]');
title('Potência Gerada - P&O vs Beta (dados reais INMET, 1 semana)');
legend('P máx disponível', 'P&O', 'Beta');
xgrid();

subplot(2,1,2);
plot(tempo_semana, G_semana, 'r');
xlabel('Tempo [h]');
ylabel('Irradiância [W/m²]');
title('Irradiância Solar - INMET A702 Campo Grande/MS');
xgrid();

// --- SOC da bateria ---
scf(11); clf();
plot(tempo_semana, SOC_po * 100, 'b');
plot(tempo_semana, SOC_beta * 100, 'r');
xlabel('Tempo [h]');
ylabel('SOC [%]');
title('Estado de Carga da Bateria (48V/100Ah) - P&O vs Beta');
legend('SOC (P&O)', 'SOC (Beta)');
xgrid();

// --- Tensão e Corrente do painel ---
scf(12); clf();
subplot(2,1,1);
plot(tempo_semana, V_po, 'b');
plot(tempo_semana, V_beta, 'r');
xlabel('Tempo [h]');
ylabel('Tensão V_PV [V]');
title('Tensão de Operação do Painel');
legend('P&O', 'Beta');
xgrid();

subplot(2,1,2);
plot(tempo_semana, I_po, 'b');
plot(tempo_semana, I_beta, 'r');
xlabel('Tempo [h]');
ylabel('Corrente I_PV [A]');
title('Corrente de Operação do Painel');
legend('P&O', 'Beta');
xgrid();

// --- Gráfico de barras: Energia total e FR ---
scf(13); clf();
subplot(1,2,1);
bar([1; 2], [FR_po; FR_beta]);
set(gca(), 'x_ticks', tlist(['ticks'; 'locations'; 'labels'], [1; 2], ['P&O'; 'Beta']));
ylabel('Fator de Rastreamento [%]');
title('FR - P&O vs Beta');
xgrid();

subplot(1,2,2);
bar([1; 2], [E_po/1000; E_beta/1000]);
set(gca(), 'x_ticks', tlist(['ticks'; 'locations'; 'labels'], [1; 2], ['P&O'; 'Beta']));
ylabel('Energia Total [kWh]');
title('Energia Gerada em 1 Semana');
xgrid();


// ============================================================
// RESUMO FINAL
// ============================================================

disp('');
disp('=========================================================');
disp('  RESUMO DOS RESULTADOS');
disp('=========================================================');
disp('');
disp('  Sistema: Painel PV 200Wp + Buck-Boost + Bateria 48V/100Ah');
disp('  Dados: INMET A702 - Campo Grande/MS - 2025');
disp('  Período: ' + string(n_dias) + ' dias');
disp('');
disp('  -----------------------------------------------');
disp('  Métrica              |  P&O     |  Beta');
disp('  -----------------------------------------------');
mprintf('  Fator Rastreamento   | %5.1f%%  | %5.1f%%\n', FR_po, FR_beta);
mprintf('  Energia total [Wh]   | %7.1f  | %7.1f\n', E_po, E_beta);
mprintf('  Energia total [kWh]  | %6.2f   | %6.2f\n', E_po/1000, E_beta/1000);
mprintf('  SOC final bateria    | %5.1f%%  | %5.1f%%\n', SOC_po($)*100, SOC_beta($)*100);
disp('  -----------------------------------------------');
disp('');
mprintf('  Ganho do Beta sobre P&O: %.1f Wh (%.1f%%)\n', ...
    E_beta - E_po, (E_beta - E_po) / E_po * 100);
disp('');
disp('  Simulação concluída! Verifique as janelas gráficas.');
disp('=========================================================');


// ============================================================
// EXPORTAÇÃO DE FIGURAS (PNG)
// ============================================================

disp('');
disp('Exportando figuras...');
mkdir('../figuras');

xs2png(scf(1),  '../figuras/curvas_IV_irradiancia.png');
xs2png(scf(2),  '../figuras/curvas_IV_temperatura.png');
xs2png(scf(9),  '../figuras/dados_inmet.png');
xs2png(scf(10), '../figuras/potencia_po_vs_beta.png');
xs2png(scf(11), '../figuras/soc_bateria.png');
xs2png(scf(12), '../figuras/tensao_corrente_painel.png');
xs2png(scf(13), '../figuras/comparacao_barras.png');
disp('  7 figuras salvas em ../figuras/');


// ============================================================
// EXPORTAÇÃO DE RESULTADOS (TXT)
// ============================================================

fd = mopen('../resultados.txt', 'w');
mfprintf(fd, 'RESULTADOS - T1 GD Fotovoltaica MPPT\n');
mfprintf(fd, '======================================\n');
mfprintf(fd, 'Sistema: Painel PV 200Wp + Buck-Boost + Bateria 48V/100Ah\n');
mfprintf(fd, 'Dados: INMET A702 - Campo Grande/MS - 2025\n');
mfprintf(fd, 'Período: %d dias (a partir do dia %d)\n\n', n_dias, dia_inicio);
mfprintf(fd, 'Métrica                | P&O      | Beta\n');
mfprintf(fd, '-----------------------|----------|----------\n');
mfprintf(fd, 'Fator Rastreamento [%%] | %5.1f    | %5.1f\n', FR_po, FR_beta);
mfprintf(fd, 'Energia total [Wh]     | %7.1f  | %7.1f\n', E_po, E_beta);
mfprintf(fd, 'Energia total [kWh]    | %6.2f   | %6.2f\n', E_po/1000, E_beta/1000);
mfprintf(fd, 'SOC final bateria [%%]  | %5.1f    | %5.1f\n', SOC_po($)*100, SOC_beta($)*100);
mfprintf(fd, '\nGanho Beta sobre P&O: %.1f Wh (%.1f%%)\n', E_beta-E_po, (E_beta-E_po)/E_po*100);
mclose(fd);
disp('  Resultados salvos em ../resultados.txt');
disp('');
disp('  PRONTO! Figuras e resultados exportados.');
