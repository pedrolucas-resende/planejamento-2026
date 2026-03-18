WITH 
    -- 1. Meses que já aconteceram (Histórico)
    meses_historico AS (
        SELECT DISTINCT
            LAST_DAY(DATE_ADD(DATE(atualizacaoData), INTERVAL -1 DAY)) as mes
        FROM `dm-mottu-aluguel.exp_frota.frota_historico_agrupado`
        WHERE LAST_DAY(DATE_ADD(DATE(atualizacaoData), INTERVAL -1 DAY)) < LAST_DAY(DATE_ADD(CURRENT_DATE(), INTERVAL -1 DAY))
    ),
    
    -- 2. Gerar próximos 12 meses a partir do mês atual
    meses_futuros AS (
        SELECT LAST_DAY(mes) as mes
        FROM UNNEST(
            GENERATE_DATE_ARRAY(
                DATE_TRUNC(CURRENT_DATE(), MONTH), 
                DATE_ADD(DATE_TRUNC(CURRENT_DATE(), MONTH), INTERVAL 11 MONTH), 
                INTERVAL 1 MONTH
            )
        ) as mes
    ),
    
    -- 3. Unificar todos os meses (passado + futuro)
    todos_meses AS (
        SELECT mes FROM meses_historico
        UNION DISTINCT
        SELECT mes FROM meses_futuros
    ),
    
    filiais AS (
        SELECT DISTINCT filial 
        FROM `dm-mottu-aluguel.exp_frota.frota_historico_agrupado`
        WHERE filial IS NOT NULL
    ),
    
    -- 4. Grade mestre com TODOS os meses e TODAS as filiais
    grade_mestre AS (
        SELECT m.mes, f.filial
        FROM todos_meses m
        CROSS JOIN filiais f
    ),
    
    vendas AS (
        SELECT
            LAST_DAY(DATE_ADD(DATE(atualizacaoData), INTERVAL -1 DAY)) as mes,
            filial,
            SUM(CASE WHEN tipo_situacao = 'Venda' THEN qtd ELSE 0 END) as venda_total
        FROM `dm-mottu-aluguel.exp_frota.frota_historico_agrupado`
        GROUP BY 2, 1
    )

SELECT
    g.mes,
    g.filial,
    COALESCE(v.venda_total, 0) as venda_total,
    -- Status dinâmico: se a data for maior ou igual ao mês atual, é previsão
    CASE 
        WHEN g.mes >= LAST_DAY(DATE_ADD(CURRENT_DATE(), INTERVAL -1 DAY)) THEN 'Previsão'
        WHEN v.venda_total IS NULL THEN 'Vazio' 
        ELSE 'Realizado' 
    END as status
FROM grade_mestre g
LEFT JOIN vendas v ON g.mes = v.mes AND g.filial = v.filial
ORDER BY g.filial, g.mes
