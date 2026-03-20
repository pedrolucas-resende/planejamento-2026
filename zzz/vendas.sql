with tudo_eop as (
 
select
date_add(date(atualizacaoData), interval -1 day )  as dataValor,
cf.pais,
cf.lugar as filial,
sum(case when tipo_situacao = 'Alugada' then qtd else 0 end) as alugadas_total,
sum(case when tipo_situacao = 'Alugada' and categoria_branch_config_tipo_moto = '0km' then qtd else 0 end) as alugadas_0km,
sum(case when tipo_situacao = 'Alugada' and categoria_branch_config_tipo_moto = 'Semi' then qtd else 0 end) as alugadas_semi,
sum(case when tipo_situacao = 'Alugada' and categoria_branch_config_tipo_moto = 'Usada' then qtd else 0 end) as alugadas_usada,
sum(case when frota_operacional = 'Frota Operacional' then qtd else 0 end) as frota_op_total,
sum(case when frota_operacional = 'Frota Operacional' and moto_0km = '0km' and tipo_situacao != 'Alugada' then qtd else 0 end) as frota_op_0km,
sum(case when frota_operacional = 'Frota Operacional' and moto_0km = 'Semi' and tipo_situacao != 'Alugada' then qtd else 0 end) as frota_op_semi,
sum(case when frota_operacional = 'Frota Operacional' and moto_0km = 'Usada' and tipo_situacao != 'Alugada' then qtd else 0 end) as frota_op_usada,
sum(case when tipo_situacao ='Pronta para Aluguel' then qtd else 0 end) as pronta_total,
sum(case when tipo_situacao ='Pronta para Aluguel' and moto_0km = '0km' then qtd else 0 end) as pronta_0km,
sum(case when tipo_situacao ='Pronta para Aluguel' and moto_0km  = 'Semi' then qtd else 0 end) as pronta_semi,
sum(case when tipo_situacao ='Pronta para Aluguel' and moto_0km  = 'Usada' then qtd else 0 end) as pronta_usada,
sum(case when descricao_situacao = 'Em manutencao' then qtd else 0 end) as manutencao_total,
sum(case when descricao_situacao = 'Em manutencao' and moto_0km = '0km' then qtd else 0 end) as manutencao_0km,
sum(case when descricao_situacao = 'Em manutencao' and moto_0km = 'Semi' then qtd else 0 end) as manutencao_semi,
sum(case when descricao_situacao = 'Em manutencao' and moto_0km = 'Usada' then qtd else 0 end) as manutencao_usada,
sum(case when descricao_situacao = 'Em transito 0km' then qtd else 0 end) as transito_0km_total,
sum(case when tipo_situacao = 'Motos 0km' then qtd else 0 end) as fabrica_0km_total,
sum(case when tipo_situacao = 'Administrativo' then qtd else 0 end) as administrativo_total,
sum(case when tipo_situacao = 'Venda' then qtd else 0 end) as venda_total,
sum(case when tipo_situacao = 'Venda' and descricao_situacao in ( 'Vendida Minha Mottu', 'Em Transferência Minha Mottu') then qtd else 0 end) as venda_mm,
sum(case when tipo_situacao = 'Venda' and descricao_situacao not in ( 'Vendida Minha Mottu', 'Em Transferência Minha Mottu' , 'Pronta no Leilão') then qtd else 0 end) as venda_direta_doacao,
sum(case when tipo_situacao = 'Venda' and descricao_situacao in ( 'Pronta no Leilão' ) then qtd else 0 end) as venda_ag_leilao,
sum(case when tipo_situacao = 'Perda Total' then qtd else 0 end) as perda_total,
sum(case when tipo_situacao = 'Perdida/Roubo' then qtd else 0 end) as roubada_total,
sum(case when tipo_situacao = 'Indisponível' and descricao_situacao in ( 'Transito entre agencias' , 'Na rua recolhida' )  then qtd else 0 end) as transito_entre_ag_total,
sum(case when tipo_situacao = 'Indisponível' and descricao_situacao not in ( 'Em manutencao', 'Em transito 0km', 'Recebida 0km', 'Transito entre agencias' ) then qtd else 0 end) as indisponivel_total,
sum(case when tipo_situacao = 'Indisponível' and descricao_situacao = 'Apreendida/Patio' then qtd else 0 end) as apreendida_total,
sum(case when tipo_situacao = 'Indisponível' and descricao_situacao = 'Apropriacao Indebita' then qtd else 0 end) as apropriacao_total,
sum(case when tipo_situacao = 'Indisponível' and descricao_situacao not in ( 'Em manutencao', 'Em transito 0km', 'Recebida 0km', 'Transito entre agencias' , 'Na rua recolhida', 'Apropriacao Indebita' , 'Apreendida/Patio' ) then qtd else 0 end) as indisponiveis_regulatorio_total,
--- Tem uma manguita aqui, Alugada ( clientes suspensos com moto mas que nao entraram em apropri ainda), Vendida a seguradora, 'Pronta para venda' e 1 moto venda iniciada
sum(case when descricao_situacao = 'Recebida 0km' then qtd else 0 end) as recebida_0km,
sum(case when tipo_situacao = 'Em transito 0km' then qtd else 0 end) as transito_0km,
from `dm-mottu-aluguel.exp_frota.frota_historico_agrupado` t
left join `dm-mottu-aluguel.exp_atendimentos.cadastro_filiais` cf on cf.lugar = t.filial
where date(atualizacaoData) = DATE_TRUNC(date(atualizacaoData),month)
group by all
 
) , intra_mes as (
 
--- motos criadas no mes pela fabrica
--- motos expedidas pela fabrica
--- motos fabricadas pelo mexico
 
select last_day(date(data_movimentacao), month) as dataValor,
filial_resultante as filial,
count(distinct  veiculoId) as qtd_faturada_mes,
 
from `dm-mottu-aluguel.exp_frota.veiculo_movimentacao_situacao` t
where situacao_anterior_id  = 0
 
 
 
group by all
order by 1 desc
 
 
 
 
 
 
), producao_mes as (
 
select
last_day(date(criacaoData), month) as mes ,
lugar_nome as filial,
pais_filial,
count(id) as qtd_produzidas
from `dm-mottu-aluguel.exp_frota.frota_atual` t
left join `dm-mottu-aluguel.exp_atendimentos.cadastro_filiais` cf on cf.lugar = t.lugar_nome
where pais = 'Brasil'
 
group by all
 
 
---- Cohort mes producao x saida da frota -
 
), pendencias_breakdown as (
 
select date_add(date(atualizacaoData), interval -1 day) as mes,
f.lugar_nome as filial,
count(f.id) as total_restricoes,
t.descricao
from `dm-mottu-aluguel.exp_frota.frota_historico` f
left join `dm-mottu-aluguel.flt_multas.restricoes_sit_pendencias` t on f.id = t.veiculoId  and f.atualizacaoData >= date(t.criacaoData) and (date(f.atualizacaoData) < date(t.delecaoData) or delecaoData is null )
where
date(atualizacaoData) = date_Trunc(date(atualizacaoData) ,month)
and f.situacao_id in (  1490 )
group by all
  
), disponibilidade as (
 
select 1
 
), producao as (
 
with mecanicos  as (
 
select
filial,
last_day(date(data_valor), month) as mes,
 
avg (qtd_mecanicos_rampa_total) as mec_total,
avg (qtd_mecanicos_que_bateram_ponto) as mec_presentes,
avg(qtd_mecanicos_na_rampa) as mec_na_rampa
from `dm-mottu-aluguel.exp_frota.indicadores_diarios_filiais`
where data_valor > "2026-01-01"
group by all
) ,  manu AS (
  SELECT
    last_day(date(data_finalizacao), month) as mes,
    COUNT(case when tipo_manutencao = 'Interno' then manutencao_id end) as qtd_internas,
    COUNT(case when tipo_manutencao != 'Interno' then manutencao_id end) as qtd_cliente,
    filial,
  FROM `dm-mottu-aluguel.man_operacao.manutencoes_agrupadas` m
 
  WHERE DATE(data_finalizacao) > DATE '2025-01-01'
  group by all
)
 
SELECT
  m.*, mec.mec_total, mec.mec_na_rampa, mec.mec_presentes
FROM manu m
left join mecanicos mec on mec.mes = m.mes and mec.filial = m.filial
 
),
 
demanda as  (
 
  select last_day(pagamentoData, month) as mes,
  count(case when tipo_moto_km = '0km' then locacaoId else null end) as qtd_vendas_0km,
    count(case when tipo_moto_km = 'Semi' then locacaoId else null end) as qtd_vendas_semi,
  count(case when tipo_moto_km = 'Usada' then locacaoId else null end) as qtd_vendas_usada,
  lugar as filial
  from `dm-mottu-aluguel.grw_aquisicao.vendas`
  where pagamentoData>= '2025-01-01'
  group by all
 
 
 
), auxiliar_budget as (
 
  select 1
 
 
), final as (
select t.*,  i.qtd_faturada_mes, qtd_produzidas, d.qtd_vendas_0km, d.qtd_vendas_semi, d.qtd_vendas_usada, prod.qtd_internas, qtd_cliente, prod.mec_total, prod.mec_presentes, prod.mec_na_rampa
from tudo_eop t
left join intra_mes i on i.dataValor = t.dataValor and t.filial = i.filial
left join producao_mes p on t.dataValor = p.mes and p.filial = t.filial
left join demanda d on d.mes = t.dataValor and d.filial = t.filial
left join producao prod on prod.filial = t.filial and prod.mes = t.dataValor
)

select * from final order by dataValor desc
