"""
Script para preparar dados para forecasting com Darts:
Data, País, Estado, Cidade, Filial, Hierarquia_Urbana, Rank, População, Produto, Vendas

Estrutura final:
- data: Data do registro
- pais: País da operação
- estado: Estado/UF
- cidade: Cidade
- filial: Nome da filial
- hierarquia_urbana: Capital ou Interior
- rank: Rank populacional (cluster)
- populacao: População da cidade
- produto: Tipo de moto (0km, semi, usada, total)
- vendas: Quantidade de motos vendidas

Filtra dados até 2025-07 para usar como histórico no backtesting
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# ============================================================================
# 1. CONFIGURAÇÃO
# ============================================================================

INPUT_FILE = "data/csv/input_o.csv"
OUTPUT_FILE = "data/csv/filial_produto_vendas_historico.csv"

# Data máxima para histórico é calculada dinamicamente (7 meses atrás da data máxima dos dados)

# Colunas de vendas por tipo de veículo
VENDAS_COLUNAS = {
    "alugadas_0km": "0km",
    "alugadas_semi": "semi",
    "alugadas_usada": "usada",
    "alugadas_total": "total"
}

# Colunas necessárias
COLUNAS_NECESSARIAS = [
    'dataValor', 'pais', 'estado', 'cidade', 'filial', 
    'hierarquia_urbana', 'populacao_cluster', 'populacao',
    'alugadas_0km', 'alugadas_semi', 'alugadas_usada', 'alugadas_total'
]

# ============================================================================
# 2. CARREGAMENTO E LIMPEZA
# ============================================================================

def load_and_clean(filepath):
    """Carrega e limpa o arquivo input_o.csv"""
    print(f"📁 Lendo arquivo: {filepath}")
    
    df = pd.read_csv(filepath, encoding='utf-8-sig')
    
    print(f"✅ Arquivo carregado: {len(df)} linhas")
    
    return df

# ============================================================================
# 3. FILTRAR E TRANSFORMAR DADOS
# ============================================================================

def filter_and_transform(df):
    """
    Filtra dados: histórico é 7 meses atrás da data máxima, resto é para teste
    Transforma para formato longo
    """
    
    # Selecionar colunas necessárias
    df_selecionado = df[COLUNAS_NECESSARIAS].copy()
    
    # Converter data
    df_selecionado['dataValor'] = pd.to_datetime(df_selecionado['dataValor'])
    
    # Calcular data máxima e data limite (7 meses atrás)
    data_maxima_geral = df_selecionado['dataValor'].max()
    
    # Subtrair 7 meses
    data_limit = data_maxima_geral - pd.DateOffset(months=7)
    
    print(f"\n📅 Data máxima dos dados: {data_maxima_geral.date()}")
    print(f"📅 Cutoff (7 meses atrás): {data_limit.date()}")
    print(f"🔄 Filtrando histórico até {data_limit.date()}...")
    print(f"🔄 Dados de teste de {(data_limit + pd.DateOffset(days=1)).date()} até {data_maxima_geral.date()}")
    
    # Filtrar até data limite
    df_filtrado = df_selecionado[df_selecionado['dataValor'] <= data_limit].copy()
    
    print(f"✅ Dados filtrados: {len(df_filtrado)} registros")
    print(f"   Período: {df_filtrado['dataValor'].min().date()} até {df_filtrado['dataValor'].max().date()}")
    
    # Transformar para formato longo (unpivot)
    print("\n🔄 Transformando para formato longo...")
    
    df_long = df_filtrado.melt(
        id_vars=['dataValor', 'pais', 'estado', 'cidade', 'filial', 
                 'hierarquia_urbana', 'populacao_cluster', 'populacao'],
        value_vars=list(VENDAS_COLUNAS.keys()),
        var_name='tipo_original',
        value_name='vendas'
    )
    
    # Mapear tipos de veículos
    df_long['produto'] = df_long['tipo_original'].map(VENDAS_COLUNAS)
    df_long = df_long.drop('tipo_original', axis=1)

    df_long = df_long[df_long['produto'] != 'total'].copy()
    
    # Renomear colunas
    df_long = df_long.rename(columns={
        'dataValor': 'data',
        'populacao_cluster': 'rank'
    })
    
    # Reordenar colunas
    df_long = df_long[['data', 'pais', 'estado', 'cidade', 'filial', 
                       'hierarquia_urbana', 'rank', 'populacao', 'produto', 'vendas']]
    
    # Converter vendas para número
    df_long['vendas'] = pd.to_numeric(df_long['vendas'], errors='coerce').fillna(0).astype(int)
    df_long['populacao'] = pd.to_numeric(df_long['populacao'], errors='coerce').fillna(0).astype(int)
    
    # Ordenar por filial, produto, data
    df_long = df_long.sort_values(['filial', 'produto', 'data']).reset_index(drop=True)
    
    print(f"✅ Transformação concluída: {len(df_long)} registros")
    
    return df_long, data_limit, data_maxima_geral

# ============================================================================
# 4. ANÁLISE DE MATURIDADE DAS FILIAIS
# ============================================================================

def calcular_maturidade_filiais(df):
    """
    Calcula dias de operação e número de registros por filial
    """
    
    print("\n🔍 Analisando maturidade das filiais...")
    
    maturidade = []
    
    for filial in df['filial'].unique():
        df_filial = df[df['filial'] == filial]
        
        data_primeira = df_filial['data'].min()
        data_ultima = df_filial['data'].max()
        dias_operacao = (data_ultima - data_primeira).days
        num_registros = len(df_filial)
        
        # Categoria de maturidade
        if dias_operacao < 2*30 or num_registros < 12:
            categoria = "Recém-aberta"
            modelos = ["NaiveModel", "NaiveMovingAverage"]
        elif dias_operacao < 6*30:
            categoria = "Jovem"
            modelos = ["NaiveDrift", "ExponentialSmoothing"]
        elif dias_operacao < 12*30:
            categoria = "Intermediária"
            modelos = ["AutoARIMA", "Theta"]
        else:
            categoria = "Madura"
            modelos = ['XGBModel', 'LightGBMModel', 'NBEATSModel', 'TFTModel']
        
        maturidade.append({
            'filial': filial,
            'data_primeira': data_primeira.date(),
            'data_ultima': data_ultima.date(),
            'dias_operacao': dias_operacao,
            'num_registros': num_registros,
            'categoria': categoria,
            'modelos_recomendados': ', '.join(modelos)
        })
    
    df_maturidade = pd.DataFrame(maturidade).sort_values('dias_operacao')
    
    print(f"\n✅ Análise concluída: {len(df_maturidade)} filiais")
    
    return df_maturidade

# ============================================================================
# 5. ESTATÍSTICAS
# ============================================================================

def print_statistics(df, df_maturidade):
    """Exibe estatísticas do dataset"""
    
    print("\n" + "="*80)
    print("📊 ESTATÍSTICAS DO DATASET")
    print("="*80)
    
    print(f"\n✓ Total de registros: {len(df):,}")
    print(f"✓ Período: {df['data'].min().date()} até {df['data'].max().date()}")
    print(f"✓ Filiais únicas: {df['filial'].nunique()}")
    print(f"✓ Cidades únicas: {df['cidade'].nunique()}")
    print(f"✓ Produtos: {list(df['produto'].unique())}")
    print(f"✓ Países: {list(df['pais'].unique())}")
    
    print(f"\n✓ Total de vendas por produto:")
    vendas_produto = df[df['produto'] != 'total'].groupby('produto')['vendas'].sum().sort_values(ascending=False)
    for produto, vendas in vendas_produto.items():
        print(f"   - {produto:10}: {vendas:>15,}")
    
    print(f"\n✓ Distribuição de filiais por categoria de maturidade:")
    cat_count = df_maturidade['categoria'].value_counts()
    for categoria, count in cat_count.items():
        print(f"   - {categoria:20}: {count:>3} filiais")
    
    print(f"\n✓ Top 10 Filiais (por dias de operação):")
    for _, row in df_maturidade.tail(10).iterrows():
        print(f"   {row['filial']:40} | {row['dias_operacao']:>4}d | {row['categoria']:15} | {row['modelos_recomendados']}")

# ============================================================================
# 6. EXPORTAÇÃO
# ============================================================================

def export_csv(df, output_filepath):
    """Exporta dataset para CSV"""
    
    print(f"\n💾 Exportando para: {output_filepath}")
    df.to_csv(output_filepath, index=False, encoding='utf-8')
    print(f"✅ Arquivo exportado com sucesso!")
    print(f"   Colunas: {', '.join(df.columns)}")
    print(f"   Primeiras linhas:")
    print(df.head(10).to_string(index=False))

# ============================================================================
# 7. EXECUÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal"""
    
    print("\n" + "="*80)
    print("🚀 PREPARAÇÃO DE DADOS: input_o → filial_produto_vendas_historico")
    print("="*80)
    
    # Carregar dados
    df = load_and_clean(INPUT_FILE)
    
    # Filtrar e transformar
    df_transformado, data_limite_historico, data_maxima_geral = filter_and_transform(df)
    
    # Analisar maturidade
    df_maturidade = calcular_maturidade_filiais(df_transformado)
    
    # Exibir estatísticas
    print_statistics(df_transformado, df_maturidade)
    
    # Exportar resultado
    export_csv(df_transformado, OUTPUT_FILE)
    
    # Salvar também a tabela de maturidade
    maturidade_file = OUTPUT_FILE.replace('.csv', '_maturidade.csv')
    df_maturidade.to_csv(maturidade_file, index=False, encoding='utf-8')
    print(f"\n💾 Tabela de maturidade salva em: {maturidade_file}")
    
    print("\n" + "="*80)
    print("✨ Processo concluído com sucesso!")
    print("="*80)
    print(f"\n📌 Próximos passos:")
    print(f"   1. Usar {OUTPUT_FILE} para backtesting")
    print(f"   2. Script #9: Testar modelos Darts (após {data_limite_historico.date()} até {data_maxima_geral.date()})")
    print(f"   3. Script #10: Forecasting produção (Histórico: até {data_maxima_geral.date()})")
    
    return df_transformado, df_maturidade, data_limite_historico, data_maxima_geral

# ============================================================================

if __name__ == "__main__":
    df_resultado, df_maturidade, data_limite, data_maxima = main()
