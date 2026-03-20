import pandas as pd
import numpy as np
import os
import warnings
from darts import TimeSeries
from darts.models import LightGBMModel
from darts.utils.timeseries_generation import datetime_attribute_timeseries
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

# ============================================================================
# 1. CONFIGURAÇÃO E CARGA
# ============================================================================
INPUT_FILE = "data/csv/filial_produto_vendas_historico.csv"
OUTPUT_FORECAST = "data/csv/forecast_12_meses_mottu.csv"

# Colunas operacionais que ajudam a prever a venda (Past Covariates)
COVARIAVEIS_OPERACIONAIS = [
    'frota_op_total', 'manutencao_total', 'pronta_total', 
    'mec_total', 'mec_presentes', 'populacao'
]

print("📂 Carregando dados históricos...")
df = pd.read_csv(INPUT_FILE)
df['data'] = pd.to_datetime(df['data'])

# 1. FILTRO DE RECÊNCIA (Ex: últimos 2 anos)
data_limite = df['data'].max() - pd.DateOffset(months=24)
df = df[df['data'] >= data_limite]
print(f"✂️ Usando dados de {data_limite.date()} até hoje para evitar padrões obsoletos.")

# Estabilização logarítmica: log(x + 1)
df['vendas'] = np.log1p(df['vendas'])

# ============================================================================
# 2. ENCODING CATEGÓRICO (Static Covariates)
# ============================================================================
print("🏷️ Codificando variáveis categóricas...")
le_dict = {}
colunas_para_encode = ['estado', 'cidade', 'filial', 'rank', 'produto', 'hierarquia_urbana']

for col in colunas_para_encode:
    le = LabelEncoder()
    df[f'{col}_enc'] = le.fit_transform(df[col].astype(str))
    le_dict[col] = le

# ============================================================================
# 3. CRIAÇÃO DAS SÉRIES (Correção para Séries Multivariadas)
# ============================================================================
print("⏳ Transformando dados e estendendo covariáveis para o futuro...")
lista_target = []
lista_past_covs = []

for (f, p), df_g in df.groupby(['filial', 'produto']):
    df_g = df_g.sort_values('data')
    
    # 1. Série Alvo (Vendas)
    target_series = TimeSeries.from_dataframe(
        df_g, 'data', 'vendas', freq='ME',
        static_covariates=df_g[[f'{c}_enc' for c in colunas_para_encode]].iloc[[0]]
    )
    
    # 2. Covariáveis Operacionais
    ops_series = TimeSeries.from_dataframe(df_g, 'data', COVARIAVEIS_OPERACIONAIS, freq='ME')
    
    # --- AJUSTE MULTIVARIADO ---
    # Pegamos a última linha de todas as colunas operacionais (shape: 1 x num_colunas)
    last_vals = ops_series.values()[-1:] 
    
    # Criamos as datas dos próximos 12 meses
    future_dates = pd.date_range(
        start=df_g['data'].max() + pd.offsets.MonthEnd(1), 
        periods=12, 
        freq='ME'
    )
    
    # Repetimos essa última linha 12 vezes para o futuro
    future_values = np.repeat(last_vals, 12, axis=0)
    
    ops_extension = TimeSeries.from_times_and_values(
        future_dates, 
        future_values, 
        columns=COVARIAVEIS_OPERACIONAIS
    )
    
    # Junta o histórico real com a projeção futura
    ops_full = ops_series.concatenate(ops_extension)
    
    # 3. Adiciona o componente de mês (calendário)
    month_series = datetime_attribute_timeseries(ops_full, attribute="month", one_hot=False)
    
    # Combina tudo: Operações Estendidas + Mês
    covs_total = ops_full.stack(month_series)
    
    lista_target.append(target_series.astype(np.float32))
    lista_past_covs.append(covs_total.astype(np.float32))

# ============================================================================
# 4. TREINAMENTO DO MODELO ELITE
# ============================================================================
print(f"🧠 Treinando LightGBM Global Model ({len(lista_target)} séries)...")

modelo_elite = LightGBMModel(
    lags=12,                # Olha 12 meses de vendas passadas
    lags_past_covariates=6,  # Olha 6 meses de histórico operacional (mecânicos, frota, etc)
    output_chunk_length=1,   # Previsão passo a passo
    use_static_covariates=True,
    learning_rate=0.05,
    n_estimators=1000,
    random_state=42
)

modelo_elite.fit(lista_target, past_covariates=lista_past_covs)

# ============================================================================
# 5. FORECAST FUTURO (PRÓXIMOS 12 MESES)
# ============================================================================
print("🔮 Gerando previsão para os próximos 12 meses...")
# Agora o modelo tem os dados "futuros" das covariáveis para conseguir prever n=12
forecasts = modelo_elite.predict(
    n=12, 
    series=lista_target, 
    past_covariates=lista_past_covs # Aqui ele já contém o horizonte estendido
)

# 2. BLOCO DE VALIDAÇÃO (Backtest)
# Vamos fingir que não sabemos os últimos 6 meses para testar o modelo
print("🧪 Rodando Backtest para calcular métricas de erro...")
historical_forecast = modelo_elite.historical_forecasts(
    series=lista_target,
    past_covariates=lista_past_covs,
    start=0.7, # Começa a testar após usar 70% dos dados para treino
    forecast_horizon=1,
    stride=1,
    retrain=False,
    verbose=False
)

# Calcula o MAE médio em unidades reais (revertendo o log)
erros_mae = []
for i, h_fcast in enumerate(historical_forecast):
    real = np.expm1(lista_target[i].slice_intersect(h_fcast).values())
    previsto = np.expm1(h_fcast.values())
    erros_mae.append(np.mean(np.abs(real - previsto)))

print(f"📊 MAE Médio do Modelo: {np.mean(erros_mae):.2f} motos por filial/mês")

# ============================================================================
# 6. PÓS-PROCESSAMENTO E EXPORTAÇÃO
# ============================================================================
resultados = []

for i, fcast in enumerate(forecasts):
    # Reverter o log: exp(x) - 1
    vendas_reais = np.expm1(fcast.values().flatten())
    datas = fcast.time_index
    
    # Recuperar metadados da série
    static = fcast.static_covariates.iloc[0]
    filial_nome = le_dict['filial'].inverse_transform([int(static['filial_enc'])])[0]
    prod_nome = le_dict['produto'].inverse_transform([int(static['produto_enc'])])[0]
    
    for d, v in zip(datas, vendas_reais):
        resultados.append({
            'mes_referencia': d,
            'filial': filial_nome,
            'produto': prod_nome,
            'venda_estimada': max(0, round(v, 2))
        })

df_final = pd.DataFrame(resultados)
df_final.to_csv(OUTPUT_FORECAST, index=False, encoding='utf-8-sig')

print(f"\n✅ Forecast concluído com sucesso!")
print(f"💾 Arquivo gerado: {OUTPUT_FORECAST}")
