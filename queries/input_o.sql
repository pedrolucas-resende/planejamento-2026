WITH
  tudo_eop AS (
    SELECT
      DATE_SUB(DATE(atualizacaoData), INTERVAL 1 DAY) AS dataValor,
      cf.pais,
      cf.lugar AS filial,
      SUM(
        CASE
          WHEN tipo_situacao = 'Alugada' THEN qtd
          ELSE 0
        END
      ) AS alugadas_total,
      SUM(
        CASE
          WHEN tipo_situacao = 'Alugada'
            AND categoria_branch_config_tipo_moto = '0km' THEN qtd
          ELSE 0
        END
      ) AS alugadas_0km,
      SUM(
        CASE
          WHEN tipo_situacao = 'Alugada'
            AND categoria_branch_config_tipo_moto = 'Semi' THEN qtd
          ELSE 0
        END
      ) AS alugadas_semi,
      SUM(
        CASE
          WHEN tipo_situacao = 'Alugada'
            AND categoria_branch_config_tipo_moto = 'Usada' THEN qtd
          ELSE 0
        END
      ) AS alugadas_usada,
      SUM(
        CASE
          WHEN frota_operacional = 'Frota Operacional' THEN qtd
          ELSE 0
        END
      ) AS frota_op_total,
      SUM(
        CASE
          WHEN frota_operacional = 'Frota Operacional'
            AND moto_0km = '0km'
            AND tipo_situacao != 'Alugada' THEN qtd
          ELSE 0
        END
      ) AS frota_op_0km,
      SUM(
        CASE
          WHEN frota_operacional = 'Frota Operacional'
            AND moto_0km = 'Semi'
            AND tipo_situacao != 'Alugada' THEN qtd
          ELSE 0
        END
      ) AS frota_op_semi,
      SUM(
        CASE
          WHEN frota_operacional = 'Frota Operacional'
            AND moto_0km = 'Usada'
            AND tipo_situacao != 'Alugada' THEN qtd
          ELSE 0
        END
      ) AS frota_op_usada,
      SUM(
        CASE
          WHEN tipo_situacao = 'Pronta para Aluguel' THEN qtd
          ELSE 0
        END
      ) AS pronta_total,
      SUM(
        CASE
          WHEN tipo_situacao = 'Pronta para Aluguel'
            AND moto_0km = '0km' THEN qtd
          ELSE 0
        END
      ) AS pronta_0km,
      SUM(
        CASE
          WHEN tipo_situacao = 'Pronta para Aluguel'
            AND moto_0km = 'Semi' THEN qtd
          ELSE 0
        END
      ) AS pronta_semi,
      SUM(
        CASE
          WHEN tipo_situacao = 'Pronta para Aluguel'
            AND moto_0km = 'Usada' THEN qtd
          ELSE 0
        END
      ) AS pronta_usada,
      SUM(
        CASE
          WHEN descricao_situacao = 'Em manutencao' THEN qtd
          ELSE 0
        END
      ) AS manutencao_total,
      SUM(
        CASE
          WHEN descricao_situacao = 'Em manutencao'
            AND moto_0km = '0km' THEN qtd
          ELSE 0
        END
      ) AS manutencao_0km,
      SUM(
        CASE
          WHEN descricao_situacao = 'Em manutencao'
            AND moto_0km = 'Semi' THEN qtd
          ELSE 0
        END
      ) AS manutencao_semi,
      SUM(
        CASE
          WHEN descricao_situacao = 'Em manutencao'
            AND moto_0km = 'Usada' THEN qtd
          ELSE 0
        END
      ) AS manutencao_usada,
      SUM(
        CASE
          WHEN descricao_situacao = 'Em transito 0km' THEN qtd
          ELSE 0
        END
      ) AS transito_0km_total,
      SUM(
        CASE
          WHEN tipo_situacao = 'Motos 0km' THEN qtd
          ELSE 0
        END
      ) AS fabrica_0km_total,
      SUM(
        CASE
          WHEN tipo_situacao = 'Administrativo' THEN qtd
          ELSE 0
        END
      ) AS administrativo_total,
      SUM(
        CASE
          WHEN tipo_situacao = 'Venda' THEN qtd
          ELSE 0
        END
      ) AS venda_total,
      SUM(
        CASE
          WHEN tipo_situacao = 'Venda'
            AND descricao_situacao IN ('Vendida Minha Mottu', 'Em Transferência Minha Mottu') THEN qtd
          ELSE 0
        END
      ) AS venda_mm,
      SUM(
        CASE
          WHEN tipo_situacao = 'Venda'
            AND descricao_situacao NOT IN ('Vendida Minha Mottu', 'Em Transferência Minha Mottu', 'Pronta no Leilão') THEN qtd
          ELSE 0
        END
      ) AS venda_direta_doacao,
      SUM(
        CASE
          WHEN tipo_situacao = 'Venda'
            AND descricao_situacao IN ('Pronta no Leilão') THEN qtd
          ELSE 0
        END
      ) AS venda_ag_leilao,
      SUM(
        CASE
          WHEN tipo_situacao = 'Perda Total' THEN qtd
          ELSE 0
        END
      ) AS perda_total,
      SUM(
        CASE
          WHEN tipo_situacao = 'Perdida/Roubo' THEN qtd
          ELSE 0
        END
      ) AS roubada_total,
      SUM(
        CASE
          WHEN tipo_situacao = 'Indisponível'
            AND descricao_situacao IN ('Transito entre agencias', 'Na rua recolhida') THEN qtd
          ELSE 0
        END
      ) AS transito_entre_ag_total,
      SUM(
        CASE
          WHEN tipo_situacao = 'Indisponível'
            AND descricao_situacao NOT IN (
              'Em manutencao',
              'Em transito 0km',
              'Recebida 0km',
              'Transito entre agencias'
            ) THEN qtd
          ELSE 0
        END
      ) AS indisponivel_total,
      SUM(
        CASE
          WHEN tipo_situacao = 'Indisponível'
            AND descricao_situacao = 'Apreendida/Patio' THEN qtd
          ELSE 0
        END
      ) AS apreendida_total,
      SUM(
        CASE
          WHEN tipo_situacao = 'Indisponível'
            AND descricao_situacao = 'Apropriacao Indebita' THEN qtd
          ELSE 0
        END
      ) AS apropriacao_total,
      SUM(
        CASE
          WHEN tipo_situacao = 'Indisponível'
            AND descricao_situacao NOT IN (
              'Em manutencao',
              'Em transito 0km',
              'Recebida 0km',
              'Transito entre agencias',
              'Na rua recolhida',
              'Apropriacao Indebita',
              'Apreendida/Patio'
            ) THEN qtd
          ELSE 0
        END
      ) AS indisponiveis_regulatorio_total,
      SUM(
        CASE
          WHEN descricao_situacao = 'Recebida 0km' THEN qtd
          ELSE 0
        END
      ) AS recebida_0km,
      SUM(
        CASE
          WHEN tipo_situacao = 'Em transito 0km' THEN qtd
          ELSE 0
        END
      ) AS transito_0km
    FROM
      `dm-mottu-aluguel.exp_frota.frota_historico_agrupado` t
    LEFT JOIN
      `dm-mottu-aluguel.exp_atendimentos.cadastro_filiais` cf
      ON cf.lugar = t.filial
WHERE
  (
    -- Meses anteriores: apenas o último dia
    DATE_TRUNC(DATE(atualizacaoData), MONTH) < DATE_TRUNC(CURRENT_DATE(), MONTH)
    AND DATE(atualizacaoData) = LAST_DAY(DATE(atualizacaoData), MONTH)
  )
  OR
  (
    -- Mês atual: todos os dias disponíveis
    DATE_TRUNC(DATE(atualizacaoData), MONTH) = DATE_TRUNC(CURRENT_DATE(), MONTH)
  )
    GROUP BY ALL
  ),
  intra_mes AS (
    SELECT
      LAST_DAY(DATE(data_movimentacao), MONTH) AS dataValor,
      filial_resultante AS filial,
      COUNT(DISTINCT veiculoId) AS qtd_faturada_mes
    FROM
      `dm-mottu-aluguel.exp_frota.veiculo_movimentacao_situacao` t
    WHERE
      situacao_anterior_id = 0
    GROUP BY ALL
    ORDER BY
      1 DESC
  ),
  producao_mes AS (
    SELECT
      LAST_DAY(DATE(criacaoData), MONTH) AS mes,
      lugar_nome AS filial,
      pais_filial,
      COUNT(id) AS qtd_produzidas
    FROM
      `dm-mottu-aluguel.exp_frota.frota_atual` t
    LEFT JOIN
      `dm-mottu-aluguel.exp_atendimentos.cadastro_filiais` cf
      ON cf.lugar = t.lugar_nome
    WHERE
      terceiro = 0
    GROUP BY ALL
  ),
  pendencias_breakdown AS (
    SELECT
      DATE_ADD(DATE(atualizacaoData), INTERVAL -1 DAY) AS mes,
      f.lugar_nome AS filial,
      COUNT(f.id) AS total_restricoes,
      t.descricao
    FROM
      `dm-mottu-aluguel.exp_frota.frota_historico` f
    LEFT JOIN
      `dm-mottu-aluguel.flt_multas.restricoes_sit_pendencias` t
      ON f.id = t.veiculoId
        AND f.atualizacaoData >= DATE(t.criacaoData)
        AND (
          DATE(f.atualizacaoData) < DATE(t.delecaoData)
          OR delecaoData IS NULL
        )
    WHERE
      DATE(atualizacaoData) = DATE_TRUNC(DATE(atualizacaoData), MONTH)
      AND f.situacao_id IN (1490)
    GROUP BY ALL
  ),
  disponibilidade AS (
    SELECT
      1
  ),
  producao AS (
    WITH
      mecanicos AS (
        SELECT
          filial,
          LAST_DAY(DATE(data_valor), MONTH) AS mes,
          AVG(qtd_mecanicos_rampa_total) AS mec_total,
          AVG(qtd_mecanicos_que_bateram_ponto) AS mec_presentes,
          AVG(qtd_mecanicos_na_rampa) AS mec_na_rampa
        FROM
          `dm-mottu-aluguel.exp_frota.indicadores_diarios_filiais`
        WHERE
          data_valor > '2026-01-01'
        GROUP BY ALL
      ),
      manu AS (
        SELECT
          LAST_DAY(DATE(data_finalizacao), MONTH) AS mes,
          COUNT(
            CASE
              WHEN tipo_manutencao = 'Interno' THEN manutencao_id
            END
          ) AS qtd_internas,
          COUNT(
            CASE
              WHEN tipo_manutencao != 'Interno' THEN manutencao_id
            END
          ) AS qtd_cliente,
          filial
        FROM
          `dm-mottu-aluguel.man_operacao.manutencoes_agrupadas` m
        GROUP BY ALL
      )
    SELECT
      m.*,
      mec.mec_total,
      mec.mec_na_rampa,
      mec.mec_presentes
    FROM
      manu m
    LEFT JOIN
      mecanicos mec
      ON mec.mes = m.mes
        AND mec.filial = m.filial
  ),
  demanda AS (
    SELECT
      LAST_DAY(pagamentoData, MONTH) AS mes,
      COUNT(
        CASE
          WHEN tipo_moto_km = '0km' THEN locacaoId
          ELSE NULL
        END
      ) AS qtd_vendas_0km,
      COUNT(
        CASE
          WHEN tipo_moto_km = 'Semi' THEN locacaoId
          ELSE NULL
        END
      ) AS qtd_vendas_semi,
      COUNT(
        CASE
          WHEN tipo_moto_km = 'Usada' THEN locacaoId
          ELSE NULL
        END
      ) AS qtd_vendas_usada,
      lugar AS filial
    FROM
      `dm-mottu-aluguel.grw_aquisicao.vendas`
    GROUP BY ALL
  ),
  auxiliar_budget AS (
    SELECT
      1
  ),
  dados_regionais AS (
    SELECT
      lugarId,
      lugar AS filial,
      cidade,
      regiao_ibge AS regiao,
      estado,
      pais,
      populacao_cidade AS populacao,
      terceiro
    FROM
      `exp_atendimentos.cadastro_filiais`
  ),
  clustered AS (
    SELECT
      *,
      NTILE(5) OVER (
        ORDER BY populacao
      ) AS populacao_percentil
    FROM
      dados_regionais
    WHERE
      populacao IS NOT NULL
  )
SELECT
  t.*,
  i.qtd_faturada_mes,
  qtd_produzidas,
  d.qtd_vendas_0km,
  d.qtd_vendas_semi,
  d.qtd_vendas_usada,
  prod.qtd_internas,
  qtd_cliente,
  prod.mec_total,
  prod.mec_presentes,
  prod.mec_na_rampa,
  cl.* EXCEPT (filial, pais),
  CASE cl.populacao_percentil
    WHEN 1 THEN 'D'
    WHEN 2 THEN 'C'
    WHEN 3 THEN 'B'
    WHEN 4 THEN 'A'
    WHEN 5 THEN 'S'
  END AS populacao_cluster,
  CASE
    WHEN cl.pais = 'México' THEN 'México'
    WHEN cl.regiao = 'Sudeste'
      AND (cidade = 'São Paulo') THEN 'São Paulo (Capital)'
    WHEN cl.regiao = 'Sudeste'
      AND (cidade = 'Rio de Janeiro') THEN 'Rio de Janeiro (Capital)'
    ELSE cl.regiao
  END AS regiao_consolidada,
  CASE
    WHEN cl.terceiro = 1 THEN 'ASP'
    WHEN cl.terceiro = 0 THEN 'Filial Mottu'
    ELSE 'Outros'
  END AS modelo_operacao,
  CASE
    WHEN cidade IN (
      'Aracaju',
      'Belém',
      'Belo Horizonte',
      'Boa Vista',
      'Brasília',
      'Cuiabá',
      'Curitiba',
      'Fortaleza',
      'Goiânia',
      'João Pessoa',
      'Macapá',
      'Maceió',
      'Manaus',
      'Natal',
      'Palmas',
      'Porto Alegre',
      'Porto Velho',
      'Recife',
      'Rio Branco',
      'Rio de Janeiro',
      'Salvador',
      'São Luís',
      'São Paulo',
      'Teresina',
      'Vitória'
    ) THEN 'Capital'
    ELSE 'Interior'
  END AS hierarquia_urbana,
  CASE
    WHEN populacao_percentil >= 90 THEN 'Megalópole'
    WHEN populacao_percentil >= 75 THEN 'Metrópole'
    WHEN populacao_percentil >= 50 THEN 'Capital Regional'
    WHEN populacao_percentil >= 25 THEN 'Centro Sub-regional'
    ELSE 'Centro Local'
  END AS classificacao_populacao
FROM
  tudo_eop t
LEFT JOIN
  intra_mes i
  ON i.dataValor = t.dataValor
    AND t.filial = i.filial
LEFT JOIN
  producao_mes p
  ON t.dataValor = p.mes
    AND p.filial = t.filial
LEFT JOIN
  demanda d
  ON d.mes = t.dataValor
    AND d.filial = t.filial
LEFT JOIN
  producao prod
  ON prod.filial = t.filial
    AND prod.mes = t.dataValor
LEFT JOIN
  clustered cl
  ON cl.filial = t.filial
ORDER BY
  t.dataValor DESC,
  t.pais,
  t.filial
