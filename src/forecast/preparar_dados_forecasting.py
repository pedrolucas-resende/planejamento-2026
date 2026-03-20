"""
Script para preparar dados para forecasting com Darts:
Data, País, Estado, Cidade, Filial, Hierarquia_Urbana, Rank, População, Produto, Vendas

Melhorias aplicadas:
- Remoção de registros nulos (NaN)
- Padronização de datas para o último dia do mês
- Preenchimento de lacunas temporais (Zero-filling para meses sem venda)
- Garantia de continuidade da série para modelos globais
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# ============================================================================
# 1. CONFIGURAÇÃO
# ============================================================================

INPUT_FILE = "data/csv/input_o.csv"
OUTPUT_FILE = "data/csv/filial_produto_vendas_historico.csv"

VENDAS_COLUNAS = {
    "alugadas_0km": "0km",
    "alugadas_semi": "semi",
    "alugadas_usada": "usada"
}

COLUNAS_NECESSARIAS = [
    'dataValor', 'pais', 'estado', 'cidade', 'filial', 
    'hierarquia_urbana', 'populacao_cluster', 'populacao',
    'alugadas_0km', 'alugadas_semi', 'alugadas_usada'
]

# ============================================================================
# 2. FUNÇÕES DE SUPORTE
# ============================================================================

def load_and_clean(filepath):
    """Carrega o arquivo e remove nulos críticos"""
    print(f"📁 Lendo arquivo: {filepath}")
    df = pd.read_csv(filepath, encoding='utf-8-sig')
    
    # Remover linhas onde a filial ou data são nulas
    df = df.dropna(subset=['filial', 'dataValor'])
    
    # Padronizar data para o último dia do mês para consistência no Darts
    df['dataValor'] = pd.to_datetime(df['dataValor']) + pd.offsets.MonthEnd(0)
    
    return df

def ensure_full_time_series(df):
    """Garante que todas as filiais/produtos tenham todos os meses (preenche com 0)"""
    print("⏳ Padronizando séries temporais e preenchendo lacunas com zero...")
    
    # 1. Definir o range de datas completo do dataset
    all_months = pd.date_range(start=df['data'].min(), end=df['data'].max(), freq='ME')

    # 2. Obter informações estáticas para não perdê-las no merge
    static_info = df[['filial', 'produto', 'pais', 'estado', 'cidade', 'hierarquia_urbana', 'rank', 'populacao']].drop_duplicates(subset=['filial', 'produto'])

    # 3. Criar esqueleto de todas as combinações (Data x Filial x Produto)
    from itertools import product
    combinations = list(product(all_months, static_info['filial'].unique(), static_info['produto'].unique()))
    template = pd.DataFrame(combinations, columns=['data', 'filial', 'produto'])

    # 4. Trazer dados geográficos de volta para o esqueleto
    template = template.merge(static_info, on=['filial', 'produto'], how='left')

    # 5. Mesclar com as vendas reais
    df_final = template.merge(df, on=['data', 'filial', 'produto', 'pais', 'estado', 'cidade', 'hierarquia_urbana', 'rank', 'populacao'], how='left')
    
    # 6. Limpeza final dos valores nulos gerados pelo merge
    df_final['vendas'] = df_final['vendas'].fillna(0).astype(int)
    df_final['populacao'] = df_final['populacao'].fillna(0).astype(int)
    
    return df_final

def calcular_maturidade_filiais(df):
    """Analisa o tempo de casa de cada filial para sugerir modelos"""
    print("\n🔍 Analisando maturidade das filiais...")
    maturidade = []
    
    # Filtrar apenas onde vendas > 0 para saber quando a filial REALMENTE começou
    df_vendas_reais = df[df['vendas'] > 0]
    
    for filial in df['filial'].unique():
        df_f = df_vendas_reais[df_vendas_reais['filial'] == filial]
        
        if df_f.empty:
            dias_operacao, num_registros = 0, 0
            data_primeira = df['data'].min()
        else:
            data_primeira = df_f['data'].min()
            data_ultima = df_f['data'].max()
            dias_operacao = (data_ultima - data_primeira).days
            num_registros = len(df_f['data'].unique())
        
        if dias_operacao < 60:
            cat, mods = "Recém-aberta", "NaiveModel, MovingAverage"
        elif dias_operacao < 180:
            cat, mods = "Jovem", "ExponentialSmoothing, Prophet"
        elif dias_operacao < 360:
            cat, mods = "Intermediária", "AutoARIMA, Theta"
        else:
            cat, mods = "Madura", "XGBModel, LightGBM, NBEATS, TFT"
            
        maturidade.append({
            'filial': filial, 'data_primeira': data_primeira.date(),
            'dias_operacao': dias_operacao, 'categoria': cat, 'modelos': mods
        })
    
    return pd.DataFrame(maturidade)

# ============================================================================
# 3. EXECUÇÃO
# ============================================================================

def main():
    # Carregar
    df = load_and_clean(INPUT_FILE)
    
    # Selecionar e Filtrar (Cutoff de 7 meses para validação futura)
    data_max = df['dataValor'].max()
    data_limit = data_max - pd.DateOffset(months=7)
    df_hist = df[df['dataValor'] <= data_limit].copy()
    
    # Transformar para Long (Unpivot)
    df_long = df_hist.melt(
        id_vars=['dataValor', 'pais', 'estado', 'cidade', 'filial', 'hierarquia_urbana', 'populacao_cluster', 'populacao'],
        value_vars=list(VENDAS_COLUNAS.keys()),
        var_name='produto_raw', value_name='vendas'
    )
    df_long['produto'] = df_long['produto_raw'].map(VENDAS_COLUNAS)
    df_long = df_long.rename(columns={'dataValor': 'data', 'populacao_cluster': 'rank'}).drop('produto_raw', axis=1)

    # NOVO: Preencher meses faltantes e remover NaNs
    df_long = ensure_full_time_series(df_long)
    
    # Analisar Maturidade
    df_maturidade = calcular_maturidade_filiais(df_long)
    
    # Estatísticas Rápidas
    print(f"\n✅ Processamento concluído!")
    print(f"📊 Registros finais: {len(df_long)}")
    print(f"🏢 Filiais processadas: {df_long['filial'].nunique()}")
    print(f"📅 Período: {df_long['data'].min().date()} até {df_long['data'].max().date()}")

    # Exportar
    df_long.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    df_maturidade.to_csv(OUTPUT_FILE.replace('.csv', '_maturidade.csv'), index=False, encoding='utf-8-sig')
    
    print(f"\n💾 Arquivos salvos em: data/csv/")
    return df_long

if __name__ == "__main__":
    df_final = main()
