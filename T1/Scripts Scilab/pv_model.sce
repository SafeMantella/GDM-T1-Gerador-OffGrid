// ============================================================
// MODELO DO PAINEL FOTOVOLTAICO - Diodo Único
// T1 - Geração Distribuída e Microrredes - UFMS 2026
// Baseado no Tema 2 - Slide 8 (parâmetros) e Slide 9 (modelo)
// ============================================================

function [I_pv, P_pv] = pv_panel(V_pv, G, T_celsius, params)
    // Calcula corrente e potência do painel PV para uma dada tensão,
    // irradiância e temperatura.
    //
    // Entradas:
    //   V_pv      - Tensão nos terminais do painel [V]
    //   G         - Irradiância solar [W/m²]
    //   T_celsius - Temperatura da célula [°C]
    //   params    - Estrutura com parâmetros do painel
    //
    // Saídas:
    //   I_pv - Corrente do painel [A]
    //   P_pv - Potência do painel [W]

    // Constantes físicas
    k = 1.381e-23;    // Boltzmann [J/K]
    q = 1.602e-19;    // Carga do elétron [C]

    // Temperatura em Kelvin
    T = T_celsius + 273.15;
    T_ref = params.T_ref + 273.15;  // 25°C em K

    // Tensão térmica do módulo
    Vt = params.Ns * params.n * k * T / q;

    // --- Efeito da irradiância na fotocorrente ---
    // I_ph é proporcional à irradiância
    I_ph = (params.Isc + params.alpha * (T_celsius - params.T_ref)) * (G / params.G_ref);

    // --- Efeito da temperatura na corrente de saturação ---
    // I_0 aumenta exponencialmente com a temperatura
    Eg = 1.12;  // Energia do bandgap do silício [eV]
    I_0 = params.I0_ref * (T / T_ref)^3 .* exp((q * Eg / (params.n * k)) * (1/T_ref - 1/T));

    // --- Equação do diodo único ---
    // I = I_ph - I_0 * [exp((V + I*Rs) / Vt) - 1] - (V + I*Rs) / Rp
    //
    // Como I aparece dos dois lados, resolvemos iterativamente (Newton-Raphson)

    I_pv = zeros(V_pv);  // Inicializa

    for i = 1:length(V_pv)
        V = V_pv(i);
        // Chute inicial: I ≈ I_ph (desconsidera diodo e Rp)
        I_est = I_ph;

        for iter = 1:50
            // f(I) = I_ph - I_0*[exp((V+I*Rs)/Vt)-1] - (V+I*Rs)/Rp - I = 0
            exp_term = exp((V + I_est * params.Rs) / Vt);
            f = I_ph - I_0 * (exp_term - 1) - (V + I_est * params.Rs) / params.Rp - I_est;

            // Derivada: df/dI
            df = -I_0 * (params.Rs / Vt) * exp_term - params.Rs / params.Rp - 1;

            // Newton-Raphson
            I_new = I_est - f / df;

            if abs(I_new - I_est) < 1e-8 then
                break;
            end
            I_est = I_new;
        end

        I_pv(i) = max(I_new, 0);  // Corrente não pode ser negativa
    end

    // Potência
    P_pv = V_pv .* I_pv;
endfunction


function params = pv_init_params()
    // Inicializa parâmetros do painel PV de 200Wp
    // Fonte: Slide 8, Tema 2 - GDM - Fotovoltaicas

    params = struct('Pmax', 0);

    // --- Dados do datasheet (STC: 1000 W/m², 25°C) ---
    params.Pmax  = 200;      // Potência máxima [Wp]
    params.Vmpp  = 26.3;     // Tensão no MPP [V]
    params.Impp  = 7.61;     // Corrente no MPP [A]
    params.Voc   = 32.9;     // Tensão de circuito aberto [V]
    params.Isc   = 8.21;     // Corrente de curto-circuito [A]
    params.Ns    = 54;       // Número de células em série
    params.alpha = 3.18e-3;  // Coeficiente de temperatura de Isc [A/°C]

    // --- Condições de referência (STC) ---
    params.G_ref = 1000;     // Irradiância de referência [W/m²]
    params.T_ref = 25;       // Temperatura de referência [°C]

    // --- Parâmetros do modelo de diodo único ---
    // Estimados a partir dos dados do datasheet
    params.n  = 1.2;         // Fator de idealidade do diodo
    params.Rs = 0.221;       // Resistência série [Ohm]
    params.Rp = 415.405;     // Resistência paralela [Ohm]

    // --- Corrente de saturação de referência ---
    // Calculada a partir de Voc: I_0 = Isc / [exp(Voc/(Ns*n*Vt)) - 1]
    k = 1.381e-23;
    q = 1.602e-19;
    T_ref_K = params.T_ref + 273.15;
    Vt_ref = params.Ns * params.n * k * T_ref_K / q;
    params.I0_ref = params.Isc / (exp(params.Voc / Vt_ref) - 1);

endfunction


function plot_pv_curves(params)
    // Plota curvas I-V e P-V para diferentes irradiâncias e temperaturas
    // Reproduz os gráficos do slide 8 do professor

    V = linspace(0, params.Voc * 1.1, 200);

    // --- Gráfico 1: Variação de Irradiância (T=25°C) ---
    scf(1); clf();

    irradiancias = [500, 750, 1000];
    cores = ['b'; 'g'; 'r'];  // Vetor coluna de strings

    subplot(2,1,1);
    for i = 1:length(irradiancias)
        [I, P] = pv_panel(V, irradiancias(i), 25, params);
        plot(V, I, cores(i));
    end
    xlabel('Tensão V_PV [V]');
    ylabel('Corrente I_PV [A]');
    title('Curvas I-V - Variação de Irradiância (T=25°C)');
    legend('500 W/m²', '750 W/m²', '1000 W/m²');
    xgrid();

    subplot(2,1,2);
    for i = 1:length(irradiancias)
        [I, P] = pv_panel(V, irradiancias(i), 25, params);
        plot(V, P, cores(i));
        // Marca o MPP
        [Pmax_val, idx] = max(P);
        plot(V(idx), Pmax_val, cores(i) + 'o');
    end
    xlabel('Tensão V_PV [V]');
    ylabel('Potência P_PV [W]');
    title('Curvas P-V - Variação de Irradiância (T=25°C)');
    legend('500 W/m²', '750 W/m²', '1000 W/m²');
    xgrid();

    // --- Gráfico 2: Variação de Temperatura (G=1000 W/m²) ---
    scf(2); clf();

    temperaturas = [25, 41, 56];
    cores_t = ['r'; 'g'; 'b'];  // Vetor coluna de strings

    subplot(2,1,1);
    for i = 1:length(temperaturas)
        [I, P] = pv_panel(V, 1000, temperaturas(i), params);
        plot(V, I, cores_t(i));
    end
    xlabel('Tensão V_PV [V]');
    ylabel('Corrente I_PV [A]');
    title('Curvas I-V - Variação de Temperatura (G=1000 W/m²)');
    legend('25°C', '41°C', '56°C');
    xgrid();

    subplot(2,1,2);
    for i = 1:length(temperaturas)
        [I, P] = pv_panel(V, 1000, temperaturas(i), params);
        plot(V, P, cores_t(i));
        [Pmax_val, idx] = max(P);
        plot(V(idx), Pmax_val, cores_t(i) + 'o');
    end
    xlabel('Tensão V_PV [V]');
    ylabel('Potência P_PV [W]');
    title('Curvas P-V - Variação de Temperatura (G=1000 W/m²)');
    legend('25°C', '41°C', '56°C');
    xgrid();

endfunction
