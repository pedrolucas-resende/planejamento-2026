import pandas as pd
import numpy as np
import os
import warnings
from darts import TimeSeries
from darts.models import LightGBMModel
from darts.utils.timeseries_generation import datetime_attribute_timeseries
from sklearn.preprocessing import LabelEncoder

# Ignorar avisos de convergência e performance para manter o log limpo
warnings.filterwarnings("ignore")

# ============================================================================
# 1. CONFIGURAÇÃO E CARGA
# ============================================================================
INPUT_FILE = "data/csv/filial_produto_vendas_historico.csv"
OUTPUT_FORECAST = "data/csv/forecast_12_meses_mottu.csv"

COVARIAVEIS_OPERACIONAIS = [
    'frota_op_total', 'manutencao_total', 'pronta_total', 
    'mec_total', 'mec_presentes', 'populacao'
]

print(f"📂 Carregando dados históricos para Python 3.12...")
df = pd.read_csv(INPUT_FILE)
df['data'] = pd.to_datetime(df['data'])

# Definindo o Corte de Validação (S&OP Best Practice)
# Treinamos até uma data específica e "escondemos" o restante para testar a precisão
data_maxima = df['data'].max()
DATA_LIMITE_TREINO = data_maxima - pd.DateOffset(months=4)

# Filtro de Recência (Últimos 24 meses para capturar o comportamento atual da Mottu)
data_inicio = df['data'].max() - pd.DateOffset(months=24)
df = df[df['data'] >= data_inicio]

# Estabilização logarítmica para lidar com outliers de vendas
df['vendas_log'] = np.log1p(df['vendas'])

# ============================================================================
# 2. ENCODING CATEGÓRICO (Static Covariates)
# ============================================================================
print("🏷️ Codificando variáveis categóricas...")
le_dict = {}
colunas_para_encode = ['estado', 'cidade', 'filial', 'rank', 'produto', 'hierarquia_urbana']

for col in colunas_para_encode:
    le = LabelEncoder()
    # Garantir que tratamos tudo como string antes do fit
    df[f'{col}_enc'] = le.fit_transform(df[col].astype(str))
    le_dict[col] = le

# ============================================================================
# 3. CRIAÇÃO DAS SÉRIES (Corte Temporal Aplicado)
# ============================================================================
print(f"⏳ Separando treino (até {DATA_LIMITE_TREINO}) e preparando séries...")

lista_target_treino = []
lista_target_full = []
lista_past_covs = []

for (f, p), df_g in df.groupby(['filial', 'produto']):
    df_g = df_g.sort_values('data')
    
    # Static Covariates (Informações que não mudam no tempo)
    static_cols = [f'{c}_enc' for c in colunas_para_encode]
    static_data = df_g[static_cols].iloc[[0]]
    
    # 1. Série Alvo Completa
    target_full = TimeSeries.from_dataframe(
        df_g, 'data', 'vendas_log', freq='ME',
        static_covariates=static_data
    )
    
    # 2. Série de Treino (Corte para Validação)
    target_treino = target_full.drop_after(pd.Timestamp(DATA_LIMITE_TREINO))
    
    # 3. Covariáveis Operacionais (Histórico + Extensão Futura)
    ops_series = TimeSeries.from_dataframe(df_g, 'data', COVARIAVEIS_OPERACIONAIS, freq='ME')
    
    # Extensão de 12 meses para o futuro (repetindo a última foto operacional)
    last_vals = ops_series.values()[-1:] 
    future_dates = pd.date_range(
        start=df_g['data'].max() + pd.offsets.MonthEnd(1), 
        periods=12, 
        freq='ME'
    )
    ops_extension = TimeSeries.from_times_and_values(
        future_dates, np.repeat(last_vals, 12, axis=0), 
        columns=COVARIAVEIS_OPERACIONAIS
    )
    
    ops_full = ops_series.concatenate(ops_extension)
    
    # Componente temporal (Mês)
    month_series = datetime_attribute_timeseries(ops_full, attribute="month", one_hot=False)
    covs_total = ops_full.stack(month_series)
    
    lista_target_treino.append(target_treino.astype(np.float32))
    lista_target_full.append(target_full.astype(np.float32))
    lista_past_covs.append(covs_total.astype(np.float32))

# ============================================================================
# 4. TREINAMENTO (LightGBM Global)
# ============================================================================
print(f"🧠 Treinando modelo com lags de 12 meses...")

modelo = LightGBMModel(
    lags=12,                
    lags_past_covariates=6,  
    output_chunk_length=1,   
    use_static_covariates=True,
    learning_rate=0.05,
    n_estimators=800,
    random_state=42
)

# Treinamos apenas com os dados até a DATA_LIMITE_TREINO
modelo.fit(lista_target_treino, past_covariates=lista_past_covs)

# ============================================================================
# 5. VALIDAÇÃO E MÉTRICAS
# ============================================================================
print("🧪 Validando modelo contra dados reais recentes...")

# Prever o período que "escondemos" para ver o erro real
historical_forecast = modelo.historical_forecasts(
    series=lista_target_full,
    past_covariates=lista_past_covs,
    start=pd.Timestamp(DATA_LIMITE_TREINO),
    forecast_horizon=1,
    retrain=False,
    verbose=False
)

erros_mae = []
for i, h_fcast in enumerate(historical_forecast):
    if h_fcast is None: continue
    # Reverter log para unidades reais (motos)
    real = np.expm1(lista_target_full[i].slice_intersect(h_fcast).values())
    previsto = np.expm1(h_fcast.values())
    erros_mae.append(np.mean(np.abs(real - previsto)))

print(f"📊 Erro Médio (MAE): {np.mean(erros_mae):.2f} motos por filial/mês")

# ============================================================================
# 6. FORECAST OFICIAL (PRÓXIMOS 12 MESES)
# ============================================================================
print("🔮 Gerando projeção oficial para 2026...")

# Agora usamos a série FULL para projetar o futuro real de Março/26 em diante
forecasts = modelo.predict(
    n=12, 
    series=lista_target_full, 
    past_covariates=lista_past_covs
)

# ============================================================================
# 7. EXPORTAÇÃO
# ============================================================================
resultados = []

for i, fcast in enumerate(forecasts):
    vendas_reais = np.expm1(fcast.values().flatten())
    datas = fcast.time_index
    
    static = fcast.static_covariates.iloc[0]
    filial_nome = le_dict['filial'].inverse_transform([int(static['filial_enc'])])[0]
    prod_nome = le_dict['produto'].inverse_transform([int(static['produto_enc'])])[0]
    
    for d, v in zip(datas, vendas_reais):
        resultados.append({
            'mes_referencia': d.date(),
            'filial': filial_nome,
            'produto': prod_nome,
            'venda_estimada': round(max(0, v), 2)
        })

df_final = pd.DataFrame(resultados)
df_final.to_csv(OUTPUT_FORECAST, index=False, encoding='utf-8-sig')

print(f"\n✅ Concluído! Resultado salvo em: {OUTPUT_FORECAST}")
