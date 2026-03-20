"""
Script #9: Testar Modelos Darts com Backtesting
Data, Filial, Produto, Melhor_Modelo, MAPE, MAE, RMSE

Estrutura:
- Carrega histórico de dados (até data_limite)
- Para cada Filial + Produto:
  - Determina categoria de maturidade
  - Testa modelos recomendados com Darts
  - Treino: até data_limite | Teste: data_limite até data_maxima
- Calcula MAPE, MAE, RMSE
- Retorna melhor modelo por Filial + Produto
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings

# Imports Darts
from darts import TimeSeries
from darts.models import (
    ExponentialSmoothing, ARIMA, Prophet
)
from darts.metrics import mape, mae, rmse

# Tentar importar modelos opcionais
try:
    from darts.models import Theta
    THETA_AVAILABLE = True
except ImportError:
    THETA_AVAILABLE = False

try:
    from darts.models import SeasonalNaiveModel
    SEASONAL_NAIVE_AVAILABLE = True
except ImportError:
    SEASONAL_NAIVE_AVAILABLE = False

warnings.filterwarnings('ignore')

# ============================================================================
# 1. CONFIGURAÇÃO
# ============================================================================

INPUT_HISTORICO = "data/csv/filial_produto_vendas_historico.csv"
INPUT_MATURIDADE = "data/csv/filial_produto_vendas_historico_maturidade.csv"
OUTPUT_RESULTADOS = "data/csv/resultado_melhor_modelo.csv"

# Mapping de categoria -> modelos a testar
MODELOS_POR_CATEGORIA = {
    'Recém-aberta': ['ExponentialSmoothing'],
    'Jovem': ['ExponentialSmoothing', 'Prophet'],
    'Intermediária': ['ExponentialSmoothing', 'Prophet', 'ARIMA'],
    'Madura': ['ARIMA', 'Prophet', 'ExponentialSmoothing']
}

# Adicionar modelos opcionais se disponíveis
if SEASONAL_NAIVE_AVAILABLE:
    MODELOS_POR_CATEGORIA['Intermediária'].insert(0, 'SeasonalNaiveModel')
    MODELOS_POR_CATEGORIA['Madura'].insert(0, 'SeasonalNaiveModel')

if THETA_AVAILABLE:
    MODELOS_POR_CATEGORIA['Madura'].append('Theta')

# ============================================================================
# 2. CARREGAMENTO
# ============================================================================

def load_data():
    """Carrega dados histórico e maturidade"""
    print(f"📁 Carregando dados histórico...")
    df_historico = pd.read_csv(INPUT_HISTORICO)
    df_historico['data'] = pd.to_datetime(df_historico['data'])
    
    print(f"📁 Carregando maturidade...")
    df_maturidade = pd.read_csv(INPUT_MATURIDADE)
    
    print(f"✅ Dados carregados: {len(df_historico)} registros")
    
    return df_historico, df_maturidade

# ============================================================================
# 3. CRIAR TIMESERIES PARA DARTS
# ============================================================================

def criar_timeseries(df_filial_produto):
    """Cria TimeSeries do Darts a partir de DataFrame"""
    try:
        # Garantir que está ordenado por data
        df_filial_produto = df_filial_produto.sort_values('data')
        
        # Criar série temporal
        ts = TimeSeries.from_times_and_values(
            times=df_filial_produto['data'],
            values=df_filial_produto['vendas'].values,
            freq='MS'  # Month Start
        )
        
        return ts
    except Exception as e:
        print(f"⚠️  Erro ao criar TimeSeries: {e}")
        return None

# ============================================================================
# 4. TREINAR E AVALIAR MODELOS
# ============================================================================

def treinar_modelo(ts_treino, modelo_nome):
    """Treina um modelo específico"""
    try:
        if modelo_nome == 'SeasonalNaiveModel':
            if not SEASONAL_NAIVE_AVAILABLE:
                return None
            model = SeasonalNaiveModel(season_length=12)
        elif modelo_nome == 'ExponentialSmoothing':
            model = ExponentialSmoothing()
        elif modelo_nome == 'ARIMA':
            model = ARIMA(p=1, d=1, q=1)
        elif modelo_nome == 'Prophet':
            model = Prophet()
        elif modelo_nome == 'Theta':
            if not THETA_AVAILABLE:
                return None
            model = Theta()
        else:
            return None
        
        # Treinar
        model.fit(ts_treino)
        return model
    
    except Exception as e:
        return None

def fazer_forecast(model, horizonte):
    """Faz forecast com o modelo"""
    try:
        forecast = model.predict(horizonte)
        return forecast
    except Exception as e:
        return None

def calcular_metricas(y_true, y_pred):
    """Calcula MAPE, MAE, RMSE"""
    try:
        mape_valor = mape(y_true, y_pred)
        mae_valor = mae(y_true, y_pred)
        rmse_valor = rmse(y_true, y_pred)
        
        return {
            'mape': float(mape_valor),
            'mae': float(mae_valor),
            'rmse': float(rmse_valor)
        }
    except Exception as e:
        return {'mape': np.inf, 'mae': np.inf, 'rmse': np.inf}

# ============================================================================
# 5. TESTAR FILIAL + PRODUTO
# ============================================================================

def testar_filial_produto(filial, produto, df_historico, df_maturidade, data_limite):
    """Testa todos os modelos para uma filial + produto"""
    
    # Filtrar dados
    df_fp = df_historico[
        (df_historico['filial'] == filial) & 
        (df_historico['produto'] == produto)
    ].copy()
    
    if len(df_fp) < 2:
        return None
    
    # Separar treino e teste
    df_treino = df_fp[df_fp['data'] <= data_limite]
    df_teste = df_fp[df_fp['data'] > data_limite]
    
    if len(df_treino) < 1 or len(df_teste) < 1:
        return None
    
    # Criar TimeSeries
    ts_treino = criar_timeseries(df_treino)
    ts_teste = criar_timeseries(df_teste)
    
    if ts_treino is None or ts_teste is None:
        return None
    
    # Buscar categoria
    df_filial_mat = df_maturidade[df_maturidade['filial'] == filial]
    if len(df_filial_mat) == 0:
        categoria = 'Intermediária'
    else:
        categoria = df_filial_mat.iloc[0]['categoria']
    
    # Modelos a testar
    modelos_teste = MODELOS_POR_CATEGORIA.get(categoria, ['NaiveModel'])
    
    resultados_modelos = []
    
    # Testar cada modelo
    for modelo_nome in modelos_teste:
        model = treinar_modelo(ts_treino, modelo_nome)
        
        if model is None:
            continue
        
        # Fazer forecast
        horizonte = len(df_teste)
        forecast = fazer_forecast(model, horizonte)
        
        if forecast is None:
            continue
        
        # Calcular métricas
        metricas = calcular_metricas(ts_teste, forecast)
        
        resultados_modelos.append({
            'modelo': modelo_nome,
            'mape': metricas['mape'],
            'mae': metricas['mae'],
            'rmse': metricas['rmse']
        })
    
    if not resultados_modelos:
        return None
    
    # Melhor modelo (menor MAPE)
    df_resultados = pd.DataFrame(resultados_modelos)
    melhor = df_resultados.loc[df_resultados['mape'].idxmin()]
    
    return {
        'filial': filial,
        'produto': produto,
        'categoria': categoria,
        'melhor_modelo': melhor['modelo'],
        'mape': melhor['mape'],
        'mae': melhor['mae'],
        'rmse': melhor['rmse'],
        'num_modelos_testados': len(resultados_modelos)
    }

# ============================================================================
# 6. EXECUTAR BACKTESTING
# ============================================================================

def executar_backtesting(df_historico, df_maturidade, data_limite):
    """Executa backtesting para todas as filiais + produtos"""
    
    print("\n" + "="*80)
    print("🧪 INICIANDO BACKTESTING DE MODELOS")
    print("="*80)
    
    filiais = df_historico['filial'].unique()
    produtos = df_historico['produto'].unique()
    
    total = len(filiais) * len(produtos)
    processados = 0
    resultados = []
    
    for filial in filiais:
        for produto in produtos:
            processados += 1
            
            # Mostrar progresso a cada 50
            if processados % 50 == 0:
                print(f"⏳ Progresso: {processados}/{total}")
            
            resultado = testar_filial_produto(
                filial, produto, df_historico, df_maturidade, data_limite
            )
            
            if resultado is not None:
                resultados.append(resultado)
    
    return pd.DataFrame(resultados)

# ============================================================================
# 7. ESTATÍSTICAS
# ============================================================================

def print_statistics(df_resultados):
    """Exibe estatísticas dos resultados"""
    
    print("\n" + "="*80)
    print("📊 ESTATÍSTICAS DO BACKTESTING")
    print("="*80)
    
    print(f"\n✓ Total de modelos testados: {len(df_resultados)}")
    print(f"✓ Filiais únicas: {df_resultados['filial'].nunique()}")
    print(f"✓ Produtos: {list(df_resultados['produto'].unique())}")
    
    print(f"\n✓ Distribuição de melhores modelos:")
    modelo_count = df_resultados['melhor_modelo'].value_counts()
    for modelo, count in modelo_count.items():
        pct = (count / len(df_resultados)) * 100
        print(f"   - {modelo:25}: {count:>4} ({pct:>5.1f}%)")
    
    print(f"\n✓ MAPE (Erro Percentual Médio Absoluto):")
    print(f"   - Mínimo: {df_resultados['mape'].min():.4f}")
    print(f"   - Máximo: {df_resultados['mape'].max():.4f}")
    print(f"   - Média:  {df_resultados['mape'].mean():.4f}")
    print(f"   - Mediana:{df_resultados['mape'].median():.4f}")
    
    print(f"\n✓ Top 10 piores MAPE:")
    worst = df_resultados.nlargest(10, 'mape')[['filial', 'produto', 'melhor_modelo', 'mape']]
    print(worst.to_string(index=False))
    
    print(f"\n✓ Top 10 melhores MAPE:")
    best = df_resultados.nsmallest(10, 'mape')[['filial', 'produto', 'melhor_modelo', 'mape']]
    print(best.to_string(index=False))

# ============================================================================
# 8. EXPORTAÇÃO
# ============================================================================

def export_resultados(df_resultados):
    """Exporta resultados para CSV"""
    
    print(f"\n💾 Exportando para: {OUTPUT_RESULTADOS}")
    
    # Ordenar por filial, produto
    df_export = df_resultados.sort_values(['filial', 'produto']).reset_index(drop=True)
    
    # Selecionar colunas principais
    df_export = df_export[['filial', 'produto', 'categoria', 'melhor_modelo', 'mape', 'mae', 'rmse']]
    
    df_export.to_csv(OUTPUT_RESULTADOS, index=False, encoding='utf-8')
    print(f"✅ Arquivo exportado com sucesso!")
    print(f"   Registros: {len(df_export)}")

# ============================================================================
# 9. EXECUÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal"""
    
    print("\n" + "="*80)
    print("🚀 SCRIPT #9: TESTAR MODELOS DARTS COM BACKTESTING")
    print("="*80)
    
    # Mostrar modelos disponíveis
    print(f"\n📦 Modelos disponíveis:")
    print(f"   ✓ ExponentialSmoothing")
    print(f"   ✓ ARIMA")
    print(f"   ✓ Prophet")
    if SEASONAL_NAIVE_AVAILABLE:
        print(f"   ✓ SeasonalNaiveModel")
    else:
        print(f"   ✗ SeasonalNaiveModel (não instalado)")
    if THETA_AVAILABLE:
        print(f"   ✓ Theta")
    else:
        print(f"   ✗ Theta (não instalado)")
    
    # Carregar dados
    df_historico, df_maturidade = load_data()
    
    # Calcular data limite
    data_maxima = df_historico['data'].max()
    data_limite = data_maxima - pd.DateOffset(months=7)
    
    print(f"\n📅 Data máxima: {data_maxima.date()}")
    print(f"📅 Data limite (teste): {data_limite.date()}")
    
    # Executar backtesting
    df_resultados = executar_backtesting(df_historico, df_maturidade, data_limite)
    
    # Estatísticas
    print_statistics(df_resultados)
    
    # Exportar
    export_resultados(df_resultados)
    
    print("\n" + "="*80)
    print("✨ Backtesting concluído!")
    print("="*80)
    
    return df_resultados

# ============================================================================

if __name__ == "__main__":
    df_resultado = main()
