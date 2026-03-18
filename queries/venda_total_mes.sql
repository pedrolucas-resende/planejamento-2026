SELECT 
    LAST_DAY(DATE_ADD(DATE(atualizacaoData), INTERVAL -1 DAY)) as mes,
    SUM(CASE WHEN tipo_situacao = 'Venda' THEN qtd ELSE 0 END) as venda_total,
    "Realizado" as status
FROM `dm-mottu-aluguel.exp_frota.frota_historico_agrupado`
GROUP BY 1
-- Usamos HAVING para filtrar após o agrupamento ou uma subquery
HAVING mes < (
    SELECT MAX(LAST_DAY(DATE_ADD(DATE(atualizacaoData), INTERVAL -1 DAY))) 
    FROM `dm-mottu-aluguel.exp_frota.frota_historico_agrupado`
)
ORDER BY 1
