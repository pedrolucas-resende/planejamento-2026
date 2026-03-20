"""
Script para preparar dados para forecasting com Darts:
Consolidação de Hierarquia, Dados Operacionais e Alvos de Venda.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

# ============================================================================
# 1. CONFIGURAÇÃO
# ============================================================================

INPUT_FILE = "data/csv/input_o.csv"
OUTPUT_FILE = "data/csv/filial_produto_vendas_historico.csv"

# Mapeamento dos alvos de previsão (Target)
VENDAS_TARGETS = {
    'qtd_vendas_0km': '0km',
    'qtd_vendas_semi': 'semi',
    'qtd_vendas_usada': 'usada'
}

# Colunas que representam o estado da operação (Past Covariates)
COLUNAS_OPERACIONAIS = [
    'frota_op_total', 'manutencao_total', 'pronta_total', 
    'mec_total', 'mec_presentes', 'indisponivel_total', 'recebida_0km'
]

# Colunas geográficas e de cluster (Static Covariates)
COLUNAS_ESTATICAS = [
    'pais', 'estado', 'cidade', 'filial', 
    'hierarquia_urbana', 'populacao_cluster', 'populacao'
]

# ============================================================================
# 2. FUNÇÕES DE SUPORTE
# ============================================================================

def load_and_clean(filepath):
    """Carrega o arquivo e padroniza datas"""
    print(f"📁 Lendo arquivo: {filepath}")
    df = pd.read_csv(filepath, encoding='utf-8-sig')
    
    # Remover linhas críticas nulas
    df = df.dropna(subset=['filial', 'dataValor'])
    
    # Padronizar data para o último dia do mês (padrão Darts 'ME')
    df['dataValor'] = pd.to_datetime(df['dataValor']) + pd.offsets.MonthEnd(0)
    
    # Preencher NAs nas colunas operacionais com 0 (importante para o modelo)
    df[COLUNAS_OPERACIONAIS] = df[COLUNAS_OPERACIONAIS].fillna(0)
    
    return df

def ensure_full_time_series(df):
    """Garante continuidade temporal para cada combinação filial/produto"""
    print("⏳ Padronizando séries temporais e preenchendo lacunas...")
    
    all_months = pd.date_range(start=df['data'].min(), end=df['data'].max(), freq='ME')
    
    # Ajuste: Removi 'populacao_cluster' da lista estática pois ela já foi renomeada para 'rank'
    colunas_para_static = [c for c in COLUNAS_ESTATICAS if c != 'populacao_cluster'] + ['rank', 'produto']
    
    # Obter info estática para não perder no merge
    static_info = df[colunas_para_static].drop_duplicates(subset=['filial', 'produto'])

    # Criar esqueleto (Data x Filial x Produto)
    from itertools import product
    combinations = list(product(all_months, df['filial'].unique(), df['produto'].unique()))
    template = pd.DataFrame(combinations, columns=['data', 'filial', 'produto'])

    # Merges para reconstruir o dataset completo
    template = template.merge(static_info, on=['filial', 'produto'], how='left')
    
    # Merge com os dados de vendas e operacionais
    df_final = template.merge(df, on=['data', 'filial', 'produto'] + [c for c in colunas_para_static if c != 'produto'], how='left')
    
    # Preenchimento de zeros
    df_final['vendas'] = df_final['vendas'].fillna(0).astype(int)
    for col in COLUNAS_OPERACIONAIS:
        df_final[col] = df_final[col].fillna(0)
        
    return df_final

def calcular_maturidade_filiais(df):
    """Gera metadados sobre o tempo de operação de cada filial"""
    print("🔍 Analisando maturidade das filiais...")
    maturidade = []
    
    df_vendas_reais = df[df['vendas'] > 0]
    
    for filial in df['filial'].unique():
        df_f = df_vendas_reais[df_vendas_reais['filial'] == filial]
        
        if df_f.empty:
            dias_operacao = 0
            data_primeira = df['data'].min()
        else:
            data_primeira = df_f['data'].min()
            data_ultima = df_f['data'].max()
            dias_operacao = (data_ultima - data_primeira).days
        
        # Lógica de categorização para o Caio
        if dias_operacao < 60:
            cat = "Recém-aberta"
        elif dias_operacao < 180:
            cat = "Jovem"
        elif dias_operacao < 360:
            cat = "Intermediária"
        else:
            cat = "Madura"
            
        maturidade.append({
            'filial': filial, 'data_primeira': data_primeira.date(),
            'dias_operacao': dias_operacao, 'meses_operacao': dias_operacao / 30,
           'categoria': cat})
    
    return pd.DataFrame(maturidade)

# ============================================================================
# 3. EXECUÇÃO PRINCIPAL
# ============================================================================

def main():
    # 1. Carga
    df = load_and_clean(INPUT_FILE)
    
    # 2. Unpivot (Melt)
    id_vars = COLUNAS_ESTATICAS + COLUNAS_OPERACIONAIS + ['dataValor']
    
    df_long = df.melt(
        id_vars=id_vars,
        value_vars=list(VENDAS_TARGETS.keys()),
        var_name='produto_raw', 
        value_name='vendas'
    )
    
    # 3. Renomear ANTES de passar para a função de séries temporais
    df_long['produto'] = df_long['produto_raw'].map(VENDAS_TARGETS)
    df_long = df_long.rename(columns={'dataValor': 'data', 'populacao_cluster': 'rank'})
    df_long = df_long.drop('produto_raw', axis=1)

    # 4. Agora a função recebe os nomes já corrigidos ('data' e 'rank')
    df_long = ensure_full_time_series(df_long)
    
    # 5. Gerar análise de maturidade
    df_maturidade = calcular_maturidade_filiais(df_long)
    
    # 6. Exportação
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df_long.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    df_maturidade.to_csv(OUTPUT_FILE.replace('.csv', '_maturidade.csv'), index=False, encoding='utf-8-sig')
    
    print(f"\n✅ Processamento concluído sem erros!")

if __name__ == "__main__":
    main()
