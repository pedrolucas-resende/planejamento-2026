WITH 
  -- 1. Snapshot da Frota (Agregado por Mês/Filial)
  base_frota_consolidada AS (
    SELECT
      -- Transformando a data diária no último dia do mês correspondente
      LAST_DAY(DATE_ADD(DATE(atualizacaoData), INTERVAL -1 DAY), MONTH) AS data_referencia,
      cf.pais,
      cf.lugar AS filial,
      
      -- Totais por Categoria Principal (Agregados por mês)
      SUM(CASE WHEN tipo_situacao = 'Alugada' THEN qtd ELSE 0 END) AS total_alugadas,
      SUM(CASE WHEN frota_operacional = 'Frota Operacional' THEN qtd ELSE 0 END) AS total_frota_operacional,
      SUM(CASE WHEN tipo_situacao = 'Pronta para Aluguel' THEN qtd ELSE 0 END) AS total_prontas,
      SUM(CASE WHEN descricao_situacao = 'Em manutencao' THEN qtd ELSE 0 END) AS total_manutencao,
      
      -- Detalhamento: Alugadas por Categoria
      SUM(CASE WHEN tipo_situacao = 'Alugada' AND categoria_branch_config_tipo_moto = '0km' THEN qtd ELSE 0 END) AS alugadas_0km,
      SUM(CASE WHEN tipo_situacao = 'Alugada' AND categoria_branch_config_tipo_moto = 'Semi' THEN qtd ELSE 0 END) AS alugadas_semi,
      SUM(CASE WHEN tipo_situacao = 'Alugada' AND categoria_branch_config_tipo_moto = 'Usada' THEN qtd ELSE 0 END) AS alugadas_usadas,
      
      -- Detalhamento: Frota Operacional
      SUM(CASE WHEN frota_operacional = 'Frota Operacional' AND moto_0km = '0km' AND tipo_situacao != 'Alugada' THEN qtd ELSE 0 END) AS frota_op_0km,
      SUM(CASE WHEN frota_operacional = 'Frota Operacional' AND moto_0km = 'Semi' AND tipo_situacao != 'Alugada' THEN qtd ELSE 0 END) AS frota_op_semi,
      SUM(CASE WHEN frota_operacional = 'Frota Operacional' AND moto_0km = 'Usada' AND tipo_situacao != 'Alugada' THEN qtd ELSE 0 END) AS frota_op_usada,

      -- Detalhamento: Prontas por Categoria
      SUM(CASE WHEN tipo_situacao = 'Pronta para Aluguel' AND moto_0km = '0km' THEN qtd ELSE 0 END) AS prontas_0km,
      SUM(CASE WHEN tipo_situacao = 'Pronta para Aluguel' AND moto_0km = 'Semi' THEN qtd ELSE 0 END) AS prontas_semi,
      SUM(CASE WHEN tipo_situacao = 'Pronta para Aluguel' AND moto_0km = 'Usada' THEN qtd ELSE 0 END) AS prontas_usada,

      -- Status Específicos e Perdas
      SUM(CASE WHEN tipo_situacao = 'Venda' THEN qtd ELSE 0 END) AS total_venda,
      SUM(CASE WHEN tipo_situacao = 'Venda' AND descricao_situacao IN ('Vendida Minha Mottu', 'Em Transferência Minha Mottu') THEN qtd ELSE 0 END) AS venda_minha_mottu,
      SUM(CASE WHEN tipo_situacao = 'Perda Total' THEN qtd ELSE 0 END) AS total_perda_total,
      SUM(CASE WHEN tipo_situacao = 'Perdida/Roubo' THEN qtd ELSE 0 END) AS total_roubo,
      SUM(CASE WHEN tipo_situacao = 'Indisponível' AND descricao_situacao = 'Apropriacao Indebita' THEN qtd ELSE 0 END) AS total_apropriacao,
      
      -- Logística 0km
      SUM(CASE WHEN descricao_situacao = 'Recebida 0km' THEN qtd ELSE 0 END) AS recebidas_0km,
      SUM(CASE WHEN tipo_situacao = 'Em transito 0km' THEN qtd ELSE 0 END) AS transito_0km
    FROM `dm-mottu-aluguel.exp_frota.frota_historico_agrupado` t
    LEFT JOIN `dm-mottu-aluguel.exp_atendimentos.cadastro_filiais` cf ON cf.lugar = t.filial
    WHERE t.pais = 'Brasil' AND cf.terceiro = 0
    GROUP BY 1, 2, 3
  ),

  -- 2. Movimentação Mensal
  movimentacao_faturada AS (
    SELECT
      LAST_DAY(DATE(data_movimentacao), MONTH) AS mes_referencia,
      filial_resultante AS filial,
      COUNT(DISTINCT veiculoId) AS qtd_faturada_mes
    FROM `dm-mottu-aluguel.exp_frota.veiculo_movimentacao_situacao`
    WHERE situacao_anterior_id = 0
    GROUP BY ALL
  ),

  -- 3. Produção e Manutenção
  produtividade_mecanica AS (
    SELECT
      m.filial,
      LAST_DAY(DATE(m.data_finalizacao), MONTH) AS mes_referencia,
      COUNT(CASE WHEN m.tipo_manutencao = 'Interno' THEN m.manutencao_id END) AS qtd_manutencoes_internas,
      COUNT(CASE WHEN m.tipo_manutencao != 'Interno' THEN m.manutencao_id END) AS qtd_manutencoes_cliente,
      AVG(mec.qtd_mecanicos_rampa_total) AS media_mec_total,
      AVG(mec.qtd_mecanicos_na_rampa) AS media_mec_na_rampa
    FROM `dm-mottu-aluguel.man_operacao.manutencoes_agrupadas` m
    LEFT JOIN `dm-mottu-aluguel.exp_frota.indicadores_diarios_filiais` mec 
      ON m.filial = mec.filial 
      AND LAST_DAY(DATE(m.data_finalizacao), MONTH) = LAST_DAY(DATE(mec.data_valor), MONTH)
    WHERE DATE(m.data_finalizacao) > '2025-01-01'
    GROUP BY ALL
  ),

  -- 4. Vendas/Demanda
  demanda_vendas AS (
    SELECT
      LAST_DAY(pagamentoData, MONTH) AS mes_referencia,
      lugar AS filial,
      COUNT(CASE WHEN tipo_moto_km = '0km' THEN locacaoId END) AS vendas_0km,
      COUNT(CASE WHEN tipo_moto_km = 'Semi' THEN locacaoId END) AS vendas_semi,
      COUNT(CASE WHEN tipo_moto_km = 'Usada' THEN locacaoId END) AS vendas_usada
    FROM `dm-mottu-aluguel.grw_aquisicao.vendas`
    WHERE pagamentoData >= '2025-01-01'
    GROUP BY ALL
  ),

  -- 5. Cadastro e Segmentação Geográfica
  segmentacao_filiais AS (
    SELECT
      lugar AS filial,
      cidade,
      regiao_ibge AS regiao,
      estado,
      pais,
      terceiro,
      populacao_cidade,
      NTILE(5) OVER (ORDER BY populacao_cidade) AS populacao_percentil
    FROM `dm-mottu-aluguel.exp_atendimentos.cadastro_filiais`
    WHERE populacao_cidade IS NOT NULL
  )

-- 6. Select Final
SELECT
  f.*,
  mov.qtd_faturada_mes,
  v.vendas_0km,
  v.vendas_semi,
  v.vendas_usada,
  p.qtd_manutencoes_internas,
  p.qtd_manutencoes_cliente,
  p.media_mec_total,
  p.media_mec_na_rampa,
  
  CASE s.populacao_percentil
    WHEN 1 THEN 'D' WHEN 2 THEN 'C' WHEN 3 THEN 'B' WHEN 4 THEN 'A' WHEN 5 THEN 'S'
  END AS populacao_cluster,

  CASE 
    WHEN s.pais = 'México' THEN 'México'
    WHEN s.regiao = 'Sudeste' AND s.cidade = 'São Paulo' THEN 'São Paulo (Capital)'
    WHEN s.regiao = 'Sudeste' AND s.cidade = 'Rio de Janeiro' THEN 'Rio de Janeiro (Capital)'
    ELSE s.regiao
  END AS regiao_consolidada,

  CASE 
    WHEN s.populacao_percentil >= 5 THEN 'Megalópole'
    WHEN s.populacao_percentil >= 4 THEN 'Metrópole'
    WHEN s.populacao_percentil >= 3 THEN 'Centro Regional'
    ELSE 'Interior'
  END AS classificacao_urbana

FROM base_frota_consolidada f
LEFT JOIN movimentacao_faturada mov ON f.data_referencia = mov.mes_referencia AND f.filial = mov.filial
LEFT JOIN demanda_vendas v ON f.data_referencia = v.mes_referencia AND f.filial = v.filial
LEFT JOIN produtividade_mecanica p ON f.data_referencia = p.mes_referencia AND f.filial = p.filial
LEFT JOIN segmentacao_filiais s ON f.filial = s.filial

WHERE f.data_referencia BETWEEN '2025-03-01' AND '2026-03-31'
ORDER BY f.data_referencia DESC, f.filial;
