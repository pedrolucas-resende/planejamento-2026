import pandas as pd
import numpy as np
from darts import TimeSeries
from darts.models import LightGBMModel
from darts.dataprocessing.transformers import Scaler
from darts.metrics import mae
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings("ignore")

# 1. CARREGAMENTO
df = pd.read_csv("data/csv/filial_produto_vendas_historico.csv")
df['data'] = pd.to_datetime(df['data'])

# 2. ENGENHARIA DE LOG (Para estabilizar a escala)
# Usamos log1p (log de x+1) para não dar erro com vendas zero
df['vendas'] = np.log1p(df['vendas'])

# 3. ENCODING CATEGÓRICO
colunas_categoricas = ['estado', 'cidade', 'filial', 'rank', 'produto']
for col in colunas_categoricas:
    df[col + '_encoded'] = LabelEncoder().fit_transform(df[col].astype(str))

# 4. CRIAÇÃO DAS SÉRIES
lista_series = []
for (f, p), df_g in df.groupby(['filial', 'produto']):
    if df_g['vendas'].sum() == 0: continue
    
    # Criar a série com Covariáveis Estáticas
    serie = TimeSeries.from_dataframe(
        df_g.sort_values('data'), 'data', 'vendas', freq='ME',
        static_covariates=df_g[['estado_encoded', 'rank_encoded', 'populacao', 'produto_encoded']].iloc[[0]]
    )
    lista_series.append(serie.astype(np.float32))

# 5. ADICIONAR COVARIÁVEIS DE CALENDÁRIO (Mês, Ano)
# O Darts cria isso automaticamente para séries mensais
from darts.utils.timeseries_generation import datetime_attribute_timeseries
series_exogenas = [datetime_attribute_timeseries(s, attribute="month", one_hot=True) for s in lista_series]

# 6. DIVISÃO (TREINO/VAL)
HORIZONTE = 7
series_treino = [s[:-HORIZONTE] for s in lista_series if len(s) > HORIZONTE + 6]
series_val = [s[-HORIZONTE:] for s in lista_series if len(s) > HORIZONTE + 6]
# Precisamos das exógenas alinhadas
exog_treino = [s[:-HORIZONTE] for s in series_exogenas if len(s) > HORIZONTE + 6]

# 7. MODELO REFINADO
modelo_elite = LightGBMModel(
    lags=6,
    lags_past_covariates=3, # Olha 3 meses de meses passados
    output_chunk_length=HORIZONTE,
    learning_rate=0.05,    # Mais lento e preciso
    n_estimators=500,      # Mais árvores para aprender detalhes
    use_static_covariates=True
)

print("🧠 Treinando Modelo Elite...")
modelo_elite.fit(series_treino, past_covariates=exog_treino)

# 8. PREVISÃO E REVERSÃO DO LOG
preds = modelo_elite.predict(n=HORIZONTE, series=series_treino, past_covariates=series_exogenas)

# Reverter log (exp - 1) para voltar a números de motos reais
total_mae = []
for r, p in zip(series_val, preds):
    real_motos = np.expm1(r.values())
    pred_motos = np.expm1(p.values())
    total_mae.append(np.mean(np.abs(real_motos - pred_motos)))

print(f"\n🎯 NOVO MAE REFINADO: {np.mean(total_mae):.2f} motos")
