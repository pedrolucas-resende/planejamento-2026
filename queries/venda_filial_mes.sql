select     LAST_DAY(DATE_ADD(DATE(atualizacaoData), INTERVAL -1 DAY)) as mes,
from `dm-mottu-aluguel.exp_frota.frota_historico_agrupado`
