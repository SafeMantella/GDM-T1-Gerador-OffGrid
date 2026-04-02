// ============================================================
// LEITOR DE DADOS DO INMET - Estação A702 Campo Grande/MS
// T1 - Geração Distribuída e Microrredes - UFMS 2026
//
// Lê o CSV do INMET e extrai:
//   - Irradiância solar global [W/m²] (convertida de kJ/m²)
//   - Temperatura do ar [°C]
//   - Data e hora
//
// Formato do CSV INMET:
//   - Separador: ponto-e-vírgula (;)
//   - Decimais: vírgula (,) - precisa converter para ponto (.)
//   - 8 linhas de cabeçalho (metadados da estação)
//   - 1 linha de nomes de colunas
//   - Coluna 7: RADIACAO GLOBAL (Kj/m²)
//   - Coluna 8: TEMPERATURA DO AR - BULBO SECO (°C)
// ============================================================


function campos = split_delim(s, delim)
    // Separa string s por delimitador, preservando campos vazios
    // (ao contrário de tokens(), que pula campos vazios)
    //
    // Exemplo: split_delim("a;;b", ";") retorna ["a"; ""; "b"]

    pos = strindex(s, delim);
    n = length(pos);
    campos = [];
    inicio = 1;

    for k = 1:n
        campo = part(s, inicio:pos(k)-1);
        campo = stripblanks(campo);  // Remove espaços extras
        campos = [campos; campo];
        inicio = pos(k) + length(delim);
    end

    // Último campo (depois do último delimitador)
    if inicio <= length(s) then
        campo = part(s, inicio:length(s));
        campo = stripblanks(campo);
        campos = [campos; campo];
    else
        campos = [campos; ''];
    end
endfunction


function [tempo_h, G_wm2, T_celsius, datas, horas] = ler_inmet(caminho_csv)
    // Lê dados do CSV INMET e retorna vetores de irradiância e temperatura
    //
    // Entrada:
    //   caminho_csv - Caminho completo para o arquivo CSV
    //
    // Saídas:
    //   tempo_h   - Tempo em horas desde o início [h]
    //   G_wm2     - Irradiância global [W/m²]
    //   T_celsius - Temperatura do ar [°C]
    //   datas     - Vetor de strings com as datas
    //   horas     - Vetor de strings com as horas

    disp('  Lendo arquivo: ' + caminho_csv);

    // Lê o arquivo como texto
    texto = mgetl(caminho_csv);

    // Pula as 8 primeiras linhas (metadados) + 1 linha de cabeçalho = 9 linhas
    N_linhas = size(texto, 1);
    N_dados = N_linhas - 9;

    disp('  Total de registros: ' + string(N_dados));

    // Aloca vetores
    G_wm2 = zeros(1, N_dados);
    T_celsius = zeros(1, N_dados);
    tempo_h = zeros(1, N_dados);
    datas = emptystr(N_dados, 1);   // Vetor de strings pré-alocado
    horas = emptystr(N_dados, 1);

    for i = 1:N_dados
        linha = texto(i + 9);  // Pula cabeçalho

        // Se linha vazia, pula
        if length(linha) < 5 then
            continue;
        end

        // Substitui vírgula decimal por ponto
        linha = strsubst(linha, ',', '.');

        // Separa por ponto-e-vírgula (preserva campos vazios)
        campos = split_delim(linha, ';');

        if size(campos, 1) < 8 then
            continue;
        end

        // Data (campo 1) e Hora (campo 2)
        datas(i) = campos(1);
        horas(i) = campos(2);

        // Radiação Global (campo 7) - em kJ/m²
        // Conversão: kJ/m² por hora → W/m²
        // 1 kJ = 1000 J, 1 hora = 3600 s
        // W/m² = (kJ/m²) × 1000 / 3600 = (kJ/m²) / 3.6
        rad_str = campos(7);
        if rad_str == '' then
            G_wm2(i) = 0;
        else
            val = evstr(rad_str);
            if isnan(val) then
                G_wm2(i) = 0;
            else
                G_wm2(i) = val / 3.6;
            end
        end

        // Temperatura do Ar (campo 8) - em °C
        temp_str = campos(8);
        if temp_str == '' then
            T_celsius(i) = 25;  // Valor padrão se dado ausente
        else
            val = evstr(temp_str);
            if isnan(val) then
                T_celsius(i) = 25;
            else
                T_celsius(i) = val;
            end
        end

        // Tempo em horas
        tempo_h(i) = (i - 1);  // Uma amostra por hora
    end

    // Remove zeros no final (caso tenha linhas vazias)
    idx_valido = find(tempo_h > 0 | (G_wm2 > 0) | (T_celsius > 0));
    if length(idx_valido) > 0 then
        ultimo = idx_valido($);
        G_wm2 = G_wm2(1:ultimo);
        T_celsius = T_celsius(1:ultimo);
        tempo_h = tempo_h(1:ultimo);
        datas = datas(1:ultimo);
        horas = horas(1:ultimo);
    end

    disp('  Dados carregados: ' + string(length(G_wm2)) + ' pontos');
    disp('  Irradiância máx: ' + string(max(G_wm2)) + ' W/m²');
    disp('  Temperatura méd: ' + string(mean(T_celsius)) + ' °C');

endfunction


function [G_sel, T_sel, tempo_sel] = selecionar_periodo(tempo_h, G_wm2, T_celsius, dia_inicio, n_dias)
    // Seleciona um período de N dias a partir de um dia específico
    //
    // Entradas:
    //   tempo_h, G_wm2, T_celsius - Dados completos
    //   dia_inicio - Dia do ano (1 = 1º de janeiro)
    //   n_dias     - Número de dias a selecionar
    //
    // Saídas:
    //   G_sel, T_sel, tempo_sel - Dados do período selecionado

    hora_inicio = (dia_inicio - 1) * 24 + 1;
    hora_fim = hora_inicio + n_dias * 24 - 1;

    hora_fim = min(hora_fim, length(G_wm2));

    G_sel = G_wm2(hora_inicio:hora_fim);
    T_sel = T_celsius(hora_inicio:hora_fim);
    tempo_sel = (0:(length(G_sel)-1));  // Horas relativas

    disp('  Período selecionado: dia ' + string(dia_inicio) + ...
         ' a dia ' + string(dia_inicio + n_dias - 1));
    disp('  ' + string(length(G_sel)) + ' horas de dados');
endfunction


function plot_dados_inmet(tempo_h, G_wm2, T_celsius, titulo)
    // Plota os dados meteorológicos do INMET

    scf(9); clf();

    subplot(2,1,1);
    plot(tempo_h, G_wm2, 'r');
    xlabel('Tempo [h]');
    ylabel('Irradiância [W/m²]');
    title(titulo + ' - Irradiância Solar Global');
    xgrid();

    subplot(2,1,2);
    plot(tempo_h, T_celsius, 'b');
    xlabel('Tempo [h]');
    ylabel('Temperatura [°C]');
    title(titulo + ' - Temperatura do Ar');
    xgrid();

endfunction
